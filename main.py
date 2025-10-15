# main.py
# Ponto de entrada do sistema para processar as planilhas.

import pandas as pd
from utils import logger

def main(input_file, report_file, output_file):
    """
    Função principal que orquestra todo o processo de ETL e Análise.
    """
    logger.info("==================================================")
    logger.info(f"Iniciando novo ciclo de processamento.")
    
    # Adia as importações para dentro da função para evitar dependências circulares
    from data_processor import DataProcessor
    from report_processor import ReportProcessor
    from analysis_processor import AnalysisProcessor

    # --- FASE 1: Processamento do arquivo base ---
    data_proc = DataProcessor(input_file)
    processed_df_step1 = data_proc.process_step1()

    if processed_df_step1 is not None:
        sheets_data_step2 = data_proc.process_step2(processed_df_step1)
        final_sheets_step4 = data_proc.process_steps_3_and_4(sheets_data_step2)

        # --- FASE 2: Processamento do relatório externo ---
        report_proc = ReportProcessor(report_file)
        report_df = report_proc.process()

        # --- FASE 3: Análise e Cruzamento de Dados ---
        if report_df is not None:
            analyzer = AnalysisProcessor()
            logger.info("--- INICIANDO ETAPA DE ANÁLISE (CRUZAMENTO DE DADOS) ---")
            # O analisador recebe o relatório limpo e as abas de lookup para cruzar os dados
            analyzed_report_df = analyzer.run_analysis(report_df, final_sheets_step4)
            logger.info("--- ANÁLISE CONCLUÍDA. ---")
        else:
            logger.warning("O relatório externo não pôde ser processado. A etapa de análise será pulada.")
            analyzed_report_df = None # Garante que nada seja salvo se o relatório falhar

        # --- FASE 4: Salvamento ---
        try:
            logger.info(f"\nIniciando a gravação do arquivo de saída: '{output_file}'")
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Salva o resultado da primeira etapa
                formatted_df_step1 = data_proc.format_date_columns(processed_df_step1)
                if formatted_df_step1 is not None and not formatted_df_step1.empty:
                    formatted_df_step1.to_excel(writer, sheet_name='Dados Consolidados', index=False)
                    logger.info("Aba 'Dados Consolidados' salva.")

                # Salva os resultados da Etapa 2 (abas intermediárias)
                if sheets_data_step2:
                    for sheet_name, df in sheets_data_step2.items():
                        formatted_sheet = data_proc.format_date_columns(df)
                        if formatted_sheet is not None and not formatted_sheet.empty:
                            formatted_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
                            logger.info(f"Aba intermediária '{sheet_name}' salva.")
                
                # Salva os resultados da Etapa 4 (abas finais de lookup)
                if final_sheets_step4:
                    for sheet_name, df in final_sheets_step4.items():
                        if df is not None and not df.empty:
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            logger.info(f"Aba de lookup '{sheet_name}' salva.")
                
                # Salva o relatório analisado
                if analyzed_report_df is not None and not analyzed_report_df.empty:
                    analyzed_report_df.to_excel(writer, sheet_name='Dados Relatorio Externo', index=False)
                    logger.info("Aba 'Dados Relatorio Externo' salva.")

            logger.info(f"Arquivo multipágina salvo com sucesso em: '{output_file}'")
        except Exception as e:
            logger.error(f"Não foi possível salvar o arquivo de saída. Erro: {e}", exc_info=True)
    else:
        logger.warning("Nenhum dado foi processado na Etapa 1. O arquivo de saída não será gerado.")
    
    logger.info("Fim do processamento.")
    logger.info("==================================================\n")

if __name__ == "__main__":
    from config import REPORT_FILE_PATH
    
    input_filepath = 'base_de_dados.xlsx'
    report_filepath = REPORT_FILE_PATH
    output_filepath = 'dados_estruturados.xlsx'
    
    main(input_filepath, report_filepath, output_filepath)

