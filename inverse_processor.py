from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

from config import COLUNA_REFERENCIA
from utils import logger


class OpenTitlesProcessor:
    """Processa a planilha de títulos em aberto e cruza com as abas FBL1."""

    CTRC_CANDIDATES: Final[list[str]] = [
        "ctrc",
        "ctr cs",
        "conhecimento",
        "num ctrc",
        "numero ctrc",
        "número do conhecimento",
        "referencia",
        "referência",
    ]
    STATUS_CANDIDATES: Final[list[str]] = ["status", "situacao", "situação"]
    TRANSPORT_CANDIDATES: Final[list[str]] = ["transportadora", "filial", "deposito"]

    SHEET_TO_TRANSPORT = {
        "Bahia": "Logtudo Bahia",
        "Ceará": "Logtudo Ceará",
        "Pernambuco": "Logtudo Pernambuco",
    }

    SUMMARY_COLUMNS = [
        "Transportadora",
        "Títulos abertos fornecidos",
        "Pagos encontrados no FBL1",
        "Pendentes",
        "Valor pago no FBL1",
    ]

    DETAIL_COLUMNS = [
        "CTRC",
        "Transportadora",
        "Status Arquivo",
        "Valor pago",
        "Data de compensação",
        "Resultado",
        "Observação",
    ]

    def __init__(self, open_titles_path: str) -> None:
        self.open_titles_path = open_titles_path

    def _resolve_engine(self) -> str:
        suffix = Path(self.open_titles_path).suffix.lower()
        return "xlrd" if suffix == ".xls" else "openpyxl"

    @staticmethod
    def _find_column(candidates: list[str], columns: list[str]) -> str | None:
        lower_map = {col.lower().strip(): col for col in columns}
        for candidate in candidates:
            if candidate in lower_map:
                return lower_map[candidate]
        return None

    def _load_dataframe(self) -> pd.DataFrame:
        engine = self._resolve_engine()
        df = pd.read_excel(self.open_titles_path, engine=engine)
        df = df.dropna(how="all")
        return df

    def _prepare_open_titles(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        ctrc_col = self._find_column(self.CTRC_CANDIDATES, list(df.columns))
        if not ctrc_col:
            raise ValueError("Não foi possível identificar a coluna de CTRC na planilha de títulos abertos")

        serie_ctrc = df[ctrc_col].astype(str).str.replace(r"\D+", "", regex=True)
        df["CTRC"] = pd.to_numeric(serie_ctrc.where(serie_ctrc != "", None), errors="coerce")
        df.dropna(subset=["CTRC"], inplace=True)
        df["CTRC"] = df["CTRC"].astype(int)

        status_col = self._find_column(self.STATUS_CANDIDATES, list(df.columns))
        df["Status Arquivo"] = df[status_col].astype(str).fillna("Aberto") if status_col else "Aberto"

        transport_col = self._find_column(self.TRANSPORT_CANDIDATES, list(df.columns))
        df["Transportadora arquivo"] = df[transport_col].astype(str).fillna("").str.strip() if transport_col else ""

        return df

    def _build_lookup(self, final_sheets: dict[str, pd.DataFrame]) -> dict[int, dict[str, str | float]]:
        lookup: dict[int, dict[str, str | float]] = {}
        for sheet_name, df in final_sheets.items():
            if df is None or df.empty:
                continue
            working = df.copy()
            working[COLUNA_REFERENCIA] = pd.to_numeric(working[COLUNA_REFERENCIA], errors="coerce")
            working.dropna(subset=[COLUNA_REFERENCIA], inplace=True)
            working[COLUNA_REFERENCIA] = working[COLUNA_REFERENCIA].astype(int)
            for record in working.to_dict("records"):
                reference_value = record.get(COLUNA_REFERENCIA)
                if reference_value is None:
                    continue
                reference = int(reference_value)
                lookup[reference] = {
                    "sheet": sheet_name,
                    "valor": float(record.get("Valor pagamento", 0.0) or 0.0),
                    "data": record.get("Data de compensação", ""),
                }
        return lookup

    def _from_sheet_transport(self, sheet: str) -> str:
        return self.SHEET_TO_TRANSPORT.get(sheet, sheet)

    def _build_detail_rows(self, df: pd.DataFrame, lookup: dict[int, dict[str, str | float]]) -> list[dict[str, str | float]]:
        rows: list[dict[str, str | float]] = []
        for idx, row in df.iterrows():
            ctrc = int(row["CTRC"])
            status = row.get("Status Arquivo", "Aberto")
            transport_from_file = str(row.get("Transportadora arquivo", "") or "").strip()
            matched = lookup.get(ctrc)
            if matched:
                valor = float(matched["valor"] or 0.0)
                data_comp = matched["data"] or ""
                result = "Pago no FBL1" if valor > 0 else "Pago (valor zerado)"
                transport = transport_from_file or self._from_sheet_transport(matched["sheet"])
                observacao = f"Encontrado na aba {matched['sheet']}"
            else:
                valor = 0.0
                data_comp = ""
                result = "Não localizado no FBL1"
                transport = transport_from_file or "Desconhecida"
                observacao = "Não encontrado na base FBL1"

            rows.append(
                {
                    "CTRC": ctrc,
                    "Transportadora": transport,
                    "Status Arquivo": status,
                    "Valor pago": valor,
                    "Data de compensação": data_comp,
                    "Resultado": result,
                    "Observação": observacao,
                }
            )
        return rows

    def _build_summary(self, detail_rows: list[dict[str, str | float]]) -> pd.DataFrame:
        if not detail_rows:
            return pd.DataFrame(columns=self.SUMMARY_COLUMNS)

        totals: dict[str, dict[str, float | int]] = {}
        for row in detail_rows:
            transport = row["Transportadora"]
            entry = totals.setdefault(
                transport,
                {
                    "Transportadora": transport,
                    "Títulos abertos fornecidos": 0,
                    "Pagos encontrados no FBL1": 0,
                    "Pendentes": 0,
                    "Valor pago no FBL1": 0.0,
                },
            )
            entry["Títulos abertos fornecidos"] += 1
            if row["Resultado"].startswith("Pago"):
                entry["Pagos encontrados no FBL1"] += 1
                entry["Valor pago no FBL1"] += float(row["Valor pago"])
            else:
                entry["Pendentes"] += 1

        summary_rows = list(totals.values())
        total_pagos = sum(row["Pagos encontrados no FBL1"] for row in summary_rows)
        total_pendentes = sum(row["Pendentes"] for row in summary_rows)
        total_abertos = sum(row["Títulos abertos fornecidos"] for row in summary_rows)
        total_valor = sum(row["Valor pago no FBL1"] for row in summary_rows)

        summary_rows.append(
            {
                "Transportadora": "Total geral",
                "Títulos abertos fornecidos": total_abertos,
                "Pagos encontrados no FBL1": total_pagos,
                "Pendentes": total_pendentes,
                "Valor pago no FBL1": total_valor,
            }
        )

        return pd.DataFrame(summary_rows, columns=self.SUMMARY_COLUMNS)

    def run(
        self,
        final_sheets: dict[str, pd.DataFrame],
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Cruza os títulos em aberto com as abas de lookup e gera os DataFrames de resumo/detalhes.
        """
        try:
            df = self._load_dataframe()
            df = self._prepare_open_titles(df)
        except Exception as exc:
            logger.error("Falha ao carregar a planilha de títulos em aberto: %s", exc)
            return pd.DataFrame(columns=self.SUMMARY_COLUMNS), pd.DataFrame(columns=self.DETAIL_COLUMNS)

        detail_rows = self._build_detail_rows(df, self._build_lookup(final_sheets))
        detail_df = pd.DataFrame(detail_rows, columns=self.DETAIL_COLUMNS)
        summary_df = self._build_summary(detail_rows)

        logger.info("Processamento dos títulos em aberto concluído (total: %d linhas)", len(detail_rows))
        return summary_df, detail_df
