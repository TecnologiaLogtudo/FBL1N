from __future__ import annotations

import pandas as pd


def parse_results(output_path: str) -> dict:
    summary_df = pd.read_excel(
        output_path,
        sheet_name="Resumo Consolidado",
        skiprows=2,
        usecols="A:E",
    )
    summary_df = summary_df.dropna(how="all")

    try:
        details_df = pd.read_excel(
            output_path,
            sheet_name="Resumo Consolidado",
            skiprows=2,
            usecols="G:T",
        )
        details_df = details_df.dropna(how="all")
    except Exception:
        details_df = pd.DataFrame()

    if "Status Pgto" in details_df.columns:
        details_df = details_df[details_df["Status Pgto"].isin(["Não lançado", "Não compensado"])]

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
