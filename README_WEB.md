# Notas Compensadas Web (v1)

## Subir com Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`

## Rodar backend local

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

## Rodar frontend local

```bash
cd frontend
npm install
npm run dev
```

## API principal

- `POST /api/process`
- `GET /api/process/{job_id}/status`
- `GET /api/process/{job_id}/results`
- `GET /api/process/{job_id}/download/xlsx`
- `GET /api/process/{job_id}/download/pdf`
- `WS /ws/jobs/{job_id}`

## Regras aplicadas

- Limite: 25MB por arquivo
- Extensões: base `.xlsx`, relatório `.xls/.xlsx`
- 1 job ativo por usuário (`X-User-Id`, fallback IP)
- Retenção temporária: 24h com cleanup periódico

## Testes

```bash
python -m pytest backend/tests -q
```

## Observações

- O pipeline legado Python foi reaproveitado sem alterar regra de negócio.
- `app_interface.py` permanece legado.
- Exportação PDF disponível na v1.1 web.

## Deploy com Coolify + Traefik

- Para publicar em `https://automacao.logtudo.com.br/NotasCompensadas-FBL1`, use:
  - `VITE_APP_BASE_PATH=/NotasCompensadas-FBL1/`
  - `VITE_API_BASE_URL=/NotasCompensadas-FBL1/`
  - `VITE_WS_BASE_URL` vazio
- O Nginx do frontend já está preparado para:
  - servir SPA em `/NotasCompensadas-FBL1/`
  - proxy de API em `/NotasCompensadas-FBL1/api/*`
  - proxy de WS em `/NotasCompensadas-FBL1/ws/*`
- Se estiverem em subdomínios diferentes, configure no serviço frontend (build args):
  - `VITE_API_BASE_URL=https://api.seudominio.com`
  - `VITE_WS_BASE_URL=wss://api.seudominio.com`
