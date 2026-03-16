from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from .config import settings
from .job_manager import JobManager
from .job_runner import JobRunner
from .realtime import RealtimeHub
from .schemas import (
    JobHistoryItem,
    JobStatus,
    JobStatusResponse,
    MetricsResponse,
    ProcessMode,
    ProcessStartResponse,
    ResultsResponse,
)
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


def _has_allowed_extension(filename: str, allowed: tuple[str, ...]) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in allowed)


def _validate_file_extension(upload: UploadFile, allowed: tuple[str, ...], field_name: str) -> None:
    name = (upload.filename or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail=f"{field_name} sem nome válido")
    if not _has_allowed_extension(name, allowed):
        allowed_list = " ou ".join(allowed)
        raise HTTPException(status_code=400, detail=f"{field_name} deve ser {allowed_list}")


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
    report_file: UploadFile | None = File(None),
    analysis_year: int = 2025,
    process_mode: ProcessMode = Form(ProcessMode.standard),
    open_titles_file: UploadFile | None = File(None),
):
    if analysis_year < settings.min_year or analysis_year > settings.max_year:
        raise HTTPException(status_code=400, detail=f"analysis_year deve estar entre {settings.min_year} e {settings.max_year}")

    _validate_file_extension(base_file, (".xlsx",), "base_file")

    if process_mode == ProcessMode.standard:
        if report_file is None:
            raise HTTPException(status_code=400, detail="report_file é obrigatório para o modo padrão")
        _validate_file_extension(report_file, (".xls", ".xlsx"), "report_file")
        if open_titles_file is not None:
            raise HTTPException(status_code=400, detail="open_titles_file deve ser omitido no modo padrão")
    else:
        if open_titles_file is None:
            raise HTTPException(status_code=400, detail="open_titles_file é obrigatório para o modo de títulos em aberto")
        _validate_file_extension(open_titles_file, (".xls", ".xlsx"), "open_titles_file")

    job_manager: JobManager = request.app.state.job_manager
    runner: JobRunner = request.app.state.job_runner

    user_id = _get_user_id(request)

    try:
        job = job_manager.create_job(
            user_id=user_id,
            analysis_year=analysis_year,
            base_filename=base_file.filename or "base.xlsx",
            report_filename=report_file.filename or "report.xls" if report_file else "report.xls",
            process_mode=process_mode,
            open_titles_filename=open_titles_file.filename if open_titles_file else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    paths = create_job_paths(
        job.job_id,
        job.base_filename,
        job.report_filename,
        open_titles_filename=open_titles_file.filename if open_titles_file else None,
    )
    job_manager.set_paths(
        job.job_id,
        paths["job_dir"],
        paths["input_path"],
        paths["report_path"],
        paths["output_path"],
        open_titles_path=paths.get("open_titles_path"),
    )

    try:
        await _save_upload(base_file, paths["input_path"], settings.max_upload_bytes)
        if report_file is not None:
            await _save_upload(report_file, paths["report_path"], settings.max_upload_bytes)
        if open_titles_file is not None and paths.get("open_titles_path"):
            await _save_upload(open_titles_file, paths["open_titles_path"], settings.max_upload_bytes)
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
        process_mode=process_mode,
        open_titles_path=paths.get("open_titles_path"),
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
        process_mode=job.process_mode,
    )


@router.get("/api/process/history", response_model=list[JobHistoryItem])
async def get_history(request: Request, limit: int = 20):
    job_manager: JobManager = request.app.state.job_manager
    user_id = _get_user_id(request)
    jobs = job_manager.list_jobs_for_user(user_id=user_id, limit=limit)
    return [
        JobHistoryItem(
            job_id=job.job_id,
            status=job.status,
            analysis_year=job.analysis_year,
            base_filename=job.base_filename,
            report_filename=job.report_filename,
            process_mode=job.process_mode,
            progress=job.progress,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error=job.error,
        )
        for job in jobs
    ]


@router.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics(request: Request):
    job_manager: JobManager = request.app.state.job_manager
    metrics = job_manager.get_metrics()
    return MetricsResponse(**metrics)


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
            "process_mode": job.process_mode.value,
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
        filename=f"Job_Processo_{job.analysis_year}.xlsx",
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
        filename=f"Job_Processo_{job.analysis_year}.pdf",
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
