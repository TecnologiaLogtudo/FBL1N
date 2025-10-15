# main.py
# Ponto de entrada do sistema para processar a planilha.

import pandas as pd
from utils import logger
from config import REPORT_FILE_PATH

def main(input_file, report_file, output_file):
    """
    Função principal que executa o processo de ETL da planilha.

    Args:
        input_file (str): Caminho do arquivo .xlsx de entrada.
        report_file (str): Caminho do arquivo .xls do relatório.
        output_file (str): Caminho onde o arquivo .xlsx processado será salvo.
    """
    # Imports locais para resolver potenciais dependências circulares
    from data_processor import DataProcessor
    from report_processor import ReportProcessor
    
    logger.info("==================================================")
    logger.info(f"Iniciando novo processamento do arquivo: {input_file}")
    
    processor = DataProcessor(input_file)
    
    # Etapa 1: Processamento inicial do arquivo principal
    processed_df_step1 = processor.process_step1()

    if processed_df_step1 is not None:
        # Etapa 2: Filtrar por 2025 e dividir por conta
        sheets_data_step2 = processor.process_step2(processed_df_step1)

        # Etapas 3 e 4: Aplicar tratamentos sequenciais
        final_sheets_step4 = processor.process_steps_3_and_4(sheets_data_step2)
        
        # Etapa 5: Processar o relatório externo
        report_processor = ReportProcessor(report_file)
        df_report = report_processor.process()

        try:
            logger.info(f"\nIniciando a gravação do arquivo de saída: '{output_file}'")
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 1. Salva o resultado da primeira etapa
                formatted_df_step1 = processor.format_date_columns(processed_df_step1)
                if formatted_df_step1 is not None and not formatted_df_step1.empty:
                    formatted_df_step1.to_excel(writer, sheet_name='Dados Consolidados', index=False)
                    logger.info("Aba 'Dados Consolidados' salva com sucesso.")

                # 2. Salva os resultados da Etapa 2
                if sheets_data_step2:
                    for sheet_name, df_sheet in sheets_data_step2.items():
                        formatted_sheet = processor.format_date_columns(df_sheet)
                        if formatted_sheet is not None and not formatted_sheet.empty:
                            formatted_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
                            logger.info(f"Aba intermediária (Etapa 2) '{sheet_name}' salva com sucesso.")
                
                # 3. Salva os resultados finais da Etapa 4
                if final_sheets_step4:
                    for sheet_name, df_sheet in final_sheets_step4.items():
                        if df_sheet is not None and not df_sheet.empty:
                            df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
                            logger.info(f"Aba final (Etapa 4) '{sheet_name}' salva com sucesso.")

                # 4. Salva o resultado do relatório externo processado
                if df_report is not None and not df_report.empty:
                    df_report.to_excel(writer, sheet_name='Dados Relatorio Externo', index=False)
                    logger.info("Aba 'Dados Relatorio Externo' salva com sucesso.")

            logger.info(f"Arquivo multipágina salvo com sucesso em: '{output_file}'")
        except Exception as e:
            logger.error(f"Não foi possível salvar o arquivo de saída. Erro: {e}")
    else:
        logger.warning("Nenhum dado foi processado na Etapa 1, o arquivo de saída não será gerado.")
    
    logger.info("Fim do processamento.")
    logger.info("==================================================\n")


if __name__ == "__main__":
    input_filepath = 'base_de_dados.xlsx'
    report_filepath = REPORT_FILE_PATH # Usando o caminho definido no config
    output_filepath = 'dados_estruturados.xlsx'
    
    main(input_filepath, report_filepath, output_filepath)
