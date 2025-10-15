# data_processor.py
# Módulo principal para o processamento e tratamento dos dados da planilha.

import pandas as pd
import copy
from utils import logger
from config import (
    COLUNAS_ETAPA1_PARA_MANTER, COLUNAS_ETAPA4_FINAIS, COLUNA_DATA_DOCUMENTO, 
    COLUNA_REFERENCIA, COLUNA_CONTA, COLUNA_MONTANTE, 
    CONTAS_MAPEAMENTO_ETAPA2, CONTAS_MAPEAMENTO_ETAPA4
)

class DataProcessor:
    """
    Classe responsável por orquestrar o processo de limpeza e transformação dos dados.
    """
    def __init__(self, filepath):
        """
        Inicializa o processador com o caminho do arquivo a ser lido.
        
        Args:
            filepath (str): Caminho para o arquivo .xlsx de entrada.
        """
        self.filepath = filepath
        self.df = None

    def load_data(self):
        """Carrega os dados da planilha Excel em um DataFrame pandas."""
        try:
            logger.info(f"Iniciando a leitura do arquivo: {self.filepath}")
            self.df = pd.read_excel(self.filepath)
            logger.info(f"Arquivo carregado com sucesso. {len(self.df)} linhas encontradas.\n")
            return True
        except FileNotFoundError:
            logger.error(f"Erro: O arquivo '{self.filepath}' não foi encontrado.")
            return False
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado ao ler o arquivo: {e}")
            return False

    def filter_by_date_step1(self):
        """(Etapa 1) Remove linhas com data vazia ou do ano de 2023."""
        if self.df is None: return
        logger.info("Iniciando etapa 1 - filtragem por data.")
        initial_rows = len(self.df)
        self.df.dropna(subset=[COLUNA_DATA_DOCUMENTO], inplace=True)
        rows_after_na = len(self.df)
        logger.info(f"  - {initial_rows - rows_after_na} linhas removidas por data vazia.")
        
        self.df[COLUNA_DATA_DOCUMENTO] = pd.to_datetime(self.df[COLUNA_DATA_DOCUMENTO], errors='coerce')
        rows_before_coerce_drop = len(self.df)
        self.df.dropna(subset=[COLUNA_DATA_DOCUMENTO], inplace=True)
        logger.info(f"  - {rows_before_coerce_drop - len(self.df)} linhas removidas por erro de conversão de data.")
        
        rows_before_year_filter = len(self.df)
        self.df = self.df[self.df[COLUNA_DATA_DOCUMENTO].dt.year != 2023]
        logger.info(f"  - {rows_before_year_filter - len(self.df)} linhas removidas por pertencerem ao ano de 2023.")

    def select_columns_step1(self):
        """Seleciona apenas as colunas especificadas para a Etapa 1."""
        if self.df is None: return
        logger.info(f"Selecionando as colunas para Etapa 1: {', '.join(COLUNAS_ETAPA1_PARA_MANTER)}")
        try:
            self.df = self.df[COLUNAS_ETAPA1_PARA_MANTER]
        except KeyError as e:
            logger.error(f"Erro: Uma das colunas para a Etapa 1 não foi encontrada. Detalhes: {e}")
            raise

    def treat_reference_column(self):
        """Aplica os tratamentos na coluna 'Referência'."""
        if self.df is None: return
        logger.info("Iniciando o tratamento da coluna 'Referência'.")
        # Garante que a coluna 'Referência' seja tratada como string para manipulação
        initial_rows = len(self.df)
        self.df[COLUNA_REFERENCIA] = self.df[COLUNA_REFERENCIA].astype(str).str.split('-').str[0].str.strip()
        logger.info("  - Removidos sufixos após '-' e espaços em branco na coluna 'Referência'.")
        
        # Converte para numérico, descartando o que não for conversível (ex: textos)
        self.df[COLUNA_REFERENCIA] = pd.to_numeric(self.df[COLUNA_REFERENCIA], errors='coerce')
        self.df.dropna(subset=[COLUNA_REFERENCIA], inplace=True)
        logger.info(f"  - {initial_rows - len(self.df)} linhas removidas por valores não numéricos na 'Referência'.")
        self.df[COLUNA_REFERENCIA] = self.df[COLUNA_REFERENCIA].astype(int)

    def format_date_columns(self, dataframe):
        """Formata as colunas de data de um dataframe para o formato dd/mm/aaaa."""
        if dataframe is None: return None
        df_formatted = dataframe.copy()
        date_columns = ['Data do documento', 'Data de lançamento', 'Data de compensação']
        for col in date_columns:
            if col in df_formatted.columns:
                # Converte para datetime, formata, e preenche os não-convertidos com string vazia
                df_formatted[col] = pd.to_datetime(df_formatted[col], errors='coerce').dt.strftime('%d/%m/%Y')
                df_formatted[col] = df_formatted[col].fillna('')
        return df_formatted

    def process_step1(self):
        """Executa o pipeline da primeira etapa de processamento."""
        if self.load_data():
            self.filter_by_date_step1()
            self.select_columns_step1()
            self.treat_reference_column()
            logger.info("Processamento da Etapa 1 concluído.\n")
            return self.df
        return None

    def process_step2(self, dataframe):
        """(Etapa 2) Filtra dados para o ano de 2025 e divide o DataFrame por conta."""
        if dataframe is None or dataframe.empty:
            logger.warning("DataFrame de entrada para Etapa 2 está vazio. Pulando.")
            return {}
        logger.info("Iniciando Etapa 2: Filtragem por ano de 2025 e divisão por conta.")
        df_step2 = dataframe.copy()
        # Assegura que a coluna de data esteja no formato datetime para o filtro de ano
        df_step2[COLUNA_DATA_DOCUMENTO] = pd.to_datetime(df_step2[COLUNA_DATA_DOCUMENTO], errors='coerce', dayfirst=True)
        df_step2.dropna(subset=[COLUNA_DATA_DOCUMENTO], inplace=True)
        
        df_2025 = df_step2[df_step2[COLUNA_DATA_DOCUMENTO].dt.year == 2025].copy()
        logger.info(f"Encontradas {len(df_2025)} linhas para o ano de 2025.")

        sheets_data = {}
        for conta, nome_aba in CONTAS_MAPEAMENTO_ETAPA2.items():
            logger.info(f"Filtrando dados para a conta {conta} -> Aba '{nome_aba}'")
            
            # --- AJUSTE PARA ETAPA ATUAL ---
            # Regra especial para a conta do Ceará (303264)
            if conta == 303264:
                # Inclui tanto os dados da conta 303264 (Ceará) quanto 302282 (Bahia)
                contas_para_incluir = [303264, 302282]
                df_conta = df_2025[df_2025[COLUNA_CONTA].isin(contas_para_incluir)].copy()
                logger.info(f"Regra especial aplicada: Incluindo dados das contas {contas_para_incluir}.")
            else:
                # Lógica padrão para as outras contas
                df_conta = df_2025[df_2025[COLUNA_CONTA] == conta].copy()
            
            sheets_data[nome_aba] = df_conta
            logger.info(f"Encontradas {len(df_conta)} linhas para a aba '{nome_aba}'.")

        logger.info("Etapa 2 concluida.\n")

        return sheets_data

    def process_steps_3_and_4(self, sheets_data_step2):
        """(Etapas 3 e 4) Executa os tratamentos sequenciais para gerar as abas finais."""
        logger.info("Iniciando Etapas 3 e 4: Tratamento final das abas por estado.")
        final_sheets = {}

        # Mapeia o nome da aba da etapa 2 para o nome da aba da etapa 4
        step2_to_step4_map = {v: CONTAS_MAPEAMENTO_ETAPA4[k] for k, v in CONTAS_MAPEAMENTO_ETAPA2.items()}
        
        for sheet_name_step2, df in sheets_data_step2.items():
            if df is None or df.empty:
                logger.warning(f"DataFrame para a aba '{sheet_name_step2}' está vazio. Pulando etapas 3 e 4.")
                continue
            
            df_copy = df.copy()
            final_sheet_name = step2_to_step4_map.get(sheet_name_step2, sheet_name_step2 + "_final")
            logger.info(f"--- Processando '{sheet_name_step2}' para gerar a aba '{final_sheet_name}' ---")
            
            # --- ETAPA 3: Filtrar e excluir linhas ---
            ref_counts = df_copy[COLUNA_REFERENCIA].value_counts()
            unique_refs = ref_counts[ref_counts == 1].index
            df_copy[COLUNA_MONTANTE] = pd.to_numeric(df_copy[COLUNA_MONTANTE], errors='coerce').fillna(0)
            indices_to_drop = df_copy[
                (df_copy[COLUNA_REFERENCIA].isin(unique_refs)) & 
                (df_copy[COLUNA_MONTANTE] > 0)
            ].index
            df_after_step3 = df_copy.drop(indices_to_drop)
            logger.info(f"[{final_sheet_name}] Etapa 3: {len(indices_to_drop)} linhas removidas (referências únicas com montante > 0).")

            # --- ETAPA 4 - Parte 1: Limpeza e formatação final ---
            df_after_step4 = df_after_step3.copy()
            initial_rows = len(df_after_step4)
            df_after_step4.drop_duplicates(subset=[COLUNA_REFERENCIA], keep='first', inplace=True)
            logger.info(f"[{final_sheet_name}] Etapa 4: {initial_rows - len(df_after_step4)} linhas duplicadas removidas com base na 'Referência'.")
            
            df_after_step4.loc[:, 'Valor pagamento'] = 0.0
            
            try:
                df_final_cols = df_after_step4[COLUNAS_ETAPA4_FINAIS].copy()
                logger.info(f"[{final_sheet_name}] Etapa 4: Colunas reordenadas para a estrutura final.")
            except KeyError as e:
                logger.error(f"[{final_sheet_name}] Erro ao selecionar colunas finais: {e}.")
                continue

            # --- ETAPA 4 - Parte 2 (Continuação): Preenchimento de colunas ---
            logger.info(f"[{final_sheet_name}] Etapa 4: Preenchendo 'Valor pagamento' com base na soma de '{sheet_name_step2}'.")
            df_intermediario = sheets_data_step2.get(sheet_name_step2)

            if df_intermediario is not None and not df_intermediario.empty:
                somas_por_referencia = df_intermediario.groupby(COLUNA_REFERENCIA)[COLUNA_MONTANTE].sum()
                df_final_cols['Valor pagamento'] = df_final_cols[COLUNA_REFERENCIA].map(somas_por_referencia).fillna(0)
            
            logger.info(f"[{final_sheet_name}] Etapa 4: Formatando e preenchendo 'Data de compensação'.")
            df_final_cols['Data de compensação'] = pd.to_datetime(df_final_cols['Data de compensação'], errors='coerce').dt.strftime('%d/%m/%Y')
            
            df_final_cols['Data de compensação'] = df_final_cols['Data de compensação'].fillna('Não compensado')
            
            final_sheets[final_sheet_name] = df_final_cols
        
        return final_sheets