# report_processor.py
# Módulo para processar o relatório externo baixado do sistema web.

import pandas as pd
import numpy as np
import locale
from utils import logger
from config import REPORT_SKIP_ROWS, REPORT_COLUMN_INDICES, REPORT_FINAL_COLUMNS

class ReportProcessor:
    """
    Classe para carregar, limpar e estruturar os dados do relatório externo.
    """
    def __init__(self, filepath):
        """
        Inicializa o processador com o caminho do arquivo do relatório.
        
        Args:
            filepath (str): Caminho para o arquivo .xls do relatório.
        """
        self.filepath = filepath
        self.df = None

    def _clean_client_column(self):
        """(Tratamento) Aplica a regra de padronização na coluna 'Cliente'."""
        logger.info("Tratando coluna 'Cliente': Padronizando nomes 'ITAMBE' e 'LACTALIS'.")
        # Garante que a coluna seja do tipo string para manipulação
        cliente_series = self.df['Cliente'].astype(str)
        # Pega a primeira palavra, converte para minúsculas para uma comparação robusta
        first_word = cliente_series.str.split().str[0].str.lower()
        
        # Define as condições de busca
        conditions = [
            first_word.str.contains('itamb', na=False),   # Busca por 'itamb' (cobre Itambé, ITAMBE, etc.)
            first_word.str.contains('lactalis', na=False) # Busca por 'lactalis'
        ]
        # Define os valores de substituição
        choices = ['Itambé', 'Lactalis']
        
        # Usa np.select para aplicar as substituições de forma vetorizada
        self.df['Cliente'] = np.select(conditions, choices, default=self.df['Cliente'])
        logger.info("Coluna 'Cliente' padronizada com sucesso.")

    def _populate_service_column(self):
        """(Tratamento) Preenche a coluna 'Serviço' com base em regras da coluna 'DT Frete'."""
        logger.info("Preenchendo coluna 'Serviço' com base em 'DT Frete'.")
        dt_frete_series = self.df['DT Frete'].astype(str)
        
        # Define as condições em ordem de prioridade. Usamos `str.match` para correspondências exatas/iniciais
        # e `str.contains` para buscas mais flexíveis.
        conditions = [
            dt_frete_series.str.match(r'^\d+$', na=False),  # 1. Se for APENAS números
            dt_frete_series.str.upper() == 'DIARIA NO CLIENTE', # 2.
            dt_frete_series.str.startswith('REENTREGA', na=False), # 3.
            dt_frete_series.str.upper() == 'DIARIA PARADO', # 4.
            dt_frete_series.str.startswith('COMPLEMENTO', na=False), # 5.
            dt_frete_series.str.startswith('AVARIAS', na=False), # 6.
            dt_frete_series.str.upper() == 'PEDAGIO', # 7.
            dt_frete_series.str.upper() == 'PERNOITE', # 8.
            dt_frete_series.str.upper().str.contains('COLETA DE PALETE|COLETA DE PALLETE', na=False, regex=True), # 3. (continuação)
            dt_frete_series.str.upper() == 'DESCARGA', # 9. Nova regra
        ]
        
        choices = [
            'Frete',
            'Diária no cliente',
            'Reentrega',
            'Diária parado',
            'Complemento',
            'Descarga',
            'Pedágio',
            'Diária no cliente', # Regra 8 leva ao mesmo resultado da 2
            'Descarga',        # Regra 3 (continuação)
            'Descarga'         # Regra 9
        ]
        
        # Aplica as regras, preenchendo onde o 'Serviço' ainda está vazio
        self.df['Serviço'] = np.select(conditions, choices, default=self.df['Serviço'])
        logger.info("Coluna 'Serviço' preenchida com base nas regras definidas.")

    def _populate_transportadora_column(self):
        """(Tratamento) Preenche a coluna 'Transportadora' com base na 'UF Origem'."""
        logger.info("Preenchendo coluna 'Transportadora' com base na 'UF Origem'.")
        uf_series = self.df['UF Origem'].astype(str).str.upper()

        conditions = [
            uf_series == 'BA',
            uf_series == 'CE',
            uf_series == 'PE'
        ]
        choices = [
            'Logtudo Bahia',
            'Logtudo Ceará',
            'Logtudo Pernambuco'
        ]
        
        # Aplica as regras de mapeamento
        self.df['Transportadora'] = np.select(conditions, choices, default='')
        logger.info("Coluna 'Transportadora' preenchida com sucesso.")

    def _treat_dt_frete_column(self):
        """(Tratamento) Substitui valores não numéricos em 'DT Frete' por '-'."""
        logger.info("Limpando a coluna 'DT Frete', substituindo textos por '-'.")
        # Cria uma máscara booleana: True para linhas onde 'DT Frete' NÃO é puramente numérico
        is_not_numeric = ~self.df['DT Frete'].astype(str).str.match(r'^\d+$', na=False)
        # Usa .loc para atribuir '-' a essas linhas de forma segura
        self.df.loc[is_not_numeric, 'DT Frete'] = '-'
        logger.info("Coluna 'DT Frete' limpa.")

    def _treat_ctrc_column(self):
        """(Tratamento) Remove o prefixo '2025' e os zeros subsequentes da coluna CTRC."""
        logger.info("Tratando coluna 'CTRC' para remover prefixo '2025' e zeros à esquerda.")
        self.df['CTRC'] = self.df['CTRC'].astype(str)
        # Usa regex para remover o prefixo '2025' e quaisquer zeros que o sigam.
        # Ex: '202500123' vira '123'. '2025123' vira '123'. '20250000' vira ''.
        self.df['CTRC'] = self.df['CTRC'].str.replace(r'^20250*', '', regex=True)
        logger.info("Prefixo '2025' e zeros subsequentes removidos da coluna 'CTRC'.")

    def _filter_valor_cte(self):
        """(Filtro) Remove linhas onde 'Valor CTe' é zero."""
        logger.info("Removendo linhas onde 'Valor CTe' é 0 ou nulo.")
        initial_rows = len(self.df)
        # Converte para numérico, tratando erros e preenchendo nulos com 0
        self.df['Valor CTe'] = pd.to_numeric(self.df['Valor CTe'], errors='coerce').fillna(0)
        # Mantém apenas as linhas onde o valor é diferente de 0
        self.df = self.df[self.df['Valor CTe'] != 0].reset_index(drop=True)
        rows_removed = initial_rows - len(self.df)
        logger.info(f"{rows_removed} linhas foram removidas com 'Valor CTe' igual a 0.")

    def process(self):
        """
        Executa o pipeline completo de processamento para o relatório externo.
        """
        logger.info("--- INICIANDO ETAPA 5: Processamento do Relatório Externo ---")
        try:
            logger.info(f"Lendo o arquivo de relatório: {self.filepath}")
            df = pd.read_excel(self.filepath, header=None, skiprows=REPORT_SKIP_ROWS, engine='xlrd')
            logger.info(f"Arquivo lido, pulando as primeiras {REPORT_SKIP_ROWS} linhas.")

            logger.info("Consolidando cabeçalho de múltiplas linhas.")
            header_row1 = df.iloc[0].fillna("").astype(str)
            header_row2 = df.iloc[1].fillna("").astype(str)
            new_header = (header_row1 + " " + header_row2).str.strip()
            df.columns = new_header
            df = df.iloc[2:].reset_index(drop=True)
            logger.info("Cabeçalho consolidado e linhas de cabeçalho iniciais removidas.")

            logger.info(f"Selecionando colunas de interesse pelos índices: {REPORT_COLUMN_INDICES}")
            df_selected = df.iloc[:, REPORT_COLUMN_INDICES]

            logger.info("Renomeando colunas para os nomes padronizados.")
            df_selected.columns = REPORT_FINAL_COLUMNS
            self.df = df_selected.copy()
            
            # --- Sequência de Tratamentos ---
            self._treat_ctrc_column()
            self._clean_client_column()
            
            logger.info("Formatando a coluna 'Emissao' para o formato de data (dd/mm/aaaa).")
            self.df['Emissao'] = pd.to_datetime(self.df['Emissao'], errors='coerce').dt.strftime('%d/%m/%Y')
            
            logger.info("Adicionando e preparando novas colunas: Mês, Transportadora, Serviço.")
            try:
                locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            except locale.Error:
                logger.warning("Locale 'pt_BR.UTF-8' não disponível. Nomes dos meses podem aparecer em inglês.")
            
            dates = pd.to_datetime(self.df['Emissao'], format='%d/%m/%Y', errors='coerce')
            self.df['Mês'] = dates.dt.strftime('%B').str.capitalize()
            self.df['Transportadora'] = '' # Cria a coluna vazia primeiro
            self.df['Serviço'] = ''

            # Adiciona as novas colunas de pagamento, inicializadas com valores padrão
            logger.info("Adicionando colunas de pagamento: Status pgto, Valor pago, Valor a receber, diferença.")
            self.df['Status pgto'] = ''
            self.df['Valor pago'] = 0.0
            self.df['Valor a receber'] = 0.0
            self.df['diferença'] = 0.0
            
            # Preenche as colunas com base nas regras
            logger.info("Preenchendo colunas com base nas regras.")
            self._populate_transportadora_column() # Nova função
            self._populate_service_column()
            self._treat_dt_frete_column() # Executado após preencher o serviço
            self._filter_valor_cte()
            
            # --- Reordenação final das colunas ---
            final_column_order = [
                'Emissao', 'Mês', 'Transportadora', 'CTRC', 'Cliente', 'Serviço',
                'Senha Ravex', 'DT Frete', 'Origem', 'UF Origem', 'Destino', 'UF',
                'Nota Fiscal', 'Valor CTe', 'Status pgto', 'Valor pago', 
                'Valor a receber', 'diferença'
            ]
            self.df = self.df[final_column_order]
            logger.info("Colunas reordenadas para a estrutura final do relatório.")
            
            logger.info(f"--- Processamento do relatório concluído. {len(self.df)} linhas finais. ---\n")
            return self.df

        except FileNotFoundError:
            logger.error(f"Erro Crítico: O arquivo de relatório '{self.filepath}' não foi encontrado.")
            return None
        except IndexError as e:
            logger.error(f"Erro Crítico de Índice: o relatório pode estar vazio ou com formato inesperado. Erro: {e}")
            return None
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado ao processar o relatório: {e}")
            return None
