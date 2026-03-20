from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProcessMode(str, Enum):
    standard = "standard"
    open_titles = "open_titles"
    midas_correlation = "midas_correlation"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    expired = "expired"


class ProcessStartResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    process_mode: ProcessMode


class ResultsResponse(BaseModel):
    summary: list[dict[str, Any]] = Field(default_factory=list)
    details: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class JobHistoryItem(BaseModel):
    job_id: str
    status: JobStatus
    analysis_year: int
    base_filename: str
    report_filename: str
    process_mode: ProcessMode
    progress: float
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class MetricsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    expired_jobs: int
    avg_duration_seconds: float
    success_rate: float


class WsMessage(BaseModel):
    type: str
    payload: dict[str, Any]
