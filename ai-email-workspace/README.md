# Inboxia - AI Email Workspace

Inboxia is a local-first AI email workspace with IMAP ingestion, SMTP sending, and a side-by-side chat assistant powered by retrieval-augmented generation (RAG). This repo is a monorepo with a FastAPI backend, Next.js frontend, and infra manifests for Docker Compose and Azure deployment.

## Repository Layout

```
/ai-email-workspace
  /backend
  /frontend
  /infra
  docker-compose.yml
  README.md
```

## Features

- Inbox list, thread view, compose/send experience.
- Side-by-side AI chat panel with citations.
- IMAP ingestion and thread reconstruction.
- Vector search using pgvector in Postgres.
- Celery + Redis for ingest and embedding tasks.
- Provider interface for OpenAI or local stub.

## Local Development

### Prerequisites

- Docker + Docker Compose
- Node 20+ (optional for local frontend dev)
- Python 3.11 (optional for local backend dev)

### Start the stack (default: local LLM + app)

```bash
cd ai-email-workspace
make up
```

The default `make up` command now brings up **everything** in one shot:

- Postgres + Redis
- Backend + Worker
- Frontend
- Local vLLM OpenAI-compatible service

> **No GPU available?** Run the app without a local LLM (stub responses) using:
>
> ```bash
> LLM_PROVIDER=stub docker compose -f docker-compose.yml up --build
> ```

If port `8000` is already in use on your machine, set `BACKEND_PORT` to pick a different host port for the backend:

```bash
BACKEND_PORT=8001 make up
```

If port `8001` is already in use on your machine, set `LLM_PORT` to pick a different host port for the local LLM:

```bash
LLM_PORT=8002 make up
```

### Run migrations

```bash
make migrate
```

### Seed demo user

```bash
make seed
```

The demo user defaults to:

- Email: `demo@example.com`
- Password: `password`

After seeding, open the UI at `http://localhost:3000` and log in with the demo credentials.

### Run tests

```bash
make test
```

Integration tests require a running Postgres with pgvector:

```bash
RUN_INTEGRATION_TESTS=1 DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/inboxia pytest
```

## Environment Variables

Backend:

- `DATABASE_URL`
- `REDIS_URL`
- `LLM_PROVIDER=stub|openai|openai_compatible` (preferred)
- `PROVIDER=stub|openai` (legacy, still supported)
- `OPENAI_API_KEY` (optional)
- `OPENAI_BASE_URL` (optional, default: `https://api.openai.com/v1`)
- `OPENAI_CHAT_MODEL` (optional, default: `gpt-4o-mini`)
- `OPENAI_EMBEDDING_MODEL` (optional, default: `text-embedding-3-small`)
- `FRONTEND_BACKEND_URL`
- `BACKEND_PORT` (optional, host port for the backend in Docker Compose; default: `8000`)
- `LLM_PORT` (optional, host port for the local LLM in Docker Compose; default: `8001`)

Frontend:

- `NEXT_PUBLIC_BACKEND_URL`

## Where to access the UI

The UI is served by the Next.js frontend on port 3000. The backend on port 8000 only serves JSON APIs, so `GET /` returns `404 Not Found` by design.

- Frontend UI: `http://localhost:3000`
- Backend API: `http://localhost:8000` (or `http://localhost:${BACKEND_PORT}`)

## Run locally with AI (default)

The default Docker Compose flow starts vLLM and points the backend/worker at it automatically:

```bash
make up
```

By default this uses:

- LLM endpoint: `http://host.docker.internal:${LLM_PORT:-8001}/v1`
- Chat model: `Qwen/Qwen2.5-7B-Instruct`
- Embedding model: `Qwen/Qwen2.5-7B-Instruct`

### Option A: vLLM via Docker Compose (GPU)

Start the local LLM service:

```bash
make llm
```

This starts a vLLM OpenAI-compatible server on `http://localhost:${LLM_PORT:-8001}/v1`. Configure the app stack to use it:

```bash
LLM_PROVIDER=openai_compatible
OPENAI_BASE_URL=http://host.docker.internal:${LLM_PORT:-8001}/v1
OPENAI_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct
OPENAI_EMBEDDING_MODEL=<embedding-model>
```

By default, `make llm` serves `Qwen/Qwen2.5-7B-Instruct` with no credentials required and persists the Hugging Face cache in a Docker volume so model weights are reused across restarts. To switch models, set `LLM_MODEL`:

```bash
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct make llm
```

To clear the cached weights, remove the `ai-email-workspace_vllm_cache` Docker volume.

### Option B: vLLM on the host

If you prefer to run vLLM directly on your host GPU:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model <chat-model> \
  --host 0.0.0.0 \
  --port 8001
```

Then set `OPENAI_BASE_URL=http://host.docker.internal:8001/v1` for the backend/worker.

### Recommended models for ~16-20GB VRAM

- `Qwen/Qwen2.5-7B-Instruct` (fp16)

Make sure your embedding model supports the OpenAI `/v1/embeddings` API. You can point both chat and embeddings to the same model if needed.

### Switching back to OpenAI

To use OpenAI's hosted API instead of a local LLM:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Using a local OpenAI-compatible service

If you run an OpenAI-compatible server on your host (for example, on `http://localhost:8001/v1`), point the backend/worker at it and switch the provider:

```bash
LLM_PROVIDER=openai_compatible
OPENAI_API_KEY=local-key
OPENAI_BASE_URL=http://host.docker.internal:8001/v1
OPENAI_CHAT_MODEL=your-chat-model
OPENAI_EMBEDDING_MODEL=your-embedding-model
```

In Docker Compose, `host.docker.internal` is wired to the host via `extra_hosts` so containers can reach the service running on your machine.

## API Endpoints

- `POST /api/auth/login`
- `GET /api/accounts`
- `POST /api/ingest/run`
- `GET /api/folders?account_id=`
- `GET /api/messages?account_id=&folder_id=&limit=&offset=`
- `GET /api/threads?account_id=&folder_id=`
- `GET /api/thread/{thread_id}`
- `POST /api/compose/draft`
- `POST /api/compose/send`
- `POST /api/chat/query`

## Azure Deployment

### Option A: Azure Container Apps

1. Build and push images to ACR:

```bash
az acr build --registry <ACR_NAME> --image inboxia-backend:latest ./backend
az acr build --registry <ACR_NAME> --image inboxia-frontend:latest ./frontend
```

2. Create Container Apps environment and deploy services:

- Backend: `inboxia-backend` (port 8000)
- Worker: `inboxia-worker`
- Frontend: `inboxia-frontend` (port 3000)
- Redis: `inboxia-redis`
- Postgres: use Azure Database for PostgreSQL or run a container

3. Configure environment variables for the backend and worker:

- `DATABASE_URL`
- `REDIS_URL`
- `PROVIDER`
- `OPENAI_API_KEY` (if using OpenAI)

### Option B: AKS

Use manifests in `infra/k8s` as a starting point:

```bash
kubectl apply -f infra/k8s
```

Update the container images and environment variables for your cluster.

## Notes

- IMAP/SMTP passwords are stored in plaintext for dev; add encryption in production.
- The stub provider is deterministic and requires no external keys.
