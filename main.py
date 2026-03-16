# main.py
# Ponto de entrada do sistema para processar as planilhas.

from __future__ import annotations

import pandas as pd
from typing import Literal

from utils import logger

PROCESS_MODE_STANDARD: Literal["standard"] = "standard"
PROCESS_MODE_OPEN_TITLES: Literal["open_titles"] = "open_titles"


def _prepare_data_pipeline(input_file: str, analysis_year: int, progress_callback=None):
    from data_processor import DataProcessor

    logger.stage("===================================================")
    logger.stage("FASE 1: Processando arquivo base...")
    data_proc = DataProcessor(input_file)
    processed_df_step1 = data_proc.process_step1()
    if progress_callback:
        progress_callback(0.2)

    if processed_df_step1 is None:
        logger.warning("Nenhum dado foi processado na Etapa 1. O pipeline será interrompido.")
        return None

    sheets_data_step2 = data_proc.process_step2(processed_df_step1, analysis_year)
    if progress_callback:
        progress_callback(0.3)

    final_sheets_step4 = data_proc.process_steps_3_and_4(sheets_data_step2, analysis_year)
    if progress_callback:
        progress_callback(0.4)

    return data_proc, processed_df_step1, sheets_data_step2, final_sheets_step4


def run_standard_process(
    input_file: str,
    report_file: str,
    output_file: str,
    analysis_year: int,
    progress_callback=None,
):
    """
    Executa o processo padrão (conciliação).
    """
    data_pipeline = _prepare_data_pipeline(input_file, analysis_year, progress_callback)
    if data_pipeline is None:
        return

    data_proc, processed_df_step1, sheets_data_step2, final_sheets_step4 = data_pipeline

    from analysis_processor import AnalysisProcessor
    from final_report_generator import FinalReportGenerator
    from report_processor import ReportProcessor

    logger.stage("FASE 2: Processando relatório externo...")
    report_proc = ReportProcessor(report_file, analysis_year)
    report_df = report_proc.process()
    if progress_callback:
        progress_callback(0.5)

    analyzed_report_df = None
    if report_df is not None:
        analyzer = AnalysisProcessor()
        logger.stage("FASE 3: Cruzando dados...")
        analyzed_report_df = analyzer.run_analysis(report_df, final_sheets_step4)
        if progress_callback:
            progress_callback(0.7)
    else:
        logger.warning("O relatório externo não pôde ser processado. A etapa de análise será pulada.")

    try:
        logger.stage("FASE 4: Gerando arquivo de saída: '%s'", output_file)
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            if not processed_df_step1.empty:
                data_proc.format_date_columns(processed_df_step1).to_excel(
                    writer, sheet_name="Dados Consolidados", index=False
                )

            for sheet_name, df in sheets_data_step2.items():
                if df is not None and not df.empty:
                    data_proc.format_date_columns(df).to_excel(writer, sheet_name=sheet_name, index=False)

            for sheet_name, df in final_sheets_step4.items():
                if df is not None and not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            if analyzed_report_df is not None and not analyzed_report_df.empty:
                analyzed_report_df.to_excel(writer, sheet_name="Dados Relatorio Externo", index=False)

            if progress_callback:
                progress_callback(0.8)

            if analyzed_report_df is not None and not analyzed_report_df.empty:
                logger.stage("FASE 5: Gerando relatório final consolidado...")
                report_generator = FinalReportGenerator(analyzed_report_df)
                report_generator.generate_report(writer)
                if progress_callback:
                    progress_callback(0.9)

        logger.success("Arquivo multipágina salvo com sucesso em: '%s'", output_file)
        if progress_callback:
            progress_callback(1.0)
    except Exception as exc:
        logger.error("Não foi possível salvar o arquivo de saída. Erro: %s", exc, exc_info=True)


def run_open_titles_process(
    input_file: str,
    open_titles_file: str,
    output_file: str,
    analysis_year: int,
    progress_callback=None,
):
    """
    Executa o processo inverso para encontrar títulos abertos já pagos.
    """
    data_pipeline = _prepare_data_pipeline(input_file, analysis_year, progress_callback)
    if data_pipeline is None:
        return

    data_proc, processed_df_step1, sheets_data_step2, final_sheets_step4 = data_pipeline

    from inverse_processor import OpenTitlesProcessor

    logger.stage("FASE 2 (Inversa): Processando títulos em aberto...")
    inverse_processor = OpenTitlesProcessor(open_titles_file)
    summary_df, detail_df = inverse_processor.run(final_sheets_step4)
    if progress_callback:
        progress_callback(0.7)

    try:
        logger.stage("FASE 3 (Inversa): Gerando arquivo diferenciado...")
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            if not processed_df_step1.empty:
                data_proc.format_date_columns(processed_df_step1).to_excel(
                    writer, sheet_name="Dados Consolidados", index=False
                )

            for sheet_name, df in sheets_data_step2.items():
                if df is not None and not df.empty:
                    data_proc.format_date_columns(df).to_excel(writer, sheet_name=sheet_name, index=False)

            for sheet_name, df in final_sheets_step4.items():
                if df is not None and not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            summary_df.to_excel(writer, sheet_name="Resumo Aberto", index=False, startrow=2)
            detail_df.to_excel(writer, sheet_name="Aberto vs Pago", index=False, startrow=2)

            # --- Estilização do Relatório Inverso ---
            workbook = writer.book

            # 1. Ocultar as abas referentes ao Ceará
            for sheet_name in ["303264 - Ceará", "Ceará"]:
                if sheet_name in workbook.sheetnames:
                    workbook[sheet_name].sheet_state = "hidden"

            # 2 e 3. Formato monetário e valores negativos em vermelho
            currency_fmt = 'R$ #,##0.00;[Red]-R$ #,##0.00'

            def _format_sheet(ws, currency_columns):
                # 4. Auto-ajustar a largura das colunas (orientação total de conteúdo)
                for col in ws.columns:
                    max_length = 0
                    col_letter = col[0].column_letter
                    for cell in col:
                        if cell.value is not None:
                            max_length = max(max_length, len(str(cell.value)))
                    ws.column_dimensions[col_letter].width = min(max_length + 2, 60)

                # Localiza as colunas de moeda no cabeçalho (que fica na linha 3 do Excel devido ao startrow=2)
                target_cols = [cell.column_letter for cell in ws[3] if cell.value in currency_columns]

                for col_letter in target_cols:
                    for cell in ws[col_letter]:
                        if cell.row > 3 and isinstance(cell.value, (int, float)):
                            cell.number_format = currency_fmt

            if "Resumo Aberto" in workbook.sheetnames:
                _format_sheet(workbook["Resumo Aberto"], ["Valor pago no FBL1"])
            if "Aberto vs Pago" in workbook.sheetnames:
                _format_sheet(workbook["Aberto vs Pago"], ["Valor pago", "Valor devido"])

        logger.success("Arquivo com processado inverso salvo em: '%s'", output_file)
        if progress_callback:
            progress_callback(1.0)
    except Exception as exc:
        logger.error("Falha ao salvar o arquivo inverso: %s", exc, exc_info=True)


def main(
    input_file: str,
    report_file: str,
    output_file: str,
    analysis_year: int,
    process_mode: Literal["standard", "open_titles"] = PROCESS_MODE_STANDARD,
    open_titles_file: str | None = None,
    progress_callback=None,
) -> None:
    """
    Função principal que decide qual caminho de processamento executar.
    """
    logger.stage("===================================================")
    logger.stage("Iniciando novo ciclo de processamento...")
    if progress_callback:
        progress_callback(0.05)

    mode_value = getattr(process_mode, "value", process_mode)
    if mode_value == PROCESS_MODE_OPEN_TITLES:
        if not open_titles_file:
            raise ValueError("O caminho para a planilha de títulos em aberto é obrigatório nesse modo.")
        run_open_titles_process(input_file, open_titles_file, output_file, analysis_year, progress_callback)
    else:
        run_standard_process(input_file, report_file, output_file, analysis_year, progress_callback)

    logger.stage("Fim do processamento.")
    logger.stage("==================================================")


if __name__ == "__main__":
    from config import REPORT_FILE_PATH

    input_filepath = "base_de_dados.xlsx"
    report_filepath = REPORT_FILE_PATH
    output_filepath = "dados_estruturados.xlsx"

    print("🚀 Iniciando processamento...")
    print(f"   - Arquivo de entrada: {input_filepath}")
    print(f"   - Relatório externo: {report_filepath}")
    print(f"   - Arquivo de saída: {output_filepath}")

    main(input_filepath, report_filepath, output_filepath, analysis_year=2025)
