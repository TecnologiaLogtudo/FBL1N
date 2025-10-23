# main.py
# Ponto de entrada do sistema para processar as planilhas.

import pandas as pd
from utils import logger

def main(input_file, report_file, output_file, progress_callback=None):
    """
    Função principal que orquestra todo o processo de ETL e Análise.
    """
    logger.stage("===================================================")
    logger.stage(f"Iniciando novo ciclo de processamento...")
    if progress_callback: progress_callback(0.05)
    
    # Adia as importações para dentro da função para evitar dependências circulares
    from data_processor import DataProcessor
    from report_processor import ReportProcessor
    from analysis_processor import AnalysisProcessor
    from final_report_generator import FinalReportGenerator

    # --- FASE 1: Processamento do arquivo base ---
    logger.stage("FASE 1: Processando arquivo base...\n")
    data_proc = DataProcessor(input_file)
    processed_df_step1 = data_proc.process_step1()
    if progress_callback: progress_callback(0.2)

    if processed_df_step1 is not None:
        sheets_data_step2 = data_proc.process_step2(processed_df_step1)
        if progress_callback: progress_callback(0.3)
        final_sheets_step4 = data_proc.process_steps_3_and_4(sheets_data_step2)
        if progress_callback: progress_callback(0.4)

        # --- FASE 2: Processamento do relatório externo ---
        logger.stage("FASE 2: Processando relatório externo...\n")
        report_proc = ReportProcessor(report_file)
        report_df = report_proc.process()
        if progress_callback: progress_callback(0.5)

        # --- FASE 3: Análise e Cruzamento de Dados ---
        if report_df is not None:
            analyzer = AnalysisProcessor()
            logger.stage("FASE 3: Cruzando dados...\n")
            analyzed_report_df = analyzer.run_analysis(report_df, final_sheets_step4)
            if progress_callback: progress_callback(0.7)
        else:
            logger.warning("O relatório externo não pôde ser processado. A etapa de análise será pulada.")
            analyzed_report_df = None

        # --- FASE 4: Salvamento ---
        try:
            logger.stage(f"FASE 4: Gerando arquivo de saída: '{output_file}'")
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                if processed_df_step1 is not None and not processed_df_step1.empty:
                    data_proc.format_date_columns(processed_df_step1).to_excel(writer, sheet_name='Dados Consolidados', index=False)

                if sheets_data_step2:
                    for sheet_name, df in sheets_data_step2.items():
                        if df is not None and not df.empty:
                            data_proc.format_date_columns(df).to_excel(writer, sheet_name=sheet_name, index=False)
                
                if final_sheets_step4:
                    for sheet_name, df in final_sheets_step4.items():
                        if df is not None and not df.empty:
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                if analyzed_report_df is not None and not analyzed_report_df.empty:
                    analyzed_report_df.to_excel(writer, sheet_name='Dados Relatorio Externo', index=False)
                
                if progress_callback: progress_callback(0.8)

                # --- FASE 5: Geração do relatório final ---
                if analyzed_report_df is not None and not analyzed_report_df.empty:                    
                    logger.stage("FASE 5: Gerando relatório final consolidado...\n")
                    report_generator = FinalReportGenerator(analyzed_report_df)
                    report_generator.generate_report(writer)
                    if progress_callback: progress_callback(0.9)

            logger.success(f"Arquivo multipágina salvo com sucesso em: '{output_file}'")
            if progress_callback: progress_callback(1.0)

        except Exception as e:
            logger.error(f"Não foi possível salvar o arquivo de saída. Erro: {e}", exc_info=True)
    else:
            logger.warning("Nenhum dado foi processado na Etapa 1. O arquivo de saída não será gerado.")
    
    logger.stage("Fim do processamento.")
    logger.stage("==================================================\n")

if __name__ == "__main__":
    from config import REPORT_FILE_PATH
    
    input_filepath = 'base_de_dados.xlsx'
    report_filepath = REPORT_FILE_PATH
    output_filepath = 'dados_estruturados.xlsx'
    
    print(f"🚀 Iniciando processamento...")
    print(f"   - Arquivo de entrada: {input_filepath}")
    print(f"   - Relatório externo: {report_filepath}")
    print(f"   - Arquivo de saída: {output_filepath}")
    
    main(input_filepath, report_filepath, output_filepath)