# config.py
# Arquivo de configuração para centralizar parâmetros e constantes do projeto.

# --- Configurações Gerais ---
LOG_FILE = 'processamento.log'

# --- Nomes das Colunas (Etapa 1 - Planilha Principal) ---
COLUNA_CONTA = 'Conta'
COLUNA_REFERENCIA = 'Referência'
COLUNA_MONTANTE = 'Montante em moeda interna'
COLUNA_DATA_DOCUMENTO = 'Data do documento'
COLUNAS_ETAPA1_PARA_MANTER = [
    COLUNA_CONTA,
    COLUNA_REFERENCIA,
    COLUNA_MONTANTE,
    COLUNA_DATA_DOCUMENTO,
    'Data de lançamento',
    'Data de compensação'
]

# --- Mapeamento de Contas (Etapas 2 e 4) ---
CONTAS_MAPEAMENTO_ETAPA2 = {
    302282: '302282 - Bahia',
    303264: '303264 - Ceará',
    303432: '303432 - Pernambuco'
}

CONTAS_MAPEAMENTO_ETAPA4 = {
    302282: 'Bahia',
    303264: 'Ceará',
    303432: 'Pernambuco'
}

# --- Estrutura das Colunas (Etapa 4) ---
COLUNAS_ETAPA4_FINAIS = [
    'Referência',
    'Data de compensação',
    'Valor pagamento'
]

# --- Configurações do Relatório Externo ---
REPORT_FILE_PATH = 'relatorio.xls'
REPORT_SKIP_ROWS = 6 # Linhas a serem puladas no início do arquivo do relatório

# Índices das colunas a serem extraídas do relatório (baseado na estrutura do arquivo)
# Corresponde a: Emissão, CTe, Remetente, Pedido, Senha, Destino, UF, Nota N.º, Valor
REPORT_COLUMN_INDICES = [3, 4, 9, 14, 15, 18, 17, 25, 27]

# Nomes finais para as colunas do relatório após o processamento.
# Esta lista agora reflete os nomes finais solicitados.
REPORT_FINAL_COLUMNS = [
    'Emissao',
    'CTRC',
    'Cliente',
    'DT Frete',
    'Senha Ravex',
    'Destino',
    'UF',
    'Nota Fiscal',
    'Valor CTe'
]
