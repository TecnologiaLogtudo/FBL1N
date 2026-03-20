from __future__ import annotations

import pandas as pd

from ..schemas import ProcessMode


def _load_summary(output_path: str) -> pd.DataFrame:
    for sheet in ("Resumo Consolidado", "Resumo Aberto"):
        try:
            df = pd.read_excel(
                output_path,
                sheet_name=sheet,
                skiprows=2,
                usecols="A:E",
            )
            df = df.dropna(how="all")
            if not df.empty:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def _load_details(output_path: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(
            output_path,
            sheet_name="Resumo Consolidado",
            skiprows=2,
            usecols="G:T",
        )
        df = df.dropna(how="all")
        if "Status Pgto" in df.columns:
            df = df[df["Status Pgto"].isin(["Não lançado", "Não compensado"])]
        if not df.empty:
            return df
    except Exception:
        pass

    try:
        df = pd.read_excel(output_path, sheet_name="Aberto vs Pago")
        df = df.dropna(how="all")
        return df
    except Exception:
        return pd.DataFrame()


def _parse_midas_results(output_path: str) -> dict:
    df = pd.read_excel(output_path).dropna(how="all")
    if df.empty:
        return {
            "summary": [],
            "details": [],
            "meta": {"summary_count": 0, "details_count": 0, "matched_count": 0, "unmatched_count": 0},
        }

    condition_column = None
    for col in df.columns:
        normalized = str(col).strip().lower()
        if normalized in {"condição", "condicao"}:
            condition_column = col
            break

    summary = df.fillna("").to_dict(orient="records")
    matched_count = 0
    unmatched_count = 0
    if condition_column is not None:
        for value in df[condition_column].fillna("").astype(str):
            if value == "Pendente Pagamento":
                matched_count += 1
            elif value == "-":
                unmatched_count += 1

    return {
        "summary": summary,
        "details": [],
        "meta": {
            "summary_count": len(summary),
            "details_count": 0,
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
        },
    }


def parse_results(output_path: str, process_mode: ProcessMode) -> dict:
    if process_mode == ProcessMode.midas_correlation:
        return _parse_midas_results(output_path)

    summary_df = _load_summary(output_path)
    details_df = _load_details(output_path)

    summary = summary_df.fillna("").to_dict(orient="records")
    details = details_df.fillna("").to_dict(orient="records")

    return {
        "summary": summary,
        "details": details,
        "meta": {
            "summary_count": len(summary),
            "details_count": len(details),
        },
    }
