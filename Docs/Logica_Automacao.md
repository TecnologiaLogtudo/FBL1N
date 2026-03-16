# Conciliação de Pagamentos de Fretes: Lógica e Automação

## 📋 Visão Geral

Este processo concilia pagamentos de fretes cruzando dados contábeis (FBL1N) com relatórios operacionais (BSoft).

### Arquivos de Entrada e Saída

| Tipo | Nome | Descrição |
|------|------|-----------|
| **Entrada 1** | `base_de_dados.xlsx` | Dados do sistema FBL1N (Contábil) |
| **Entrada 2** | `relatorio.xls` | Relatório Externo (Operacional) |
| **Saída** | `dados_estruturados.xlsx` | Arquivo Excel consolidado com múltiplas abas |

---

## 🔄 FASE 1: Processamento da Base de Dados (FBL1N)

**Responsável:** `data_processor.py`

Limpa dados contábeis e prepara "Abas de Lookup" para o cruzamento posterior.

### 1.1 Leitura e Filtros Iniciais

- **Dados coletados:** Todas as colunas do arquivo Excel
- **Filtros de exclusão:**
    - Linhas com Data do documento vazia
    - Linhas com Data do documento inválida
    - Linhas com ano 2023
- **Seleção de colunas:** Conta, Referência, Montante, Data do documento, Data de lançamento, Data de compensação
- **Tratamento da Referência:**
    - Remove sufixos após traço (`12345-A` → `12345`)
    - Converte para número (deleta texto não numérico)
    - Converte para inteiro

### 1.2 Separação por Conta e Ano

- Mantém apenas ano selecionado pelo usuário (ex: 2025)
- Divide dados por número da Conta:
    - **302282** → Aba "302282 - Bahia"
    - **303432** → Aba "303432 - Pernambuco"
    - **303264** → Inclui dados de 303264 E 302282 (Bahia)

### 1.3 Limpeza de Referências Únicas

Para cada aba:
- **Identifica:** Referências que aparecem apenas uma vez com Montante > 0
- **Ação:** Deleta essas linhas
- **Objetivo:** Remover lançamentos únicos sem contrapartida

### 1.4 Consolidação Final por Aba

- **Cálculo:** Soma Montante por Referência → coluna "Valor pagamento"
- **Deduplicação:** Remove duplicatas por Referência, mantém primeira ocorrência
- **Formatação:**
    - Data de compensação: `dd/mm/aaaa` (ou "Não compensado")
- **Colunas finais:** Referência | Data de compensação | Valor pagamento

---

## 🔄 FASE 2: Processamento do Relatório Externo

**Responsável:** `report_processor.py`

Transforma o relatório operacional bruto em tabela padronizada.

### 2.1 Leitura e Estruturação

- Pula primeiras 6 linhas
- Consolida linhas 0 e 1 para cabeçalho único
- Seleciona colunas por índice e renomeia:
    - `[3, 4, 9, 14, 15, 16, 17, 18, 20, 25, 35]` → `Emissao, CTRC, Cliente, DT Frete, Senha Ravex, Origem, UF Origem, Destino, UF, Nota Fiscal, Valor CTe`

### 2.2 Tratamentos e Regras de Negócio

| Campo | Regra |
|-------|-------|
| **Data** | Converte para `dd/mm/aaaa`, cria coluna Mês |
| **Cliente** | "ITAMBE" → "Itambé", "LACTALIS" → "Lactalis" |
| **Transportadora** | BA → Logtudo Bahia; CE → Logtudo Ceará; PE → Logtudo Pernambuco |
| **Serviço** | Classifica via Regex: Frete, Diária no cliente, Reentrega, Diária parado, Complemento, Descarga, Pedágio, Outros |
| **CTRC** | Remove prefixos/sufixos de ano (Frete + Origem≠Destino), deleta se ≥7 caracteres |
| **Valor CTe** | Remove linhas com valor 0 ou 0.01 |

---

## 🔄 FASE 3: Análise e Cruzamento

**Responsável:** `analysis_processor.py`

Cruza Relatório Externo (Fase 2) com Abas Finais (Fase 1).

### 3.1 Chave de Cruzamento

**CTRC** (Relatório) == **Referência** (FBL1N)

### 3.2 Preenchimento de Colunas

| Coluna | Lógica |
|--------|--------|
| **Status pgto** | Se CTRC encontrado na aba → Data compensação; senão → "Não lançado" |
| **Valor pago** | Se CTRC encontrado → Valor pagamento; senão → "Não lançado" |
| **Recebido/A receber** | Se "Não lançado" → Valor CTe; se Valor pago = texto → "-"; senão → `abs(Valor pago)` |
| **Diferença** | Valor CTe - Recebido/A receber |

---

## 🔄 FASE 4: Geração do Arquivo Final

**Responsável:** `final_report_generator.py` e `main.py`

### Estrutura de Abas em `dados_estruturados.xlsx`

1. **Dados Consolidados:** Dados brutos Fase 1 após filtros (auditoria)
2. **Bahia, Ceará, Pernambuco:** Dados processados Fase 1 (lookup)
3. **Dados Relatorio Externo:** Relatório completo com análise (Fase 3)
4. **Resumo Consolidado** (Principal):
     - **Tabela Esquerda (Pivot):** Agrupa por Transportadora/Serviço
         - Colunas: Não compensado | Não lançado | Total Geral
         - Estilo: Cores azuis, negrito em totais, fundo laranja para Ceará
     - **Tabela Direita (Pendências):** Coluna G+
         - Filtro: Status = "Não lançado" ou "Não compensado"
         - Destaque: Vermelho claro em "Recebido/A receber" quando "Não lançado"

---

## 🔁 FASE INVERSA: Revisão de Títulos em Aberto

**Responsável:** `inverse_processor.py` e `main.py` (modo `open_titles`)

### Objetivo
A automação inversa identifica quais títulos marcados como "em aberto" no BSoft já foram pagos no FBL1, sem a necessidade de processar o relatório completo.

### Entradas
- `base_de_dados.xlsx` (mesmos dados FBL1)
- **Planilha de títulos em aberto** (arquivo Excel filtrado da BSoft contendo apenas os fretes pendentes)

### Processamento
1. O `DataProcessor` prepara as abas de lookup (Bahia, Ceará, Pernambuco) da mesma maneira que na Fase 1.
2. O `OpenTitlesProcessor` limpa os CTRCs da planilha aberta (a coluna pode se chamar “CTe”, “CTRC”, “Conhecimento” ou “Referência”), padroniza status/transportadora e cruza cada número com as abas finais por referência; contudo, nesta análise específica só consideramos os lançamentos da conta Bahia (302282) da base FBL1.
3. Para cada CTRC aberto são registrados:
   - o valor pago e a data de compensação identificados no FBL1 (quando existentes);
   - o status do arquivo original e a transportadora informada;
   - o resultado textual (“Pago no FBL1” ou “Não localizado no FBL1”) com observações.

### Saídas
- `Resumo Aberto`: tabela consolidada por transportadora com contagem de títulos abertos fornecidos, quantos já constam pagos no FBL1, quantos permanecem pendentes e o total pago identificado (linha extra “Total geral”).
- `Aberto vs Pago`: lista detalhada de cada CTRC aberto, com transportadora, status, valor pago e observações.
- As abas `Dados Consolidados`, `Bahia`, `Ceará` e `Pernambuco` seguem presentes para fins de auditoria.

### Observações
- O modo inverso roda isoladamente; basta selecionar “Títulos em aberto” na interface e carregar o arquivo filtrado (não é necessário reenviar o relatório padrão).
- No modo inverso o arquivo final deixa de gerar o `Resumo Consolidado` tradicional e passa a exibir os novos sheets.

## 🔒 Segurança de Dados

- Arquivos originais não são alterados
- Pagamentos parciais preservados (soma por referência)
- Referências únicas positivas excluídas na Fase 1.3 (considerar como ruído/fora escopo)
