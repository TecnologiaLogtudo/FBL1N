from __future__ import annotations

import traceback
from concurrent.futures import ThreadPoolExecutor

from .job_manager import JobManager
from .schemas import ProcessMode
from .realtime import RealtimeHub
from .service.pipeline import run_legacy_pipeline


class JobRunner:
    def __init__(self, job_manager: JobManager, realtime: RealtimeHub, max_workers: int = 2) -> None:
        self._job_manager = job_manager
        self._realtime = realtime
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(
        self,
        job_id: str,
        input_path: str,
        report_path: str,
        output_path: str,
        analysis_year: int,
        process_mode: ProcessMode,
        open_titles_path: str | None = None,
    ) -> None:
        self._executor.submit(
            self._run,
            job_id,
            input_path,
            report_path,
            output_path,
            analysis_year,
            process_mode,
            open_titles_path,
        )

    def _run(
        self,
        job_id: str,
        input_path: str,
        report_path: str,
        output_path: str,
        analysis_year: int,
        process_mode: ProcessMode,
        open_titles_path: str | None,
    ) -> None:
        self._job_manager.set_running(job_id)
        self._realtime.status(job_id, "running")

        try:
            run_legacy_pipeline(
                job_id=job_id,
                input_path=input_path,
                report_path=report_path,
                output_path=output_path,
                analysis_year=analysis_year,
                process_mode=process_mode,
                open_titles_path=open_titles_path,
                job_manager=self._job_manager,
                realtime=self._realtime,
            )
            self._job_manager.set_completed(job_id)
            self._realtime.status(job_id, "completed")
            self._realtime.done(job_id)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            error = f"{exc}\n{traceback.format_exc()}"
            self._job_manager.set_failed(job_id, error)
            self._realtime.status(job_id, "failed")
            self._realtime.error(job_id, str(exc))
