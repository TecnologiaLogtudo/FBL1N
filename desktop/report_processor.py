# report_processor.py
# 2º Etapa: Processamento do Relatório Externo
# Módulo para processar o relatório externo baixado do sistema web.

import pandas as pd
import numpy as np
import locale
from pathlib import Path
from desktop.utils import logger
from desktop.config import REPORT_SKIP_ROWS, REPORT_COLUMN_INDICES, REPORT_FINAL_COLUMNS

class ReportProcessor:
    """
    Classe para carregar, limpar e estruturar os dados do relatório externo.
    Sua única responsabilidade é transformar o arquivo .xls bruto em um DataFrame limpo e padronizado.
    """
    def __init__(self, filepath, analysis_year):
        """
        Inicializa o processador com o caminho do arquivo do relatório.
        
        Args:
            filepath (str): Caminho para o arquivo .xls do relatório.
            analysis_year (int): O ano a ser usado para o processamento.
        """
        self.filepath = filepath
        self.analysis_year = str(analysis_year)
        self.df = None

    def _resolve_engine(self) -> str:
        """Resolve o engine de leitura do pandas com base na extensão do arquivo."""
        suffix = Path(self.filepath).suffix.lower()
        return "xlrd" if suffix == ".xls" else "openpyxl"

    def _clean_client_column(self):
        """(Tratamento) Aplica a regra de padronização na coluna 'Cliente'."""
        logger.info("Tratando coluna 'Cliente': Padronizando nomes 'ITAMBE' e 'LACTALIS'.")
        cliente_series = self.df['Cliente'].astype(str)
        first_word = cliente_series.str.split().str[0].str.lower()
        
        conditions = [
            first_word.str.contains('itamb', na=False),
            first_word.str.contains('lactalis', na=False)
        ]
        choices = ['Itambé', 'Lactalis']
        
        self.df['Cliente'] = np.select(conditions, choices, default=self.df['Cliente'])
        logger.info("Coluna 'Cliente' padronizada com sucesso.")

    def _populate_service_column(self):
        """(Tratamento) Preenche a coluna 'Serviço' com base em regras da coluna 'DT Frete'."""
        logger.info("Preenchendo coluna 'Serviço' com base em 'DT Frete'.")
        
        # Normaliza a série para evitar problemas com NaN e espaços
        dt_frete_series = self.df['DT Frete'].fillna('').astype(str).str.strip().str.upper()
        
        # Padrões regex mais flexíveis para capturar variações comuns
        patterns = {
            'Frete_numerico': r'^\d+$|(?:\d+[\s/E]+\d+)+',
            'Frete_texto': r'FRETE|SILVA',
            'Frete_substituicao': r'SUBSTITUI[ÇC][AÃ]O|SUBSTI[TÇ]UIR|SUS?BT?UITI[ÇC][AÃ]O|(?:CTE\s*)?SU[BS]?[TB]I?TUI[CÇ][AÃ]O|TROC[AS]|SUSBTITUIÇÃO|SUSBTITUICAO',
            'Diária no cliente': r'D[IÍ][AÁ]RIA\s*(NO|N[AO])?\s*CLI?ENT[EI]|PERNO[IY]TE|ESA[YI]ADIA.*ROTA|ROTA',
            'Reentrega': r'R[EÉ]+[\-\s]*[EH]?NT[RE]*G[AS]|RET[OÔ]RN[OÔ]|DEVOLU[CÇ][AÃ]O|CAR[OÔ]NA',
            'Diaria_parado': r'D[IÍ][AÁ]RIA\s*(PARAD[OA]|ESPERA|PÁRADO)|PARAD[OA]',
            'Complemento': r'CO[MN]PLE[MN][EÊ]NTO?|COMPLEMENTAR|COMPLEMEN?TAR|COMPLENETAR|AJUSTE|AC[EÊ]RTO|DIFEREN[CÇ]A|.*[CO][MN]PLE[MN][EÊ]NTAR|.*COMPLEMENATR',
            'Avarias': r'AVAR[IÍ][AS]|DAN[OÔ]S?|PREJU[IÍ]Z[OÔ]S?|SINISTR[OÔ]',
            'Pedagio': r'P[AE]D[AÁ]?[GJ][IÍ][OÔ]|TAG[S]?',
            'Descarga_palete': r'COL[EÊ]TA\s*(DE\s*)?(PAL+[EÊ]?T[ES]|PALHETE)|PALL?ETS?',
            'Descarga_geral': r'DESCARGA|DESCARTGA|DE[SC][AC]*[AR]*G[AS]|DESCARR[EÊ]G[AS]|DESCARR[EÊ][GJ]AMENTO',
            'Descarga_ajudante': r'AJUD[AÁ]NTE|CHAP[AS]?|AUX[IÍ]LI[AO]R?',
            'Descarga_classificacao': r'CLASSIFIC[AÇ][AÃ]O|SEPAR[AÇ][AÃ]O',
            'Estadia': r'EST[AÁ]DIA|PERMAN[EÊ]NCIA',
            'Frete_B49': r'B49',
            'Frete_municipal': r'^PCH|FRETE\s*MUNICIPAL',
            'Nota_debito': r'NOTA\s*DE\s*D[EÉ]BITO|DE[BV][IÍ]TO|NOTA\s*D[EÉ]B[ÍI]TO'
        }
        
        conditions = [dt_frete_series.str.contains(pattern, regex=True, na=False) 
                    for pattern in patterns.values()]
        
        choices = [
            'Frete',             # Frete_numerico
            'Frete',             # Frete_texto
            'Frete',             # Frete_substituicao
            'Diária no cliente', # Diária no cliente
            'Reentrega',         # Reentrega
            'Diária parado',     # Diária parado
            'Complemento',       # Complemento
            'Descarga',          # Avarias
            'Pedágio',           # Pedágio
            'Descarga',          # Descarga_palete
            'Descarga',          # Descarga_geral
            'Descarga',          # Descarga_ajudante
            'Descarga',          # Descarga_classificacao
            'Diária no cliente', # Estadia
            'Frete',             # Frete_B49
            'Frete municipal',   # Frete_municipal
            'Diária parado'      # Nota_debito
        ]
        
        # Aplica as regras e registra no log casos não mapeados
        self.df['Serviço'] = np.select(conditions, choices, default='Outros')
        
        # Identifica valores não mapeados para análise
        valores_nao_mapeados = dt_frete_series[self.df['Serviço'] == 'Outros'].unique()
        if len(valores_nao_mapeados) > 0:
            logger.warning("Valores não mapeados encontrados em 'DT Frete': %s", valores_nao_mapeados)
        
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
        choices = [ 'Logtudo Bahia', 'Logtudo Ceará', 'Logtudo Pernambuco' ]
        
        self.df['Transportadora'] = np.select(conditions, choices, default='')
        logger.info("Coluna 'Transportadora' preenchida com sucesso.")

    def _treat_dt_frete_column(self):
        """(Tratamento) Substitui valores não numéricos em 'DT Frete' por '-'."""
        logger.info("Limpando a coluna 'DT Frete', substituindo textos por '-'.")
        is_not_numeric = ~self.df['DT Frete'].astype(str).str.match(r'^\d+$', na=False)
        self.df.loc[is_not_numeric, 'DT Frete'] = '-'
        logger.info("Coluna 'DT Frete' limpa.")

    def _treat_ctrc_column(self):
        """(Tratamento) Remove o prefixo e, condicionalmente, o sufixo do ano de análise da coluna CTRC."""
        logger.info("Tratando coluna 'CTRC' para remover prefixos e sufixos '%s'.", self.analysis_year)
        
        df_copy = self.df.copy()
        
        # Condição: Serviço é 'Frete' E Origem é diferente de Destino
        condition_to_keep_suffix = (
            (df_copy['Serviço'] == 'Frete') & 
            (df_copy['Origem'] != df_copy['Destino'])
        )
        
        # Aplica a remoção do prefixo para todas as linhas
        df_copy['CTRC'] = df_copy['CTRC'].astype(str).str.replace(f'^{self.analysis_year}0*', '', regex=True)
        
        # Remove o sufixo do ano apenas onde a condição NÃO é atendida
        df_copy.loc[~condition_to_keep_suffix, 'CTRC'] = df_copy.loc[~condition_to_keep_suffix, 'CTRC'].str.replace(f'{self.analysis_year}$', '', regex=True)
        
        self.df = df_copy
        logger.info("Coluna 'CTRC' tratada com a nova lógica condicional.")
        
        logger.info("Removendo linhas onde a coluna 'CTRC' tem 7 ou mais caracteres.")
        self.df = self.df[self.df['CTRC'].str.len() < 7]
        logger.info("Linhas com 7 ou mais caracteres em 'CTRC' removidas.")

    def _filter_valor_cte(self):
        """(Filtro) Remove linhas onde 'Valor CTe' é zero ou 0,01."""
        logger.info("Removendo linhas onde 'Valor CTe' é 0, 0.01 ou nulo.")
        initial_rows = len(self.df)
        self.df['Valor CTe'] = pd.to_numeric(self.df['Valor CTe'], errors='coerce').fillna(0)
        self.df = self.df[~self.df['Valor CTe'].isin([0, 0.01])].reset_index(drop=True)
        rows_removed = initial_rows - len(self.df)
        logger.info("%d linhas foram removidas com 'Valor CTe' igual a 0 ou 0.01.", rows_removed)

    def process(self):
        """
        Executa o pipeline de limpeza e estruturação do relatório externo.
        """
        logger.stair("--- INICIANDO PROCESSAMENTO DO RELATÓRIO EXTERNO ---")
        try:
            logger.info("Lendo o arquivo de relatório: %s", self.filepath)
            engine = self._resolve_engine()
            suffix = Path(self.filepath).suffix.lower()
            logger.info("Engine de leitura resolvido para extensão '%s': %s", suffix, engine)
            df = pd.read_excel(self.filepath, header=None, skiprows=REPORT_SKIP_ROWS, engine=engine)
            logger.info("Arquivo lido, pulando as primeiras %d linhas.", REPORT_SKIP_ROWS)

            logger.info("Consolidando cabeçalho de múltiplas linhas.")
            header_row1 = df.iloc[0].fillna("").astype(str)
            header_row2 = df.iloc[1].fillna("").astype(str)
            new_header = (header_row1 + " " + header_row2).str.strip()
            df.columns = new_header
            df = df.iloc[2:].reset_index(drop=True)
            logger.info("Cabeçalho consolidado e linhas de cabeçalho iniciais removidas.")

            logger.info("Selecionando colunas de interesse pelos índices: %s", REPORT_COLUMN_INDICES)
            
            # --- Verificação de segurança para evitar IndexError ---
            num_cols_disponiveis = df.shape[1]
            colunas_validas = [idx for idx in REPORT_COLUMN_INDICES if idx < num_cols_disponiveis]
            if len(colunas_validas) < len(REPORT_COLUMN_INDICES):
                colunas_faltantes = [idx for idx in REPORT_COLUMN_INDICES if idx >= num_cols_disponiveis]
                logger.warning("O arquivo de relatório tem apenas %d colunas. As colunas nos índices %s não puderam ser encontradas e serão ignoradas.", num_cols_disponiveis, colunas_faltantes)
            
            df_selected = df.iloc[:, colunas_validas]

            logger.info("Renomeando colunas para os nomes padronizados.")
            df_selected.columns = REPORT_FINAL_COLUMNS
            self.df = df_selected.copy()
            
            # --- Sequência de Tratamentos ---
            
            logger.info("Formatando a coluna 'Emissao' para o formato de data (dd/mm/aaaa).")
            self.df['Emissao'] = pd.to_datetime(self.df['Emissao'], errors='coerce').dt.strftime('%d/%m/%Y')
            
            logger.info("Adicionando e preparando novas colunas: Mês, Transportadora, Serviço.")
            try:
                locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            except locale.Error:
                logger.warning("Locale 'pt_BR.UTF-8' não disponível. Nomes dos meses podem aparecer em inglês.")
            
            dates = pd.to_datetime(self.df['Emissao'], format='%d/%m/%Y', errors='coerce')
            self.df['Mês'] = dates.dt.strftime('%B').str.capitalize()
            self.df['Transportadora'] = ''
            self.df['Serviço'] = ''

            logger.info("Adicionando colunas de pagamento (serão preenchidas na etapa de análise).")
            self.df['Status pgto'] = ''
            self.df['Valor pago'] = 0.0
            self.df['Recebido/A receber'] = 0.0
            self.df['diferença'] = 0.0
            
            logger.info("Preenchendo colunas com base nas regras.")
            self._clean_client_column()
            self._populate_transportadora_column()
            self._populate_service_column()
            self._treat_ctrc_column() # Movido para depois de _populate_service_column
            self._treat_dt_frete_column()
            self._filter_valor_cte()
            
            final_column_order = [
                'Emissao', 'Mês', 'Transportadora', 'CTRC', 'Cliente', 'Serviço',
                'Senha Ravex', 'DT Frete', 'Origem', 'UF Origem', 'Destino', 'UF',
                'Nota Fiscal', 'Valor CTe', 'Status pgto', 'Valor pago', 
                'Recebido/A receber', 'diferença'
            ]
            self.df = self.df[final_column_order]
            logger.info("Colunas reordenadas para a estrutura final do relatório.")

            logger.success("--- Processamento do relatório concluído. %d linhas finais. ---\n", len(self.df))
            return self.df

        except FileNotFoundError:
            logger.error("Erro Crítico: O arquivo de relatório '%s' não foi encontrado.", self.filepath)
            return None
        except IndexError as e:
            logger.error("Erro Crítico de Índice: o relatório pode estar vazio ou com formato inesperado. Erro: %s", e)
            return None
        except Exception as e:
            logger.error("Ocorreu um erro inesperado ao processar o relatório: %s", e, exc_info=True)
            return None
        

