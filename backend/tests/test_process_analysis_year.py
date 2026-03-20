from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import create_app


def _xlsx_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()


def test_start_process_uses_analysis_year_from_form_data() -> None:
    app = create_app()
    app.state.job_runner.submit = lambda **kwargs: None  # type: ignore[assignment]
    client = TestClient(app)

    response = client.post(
        "/api/process",
        data={"analysis_year": "2026", "process_mode": "standard"},
        files={
            "base_file": (
                "base.xlsx",
                _xlsx_bytes(pd.DataFrame({"Conta": [1]})),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            "report_file": (
                "report.xlsx",
                _xlsx_bytes(pd.DataFrame({"CTRC": [1]})),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        },
        headers={"X-User-Id": "u-ano"},
    )

    assert response.status_code == 202
    job_id = response.json()["job_id"]
    job = app.state.job_manager.get_job(job_id)
    assert job is not None
    assert job.analysis_year == 2026

