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

### Start the stack

```bash
cd ai-email-workspace
make up
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

- Email: `demo@inboxia.local`
- Password: `password`

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
- `PROVIDER=stub|openai`
- `OPENAI_API_KEY` (optional)
- `FRONTEND_BACKEND_URL`

Frontend:

- `NEXT_PUBLIC_BACKEND_URL`

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
