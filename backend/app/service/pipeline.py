from __future__ import annotations

import logging
from pathlib import Path

from ..job_manager import JobManager
from ..realtime import RealtimeHub
from ..schemas import ProcessMode
from .midas_correlation import run_midas_correlation


class _JobLogHandler(logging.Handler):
    def __init__(self, job_id: str, realtime: RealtimeHub) -> None:
        super().__init__()
        self.job_id = job_id
        self.realtime = realtime

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        self.realtime.log(self.job_id, record.levelname, message)


def run_legacy_pipeline(
    job_id: str,
    input_path: str,
    report_path: str,
    output_path: str,
    analysis_year: int,
    process_mode: ProcessMode,
    open_titles_path: str | None,
    job_manager: JobManager,
    realtime: RealtimeHub,
) -> None:
    from desktop import main as legacy_main
    from desktop.utils import logger as legacy_logger

    handler = _JobLogHandler(job_id, realtime)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    legacy_logger.addHandler(handler)

    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        def progress_callback(value: float) -> None:
            job_manager.set_progress(job_id, value)
            realtime.progress(job_id, value)

        legacy_main.main(
            input_file=input_path,
            report_file=report_path,
            output_file=output_path,
            analysis_year=analysis_year,
            process_mode=process_mode,
            open_titles_file=open_titles_path,
            progress_callback=progress_callback,
        )
    finally:
        legacy_logger.removeHandler(handler)


def run_midas_pipeline(
    job_id: str,
    midas_path: str,
    source_conciliation_output_path: str,
    output_path: str,
    job_manager: JobManager,
    realtime: RealtimeHub,
) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    job_manager.set_progress(job_id, 0.2)
    realtime.progress(job_id, 0.2)

    stats = run_midas_correlation(
        midas_path=midas_path,
        conciliation_output_path=source_conciliation_output_path,
        output_path=output_path,
    )

    realtime.log(job_id, "INFO", f"Correlação Midas concluída: {stats}")
    job_manager.set_progress(job_id, 0.95)
    realtime.progress(job_id, 0.95)

