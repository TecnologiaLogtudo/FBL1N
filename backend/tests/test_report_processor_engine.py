from __future__ import annotations

import importlib
import logging
import sys


def _load_report_processor_class(monkeypatch):
    monkeypatch.setattr(logging, "FileHandler", lambda *args, **kwargs: logging.NullHandler())
    sys.modules.pop("desktop.utils", None)
    sys.modules.pop("desktop.report_processor", None)
    module = importlib.import_module("desktop.report_processor")
    return module.ReportProcessor, module


def _run_and_capture_engine(monkeypatch, filepath: str) -> str | None:
    captured_engine: dict[str, str | None] = {"value": None}
    report_processor_class, report_processor_module = _load_report_processor_class(monkeypatch)

    def fake_read_excel(*args, **kwargs):
        captured_engine["value"] = kwargs.get("engine")
        raise RuntimeError("stop-after-engine-capture")

    monkeypatch.setattr(report_processor_module.pd, "read_excel", fake_read_excel)

    processor = report_processor_class(filepath=filepath, analysis_year=2026)
    processor.process()
    return captured_engine["value"]


def test_report_processor_uses_openpyxl_for_xlsx(monkeypatch) -> None:
    engine = _run_and_capture_engine(monkeypatch, "relatorio.xlsx")
    assert engine == "openpyxl"


def test_report_processor_uses_xlrd_for_xls(monkeypatch) -> None:
    engine = _run_and_capture_engine(monkeypatch, "relatorio.xls")
    assert engine == "xlrd"
