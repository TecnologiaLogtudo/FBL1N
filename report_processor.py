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
        """Aplica a regra de renomeação na coluna 'Cliente'."""
        logger.info("Aplicando regras de renomeação na coluna 'Cliente'.")
        
        # Garante que a coluna 'Cliente' seja do tipo string
        cliente_series = self.df['Cliente'].astype(str)
        
        # Pega a primeira palavra, converte para minúsculas e remove acentos para comparação
        first_word = cliente_series.str.split().str[0].str.lower()
        
        # Define as condições e os valores correspondentes
        conditions = [
            first_word.str.contains('itamb', na=False),
            first_word.str.contains('lactalis', na=False)
        ]
        choices = ['Itambé', 'Lactalis']
        
        # Aplica a lógica condicional
        self.df['Cliente'] = np.select(conditions, choices, default=self.df['Cliente'])
        logger.info("Coluna 'Cliente' padronizada.")

    def _populate_service_column(self):
        """Preenche a coluna 'Serviço' com base na coluna 'DT Frete'."""
        logger.info("Preenchendo a coluna 'Serviço' com base em 'DT Frete'.")
        
        # Garante que a coluna 'DT Frete' seja do tipo string para aplicar as regras
        dt_frete_series = self.df['DT Frete'].astype(str)
        
        # Define as condições de mapeamento
        conditions = [
            dt_frete_series.str.contains(r'\d', na=False), # Contém números
            dt_frete_series.str.contains('DESCARGA', case=False, na=False),
            dt_frete_series.str.contains('DIARIA DO CLIENTE', case=False, na=False),
            dt_frete_series.str.contains('DIARIA PARADO', case=False, na=False),
            dt_frete_series.str.contains('AVARIAS', case=False, na=False),
            dt_frete_series.str.contains('PEDAGIO', case=False, na=False),
            dt_frete_series.str.contains('REENTREGA', case=False, na=False),
            dt_frete_series.str.contains('COMPLEMENTO DE FRETE', case=False, na=False),
            dt_frete_series.str.contains('PERNOITE', case=False, na=False)
        ]
        
        # Define os resultados correspondentes a cada condição
        choices = [
            'Frete',
            'Descarga',
            'Diária no cliente',
            'Diária parado',
            'Descarga',
            'Pedágio',
            'Reentrega',
            'Complemento',
            'Diária no cliente'
        ]
        
        # Aplica a lógica e preenche a coluna 'Serviço'
        self.df['Serviço'] = np.select(conditions, choices, default='')
        logger.info("Coluna 'Serviço' preenchida.")

    def process(self):
        """
        Executa o pipeline completo de processamento para o relatório externo.

        Returns:
            pd.DataFrame: DataFrame processado e limpo, ou None em caso de erro.
        """
        try:
            logger.info(f"Iniciando o processamento do relatório externo: {self.filepath}")
            
            df = pd.read_excel(self.filepath, header=None, skiprows=REPORT_SKIP_ROWS, engine='xlrd')
            logger.info(f"Arquivo lido, pulando as primeiras {REPORT_SKIP_ROWS} linhas.")

            logger.info("Consolidando cabeçalho de múltiplas linhas.")
            header_row1 = df.iloc[0].fillna("").astype(str)
            header_row2 = df.iloc[1].fillna("").astype(str)
            new_header = (header_row1 + " " + header_row2).str.strip()
            df.columns = new_header
            df = df.iloc[2:].reset_index(drop=True)
            logger.info("Cabeçalho consolidado e linhas de cabeçalho removidas.")

            logger.info(f"Selecionando colunas pelos índices: {REPORT_COLUMN_INDICES}")
            df_selected = df.iloc[:, REPORT_COLUMN_INDICES]

            logger.info(f"Renomeando colunas para: {REPORT_FINAL_COLUMNS}")
            df_selected.columns = REPORT_FINAL_COLUMNS
            self.df = df_selected.copy()
            
            logger.info("Formatando a coluna 'Emissao' para o formato de data dd/mm/aaaa.")
            self.df['Emissao'] = pd.to_datetime(self.df['Emissao'], errors='coerce').dt.strftime('%d/%m/%Y')
            
            logger.info("Adicionando e preparando novas colunas: Mês, Transportadora, Serviço.")
            try:
                locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            except locale.Error:
                logger.warning("Locale 'pt_BR.UTF-8' não encontrado. O nome do mês pode ficar em inglês.")
            
            dates = pd.to_datetime(self.df['Emissao'], format='%d/%m/%Y', errors='coerce')
            self.df['Mês'] = dates.dt.strftime('%B').str.capitalize()
            self.df['Transportadora'] = ''
            self.df['Serviço'] = ''
            
            # Aplica os tratamentos de dados nas colunas 'Cliente' e 'Serviço'
            self._clean_client_column()
            self._populate_service_column()

            # Reordena as colunas para a estrutura final
            final_column_order = [
                'Emissao', 'Mês', 'Transportadora', 'CTRC', 'Cliente', 'Serviço',
                'Senha Ravex', 'DT Frete', # Ordem invertida conforme solicitado
                'Destino', 'UF', 'Nota Fiscal', 'Valor CTe'
            ]
            self.df = self.df[final_column_order]
            logger.info("Colunas reordenadas para a estrutura final do relatório.")
            
            logger.info(f"Processamento do relatório concluído. {len(self.df)} linhas processadas.\n")
            return self.df

        except FileNotFoundError:
            logger.error(f"Erro: O arquivo de relatório '{self.filepath}' não foi encontrado.")
            return None
        except IndexError:
            logger.error("Erro de índice: o arquivo pode não ter as linhas de cabeçalho esperadas ou está vazio.")
            return None
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado ao processar o relatório: {e}")
            return None
