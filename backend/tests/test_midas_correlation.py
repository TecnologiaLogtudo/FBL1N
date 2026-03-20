from __future__ import annotations

from io import BytesIO
from pathlib import Path
import shutil
from uuid import uuid4

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas import ProcessMode


def _xlsx_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()


def _create_source_job(
    app,
    *,
    user_id: str,
    output_path: str,
    process_mode: ProcessMode = ProcessMode.standard,
    completed: bool = True,
):
    manager = app.state.job_manager
    job = manager.create_job(
        user_id=user_id,
        analysis_year=2025,
        base_filename="base.xlsx",
        report_filename="report.xls",
        process_mode=process_mode,
    )
    manager.set_paths(
        job_id=job.job_id,
        job_dir=str(Path(output_path).parent),
        input_path=str(Path(output_path).parent / "base.xlsx"),
        report_path=str(Path(output_path).parent / "report.xls"),
        output_path=output_path,
    )
    if completed:
        manager.set_completed(job.job_id)
    return job


def _run_jobs_inline(app) -> None:
    runner = app.state.job_runner

    def _submit(**kwargs):
        runner._run(
            kwargs["job_id"],
            kwargs["input_path"],
            kwargs["report_path"],
            kwargs["output_path"],
            kwargs["analysis_year"],
            kwargs["process_mode"],
            kwargs.get("open_titles_path"),
            kwargs.get("midas_path"),
            kwargs.get("source_conciliation_output_path"),
        )

    runner.submit = _submit  # type: ignore[assignment]


def _make_test_dir() -> Path:
    test_dir = Path("backend/tests/.tmp_midas") / str(uuid4())
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def test_midas_correlation_happy_path() -> None:
    test_dir = _make_test_dir()
    try:
        conciliation_output = test_dir / "conciliation.xlsx"
        pd.DataFrame({"CTRC": ["00123", "456"]}).to_excel(conciliation_output, sheet_name="Resumo Consolidado", index=False)

        app = create_app()
        _run_jobs_inline(app)
        source_job = _create_source_job(app, user_id="u1", output_path=str(conciliation_output))
        client = TestClient(app)

        midas_df = pd.DataFrame({"Número": ["123", "999"], "Status": ["ok", "ok"]})
        response = client.post(
            "/api/midas/correlate",
            data={"conciliation_job_id": source_job.job_id},
            files={
                "midas_file": (
                    "midas.xlsx",
                    _xlsx_bytes(midas_df),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers={"X-User-Id": "u1"},
        )

        assert response.status_code == 202
        job_id = response.json()["job_id"]
        job = app.state.job_manager.get_job(job_id)
        assert job is not None
        assert job.status.value == "completed"
        assert job.output_path is not None
        assert Path(job.output_path).exists()

        output_df = pd.read_excel(job.output_path)
        assert "Condição" in output_df.columns
        assert output_df["Condição"].tolist() == ["Pendente Pagamento", "-"]
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_midas_correlation_accepts_ctrc_header_on_third_row() -> None:
    test_dir = _make_test_dir()
    try:
        conciliation_output = test_dir / "conciliation_l3.xlsx"
        with pd.ExcelWriter(conciliation_output, engine="openpyxl") as writer:
            pd.DataFrame({"A": ["meta1"], "B": ["meta1"]}).to_excel(
                writer, sheet_name="Resumo Consolidado", index=False, header=False
            )
            pd.DataFrame({"A": ["meta2"], "B": ["meta2"]}).to_excel(
                writer, sheet_name="Resumo Consolidado", index=False, header=False, startrow=1
            )
            pd.DataFrame({"CTRC": ["00123", "456"]}).to_excel(
                writer, sheet_name="Resumo Consolidado", index=False, startrow=2
            )

        app = create_app()
        _run_jobs_inline(app)
        source_job = _create_source_job(app, user_id="u1", output_path=str(conciliation_output))
        client = TestClient(app)

        midas_df = pd.DataFrame({"Número": ["123", "999"]})
        response = client.post(
            "/api/midas/correlate",
            data={"conciliation_job_id": source_job.job_id},
            files={
                "midas_file": (
                    "midas.xlsx",
                    _xlsx_bytes(midas_df),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers={"X-User-Id": "u1"},
        )

        assert response.status_code == 202
        job = app.state.job_manager.get_job(response.json()["job_id"])
        assert job is not None
        assert job.output_path is not None
        output_df = pd.read_excel(job.output_path)
        assert output_df["Condição"].tolist() == ["Pendente Pagamento", "-"]
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_midas_correlation_requires_completed_source_job() -> None:
    test_dir = _make_test_dir()
    try:
        conciliation_output = test_dir / "conciliation.xlsx"
        pd.DataFrame({"CTRC": ["1"]}).to_excel(conciliation_output, sheet_name="Resumo Consolidado", index=False)

        app = create_app()
        source_job = _create_source_job(app, user_id="u1", output_path=str(conciliation_output), completed=False)
        client = TestClient(app)

        response = client.post(
            "/api/midas/correlate",
            data={"conciliation_job_id": source_job.job_id},
            files={
                "midas_file": (
                    "midas.xlsx",
                    _xlsx_bytes(pd.DataFrame({"Número": ["1"]})),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers={"X-User-Id": "u1"},
        )
        assert response.status_code == 409
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_midas_correlation_source_job_not_found() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/midas/correlate",
        data={"conciliation_job_id": "job-inexistente"},
        files={
            "midas_file": (
                "midas.xlsx",
                _xlsx_bytes(pd.DataFrame({"Número": ["1"]})),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"X-User-Id": "u1"},
    )
    assert response.status_code == 404


def test_midas_correlation_requires_standard_source_job() -> None:
    test_dir = _make_test_dir()
    try:
        conciliation_output = test_dir / "conciliation.xlsx"
        pd.DataFrame({"CTRC": ["1"]}).to_excel(conciliation_output, sheet_name="Resumo Consolidado", index=False)

        app = create_app()
        source_job = _create_source_job(
            app,
            user_id="u1",
            output_path=str(conciliation_output),
            process_mode=ProcessMode.open_titles,
        )
        client = TestClient(app)

        response = client.post(
            "/api/midas/correlate",
            data={"conciliation_job_id": source_job.job_id},
            files={
                "midas_file": (
                    "midas.xlsx",
                    _xlsx_bytes(pd.DataFrame({"Número": ["1"]})),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers={"X-User-Id": "u1"},
        )
        assert response.status_code == 400
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_midas_correlation_requires_midas_numero_column() -> None:
    test_dir = _make_test_dir()
    try:
        conciliation_output = test_dir / "conciliation.xlsx"
        pd.DataFrame({"CTRC": ["1"]}).to_excel(conciliation_output, sheet_name="Resumo Consolidado", index=False)

        app = create_app()
        source_job = _create_source_job(app, user_id="u1", output_path=str(conciliation_output))
        client = TestClient(app)

        response = client.post(
            "/api/midas/correlate",
            data={"conciliation_job_id": source_job.job_id},
            files={
                "midas_file": (
                    "midas.xlsx",
                    _xlsx_bytes(pd.DataFrame({"Outra Coluna": ["1"]})),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers={"X-User-Id": "u1"},
        )
        assert response.status_code == 400
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_midas_correlation_pdf_not_supported() -> None:
    test_dir = _make_test_dir()
    try:
        conciliation_output = test_dir / "conciliation.xlsx"
        pd.DataFrame({"CTRC": ["00123"]}).to_excel(conciliation_output, sheet_name="Resumo Consolidado", index=False)

        app = create_app()
        _run_jobs_inline(app)
        source_job = _create_source_job(app, user_id="u1", output_path=str(conciliation_output))
        client = TestClient(app)

        start = client.post(
            "/api/midas/correlate",
            data={"conciliation_job_id": source_job.job_id},
            files={
                "midas_file": (
                    "midas.xlsx",
                    _xlsx_bytes(pd.DataFrame({"Número": ["123"]})),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            headers={"X-User-Id": "u1"},
        )
        assert start.status_code == 202
        job_id = start.json()["job_id"]

        pdf = client.get(f"/api/process/{job_id}/download/pdf")
        assert pdf.status_code == 409
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
