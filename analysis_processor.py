# analysis_processor.py
# 5º Etapa: Cruzamento e Análise de Dados
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
        # Converte a coluna de junção para um tipo numérico que suporta valores nulos (Int64)
        df['CTRC'] = pd.to_numeric(df['CTRC'], errors='coerce').astype('Int64')

        # Mapeamento de transportadora para nome da aba
        transportadora_to_sheet_map = {
            'Logtudo Bahia': 'Bahia',
            'Logtudo Ceará': 'Ceará',
            'Logtudo Pernambuco': 'Pernambuco'
        }
        
        # Lista para armazenar os resultados de cada merge
        all_merged_dfs = []
        # Conjunto para rastrear quais transportadoras foram processadas
        processed_transportadoras = set()

        for transportadora, sheet_name in transportadora_to_sheet_map.items():
            # Isola o subconjunto de dados do relatório para a transportadora atual
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

            # Prepara o DataFrame de lookup para o merge, selecionando apenas as colunas necessárias
            lookup_prepared = lookup_df[['Referência', 'Data de compensação']].copy()
            lookup_prepared['Referência'] = pd.to_numeric(lookup_prepared['Referência'], errors='coerce').astype('Int64')
            
            # Executa a junção (merge), que é a forma eficiente de fazer o "PROCV"
            merged = pd.merge(report_subset, lookup_prepared, left_on='CTRC', right_on='Referência', how='left')

            # Preenche a coluna 'Status pgto': onde a junção encontrou uma correspondência, usa 'Data de compensação'.
            # Onde não encontrou (gerando NaT/NaN), preenche com 'Não lançado'.
            merged['Status pgto'] = merged['Data de compensação'].fillna('Não lançado')

            # Remove as colunas auxiliares do merge
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
        (Análise) Preenche as colunas 'Valor pago', 'Recebido/A receber' e 'diferença'.
        
        Args:
            report_df (pd.DataFrame): DataFrame do relatório (já com 'Status pgto' preenchido).
            final_sheets_data (dict): Dicionário com os DataFrames de lookup.
        
        Returns:
            pd.DataFrame: DataFrame do relatório com as colunas de pagamento preenchidas.
        """
        logger.info("Iniciando o preenchimento das colunas 'Valor pago', 'Recebido/A receber' e 'diferença'.")
        df = report_df.copy()

        # Mapeamento de transportadora para nome da aba
        transportadora_to_sheet_map = {
            'Logtudo Bahia': 'Bahia',
            'Logtudo Ceará': 'Ceará',
            'Logtudo Pernambuco': 'Pernambuco'
        }
        
        # Garante que as colunas de valor sejam do tipo 'object' para aceitar textos e números
        df[['Valor pago', 'Recebido/A receber']] = df[['Valor pago', 'Recebido/A receber']].astype(object)

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

        # 2. Preenchimento de 'Recebido/A receber' com base no módulo de 'Valor pago'
        logger.info("Preenchendo a coluna 'Recebido/A receber' com base no módulo de 'Valor pago'.")
        
        # Lógica para 'Recebido/A receber':
        # Se 'Status pgto' for 'Não lançado', copia 'Valor CTe'.
        # Se 'Valor pago' não for numérico (ex: 'Não compensado'), usa '-'.
        # Caso contrário, usa o valor absoluto de 'Valor pago'.
        
        # Inicializa a coluna 'Recebido/A receber' com NaN para facilitar o preenchimento condicional
        df['Recebido/A receber'] = pd.NA

        # Condição 1: 'Status pgto' é 'Não lançado'
        mask_nao_lancado = df['Status pgto'] == 'Não lançado'
        df.loc[mask_nao_lancado, 'Recebido/A receber'] = df.loc[mask_nao_lancado, 'Valor CTe']

        # Condição 2: 'Valor pago' não é numérico (e não foi tratado pela condição 1)
        # Converte 'Valor pago' para numérico, transformando textos em NaN
        valor_pago_numeric = pd.to_numeric(df['Valor pago'], errors='coerce')
        mask_nao_numerico_valor_pago = valor_pago_numeric.isna() & ~mask_nao_lancado
        df.loc[mask_nao_numerico_valor_pago, 'Recebido/A receber'] = '-'

        # Condição 3: 'Valor pago' é numérico (e não foi tratado pelas condições anteriores)
        mask_numerico_valor_pago = valor_pago_numeric.notna() & ~mask_nao_lancado & ~mask_nao_numerico_valor_pago
        df.loc[mask_numerico_valor_pago, 'Recebido/A receber'] = valor_pago_numeric.abs()
        
        logger.info("Coluna 'Recebido/A receber' preenchida.")

        # 3. Cálculo da 'diferença'
        logger.info("Calculando a coluna 'diferença' ('Valor CTe' - 'Recebido/A receber').")
        # Converte 'Valor CTe' para numérico, tratando erros e preenchendo nulos com 0.
        valor_cte_numeric = pd.to_numeric(df['Valor CTe'], errors='coerce').fillna(0)
        # Converte 'Recebido/A receber' para numérico, tratando o texto '-' como 0.
        valor_recebido_numeric = pd.to_numeric(df['Recebido/A receber'], errors='coerce').fillna(0)
        
        # Realiza a subtração para calcular a diferença.
        df['diferença'] = valor_cte_numeric - valor_recebido_numeric
        logger.info("Coluna 'diferença' calculada com sucesso.\n")

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
            report_df['Recebido/A receber'] = '-' # Se não há lookup, não há valor pago
            report_df['diferença'] = pd.to_numeric(report_df['Valor CTe'], errors='coerce').fillna(0)
            return report_df

        # Etapa 1 da Análise: Preencher Status de Pagamento
        df_with_status = self._populate_payment_status(report_df, final_sheets_data)

        # Etapa 2 da Análise: Preencher Valores de Pagamento e Calcular Diferença
        final_analyzed_df = self._populate_payment_values(df_with_status, final_sheets_data)
        
        return final_analyzed_df
