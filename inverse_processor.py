from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

from config import COLUNA_REFERENCIA
from utils import logger


class OpenTitlesProcessor:
    """Processa a planilha de títulos em aberto e cruza com as abas FBL1."""

    CTRC_CANDIDATES: Final[list[str]] = [
        "cte",
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
    VALUE_CANDIDATES: Final[list[str]] = ["Total", "valor", "valor cte", "valor cotação", "valor do conhecimento", "montante"]

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
        "Valor devido não encontrado FBL1",
    ]

    DETAIL_COLUMNS = [
        "CTRC",
        "Transportadora",
        "Status Arquivo",
        "Valor pago",
        "Valor devido",
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
    def _normalize(name: str) -> str:
        return "".join(ch for ch in name.lower() if ch.isalnum())

    def _find_column(self, candidates: list[str], columns: list[str]) -> str | None:
        normalized_columns = {self._normalize(col): col for col in columns}
        lower_map = {col.lower().strip(): col for col in columns}
        for candidate in candidates:
            norm = self._normalize(candidate)
            if norm in normalized_columns:
                return normalized_columns[norm]
            if candidate in lower_map:
                return lower_map[candidate]
        return None

    def _load_dataframe(self) -> pd.DataFrame:
        engine = self._resolve_engine()
        # Lê o arquivo sem cabeçalho (header=None) para localizar dinamicamente a linha de títulos
        df_raw = pd.read_excel(self.open_titles_path, engine=engine, header=None)
        
        header_idx = 0
        # Varre as primeiras 30 linhas procurando pela coluna de CTRC/CTe
        for idx, row in df_raw.head(30).iterrows():
            row_values = [str(val) for val in row.values if pd.notna(val)]
            if self._find_column(self.CTRC_CANDIDATES, row_values):
                header_idx = idx
                break
                
        h1_str = df_raw.iloc[header_idx].fillna("").astype(str).replace("nan", "").str.strip()
        
        # Verifica se a próxima linha contém sub-cabeçalhos (ex: linha 8 no BSoft com 'Total' em AJ8)
        h2_str = df_raw.iloc[header_idx + 1].fillna("").astype(str).replace("nan", "").str.strip() if (header_idx + 1) < len(df_raw) else pd.Series(dtype=str)
        
        is_sub_header = False
        all_candidates = [self._normalize(c) for c in self.VALUE_CANDIDATES + self.STATUS_CANDIDATES + self.TRANSPORT_CANDIDATES]
        for val in h2_str:
            norm_val = self._normalize(val)
            if norm_val and norm_val in all_candidates:
                is_sub_header = True
                break
                
        if is_sub_header:
            df_raw.columns = (h1_str + " " + h2_str).str.strip().str.replace(r"\s+", " ", regex=True)
            df = df_raw.iloc[header_idx + 2:].reset_index(drop=True)
        else:
            df_raw.columns = h1_str
            df = df_raw.iloc[header_idx + 1:].reset_index(drop=True)
        
        return df.dropna(how="all")

    def _prepare_open_titles(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        ctrc_col = self._find_column(self.CTRC_CANDIDATES, list(df.columns))
        if not ctrc_col:
            raise ValueError(
                "Não foi possível identificar a coluna CTRC/CTe na planilha de títulos abertos. "
                f"Os nomes aceitos são: {', '.join(self.CTRC_CANDIDATES)}."
            )

        serie_ctrc = df[ctrc_col].astype(str).str.replace(r"\D+", "", regex=True)
        df["CTRC"] = pd.to_numeric(serie_ctrc.where(serie_ctrc != "", None), errors="coerce")
        df.dropna(subset=["CTRC"], inplace=True)
        df["CTRC"] = df["CTRC"].astype(int)

        status_col = self._find_column(self.STATUS_CANDIDATES, list(df.columns))
        df["Status Arquivo"] = df[status_col].astype(str).fillna("Aberto") if status_col else "Aberto"

        transport_col = self._find_column(self.TRANSPORT_CANDIDATES, list(df.columns))
        df["Transportadora arquivo"] = df[transport_col].astype(str).fillna("").str.strip() if transport_col else ""

        value_col = self._find_column(self.VALUE_CANDIDATES, list(df.columns))
        if value_col:
            logger.info("Coluna de valor encontrada na planilha de títulos abertos: '%s'", value_col)
            
            def clean_currency(val):
                if pd.isna(val): return 0.0
                if isinstance(val, (int, float)): return float(val)
                s = str(val).upper().replace('R$', '').strip()
                if ',' in s:
                    s = s.replace('.', '').replace(',', '.')
                try:
                    return float(s)
                except ValueError:
                    return 0.0
                    
            df["Valor Arquivo"] = df[value_col].apply(clean_currency)
        else:
            logger.warning("Coluna de valor não encontrada na planilha de títulos abertos. 'Valor devido' será 0.")
            df["Valor Arquivo"] = 0.0

        return df

    def _build_lookup(self, final_sheets: dict[str, pd.DataFrame]) -> dict[int, dict[str, str | float]]:
        lookup: dict[int, dict[str, str | float]] = {}
        allowed_sheets = {"Bahia"}
        for sheet_name, df in final_sheets.items():
            if sheet_name not in allowed_sheets:
                continue
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
            valor_arquivo = float(row.get("Valor Arquivo", 0.0))
            matched = lookup.get(ctrc)
            if matched:
                valor_pago = float(matched["valor"] or 0.0)
                valor_devido = 0.0
                data_comp = matched["data"] or ""
                result = "Pago no FBL1" if valor_pago > 0 else "Pago (valor zerado)"
                transport = transport_from_file or self._from_sheet_transport(matched["sheet"])
                observacao = f"Encontrado na aba {matched['sheet']}"
            else:
                valor_pago = 0.0
                valor_devido = valor_arquivo
                data_comp = ""
                result = "Não localizado no FBL1"
                transport = transport_from_file or "Desconhecida"
                observacao = "Não encontrado na base FBL1"

            rows.append(
                {
                    "CTRC": ctrc,
                    "Transportadora": transport,
                    "Status Arquivo": status,
                    "Valor pago": valor_pago,
                    "Valor devido": valor_devido,
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
                    "Valor devido não encontrado FBL1": 0.0,
                },
            )
            entry["Títulos abertos fornecidos"] += 1
            entry["Valor devido não encontrado FBL1"] += float(row["Valor devido"])

            if row["Resultado"].startswith("Pago"):
                entry["Pagos encontrados no FBL1"] += 1
                entry["Valor pago no FBL1"] += float(row["Valor pago"])
            else:
                entry["Pendentes"] += 1

        summary_rows = list(totals.values())
        total_abertos = sum(r["Títulos abertos fornecidos"] for r in summary_rows)
        total_pagos = sum(r["Pagos encontrados no FBL1"] for r in summary_rows)
        total_pendentes = sum(r["Pendentes"] for r in summary_rows)
        total_valor_pago = sum(r["Valor pago no FBL1"] for r in summary_rows)
        total_valor_devido = sum(r["Valor devido não encontrado FBL1"] for r in summary_rows)

        summary_rows.append(
            {
                "Transportadora": "Total geral",
                "Títulos abertos fornecidos": total_abertos,
                "Pagos encontrados no FBL1": total_pagos,
                "Pendentes": total_pendentes,
                "Valor pago no FBL1": total_valor_pago,
                "Valor devido não encontrado FBL1": total_valor_devido,
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
