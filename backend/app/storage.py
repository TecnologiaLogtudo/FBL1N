from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path

BASE_DIR = Path(os.getenv("JOBS_BASE_DIR") or Path(tempfile.gettempdir()) / "notas_compensadas")


def _sanitize_filename(filename: str) -> str:
    base = os.path.basename(filename)
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)


def create_job_paths(job_id: str, base_filename: str, report_filename: str) -> dict[str, str]:
    job_dir = BASE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_path = job_dir / _sanitize_filename(base_filename)
    report_path = job_dir / _sanitize_filename(report_filename)
    output_path = job_dir / "dados_estruturados.xlsx"

    return {
        "job_dir": str(job_dir),
        "input_path": str(input_path),
        "report_path": str(report_path),
        "output_path": str(output_path),
    }


def delete_job_dir(job_dir: str | None) -> None:
    if not job_dir:
        return
    shutil.rmtree(job_dir, ignore_errors=True)
