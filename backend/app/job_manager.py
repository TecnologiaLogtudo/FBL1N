from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Dict
from uuid import uuid4

from .schemas import JobStatus


@dataclass
class JobRecord:
    job_id: str
    user_id: str
    analysis_year: int
    base_filename: str
    report_filename: str
    status: JobStatus = JobStatus.queued
    progress: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    job_dir: str | None = None
    input_path: str | None = None
    report_path: str | None = None
    output_path: str | None = None


class JobManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: Dict[str, JobRecord] = {}

    def create_job(self, user_id: str, analysis_year: int, base_filename: str, report_filename: str) -> JobRecord:
        with self._lock:
            for record in self._jobs.values():
                if record.user_id == user_id and record.status in {JobStatus.queued, JobStatus.running}:
                    raise ValueError("Usuário já possui um job em execução")

            job = JobRecord(
                job_id=str(uuid4()),
                user_id=user_id,
                analysis_year=analysis_year,
                base_filename=base_filename,
                report_filename=report_filename,
            )
            self._jobs[job.job_id] = job
            return job

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def set_paths(self, job_id: str, job_dir: str, input_path: str, report_path: str, output_path: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.job_dir = job_dir
            job.input_path = input_path
            job.report_path = report_path
            job.output_path = output_path

    def set_running(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.running
            job.started_at = datetime.now(timezone.utc)
            job.progress = 0.01

    def set_progress(self, job_id: str, value: float) -> None:
        with self._lock:
            job = self._jobs[job_id]
            if job.status == JobStatus.running:
                job.progress = max(0.0, min(1.0, value))

    def set_completed(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.completed
            job.progress = 1.0
            job.finished_at = datetime.now(timezone.utc)

    def set_failed(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.failed
            job.error = error
            job.finished_at = datetime.now(timezone.utc)

    def remove_job(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)

    def expire_jobs(self, ttl_seconds: int) -> list[JobRecord]:
        now = datetime.now(timezone.utc)
        expired: list[JobRecord] = []

        with self._lock:
            for job in self._jobs.values():
                if job.status in {JobStatus.queued, JobStatus.running, JobStatus.expired}:
                    continue
                reference = job.finished_at or job.created_at
                age = (now - reference).total_seconds()
                if age >= ttl_seconds:
                    job.status = JobStatus.expired
                    expired.append(job)

        return expired

    def list_jobs_for_user(self, user_id: str, limit: int = 20) -> list[JobRecord]:
        with self._lock:
            items = [job for job in self._jobs.values() if job.user_id == user_id]
            items.sort(key=lambda job: job.created_at, reverse=True)
            return items[: max(1, min(limit, 100))]

    def get_metrics(self) -> dict[str, float | int]:
        with self._lock:
            total_jobs = len(self._jobs)
            active_jobs = sum(1 for job in self._jobs.values() if job.status in {JobStatus.queued, JobStatus.running})
            completed_jobs = sum(1 for job in self._jobs.values() if job.status == JobStatus.completed)
            failed_jobs = sum(1 for job in self._jobs.values() if job.status == JobStatus.failed)
            expired_jobs = sum(1 for job in self._jobs.values() if job.status == JobStatus.expired)

            durations = []
            for job in self._jobs.values():
                if job.started_at and job.finished_at:
                    durations.append((job.finished_at - job.started_at).total_seconds())

            avg_duration_seconds = sum(durations) / len(durations) if durations else 0.0
            finished_count = completed_jobs + failed_jobs
            success_rate = (completed_jobs / finished_count) if finished_count > 0 else 0.0

            return {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "expired_jobs": expired_jobs,
                "avg_duration_seconds": round(avg_duration_seconds, 2),
                "success_rate": round(success_rate, 4),
            }
