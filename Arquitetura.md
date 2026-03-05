# 🏛️ Arquitetura Proposta: Frontend React + Backend API

A abordagem mais eficaz é desacoplar a lógica de processamento (seu código Python atual) da interface do usuário (o novo sistema em React). Faremos isso transformando seu backend em uma API que o frontend consumirá.

## 1. Backend: API de Processamento com FastAPI

Seu código Python atual será encapsulado por um framework de API. Recomendo o FastAPI por sua alta performance, suporte nativo a tarefas assíncronas e documentação automática.

### Refatoração
O `main.py` será adaptado para criar endpoints de API. Os módulos de lógica (`data_processor.py`, `report_processor.py`, `analysis_processor.py`, `final_report_generator.py`) serão mantidos e chamados por esses endpoints. O `app_interface.py` será descartado.

### Processamento Assíncrono
Como o processamento pode demorar, a API não deve bloquear. Ao receber uma requisição para processar, a API iniciará a tarefa em background e retornará imediatamente um `job_id`.

### Comunicação em Tempo Real
Para os logs e a barra de progresso, usaremos WebSockets. O frontend se conectará a um endpoint WebSocket para receber atualizações em tempo real sobre o andamento do processo.

### Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| **POST** | `/api/process` | Inicia processamento, retorna `job_id` |
| **GET** | `/api/process/{job_id}/status` | Consulta status do trabalho |
| **GET** | `/api/process/{job_id}/results` | Retorna dados das tabelas em JSON |
| **GET** | `/api/process/{job_id}/download/{file_type}` | Download do relatório (xlsx/pdf) |
| **WS** | `/ws/logs/{job_id}` | WebSocket para logs e progresso em tempo real |

## 2. Frontend: Aplicação com React (Vite)

A interface será uma SPA (Single Page Application) moderna, reativa e intuitiva.

### Stack Tecnológico
- **Vite + React + TypeScript** para ambiente de desenvolvimento rápido e tipagem segura
- **Mantine** para componentes UI completos e profissionais
- **Zustand** para gerenciamento de estado leve e poderoso
- **TanStack Table** para tabelas flexíveis e performáticas
- **Axios** para requisições HTTP

### Estrutura de Pastas

```
/src
├── /api           # Funções para chamar a API backend
├── /components    # Componentes reutilizáveis (Button, Table, ProgressBar)
├── /hooks         # Hooks customizados (useWebSocket)
├── /pages         # Componentes de página (HomePage)
├── /store         # Gerenciamento de estado (Zustand)
├── /styles        # Estilos globais e temas
└── App.tsx        # Componente raiz
```

### Fluxo de Interação

1. **Tela Inicial**: Usuário vê campos para upload dos dois arquivos e seleção do ano
2. **Início do Processamento**: Ao clicar em "Executar":
    - Envia arquivos para `POST /api/process`
    - Recebe `job_id`
    - Conecta ao WebSocket `/ws/logs/{job_id}`
    - UI exibe barra de progresso e logs em tempo real
3. **Conclusão**: Backend sinaliza fim do processo:
    - Frontend busca dados de `GET /api/process/{job_id}/results`
    - Renderiza tabelas nas abas "Resumo Consolidado" e "Detalhes de Pendências"
    - Ativa botões de exportação
4. **Exportação**: Links para download em `GET /api/process/{job_id}/download/{xlsx|pdf}`

---

## 🤖 Prompt para Geração do Sistema Web

```
Você é um desenvolvedor full-stack sênior, especialista em Python e React.

Sua tarefa é criar o código para uma aplicação web completa que substitui uma antiga interface em Tkinter. 
A aplicação web orquestra um processo de análise de dados em Python.

**Stack de Tecnologia:**
- Backend: Python com FastAPI
- Frontend: React com Vite, TypeScript, Zustand, Mantine e TanStack Table

**Requisitos do Backend (FastAPI):**
1. Estrutura de projeto FastAPI
2. Lógica de processamento em background tasks
3. Endpoints: POST /api/process, GET /api/process/{job_id}/results, GET /api/process/{job_id}/download/{file_type}
4. WebSocket /ws/logs/{job_id} para logs e progresso em tempo real

**Requisitos do Frontend (React):**
1. Vite + React + TypeScript
2. Mantine para componentes UI
3. Zustand store com: jobId, isProcessing, progress, logs, results, error
4. HomePage com formulário de upload e seção de resultados
5. Tabs com TanStack Table para "Resumo Consolidado" e "Detalhes de Pendências"
6. Botões de exportação (xlsx/pdf)
7. Conexão WebSocket para atualizações em tempo real

Gere o código inicial para estrutura de pastas e arquivos com lógica básica implementada.
```

### Sugestões de Próximos Passos
- Refatore o código Python para integrar com FastAPI, criando endpoints e background tasks
- Crie componentes React com Mantine e TanStack Table para exibir dados
