from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _load_summary(output_path: str) -> pd.DataFrame:
    for sheet in ("Resumo Consolidado", "Resumo Aberto"):
        try:
            df = pd.read_excel(
                output_path,
                sheet_name=sheet,
                skiprows=2,
            usecols="A:F",
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


def generate_pdf_from_output(output_path: str, pdf_path: str) -> str:
    summary_df = _load_summary(output_path).fillna("")
    details_df = _load_details(output_path).fillna("")

    def _format_currency_pdf(val):
        if pd.isna(val) or str(val).strip() in ['', '-', 'Não lançado', 'Não compensado']:
            return val
        try:
            clean_val = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
            return f"R$ {float(clean_val):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return val

    for col in ['Não compensado', 'Não lançado', 'Total Geral', 'Valor pago no FBL1', 'Valor devido não encontrado FBL1', 'Valor CTe', 'Valor pago', 'Recebido/A receber']:
        if col in summary_df.columns:
            summary_df[col] = summary_df[col].apply(_format_currency_pdf)
        if col in details_df.columns:
            details_df[col] = details_df[col].apply(_format_currency_pdf)

    Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter), leftMargin=18, rightMargin=18, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("RESUMO CONSOLIDADO DE TRANSPORTES", styles["Heading1"]))
    elements.append(Spacer(1, 8))

    if not summary_df.empty:
        summary_data = [summary_df.columns.tolist()] + summary_df.astype(str).values.tolist()
        summary_table = Table(summary_data, repeatRows=1)
        style_summary = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#366092")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
        
        # Formatação para números negativos em vermelho no Resumo
        for i, row_values in enumerate(summary_df.values):
            table_row_index = i + 1
            for j, cell_value in enumerate(row_values):
                try:
                    val_str = str(cell_value).replace('R$', '').replace('.', '').replace(',', '.').strip()
                    if val_str and float(val_str) < 0:
                        style_summary.add('TEXTCOLOR', (j, table_row_index), (j, table_row_index), colors.red)
                except (ValueError, TypeError):
                    continue
        summary_table.setStyle(style_summary)
        elements.append(summary_table)
    else:
        elements.append(Paragraph("Sem dados de resumo no arquivo processado.", styles["BodyText"]))

    elements.append(Spacer(1, 16))
    elements.append(Paragraph("DETALHES DE PENDÊNCIAS", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    if not details_df.empty:
        preferred_cols = [
            "Emissão",
            "Mês",
            "Transportadora",
            "CTRC",
            "Cliente",
            "Serviço",
            "Valor CTe",
            "Status Pgto",
            "Valor pago",
            "Recebido/A receber",
        ]
        selected_cols = [col for col in preferred_cols if col in details_df.columns]
        if selected_cols:
            details_df = details_df[selected_cols]

        details_data = [details_df.columns.tolist()] + details_df.astype(str).values.tolist()
        details_table = Table(details_data, repeatRows=1)
        style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.darkgrey),
            ]
        )

        if "Status Pgto" in details_df.columns and "Recebido/A receber" in details_df.columns:
            status_idx = details_df.columns.get_loc("Status Pgto")
            recebido_idx = details_df.columns.get_loc("Recebido/A receber")
            for i, row in enumerate(details_df.itertuples(index=False), start=1):
                if str(row[status_idx]).strip() == "Não lançado":
                    style.add("BACKGROUND", (recebido_idx, i), (recebido_idx, i), colors.HexColor("#FFCCCC"))

        # Formatação para números negativos em vermelho nos Detalhes
        for i, row_values in enumerate(details_df.values):
            table_row_index = i + 1
            for j, cell_value in enumerate(row_values):
                try:
                    val_str = str(cell_value).replace('R$', '').replace('.', '').replace(',', '.').strip()
                    if val_str and float(val_str) < 0:
                        style.add('TEXTCOLOR', (j, table_row_index), (j, table_row_index), colors.red)
                except (ValueError, TypeError):
                    continue
        details_table.setStyle(style)
        elements.append(details_table)
    else:
        elements.append(Paragraph("Sem pendências para exibição.", styles["BodyText"]))

    doc.build(elements)
    return pdf_path
