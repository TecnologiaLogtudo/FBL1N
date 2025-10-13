# config.py
# Arquivo para armazenar configurações e constantes do projeto.

# Colunas que serão mantidas na planilha final da Etapa 1
COLUNAS_ETAPA1_PARA_MANTER = [
    'Conta',
    'Referência',
    'Montante em moeda interna',
    'Data do documento',
    'Data de lançamento',
    'Data de compensação'
]

# Colunas para as abas finais da Etapa 4
COLUNAS_ETAPA4_FINAIS = [
    'Referência',
    'Data de compensação',
    'Valor pagamento'
]

# Nomes de colunas usados para referência no código
COLUNA_DATA_DOCUMENTO = 'Data do documento'
COLUNA_REFERENCIA = 'Referência'
COLUNA_CONTA = 'Conta'
COLUNA_MONTANTE = 'Montante em moeda interna'

# Mapeamento de contas para os nomes das abas da Etapa 2 (intermediárias)
CONTAS_MAPEAMENTO_ETAPA2 = {
    302282: '302282 - Bahia',
    303264: '303264 - Ceará',
    303432: '303432 - Pernambuco'
}

# Mapeamento de contas para os nomes das abas da Etapa 4 (finais)
CONTAS_MAPEAMENTO_ETAPA4 = {
    302282: 'Bahia',
    303264: 'Ceará',
    303432: 'Pernambuco'
}

