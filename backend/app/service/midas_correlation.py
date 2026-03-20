from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

from ..Midas.spreadsheet_processor import MidasSpreadsheetProcessor
from ..Midas.workflow_carrier import MidasCarrierWorkflow


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", normalized)


def _normalize_digits(value: object) -> str:
    if value is None:
        return ""
    return "".join(ch for ch in str(value) if ch.isdigit())


def _find_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    normalized_columns = {_normalize_text(str(col)): str(col) for col in df.columns}
    for candidate in candidates:
        found = normalized_columns.get(_normalize_text(candidate))
        if found:
            return found
    return None


def _load_conciliation_sheet(conciliation_output_path: str) -> pd.DataFrame:
    last_error: Exception | None = None
    for kwargs in ({"sheet_name": "Resumo Consolidado"}, {"sheet_name": "Resumo Consolidado", "skiprows": 2}):
        try:
            df = pd.read_excel(conciliation_output_path, **kwargs)
            df = df.dropna(how="all")
            if not df.empty:
                return df
        except Exception as exc:  # pylint: disable=broad-exception-caught
            last_error = exc
    if last_error:
        raise ValueError("Não foi possível ler a aba 'Resumo Consolidado' da planilha de Conciliação.") from last_error
    raise ValueError("Não foi possível ler a aba 'Resumo Consolidado' da planilha de Conciliação.")


def _load_midas_file(midas_path: str) -> pd.DataFrame:
    file_path = Path(midas_path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(midas_path, sep=None, engine="python")
    else:
        df = pd.read_excel(midas_path)
    return df.dropna(how="all")


def validate_conciliation_output(conciliation_output_path: str) -> None:
    df = _load_conciliation_sheet(conciliation_output_path)
    ctrc_column = _find_column(df, ("CTRC",))
    if not ctrc_column:
        raise ValueError("A planilha de Conciliação precisa conter a coluna 'CTRC' na aba 'Resumo Consolidado'.")


def validate_midas_file(midas_path: str) -> None:
    df = _load_midas_file(midas_path)
    number_column = _find_column(df, ("Número", "Numero"))
    if not number_column:
        raise ValueError("A planilha Midas precisa conter a coluna 'Número'.")


def run_midas_correlation(
    midas_path: str,
    conciliation_output_path: str,
    output_path: str,
) -> dict[str, int]:
    conciliation_df = _load_conciliation_sheet(conciliation_output_path)
    ctrc_column = _find_column(conciliation_df, ("CTRC",))
    if not ctrc_column:
        raise ValueError("A planilha de Conciliação precisa conter a coluna 'CTRC' na aba 'Resumo Consolidado'.")

    midas_df = _load_midas_file(midas_path)
    number_column = _find_column(midas_df, ("Número", "Numero"))
    if not number_column:
        raise ValueError("A planilha Midas precisa conter a coluna 'Número'.")

    condition_column = _find_column(midas_df, ("Condição", "Condicao"))
    if not condition_column:
        condition_column = "Condição"
        midas_df[condition_column] = ""

    ctrc_values = {
        value
        for value in (_normalize_digits(item) for item in conciliation_df[ctrc_column].tolist())
        if value
    }

    matched_count = 0
    unmatched_count = 0
    statuses: list[str] = []
    for raw_value in midas_df[number_column].tolist():
        normalized = _normalize_digits(raw_value)
        if normalized and normalized in ctrc_values:
            statuses.append("Pendente Pagamento")
            matched_count += 1
        else:
            statuses.append("-")
            unmatched_count += 1

    midas_df[condition_column] = statuses
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    midas_df.to_excel(output_path, index=False)

    return {
        "matched_count": matched_count,
        "unmatched_count": unmatched_count,
        "total_rows": len(statuses),
    }


def generate_and_prepare_midas_file(
    *,
    prepared_output_path: str,
    username: str,
    password: str,
    starting_date: str,
    ending_date: str,
    headless: bool = True,
) -> str:
    if not username or not password:
        raise ValueError("Credenciais do Midas não configuradas para geração automática.")

    workflow = MidasCarrierWorkflow(
        username=username,
        password=password,
        starting_date=starting_date,
        ending_date=ending_date,
        headless=headless,
    )
    raw_path = workflow.run()
    return MidasSpreadsheetProcessor.process_to_excel(raw_path, prepared_output_path)
