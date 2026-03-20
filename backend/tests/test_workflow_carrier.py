from __future__ import annotations

from pathlib import Path
import shutil
from uuid import uuid4

import pytest

from backend.app.Midas.workflow_carrier import MidasCarrierWorkflow


class _FakeDownload:
    suggested_filename = "midas_export.csv"

    def __init__(self, target_dir: Path):
        self._target_dir = target_dir

    def save_as(self, destination: str) -> None:
        Path(destination).write_text("conteudo")


class _FakeDownloadInfo:
    def __init__(self, download: _FakeDownload):
        self.value = download


class _FakeExpectDownload:
    def __init__(self, download: _FakeDownload):
        self._download = download
        self._info = _FakeDownloadInfo(download)

    def __enter__(self) -> _FakeDownloadInfo:
        return self._info

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeLocatorFirst:
    def __init__(self, page):
        self._page = page

    def click(self) -> None:
        self._page.fallback_clicked = True


class _FakeLocator:
    def __init__(self, page):
        self.first = _FakeLocatorFirst(page)


class _FakePage:
    def __init__(self, target_dir: Path, fail_enter_once: bool = False, fail_export: bool = False):
        self.target_dir = target_dir
        self.fail_enter_once = fail_enter_once
        self.fail_export = fail_export
        self.fallback_clicked = False
        self._panel_checks = 0
        self.actions: list[str] = []

    def goto(self, *_args, **_kwargs) -> None:
        self.actions.append("goto")

    def wait_for_selector(self, selector: str, **kwargs) -> None:
        self.actions.append(f"wait:{selector}")
        if selector == "select#dateType":
            self._panel_checks += 1
            if self.fail_enter_once and self._panel_checks == 1 and kwargs.get("timeout") == 8000:
                raise TimeoutError("panel timeout")

    def fill(self, selector: str, _value: str) -> None:
        self.actions.append(f"fill:{selector}")

    def press(self, selector: str, _key: str) -> None:
        self.actions.append(f"press:{selector}")

    def locator(self, _selector: str):
        return _FakeLocator(self)

    def wait_for_load_state(self, _state: str) -> None:
        self.actions.append("networkidle")

    def select_option(self, selector: str, value: str) -> None:
        self.actions.append(f"select:{selector}={value}")

    def wait_for_timeout(self, _ms: int) -> None:
        self.actions.append("wait-timeout")

    def click(self, selector: str) -> None:
        self.actions.append(f"click:{selector}")
        if selector == "input[value='Exportar']" and self.fail_export:
            raise RuntimeError("erro export")

    def expect_download(self):
        return _FakeExpectDownload(_FakeDownload(self.target_dir))


class _FakeClient:
    def __init__(self, _config, *, page: _FakePage):
        self.page = page

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

def _make_test_dir() -> Path:
    test_dir = Path("backend/tests/.tmp_workflow_carrier") / str(uuid4())
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def test_workflow_carrier_success(monkeypatch: pytest.MonkeyPatch) -> None:
    test_dir = _make_test_dir()
    try:
        page = _FakePage(test_dir)
        monkeypatch.setattr(
            "backend.app.Midas.workflow_carrier.PlaywrightRuntimeClient",
            lambda config: _FakeClient(config, page=page),
        )

        workflow = MidasCarrierWorkflow(
            username="user",
            password="pass",
            starting_date="01/03/2026",
            ending_date="20/03/2026",
            download_dir=str(test_dir),
        )
        output = workflow.run()
        output_path = Path(output)

        assert output_path.exists()
        assert output_path.name == "midas_export.csv"
        assert page.fallback_clicked is False
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_workflow_carrier_fallback_when_enter_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    test_dir = _make_test_dir()
    try:
        page = _FakePage(test_dir, fail_enter_once=True)
        monkeypatch.setattr(
            "backend.app.Midas.workflow_carrier.PlaywrightRuntimeClient",
            lambda config: _FakeClient(config, page=page),
        )

        workflow = MidasCarrierWorkflow(download_dir=str(test_dir))
        workflow.run()

        assert page.fallback_clicked is True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_workflow_carrier_raises_clear_message_on_export_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    test_dir = _make_test_dir()
    try:
        page = _FakePage(test_dir, fail_export=True)
        monkeypatch.setattr(
            "backend.app.Midas.workflow_carrier.PlaywrightRuntimeClient",
            lambda config: _FakeClient(config, page=page),
        )

        workflow = MidasCarrierWorkflow(download_dir=str(test_dir))

        with pytest.raises(RuntimeError, match="Falha no workflow Midas durante login/exportação"):
            workflow.run()
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
