# Manual de Uso - Notas Compensadas FBL1 (Web)

Versao: 1.2  
Ultima atualizacao: 05/03/2026

## 1. Objetivo

A aplicacao web "Notas Compensadas FBL1" automatiza a conciliacao de pagamentos de frete, cruzando:
- Base contabil (FBL1N)
- Relatorio operacional (BSoft)

Ela gera analise de pendencias e permite exportacao em XLSX e PDF.

## 2. Acesso

URL do sistema:
- https://automacao.logtudo.com.br/NotasCompensadas-FBL1/

Manual online:
- https://automacao.logtudo.com.br/NotasCompensadas-FBL1/manual-de-uso

## 3. Arquivos necessarios

### 3.1 Base de Dados
- Formato: `.xlsx`
- Origem: FBL1N
- Limite: ate 25 MB

### 3.2 Relatorio Externo
- Formato: `.xls` ou `.xlsx`
- Origem: BSoft
- Limite: ate 25 MB

## 4. Como processar

1. Acesse o sistema.
2. Selecione a Base de Dados (.xlsx).
3. Selecione o Relatorio Externo (.xls/.xlsx).
4. Informe o Ano de Analise.
5. Clique em **Executar Processamento**.
6. Aguarde:
- barra de envio dos arquivos
- barra de progresso do processamento
- logs em tempo real

## 5. Resultados

Apos concluir, o sistema exibe:
- **Resumo Consolidado**
- **Detalhes de Pendencias**

Tambem permite download:
- **Baixar XLSX**
- **Baixar PDF**

## 6. Historico e Operacao

Na tela inicial, a secao **Operacao** mostra:
- total de jobs
- jobs ativos
- concluidos/falhos
- taxa de sucesso
- historico recente de execucoes

## 7. Erros comuns

### 7.1 Arquivo excede limite
- Mensagem: "Arquivo excede 25MB"
- Acao: reduzir/compactar a planilha de origem.

### 7.2 Formato invalido
- Base deve ser `.xlsx`.
- Relatorio deve ser `.xls` ou `.xlsx`.

### 7.3 Job ja em execucao
- Mensagem: usuario ja possui job em execucao.
- Acao: aguardar finalizacao e tentar novamente.

## 8. Boas praticas

- Validar se os arquivos correspondem ao mesmo periodo.
- Revisar pendencias "Nao lancado" e "Nao compensado" apos cada execucao.
- Guardar o XLSX/PDF final para auditoria interna.

## 9. Gerar PDF deste manual

Opcao 1 (Word/Google Docs):
1. Copie este conteudo para o editor.
2. Exporte em PDF.

Opcao 2 (Navegador):
1. Abra a URL do manual online.
2. Use "Imprimir" (Ctrl+P).
3. Escolha "Salvar como PDF".
