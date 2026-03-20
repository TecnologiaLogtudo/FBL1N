# Deploy VPS com Playwright (stack separado)

Este diretório contém o stack dedicado para rodar a API com geração automática Midas via Playwright em VPS Linux.

## Arquivos

- `Dockerfile.playwright-vps`: imagem da API com runtime Playwright pronto.
- `docker-compose.playwright-vps.yml`: compose dedicado do backend com `ipc: host` + `seccomp`.
- `seccomp-playwright.json`: permite syscalls exigidas pelo sandbox do Chromium.
- `.env.playwright-vps.example`: base de variáveis de ambiente para produção.
- `playwright_vps_connect.py`: referência do cliente Playwright para VPS.

## Passo a passo

1. Copie o arquivo de ambiente:

```bash
cp Conectividade/.env.playwright-vps.example Conectividade/.env.playwright-vps
```

2. Edite `Conectividade/.env.playwright-vps` e preencha:
- `MIDAS_USERNAME`
- `MIDAS_PASSWORD`
- `MIDAS_STARTING_DATE`
- `MIDAS_ENDING_DATE`
- `ALLOWED_ORIGINS` (domínio do frontend)

3. Suba o backend Playwright:

```bash
docker compose --env-file Conectividade/.env.playwright-vps -f Conectividade/docker-compose.playwright-vps.yml up -d --build
```

## Validação operacional

1. Healthcheck da API:

```bash
curl http://localhost:8000/health/ready
```

2. Fluxo Midas:
- Chame `POST /api/midas/correlate` sem enviar `midas_file` para forçar geração automática.
- Verifique status `completed` em `GET /api/process/{job_id}/status`.

## Notas importantes

- Em Linux, os paths são case-sensitive. Este projeto usa `Conectividade/` com `C` maiúsculo.
- O stack principal (`docker-compose.yml`) permanece inalterado.
- O modo `MIDAS_PLAYWRIGHT_RUNTIME_MODE=auto` ativa comportamento híbrido (container VPS vs local).
