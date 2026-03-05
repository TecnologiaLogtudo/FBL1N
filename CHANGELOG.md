# Changelog

## v1.2.0 (2026-03-05)

- Adicionado endpoint `GET /api/process/history` para histórico de jobs por usuário (`X-User-Id`/IP).
- Adicionado endpoint `GET /api/metrics` com métricas operacionais (jobs ativos, taxa de sucesso, duração média).
- Frontend passou a exibir seção de Operação com:
  - métricas resumidas,
  - histórico recente dos últimos jobs,
  - botão de atualização manual.
- Melhorias de UX já incluídas:
  - progresso de upload antes da criação do job,
  - erros detalhados de API,
  - `X-User-Id` estável por navegador (sem auth interna).

## v1.1.0 (2026-03-05)

- Exportação PDF implementada (`GET /api/process/{job_id}/download/pdf`).
- Ajustes de deploy para subdiretório `/NotasCompensadas-FBL1`.
- Compatibilização com Coolify + Traefik.
