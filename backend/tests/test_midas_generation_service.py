from __future__ import annotations

from pathlib import Path
import shutil
from uuid import uuid4

import pytest

from backend.app.service import midas_correlation


def _make_test_dir() -> Path:
    test_dir = Path("backend/tests/.tmp_midas_generation") / str(uuid4())
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def test_generate_and_prepare_midas_file_requires_credentials() -> None:
    test_dir = _make_test_dir()
    try:
        with pytest.raises(ValueError, match="Credenciais do Midas não configuradas"):
            midas_correlation.generate_and_prepare_midas_file(
                prepared_output_path=str(test_dir / "midas.xlsx"),
                username="",
                password="",
                starting_date="01/03/2026",
                ending_date="20/03/2026",
                headless=True,
            )
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_generate_and_prepare_midas_file_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    test_dir = _make_test_dir()
    try:
        raw_file = test_dir / "midas_raw.csv"
        raw_file.write_text("raw")
        output_file = test_dir / "midas_prepared.xlsx"

        captured: dict[str, object] = {}

        class _FakeWorkflow:
            def __init__(self, **kwargs):
                captured["kwargs"] = kwargs

            def run(self) -> str:
                return str(raw_file)

        class _FakeProcessor:
            @staticmethod
            def process_to_excel(file_path: str, prepared_output_path: str) -> str:
                captured["file_path"] = file_path
                Path(prepared_output_path).write_text("ok")
                return prepared_output_path

        monkeypatch.setattr("backend.app.Midas.workflow_carrier.MidasCarrierWorkflow", _FakeWorkflow)
        monkeypatch.setattr("backend.app.Midas.spreadsheet_processor.MidasSpreadsheetProcessor", _FakeProcessor)

        generated = midas_correlation.generate_and_prepare_midas_file(
            prepared_output_path=str(output_file),
            username="user",
            password="pass",
            starting_date="01/03/2026",
            ending_date="20/03/2026",
            headless=True,
        )

        assert generated == str(output_file)
        assert Path(generated).exists()
        assert captured["file_path"] == str(raw_file)
        assert "download_dir" in captured["kwargs"]
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
