from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from .config import settings
from .job_manager import JobManager
from .job_runner import JobRunner
from .realtime import RealtimeHub
from .schemas import JobStatus, JobStatusResponse, ProcessStartResponse, ResultsResponse
from .service.pdf_export import generate_pdf_from_output
from .service.result_parser import parse_results
from .storage import create_job_paths

router = APIRouter()


def _get_user_id(request: Request) -> str:
    x_user_id = request.headers.get("X-User-Id")
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"


def _ensure_job(job_manager: JobManager, job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job


async def _save_upload(upload: UploadFile, destination: str, max_bytes: int) -> None:
    total = 0
    with open(destination, "wb") as buffer:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise HTTPException(status_code=413, detail="Arquivo excede limite de 25MB")
            buffer.write(chunk)


def _validate_extensions(base_file: UploadFile, report_file: UploadFile) -> None:
    base_name = (base_file.filename or "").lower()
    report_name = (report_file.filename or "").lower()

    if not base_name.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="base_file deve ser .xlsx")
    if not (report_name.endswith(".xls") or report_name.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="report_file deve ser .xls ou .xlsx")


@router.get("/health/live")
async def health_live() -> dict:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/ready")
async def health_ready() -> dict:
    return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/api/process", response_model=ProcessStartResponse, status_code=202)
async def start_process(
    request: Request,
    base_file: UploadFile = File(...),
    report_file: UploadFile = File(...),
    analysis_year: int = 2025,
):
    if analysis_year < settings.min_year or analysis_year > settings.max_year:
        raise HTTPException(status_code=400, detail=f"analysis_year deve estar entre {settings.min_year} e {settings.max_year}")

    _validate_extensions(base_file, report_file)

    job_manager: JobManager = request.app.state.job_manager
    runner: JobRunner = request.app.state.job_runner

    user_id = _get_user_id(request)

    try:
        job = job_manager.create_job(
            user_id=user_id,
            analysis_year=analysis_year,
            base_filename=base_file.filename or "base.xlsx",
            report_filename=report_file.filename or "report.xls",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    paths = create_job_paths(job.job_id, job.base_filename, job.report_filename)
    job_manager.set_paths(job.job_id, paths["job_dir"], paths["input_path"], paths["report_path"], paths["output_path"])

    try:
        await _save_upload(base_file, paths["input_path"], settings.max_upload_bytes)
        await _save_upload(report_file, paths["report_path"], settings.max_upload_bytes)
    except Exception:
        from .storage import delete_job_dir

        delete_job_dir(paths["job_dir"])
        job_manager.remove_job(job.job_id)
        raise

    runner.submit(
        job_id=job.job_id,
        input_path=paths["input_path"],
        report_path=paths["report_path"],
        output_path=paths["output_path"],
        analysis_year=analysis_year,
    )

    return ProcessStartResponse(job_id=job.job_id, status=JobStatus.queued)


@router.get("/api/process/{job_id}/status", response_model=JobStatusResponse)
async def get_status(request: Request, job_id: str):
    job_manager: JobManager = request.app.state.job_manager
    job = _ensure_job(job_manager, job_id)
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error=job.error,
    )


@router.get("/api/process/{job_id}/results", response_model=ResultsResponse)
async def get_results(request: Request, job_id: str):
    job_manager: JobManager = request.app.state.job_manager
    job = _ensure_job(job_manager, job_id)

    if job.status != JobStatus.completed:
        raise HTTPException(status_code=409, detail="Resultados disponíveis apenas quando status=completed")

    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="Arquivo de saída não encontrado")

    payload = parse_results(job.output_path)
    payload["meta"].update(
        {
            "job_id": job.job_id,
            "created_at": job.created_at.isoformat(),
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }
    )
    return ResultsResponse(**payload)


@router.get("/api/process/{job_id}/download/xlsx")
async def download_xlsx(request: Request, job_id: str):
    job_manager: JobManager = request.app.state.job_manager
    job = _ensure_job(job_manager, job_id)

    if job.status != JobStatus.completed:
        raise HTTPException(status_code=409, detail="Download disponível apenas quando status=completed")

    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="Arquivo de saída não encontrado")

    return FileResponse(
        path=job.output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"dados_estruturados_{job.job_id}.xlsx",
    )


@router.get("/api/process/{job_id}/download/pdf")
async def download_pdf(request: Request, job_id: str):
    job_manager: JobManager = request.app.state.job_manager
    job = _ensure_job(job_manager, job_id)

    if job.status != JobStatus.completed:
        raise HTTPException(status_code=409, detail="Download disponível apenas quando status=completed")

    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="Arquivo de saída não encontrado")

    pdf_path = str(Path(job.output_path).with_suffix(".pdf"))
    generate_pdf_from_output(job.output_path, pdf_path)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"resumo_conciliacao_{job.job_id}.pdf",
    )


@router.websocket("/ws/jobs/{job_id}")
async def ws_job_updates(websocket: WebSocket, job_id: str):
    realtime: RealtimeHub = websocket.app.state.realtime
    job_manager: JobManager = websocket.app.state.job_manager
    await realtime.connect(job_id, websocket)

    job = job_manager.get_job(job_id)
    if job:
        await websocket.send_json({"type": "status", "status": job.status})
        await websocket.send_json({"type": "progress", "value": job.progress})

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime.disconnect(job_id, websocket)
