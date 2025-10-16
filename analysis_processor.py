# analysis_processor.py
# Módulo responsável por cruzar e analisar dados de diferentes fontes já processadas.

import pandas as pd
from utils import logger

class AnalysisProcessor:
    """
    Classe para executar a lógica de negócio que envolve o cruzamento de dados
    entre o relatório externo e os dados de pagamentos processados.
    """
    def __init__(self):
        """Inicializa o processador de análise."""
        logger.info("Processador de Análise inicializado.")

    def _populate_payment_status(self, report_df, final_sheets_data):
        """
        (Análise) Preenche a coluna 'Status pgto' cruzando dados com as abas de lookup.
        
        Args:
            report_df (pd.DataFrame): O DataFrame do relatório já limpo.
            final_sheets_data (dict): Dicionário com os DataFrames de lookup (ex: {'Bahia': df_bahia}).
        
        Returns:
            pd.DataFrame: O DataFrame do relatório com a coluna 'Status pgto' preenchida.
        """
        logger.info("Iniciando o cruzamento de dados para preencher a coluna 'Status pgto'.")
        
        df = report_df.copy()
        df['CTRC'] = pd.to_numeric(df['CTRC'], errors='coerce').astype('Int64')

        # Mapeamento de transportadora para nome da aba
        transportadora_to_sheet_map = {
            'Logtudo Bahia': 'Bahia',
            'Logtudo Ceará': 'Ceará',
            'Logtudo Pernambuco': 'Pernambuco'
        }
        
        # Lista para armazenar os resultados de cada merge
        all_merged_dfs = []
        processed_transportadoras = set()

        for transportadora, sheet_name in transportadora_to_sheet_map.items():
            report_subset = df[df['Transportadora'] == transportadora]
            if report_subset.empty:
                continue
            
            processed_transportadoras.add(transportadora)
            lookup_df = final_sheets_data.get(sheet_name)

            if lookup_df is None or lookup_df.empty:
                logger.warning(f"Aba de lookup '{sheet_name}' está vazia. Status para '{transportadora}' será 'Não lançado'.")
                report_subset = report_subset.copy()
                report_subset['Status pgto'] = 'Não lançado'
                all_merged_dfs.append(report_subset)
                continue

            lookup_prepared = lookup_df[['Referência', 'Data de compensação']].copy()
            lookup_prepared['Referência'] = pd.to_numeric(lookup_prepared['Referência'], errors='coerce').astype('Int64')
            
            merged = pd.merge(report_subset, lookup_prepared, left_on='CTRC', right_on='Referência', how='left')
            merged['Status pgto'] = merged['Data de compensação'].fillna('Não lançado')
            merged.drop(columns=['Referência', 'Data de compensação'], inplace=True)
            all_merged_dfs.append(merged)
        
        # Concatena os resultados e retorna
        if all_merged_dfs:
            final_df = pd.concat(all_merged_dfs, ignore_index=True)
            logger.info("Coluna 'Status pgto' preenchida com sucesso.")
            return final_df
        else:
            logger.warning("Nenhum dado processado para 'Status pgto'.")
            return df

    def _populate_payment_values(self, report_df, final_sheets_data):
        """
        (Análise) Preenche as colunas 'Valor pago', 'Valor recebido' e 'diferença'.
        
        Args:
            report_df (pd.DataFrame): DataFrame do relatório (já com 'Status pgto' preenchido).
            final_sheets_data (dict): Dicionário com os DataFrames de lookup.
        
        Returns:
            pd.DataFrame: DataFrame do relatório com as colunas de pagamento preenchidas.
        """
        logger.info("Iniciando o preenchimento das colunas 'Valor pago', 'Valor recebido' e 'diferença'.")
        df = report_df.copy()

        # Mapeamento de transportadora para nome da aba
        transportadora_to_sheet_map = {
            'Logtudo Bahia': 'Bahia',
            'Logtudo Ceará': 'Ceará',
            'Logtudo Pernambuco': 'Pernambuco'
        }
        
        # Garante que as colunas de valor sejam do tipo 'object' para aceitar textos e números
        df[['Valor pago', 'Valor recebido']] = df[['Valor pago', 'Valor recebido']].astype(object)

        # 1. Preenchimento de 'Valor pago' (lógica similar ao PROCV)
        for transportadora, sheet_name in transportadora_to_sheet_map.items():
            lookup_df = final_sheets_data.get(sheet_name)
            if lookup_df is None or lookup_df.empty:
                logger.warning(f"Aba de lookup '{sheet_name}' para 'Valor pago' está vazia.")
                continue

            # Cria um dicionário de mapeamento: {Referência: Valor pagamento}
            lookup_map = lookup_df.set_index('Referência')['Valor pagamento'].to_dict()
            
            # Identifica as linhas correspondentes à transportadora atual
            mask = df['Transportadora'] == transportadora
            # Aplica o mapeamento e preenche com 'Não lançado' onde não houver correspondência
            df.loc[mask, 'Valor pago'] = df.loc[mask, 'CTRC'].map(lookup_map).fillna('Não lançado')
        
        logger.info("Coluna 'Valor pago' preenchida.")

        # 2. Preenchimento de 'Valor recebido' com base no módulo de 'Valor pago'
        logger.info("Preenchendo a coluna 'Valor recebido' com base no módulo de 'Valor pago'.")
        
        # Converte 'Valor pago' para numérico, transformando textos (ex: 'Não lançado') em NaN
        valor_pago_numeric = pd.to_numeric(df['Valor pago'], errors='coerce')
        
        # Calcula o valor absoluto (módulo) onde 'Valor pago' é numérico
        df['Valor recebido'] = valor_pago_numeric.abs()
        
        # Onde o valor original não era numérico (resultando em NaN), preenche com '-'
        df['Valor recebido'] = df['Valor recebido'].fillna('-')
        logger.info("Coluna 'Valor recebido' preenchida.")

        # 3. Cálculo da 'diferença'
        logger.info("Calculando a coluna 'diferença' ('Valor CTe' - 'Valor recebido').")
        # Converte 'Valor CTe' para numérico, tratando erros e preenchendo nulos com 0.
        valor_cte_numeric = pd.to_numeric(df['Valor CTe'], errors='coerce').fillna(0)
        # Converte 'Valor recebido' para numérico, tratando o texto '-' como 0.
        valor_recebido_numeric = pd.to_numeric(df['Valor recebido'], errors='coerce').fillna(0)
        
        # Realiza a subtração para calcular a diferença.
        df['diferença'] = valor_cte_numeric - valor_recebido_numeric
        logger.info("Coluna 'diferença' calculada com sucesso.")

        return df

    def run_analysis(self, report_df, final_sheets_data):
        """
        Orquestra todas as etapas de análise e cruzamento de dados.
        
        Args:
            report_df (pd.DataFrame): DataFrame do relatório limpo.
            final_sheets_data (dict): Dicionário com os DataFrames de lookup.
        
        Returns:
            pd.DataFrame: DataFrame final, totalmente analisado.
        """
        if report_df is None or report_df.empty:
            logger.warning("DataFrame do relatório está vazio. Nenhuma análise será executada.")
            return report_df
        if not final_sheets_data:
            logger.warning("Dados de lookup (abas finais) estão vazios. A análise será limitada.")
            # Mesmo sem lookup, ainda podemos preencher as outras colunas
            report_df['Status pgto'] = 'Não lançado'
            report_df['Valor pago'] = 'Não lançado'
            report_df['Valor recebido'] = '-' # Se não há lookup, não há valor pago
            report_df['diferença'] = pd.to_numeric(report_df['Valor CTe'], errors='coerce').fillna(0)
            return report_df

        # Etapa 1 da Análise: Preencher Status de Pagamento
        df_with_status = self._populate_payment_status(report_df, final_sheets_data)

        # Etapa 2 da Análise: Preencher Valores de Pagamento e Calcular Diferença
        final_analyzed_df = self._populate_payment_values(df_with_status, final_sheets_data)
        
        return final_analyzed_df
