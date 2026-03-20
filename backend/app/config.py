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
    midas_username: str = os.getenv("MIDAS_USERNAME", "")
    midas_password: str = os.getenv("MIDAS_PASSWORD", "")
    midas_starting_date: str = os.getenv("MIDAS_STARTING_DATE", "01/01/2026")
    midas_ending_date: str = os.getenv("MIDAS_ENDING_DATE", "31/12/2026")
    midas_headless: bool = os.getenv("MIDAS_HEADLESS", "true").strip().lower() not in {"0", "false", "no"}
    midas_target_url: str = os.getenv(
        "MIDAS_TARGET_URL",
        "https://nixweb.midassolutions.com.br/028/web/Account/Login"
        "?ReturnUrl=%2f028%2fweb%2fCarrierManagementPanel%2f%3fdateType%3dE%26startingDate%3d24%252F01%252F2023"
        "%26endingDate%3d08%252F02%252F2023%26status%3dF%252CA%252CR%26chk_status_1%3dF%26chk_status_2%3dA%26chk_status_3%3dR"
        "&dateType=E&startingDate=24%2F01%2F2023&endingDate=08%2F02%2F2023&status=F%2CA%2CR&chk_status_1=F&chk_status_2=A&chk_status_3=R",
    )
    midas_playwright_runtime_mode: str = os.getenv("MIDAS_PLAYWRIGHT_RUNTIME_MODE", "auto")
    midas_playwright_timeout_ms: int = int(os.getenv("MIDAS_PLAYWRIGHT_TIMEOUT_MS", "30000"))
    midas_playwright_viewport_width: int = int(os.getenv("MIDAS_PLAYWRIGHT_VIEWPORT_WIDTH", "1280"))
    midas_playwright_viewport_height: int = int(os.getenv("MIDAS_PLAYWRIGHT_VIEWPORT_HEIGHT", "720"))
    midas_playwright_locale: str = os.getenv("MIDAS_PLAYWRIGHT_LOCALE", "pt-BR")
    midas_playwright_user_agent: str = os.getenv(
        "MIDAS_PLAYWRIGHT_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    midas_playwright_browser_args: str = os.getenv(
        "MIDAS_PLAYWRIGHT_BROWSER_ARGS",
        "--disable-blink-features=AutomationControlled,--no-first-run,--no-default-browser-check",
    )


settings = Settings()
