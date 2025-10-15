# config.py
# Arquivo central de configurações para o projeto de processamento de planilhas.

# --- Configurações Gerais ---
LOG_FILE = 'processamento.log'

# --- Configurações para a Etapa 1 (DataProcessor) ---
# Nomes exatos das colunas a serem mantidas após a leitura inicial
COLUNAS_ETAPA1_PARA_MANTER = [
    'Conta', 'Referência', 'Montante em moeda interna', 
    'Data do documento', 'Data de lançamento', 'Data de compensação'
]
# Nomes das colunas chave para manipulação
COLUNA_DATA_DOCUMENTO = 'Data do documento'
COLUNA_REFERENCIA = 'Referência'
COLUNA_CONTA = 'Conta'
COLUNA_MONTANTE = 'Montante em moeda interna'

# --- Configurações para a Etapa 2 (DataProcessor) ---
# Mapeamento do número da conta para o nome da aba intermediária
CONTAS_MAPEAMENTO_ETAPA2 = {
    302282: '302282 - Bahia',
    303264: '303264 - Ceará',
    303432: '303432 - Pernambuco'
}

# --- Configurações para a Etapa 4 (DataProcessor) ---
# Mapeamento do número da conta para o nome da aba final
CONTAS_MAPEAMENTO_ETAPA4 = {
    302282: 'Bahia',
    303264: 'Ceará',
    303432: 'Pernambuco'
}
# Colunas que devem estar presentes nas abas finais da Etapa 4
COLUNAS_ETAPA4_FINAIS = ['Referência', 'Data de compensação', 'Valor pagamento']

# --- Configurações para a Etapa 5 (ReportProcessor) ---
# Caminho do arquivo de relatório a ser processado
REPORT_FILE_PATH = 'relatorio.xls'
# Número de linhas a serem puladas no início do arquivo de relatório
REPORT_SKIP_ROWS = 6

# Índices das colunas a serem selecionadas do relatório original.
# Correspondem a: Emissão, CTe, Remetente, Pedido, Senha, Origem, UF Origem, Destino, UF Destino, N.º Nota, Valor Nota
REPORT_COLUMN_INDICES = [3, 4, 9, 14, 15, 16, 17, 18, 20, 25, 27]

# Nomes finais para as colunas após a seleção e renomeação
REPORT_FINAL_COLUMNS = [
    'Emissao', 'CTRC', 'Cliente', 'DT Frete', 'Senha Ravex', 'Origem', 
    'UF Origem', 'Destino', 'UF', 'Nota Fiscal', 'Valor CTe'
]
