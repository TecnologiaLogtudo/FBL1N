from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    ttl_seconds: int = int(os.getenv("JOB_TTL_SECONDS", str(24 * 60 * 60)))
    cleanup_interval_seconds: int = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "600"))
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",")
        if origin.strip()
    )
    min_year: int = int(os.getenv("MIN_ANALYSIS_YEAR", "2020"))
    max_year: int = int(os.getenv("MAX_ANALYSIS_YEAR", "2100"))


settings = Settings()
