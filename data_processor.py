# data_processor.py
# 1º Etapa: Processamento da Planilha Principal
# Módulo para o processamento da planilha principal (FBL1.xlsx).

import pandas as pd
from utils import logger
from config import (
    COLUNAS_ETAPA1_PARA_MANTER, COLUNAS_ETAPA4_FINAIS, COLUNA_DATA_DOCUMENTO,
    COLUNA_REFERENCIA, COLUNA_CONTA, COLUNA_MONTANTE,
    CONTAS_MAPEAMENTO_ETAPA2, CONTAS_MAPEAMENTO_ETAPA4
)

class DataProcessor:
    """
    Classe responsável por orquestrar o processo de limpeza e transformação 
    dos dados da planilha principal.
    """
    def __init__(self, filepath):
        """
        Inicializa o processador com o caminho do arquivo a ser lido.
        
        Args:
            filepath (str): Caminho para o arquivo .xlsx de entrada.
        """
        self.filepath = filepath  # Armazena o caminho do arquivo
        self.df = None            # DataFrame que será usado para manipulação

    def load_data(self):
        """Carrega os dados da planilha Excel em um DataFrame pandas."""
        try:
            logger.info("Iniciando a leitura do arquivo principal: %s", self.filepath)
            self.df = pd.read_excel(self.filepath)
            logger.info("Arquivo principal carregado com sucesso. %d linhas encontradas.\n", len(self.df))
            return True
        except FileNotFoundError:
            logger.error("Erro: O arquivo principal '%s' não foi encontrado.", self.filepath)
            return False
        except Exception as e:
            logger.error("Ocorreu um erro inesperado ao ler o arquivo principal: %s", e)
            return False

    def filter_by_date_step1(self):
        """(Etapa 1) Remove linhas com data vazia ou do ano de 2023."""
        if self.df is None: return
        logger.info("Filtrando por data (removendo vazios e ano 2023).")
        
        initial_rows = len(self.df)
        
        # Remove linhas onde a data do documento é nula
        self.df.dropna(subset=[COLUNA_DATA_DOCUMENTO], inplace=True)
        rows_after_na = len(self.df)
        logger.info("  - %d linhas removidas por data vazia.", initial_rows - rows_after_na)
        
        # Converte a coluna para o formato de data, tratando erros
        self.df[COLUNA_DATA_DOCUMENTO] = pd.to_datetime(self.df[COLUNA_DATA_DOCUMENTO], errors='coerce')
        
        # Remove linhas que não puderam ser convertidas para data
        rows_before_coerce_drop = len(self.df)
        self.df.dropna(subset=[COLUNA_DATA_DOCUMENTO], inplace=True)
        logger.info("  - %d linhas removidas por erro de conversão de data.", rows_before_coerce_drop - len(self.df))
        
        # Filtra para remover qualquer linha cujo ano seja 2023
        rows_before_year_filter = len(self.df)
        self.df = self.df[self.df[COLUNA_DATA_DOCUMENTO].dt.year != 2023]
        logger.info("  - %d linhas removidas por pertencerem ao ano de 2023.", rows_before_year_filter - len(self.df))

    def select_columns_step1(self):
        """(Etapa 1) Seleciona apenas as colunas especificadas para a Etapa 1."""
        if self.df is None: return
        
        # Verifica se a coluna 'Conta' existe. Se não, cria com valor padrão (Bahia).
        if COLUNA_CONTA not in self.df.columns:
            logger.warning(f"Coluna '{COLUNA_CONTA}' não encontrada. Aplicando regra de contingência: Assumindo conta 302282 (Bahia) para todos os registros.")
            self.df[COLUNA_CONTA] = 302282
            
        logger.info("Selecionando colunas: %s", ', '.join(COLUNAS_ETAPA1_PARA_MANTER))
        try:
            # Filtra o DataFrame para manter apenas as colunas desejadas
            self.df = self.df[COLUNAS_ETAPA1_PARA_MANTER]
        except KeyError as e:
            # Se uma coluna não for encontrada, o programa para com um erro claro
            logger.error(f"Erro Crítico: Uma das colunas para a Etapa 1 não foi encontrada. Detalhes: {e}")
            raise

    def treat_reference_column(self):
        """(Etapa 1) Aplica os tratamentos na coluna 'Referência'."""
        if self.df is None: return
        logger.info("Tratando a coluna 'Referência'.")
        initial_rows = len(self.df)
        
        # Converte para string, remove o traço e o que vem depois, e remove espaços
        self.df[COLUNA_REFERENCIA] = self.df[COLUNA_REFERENCIA].astype(str).str.split('-').str[0].str.strip()
        logger.info("  - Removidos sufixos após '-' na coluna 'Referência'.")
        
        # Converte para numérico. Valores que não são números (texto, etc.) se tornarão 'NaN'
        self.df[COLUNA_REFERENCIA] = pd.to_numeric(self.df[COLUNA_REFERENCIA], errors='coerce')
        
        # Remove linhas onde a 'Referência' se tornou nula (era texto ou vazia)
        self.df.dropna(subset=[COLUNA_REFERENCIA], inplace=True)
        logger.info("  - %d linhas removidas por valores não numéricos em 'Referência'.", initial_rows - len(self.df))
        
        # Converte a coluna para inteiro para remover casas decimais
        self.df[COLUNA_REFERENCIA] = self.df[COLUNA_REFERENCIA].astype(int)

    def format_date_columns(self, dataframe):
        """
        Formata as colunas de data de um dataframe para o formato dd/mm/aaaa.

        Args:
            dataframe (pd.DataFrame): O DataFrame a ser formatado.

        Returns:
            pd.DataFrame: O DataFrame com as colunas de data formatadas.
        """
        if dataframe is None: return None
        df_formatted = dataframe.copy()
        date_columns = ['Data do documento', 'Data de lançamento', 'Data de compensação']
        for col in date_columns:
            if col in df_formatted.columns:
                # Converte para datetime, formata para string e preenche valores nulos
                df_formatted[col] = pd.to_datetime(df_formatted[col], errors='coerce').dt.strftime('%d/%m/%Y')
                df_formatted[col] = df_formatted[col].fillna('')
        return df_formatted

    def process_step1(self):
        """Executa o pipeline da primeira etapa de processamento."""
        logger.stair("--- INICIANDO ETAPA 1: Processamento da Planilha Principal ---")
        if self.load_data():
            self.filter_by_date_step1()
            self.select_columns_step1()
            self.treat_reference_column()
            logger.success("--- Processamento da Etapa 1 concluído --- \n")
            return self.df
        return None

    def process_step2(self, dataframe, analysis_year):
        """(Etapa 2) Filtra dados para o ano selecionado e divide o DataFrame por conta."""
        if dataframe is None or dataframe.empty:
            logger.warning("DataFrame de entrada para Etapa 2 está vazio. Pulando etapa.")
            return {}
        
        logger.stair(f"--- INICIANDO ETAPA 2: Divisão por Conta para o Ano de {analysis_year} ---")
        df_step2 = dataframe.copy()
        
        # Garante que a coluna de data é do tipo datetime para filtrar pelo ano
        df_step2[COLUNA_DATA_DOCUMENTO] = pd.to_datetime(df_step2[COLUNA_DATA_DOCUMENTO], errors='coerce')
        df_step2.dropna(subset=[COLUNA_DATA_DOCUMENTO], inplace=True)
        
        df_filtered_year = df_step2[df_step2[COLUNA_DATA_DOCUMENTO].dt.year == analysis_year].copy()
        logger.info("Total de %d linhas encontradas para o ano de %d.\n", len(df_filtered_year), analysis_year)

        sheets_data = {}
        for conta, nome_aba in CONTAS_MAPEAMENTO_ETAPA2.items():
            logger.info("Filtrando dados para a conta %d para gerar a aba '%s'...", conta, nome_aba)
            
            # Condição especial para a conta do Ceará
            if conta == 303264:
                df_conta = df_filtered_year[df_filtered_year[COLUNA_CONTA].isin([303264, 302282])].copy()
                logger.info("  - Regra especial aplicada: Incluindo dados da conta 302282 (Bahia) na aba de Ceará.")
            else:
                df_conta = df_filtered_year[df_filtered_year[COLUNA_CONTA] == conta].copy()
            
            sheets_data[nome_aba] = df_conta
            logger.info("  - %d linhas separadas para a conta %d.", len(df_conta), conta)

        logger.success("--- Etapa 2 concluída --- \n")
        return sheets_data

    def process_steps_3_and_4(self, sheets_data_step2, analysis_year):
        """(Etapas 3 e 4) Executa os tratamentos sequenciais para gerar as abas finais, considerando o ano."""
        logger.stair("--- INICIANDO ETAPAS 3 e 4: Tratamento e Estruturação Final ---")
        final_sheets = {}
        step2_to_step4_map = {v: CONTAS_MAPEAMENTO_ETAPA4[k] for k, v in CONTAS_MAPEAMENTO_ETAPA2.items()}
        
        for sheet_name_step2, df in sheets_data_step2.items():
            if df is None or df.empty:
                logger.warning("DataFrame para a aba '%s' está vazio. Pulando etapas 3 e 4.", sheet_name_step2)
                continue
            
            df_copy = df.copy()
            final_sheet_name = step2_to_step4_map.get(sheet_name_step2, sheet_name_step2 + "_final")
            logger.info("\n--- Processando '%s' para gerar a aba '%s' ---", sheet_name_step2, final_sheet_name)
            
            # --- ETAPA 3: Filtrar e excluir linhas ---
            logger.info("[%s] Etapa 3: Identificando referências únicas com valor positivo para exclusão.", final_sheet_name)
            ref_counts = df_copy[COLUNA_REFERENCIA].value_counts()
            unique_refs = ref_counts[ref_counts == 1].index
            df_copy[COLUNA_MONTANTE] = pd.to_numeric(df_copy[COLUNA_MONTANTE], errors='coerce').fillna(0)
            
            indices_to_drop = df_copy[(df_copy[COLUNA_REFERENCIA].isin(unique_refs)) & (df_copy[COLUNA_MONTANTE] > 0)].index
            df_after_step3 = df_copy.drop(indices_to_drop)
            logger.info("[%s] Etapa 3: %d linhas removidas.", final_sheet_name, len(indices_to_drop))

            # --- ETAPA 4: Limpeza, formatação e preenchimento ---
            df_after_step4 = df_after_step3.copy()
            initial_rows = len(df_after_step4)
            df_after_step4.drop_duplicates(subset=[COLUNA_REFERENCIA], keep='first', inplace=True)
            logger.info("[%s] Etapa 4: %d linhas duplicadas removidas com base na 'Referência'.", final_sheet_name, initial_rows - len(df_after_step4))
            
            # Seleciona e reordena as colunas para o formato final
            try:
                df_final_cols = df_after_step4.reindex(columns=COLUNAS_ETAPA4_FINAIS).copy()
                logger.info("[%s] Etapa 4: Estrutura final de colunas aplicada.", final_sheet_name)
            except KeyError as e:
                logger.error("[%s] Erro ao selecionar colunas finais: %s.", final_sheet_name, e)
                continue

            # Preenchimento do 'Valor pagamento' (lógica SOMASE)
            logger.info("[%s] Etapa 4: Preenchendo 'Valor pagamento' com base na soma de '%s'.", final_sheet_name, sheet_name_step2)
            df_intermediario = sheets_data_step2.get(sheet_name_step2)
            if df_intermediario is not None and not df_intermediario.empty:
                somas_por_referencia = df_intermediario.groupby(COLUNA_REFERENCIA)[COLUNA_MONTANTE].sum()
                df_final_cols['Valor pagamento'] = df_final_cols[COLUNA_REFERENCIA].map(somas_por_referencia).fillna(0)
            
            # Preenchimento da 'Data de compensação'
            logger.info("[%s] Etapa 4: Formatando e preenchendo 'Data de compensação'.", final_sheet_name)
            df_final_cols['Data de compensação'] = pd.to_datetime(df_final_cols['Data de compensação'], errors='coerce').dt.strftime('%d/%m/%Y')
            df_final_cols['Data de compensação'] = df_final_cols['Data de compensação'].fillna('Não compensado')
            
            final_sheets[final_sheet_name] = df_final_cols
        
        logger.success("--- Etapas 3 e 4 concluídas ---\n")
        return final_sheets
