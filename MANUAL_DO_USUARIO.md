# 📋 Manual do Usuário - Análise de Transportes

## O que é este programa?

Este programa automatiza o processamento e análise de dados de notas, comparando informações de duas fontes:
- **Arquivo Base**: Dados do sistema FBL1N (contas a receber)
- **Relatório Externo**: Dados do sistema BSoft (notas de frete)

O resultado é um relatório consolidado mostrando compensações, pendências e diferenças de valores.

---

## ✅ Preparação antes de usar

### 1. Prepare seus arquivos

Você precisará de **dois arquivos**:

#### **Arquivo 1: Base de Dados (Excel)**
- Nome padrão: `base_de_dados.xlsx`
- Formato: Arquivo Excel com dados do FBL1N
- Deve conter as colunas: Conta, Referência, Data do Documento, Data de Lançamento, Montante, etc.

#### **Arquivo 2: Relatório Externo (Excel ou XLS)**
- Nome padrão: `relatorio.xls`
- Formato: Relatório exportado do BSoft com as bases Bahia, Pernambuco e Ceará
- Contém informações de CTe, clientes, valores de frete, etc.

### 2. Defina o ano de análise
- Padrão: 2025
- Altere conforme necessário na interface

---

## 🚀 Como usar

### **Passo 1: Abrir o programa**

Execute o executável compilado:

A interface gráfica será aberta.

---

### **Passo 2: Configurar os arquivos**

1. **Base de Dados (.xlsx)**
   - Clique no botão "Selecionar" ao lado do campo
   - Procure e selecione seu arquivo Excel com os dados FBL1N
   - O caminho aparecerá no campo de texto

2. **Relatório Externo (.xls)**
   - Clique no botão "Selecionar" ao lado do campo
   - Procure e selecione seu arquivo de relatório BSoft
   - O caminho aparecerá no campo de texto

3. **Ano de Análise**
   - Se necessário, altere o ano (padrão: 2025)
   - Digite apenas números (ex: 2024)

---

### **Passo 3: Executar o processamento**

1. Verifique se os arquivos estão corretos
2. Clique no botão verde **"Executar Processamento"**
3. Aguarde enquanto o programa processa:
   - A barra de progresso mostra o andamento
   - A aba "Logs" mostra o que está acontecendo
   - **Não feche o programa!**

---

### **Passo 4: Visualizar resultados**

Após o processamento ser concluído com sucesso:

#### **Aba: Resumo Consolidado**
- Mostra totais por mês e transportadora
- Indicadores: compensado, não compensado, não lançado
- Total geral consolidado

#### **Aba: Detalhes de Pendências**
- Lista completa de cada frete processado
- Mostra status de pagamento, valores e diferenças
- Filtra pendências (status "Não lançado" em vermelho)

---

### **Passo 5: Exportar resultados**

Após o sucesso, botões de exportação aparecerão:

#### **Exportar para .xlsx**
- Salva um arquivo Excel completo com todas as abas
- Use para análise detalhada, filtros e gráficos
- Recomendado para relatórios

#### **Exportar para .pdf**
- Gera um relatório visual em PDF
- Inclui tabela de resumo e detalhes
- Pronto para imprimir ou enviar

---

## 📊 Entendendo os resultados

### Colunas principais no relatório:

| Coluna | Significado |
|--------|------------|
| **Emissão** | Data da emissão do frete |
| **Mês** | Mês de processamento |
| **Transportadora** | Qual filial (Bahia, Ceará, Pernambuco) |
| **CTRC** | Número do conhecimento de transporte |
| **Cliente** | Cliente/Empresa |
| **Serviço** | Tipo: Frete, Descarga, Diária, etc. |
| **Valor CTe** | Valor original do frete |
| **Status Pgto** | Situação: Pago, Não lançado, Compensado |
| **Valor pago** | Quanto foi efetivamente pago |
| **Recebido/A receber** | Diferença entre esperado e recebido |

### Status de Pagamento:

- 🟢 **Compensado**: Frete foi devidamente recebido e registrado
- 🟡 **Não lançado**: Frete não consta no sistema de contas
- 🔵 **Pago**: Frete foi pago normalmente

### Valores em Vermelho:

Indicam pendências - valores não registrados ou diferenças a investigar.

---

## ⚠️ Solução de problemas

### Erro: "Arquivo não encontrado"
- Verifique o caminho do arquivo
- Certifique-se de que o arquivo existe e está no local informado
- Tente usar o botão "Selecionar" novamente

### Erro: "Ano de análise inválido"
- Digite apenas números (ex: 2025)
- Não use símbolos ou letras

### Processamento muito lento
- Arquivos muito grandes podem levar tempo
- Feche outros programas para liberar memória
- Redimensione seus dados se possível

### Erro ao exportar PDF
- A biblioteca reportlab pode não estar instalada
- Instale com: `pip install reportlab`
- Use a exportação Excel como alternativa

### Arquivo não abre ou está corrompido
- Verifique se o arquivo já não está aberto em outro programa
- Tente salvar com outro nome
- Verifique o espaço em disco disponível

---

## 💡 Dicas úteis

✓ **Sempre fazer backup** dos arquivos originais antes de processar

✓ **Verificar os logs** na aba "Logs" se algo der errado

✓ **Usar Excel** para visualização e análise detalhada dos dados

✓ **Processar regularmente** para manter dados atualizados

✓ **Documentar mudanças** - anote quando processou e com quais datas

---

## 📞 Suporte

Se tiver problemas:
1. Verifique a aba "Logs" para mensagens de erro
2. Consulte as dicas de solução de problemas acima
3. Verifique se os arquivos de entrada estão no formato correto
4. Contacte o administrador do sistema

---

## 📝 Exemplo prático

### Cenário: Processar dados de novembro/2025

1. **Preparação**
   - Baixe `FBL1_nov_2025.xlsx` do sistema
   - Baixe `Relatorio_nov_2025.xls` do BSoft

2. **Configuração**
   - Abra o programa
   - Selecione `FBL1_nov_2025.xlsx`
   - Selecione `Relatorio_nov_2025.xls`
   - Deixe ano como 2025

3. **Execução**
   - Clique "Executar Processamento"
   - Aguarde conclusão (2-5 minutos aprox.)

4. **Resultados**
   - Verifique "Resumo Consolidado"
   - Procure por linhas em vermelho em "Detalhes de Pendências"
   - Exporte para Excel para análise adicional

5. **Ação**
   - Investigue valores não lançados
   - Corrija no sistema se necessário
   - Processe novamente quando corrigido

---

**Versão**: 1.0  
**Última atualização**: Novembro de 2025  
**Desenvolvido para**: Logtudo Soluções logísticas
