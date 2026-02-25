Este processo visa conciliar pagamentos de fretes cruzando dados contábeis (FBL1N) com relatórios operacionais (BSoft).

📂 Visão Geral dos Arquivos de Entrada e Saída
Entrada 1: base_de_dados.xlsx (Dados do sistema FBL1N - Contábil).
Entrada 2: relatorio.xls (Relatório Externo - Operacional).
Saída: dados_estruturados.xlsx (Arquivo Excel consolidado com múltiplas abas).
🔄 FASE 1: Processamento da Base de Dados (FBL1N)
Responsável: data_processor.py

O objetivo desta fase é limpar os dados contábeis e preparar "Abas de Lookup" (Consulta) para o cruzamento posterior.

1.1. Leitura e Filtros Iniciais (Etapa 1)
Dados Coletados: Lê todas as colunas do arquivo Excel.
Filtros de Exclusão (Dados Deletados):
Linhas onde a coluna Data do documento está vazia.
Linhas onde a Data do documento não pode ser convertida para data válida.
Filtro de Ano: Remove todas as linhas onde o ano da Data do documento é 2023.
Seleção de Colunas: Mantém apenas:
Conta
Referência
Montante em moeda interna
Data do documento
Data de lançamento
Data de compensação
Tratamento da Coluna Referência:
Remove sufixos após o traço (ex: "12345-A" vira "12345").
Converte para número (linhas com texto não numérico são deletadas).
Converte para Inteiro (remove casas decimais).
1.2. Separação por Conta e Ano (Etapa 2)
Filtro de Ano de Análise: Mantém apenas dados do ano selecionado pelo usuário (ex: 2025).
Separação em Abas Intermediárias: Os dados são divididos baseados no número da Conta:
Conta 302282: Gera dados para aba interna "302282 - Bahia".
Conta 303432: Gera dados para aba interna "303432 - Pernambuco".
Conta 303264 (Ceará): Regra Especial: Inclui dados da conta 303264 E da conta 302282 (Bahia).
1.3. Limpeza de Referências Únicas (Etapa 3)
Para cada aba separada acima:

Lógica de Exclusão: O sistema identifica referências que aparecem apenas uma vez na planilha e cujo Montante seja positivo (> 0).
Ação: Essas linhas são deletadas.
Interpretação: Isso geralmente visa remover lançamentos únicos de provisão ou pendência que não possuem contrapartida (pagamento/estorno) no período.
1.4. Consolidação Final por Aba (Etapa 4)
Gera as abas finais que serão usadas para o cruzamento (Bahia, Ceará, Pernambuco).

Cálculo de Valores:
Soma-se o Montante em moeda interna de todas as linhas com a mesma Referência (da Etapa 2).
Esse valor somado é salvo na nova coluna Valor pagamento.
Remoção de Duplicatas: Remove linhas duplicadas baseadas na Referência, mantendo apenas a primeira ocorrência.
Formatação:
Data de compensação: Formatada para dd/mm/aaaa. Se vazia, preenche com "Não compensado".
Colunas Finais nestas abas:
Referência
Data de compensação
Valor pagamento (Soma consolidada)
🔄 FASE 2: Processamento do Relatório Externo
Responsável: report_processor.py

Transforma o relatório operacional bruto em uma tabela padronizada.

2.1. Leitura e Estruturação
Limpeza de Cabeçalho: Pula as primeiras 6 linhas. Consolida as linhas 0 e 1 do dataframe resultante para formar um cabeçalho único.
Seleção de Colunas: Seleciona colunas específicas pelos índices (3, 4, 9, 14, 15, 16, 17, 18, 20, 25, 35) e as renomeia para:
Emissao, CTRC, Cliente, DT Frete, Senha Ravex, Origem, UF Origem, Destino, UF, Nota Fiscal, Valor CTe.
2.2. Tratamentos e Regras de Negócio
Data: Emissao convertida para dd/mm/aaaa. Cria coluna Mês (nome do mês por extenso).
Cliente: Padroniza nomes contendo "ITAMBE" para "Itambé" e "LACTALIS" para "Lactalis".
Transportadora (Definida pela UF Origem):
BA -> "Logtudo Bahia"
CE -> "Logtudo Ceará"
PE -> "Logtudo Pernambuco"
Serviço (Classificação via Regex na coluna DT Frete):
Identifica se é: Frete, Diária no cliente, Reentrega, Diária parado, Complemento, Descarga, Pedágio.
Se não casar com nenhum padrão, marca como "Outros".
Limpa a coluna DT Frete substituindo textos por "-".
CTRC (Número do Conhecimento):
Remove prefixo do ano (ex: "20250...") e sufixo do ano (ex: "...2025") sob condições específicas (Serviço=Frete e Origem!=Destino).
Filtro: Remove linhas onde o CTRC resultante tem 7 ou mais caracteres (considerado inválido/erro).
Valor CTe:
Exclusão: Remove linhas onde o valor é 0 ou 0.01.
🔄 FASE 3: Análise e Cruzamento (O "PROCV")
Responsável: analysis_processor.py

Aqui ocorre o encontro de contas. O sistema cruza o Relatório Externo (Fase 2) com as Abas Finais (Fase 1).

3.1. Chave de Cruzamento
A chave utilizada é: CTRC (do Relatório) == Referência (da Base FBL1N).
3.2. Preenchimento de Colunas de Análise
O sistema adiciona e preenche 4 colunas cruciais no relatório:

Status pgto:

Procura o CTRC na aba correspondente à Transportadora (ex: Logtudo Bahia -> aba Bahia).
Encontrou? Copia a Data de compensação (ex: "15/05/2025" ou "Não compensado").
Não encontrou? Preenche com "Não lançado".
Valor pago:

Busca o CTRC na aba correspondente.
Encontrou? Copia o Valor pagamento (calculado na Fase 1.4).
Não encontrou? Preenche com "Não lançado".
Recebido/A receber:

Se Status pgto for "Não lançado" -> Copia o Valor CTe (Valor cheio a receber).
Se Valor pago for texto (ex: "Não compensado") -> Preenche com "-".
Caso contrário -> Usa o valor absoluto (positivo) do Valor pago.
diferença:

Cálculo: Valor CTe - Recebido/A receber.
Mostra se houve pagamento a menor ou a maior.
🔄 FASE 4: Geração do Arquivo Final
Responsável: final_report_generator.py e main.py

O arquivo dados_estruturados.xlsx é gerado contendo as seguintes abas:

1. Aba: Dados Consolidados
Contém os dados brutos da Fase 1 (Etapa 1) após filtros iniciais. Útil para auditoria completa.
2. Abas: Bahia, Ceará, Pernambuco
Contêm os dados processados da Fase 1 (Etapa 4).
São as tabelas usadas como referência ("Lookup") para o cruzamento.
Colunas: Referência, Data de compensação, Valor pagamento.
3. Aba: Dados Relatorio Externo
Contém o relatório operacional completo processado na Fase 3, com todas as colunas de análise preenchidas (Status pgto, diferença, etc.), linha a linha.
4. Aba: Resumo Consolidado (Aba Principal para o Usuário)
Esta é a aba visual formatada ("Executiva"). Ela contém duas tabelas:

Tabela Esquerda (Resumo):

Uma tabela dinâmica (Pivot) consolidada.
Agrupa por Transportadora e Serviço.
Colunas:
Não compensado: Soma dos valores que estão no sistema mas ainda não compensaram.
Não lançado: Soma dos valores que constam no BSoft mas não no FBL1N.
Total Geral: Soma das pendências.
Estilização: Cores azuladas, negrito nos totais, fundo laranja para linhas da Logtudo Ceará.
Tabela Direita (Detalhes de Pendências - a partir da coluna G):

Lista detalhada de todos os itens com problemas.
Filtro: Apenas itens com Status pgto igual a "Não lançado" ou "Não compensado".
Colunas exibidas: Emissão, Mês, Transportadora, CTRC, Cliente, Serviço, Senha Ravex, DT Frete, Destino, Nota fiscal, Valor CTe, Status Pgto, Valor pago, Recebido/A receber.
Alerta Visual: Células da coluna Recebido/A receber ficam com fundo Vermelho Claro quando o status é "Não lançado".
Resumo da Segurança de Dados (Valores Altos)
O sistema não altera os arquivos originais (base_de_dados.xlsx e relatorio.xls).
O cálculo de Valor pagamento soma todas as ocorrências de uma referência, garantindo que pagamentos parciais não sejam perdidos antes do cruzamento.
A lógica de exclusão de "referências únicas positivas" na Fase 1.3 é um ponto de atenção: ela assume que se um título positivo está sozinho (sem pagamento atrelado) na base FBL1N filtrada, ele deve ser descartado dessa visão específica (possivelmente considerado ruído ou fora do escopo de compensação imediata nesta lógica de negócio específica).