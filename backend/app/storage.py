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


def create_job_paths(
    job_id: str,
    base_filename: str,
    report_filename: str,
    open_titles_filename: str | None = None,
) -> dict[str, str | None]:
    job_dir = BASE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_path = job_dir / _sanitize_filename(base_filename)
    report_path = job_dir / _sanitize_filename(report_filename)
    output_path = job_dir / "dados_estruturados.xlsx"
    open_titles_path = (
        job_dir / _sanitize_filename(open_titles_filename) if open_titles_filename else None
    )

    return {
        "job_dir": str(job_dir),
        "input_path": str(input_path),
        "report_path": str(report_path),
        "output_path": str(output_path),
        "open_titles_path": str(open_titles_path) if open_titles_path else None,
    }


def delete_job_dir(job_dir: str | None) -> None:
    if not job_dir:
        return
    shutil.rmtree(job_dir, ignore_errors=True)
