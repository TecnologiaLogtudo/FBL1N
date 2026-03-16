from __future__ import annotations

import pandas as pd


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


def parse_results(output_path: str) -> dict:
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
