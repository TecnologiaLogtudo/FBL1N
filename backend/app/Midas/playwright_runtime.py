from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

try:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
except Exception:  # pragma: no cover - exercised in environments without playwright
    Browser = BrowserContext = Page = Playwright = None  # type: ignore[assignment]
    sync_playwright = None  # type: ignore[assignment]


def _running_in_container() -> bool:
    return os.path.exists("/.dockerenv") or bool(os.getenv("KUBERNETES_SERVICE_HOST"))


@dataclass(frozen=True)
class PlaywrightRuntimeConfig:
    runtime_mode: str = "auto"  # auto | local | vps
    headless: bool = True
    timeout_ms: int = 30_000
    viewport_width: int = 1280
    viewport_height: int = 720
    locale: str = "pt-BR"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    browser_args: tuple[str, ...] = field(
        default_factory=lambda: (
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        )
    )
    extra_http_headers: Dict[str, str] = field(
        default_factory=lambda: {
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    record_video_dir: Optional[str] = None

    def resolved_mode(self) -> str:
        mode = self.runtime_mode.strip().lower()
        if mode in {"local", "vps"}:
            return mode
        return "vps" if _running_in_container() else "local"

    @classmethod
    def from_env(
        cls,
        *,
        headless: bool,
        runtime_mode: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        viewport_width: Optional[int] = None,
        viewport_height: Optional[int] = None,
        locale: Optional[str] = None,
        user_agent: Optional[str] = None,
        browser_args: Optional[str] = None,
        record_video_dir: Optional[str] = None,
    ) -> "PlaywrightRuntimeConfig":
        parsed_args = tuple(
            item.strip()
            for item in (browser_args or os.getenv("MIDAS_PLAYWRIGHT_BROWSER_ARGS", "")).split(",")
            if item.strip()
        )
        return cls(
            runtime_mode=runtime_mode or os.getenv("MIDAS_PLAYWRIGHT_RUNTIME_MODE", "auto"),
            headless=headless,
            timeout_ms=timeout_ms or int(os.getenv("MIDAS_PLAYWRIGHT_TIMEOUT_MS", "30000")),
            viewport_width=viewport_width or int(os.getenv("MIDAS_PLAYWRIGHT_VIEWPORT_WIDTH", "1280")),
            viewport_height=viewport_height or int(os.getenv("MIDAS_PLAYWRIGHT_VIEWPORT_HEIGHT", "720")),
            locale=locale or os.getenv("MIDAS_PLAYWRIGHT_LOCALE", "pt-BR"),
            user_agent=user_agent or os.getenv(
                "MIDAS_PLAYWRIGHT_USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ),
            browser_args=parsed_args
            or (
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ),
            record_video_dir=record_video_dir or os.getenv("MIDAS_PLAYWRIGHT_RECORD_VIDEO_DIR") or None,
        )


class PlaywrightRuntimeClient:
    def __init__(self, config: Optional[PlaywrightRuntimeConfig] = None):
        self.config = config or PlaywrightRuntimeConfig()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self):
        if sync_playwright is None:
            raise RuntimeError("Playwright não está instalado no ambiente atual.")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.config.headless,
            args=list(self.config.browser_args),
        )

        context_args = {
            "viewport": {"width": self.config.viewport_width, "height": self.config.viewport_height},
            "user_agent": self.config.user_agent,
            "locale": self.config.locale,
            "extra_http_headers": self.config.extra_http_headers,
        }
        if self.config.record_video_dir:
            context_args["record_video_dir"] = self.config.record_video_dir

        self.context = self.browser.new_context(**context_args)
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.config.timeout_ms)
        self.page.set_default_navigation_timeout(self.config.timeout_ms)
        self._apply_basic_stealth()
        return self.page

    def stop(self) -> None:
        if self.context:
            self.context.close()
            self.context = None
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        self.page = None

    def _apply_basic_stealth(self) -> None:
        if not self.page:
            return
        self.page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
            window.chrome = { runtime: {} };
            """
        )

    def __enter__(self) -> "PlaywrightRuntimeClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.stop()
        return False
