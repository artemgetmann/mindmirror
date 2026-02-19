# MindMirror MCP Memory

Persistent memory service for AI assistants using the Model Context Protocol (MCP).

## Project Status

This project is currently on pause. The codebase remains available for reference, self-hosting, and future continuation.

This repository provides:
- `memory_server.py`: FastAPI API for memory storage/search, token management, and checkpoints.
- `memory_mcp_direct.py`: MCP server (Streamable HTTP + SSE compatibility) that exposes memory tools.
- `frontend/`: React app for token generation and integration onboarding.
- `examples/`: Node examples for MCP + OpenAI function-calling integration.

## Core Features

- Multi-tenant token auth (`auth_tokens` table)
- Semantic memory search with pgvector + SentenceTransformers (`all-MiniLM-L6-v2`)
- Conflict detection and duplicate prevention
- Checkpoint/resume for short-term conversation handoff
- MCP tools: `remember`, `recall`, `forget`, `what_do_you_know`, `checkpoint`, `resume`

## Architecture

```text
Client (Claude/Cursor/Custom) -> MCP Server (memory_mcp_direct.py) -> Memory API (memory_server.py) -> PostgreSQL + pgvector
```

## Hosted URLs

- Frontend: https://usemindmirror.com
- Backend API: https://memory.usemindmirror.com

## Quick Start (Local)

1. Create local secrets file (not committed):
```bash
cp .env.local.example .env.local
$EDITOR .env.local
```

2. Set required DB config in `.env.local`:
- `DATABASE_URL` (recommended), or
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (+ optional `DB_PORT`, `DB_SSLMODE`)

3. Start the stack (recommended for AIs and local dev):
```bash
docker compose --env-file .env.local up --build
```

4. Health checks:
```bash
curl http://localhost:8001/health
curl http://localhost:8000/health
```

Optional non-Docker run:
```bash
cp .env.example .env
pip install -r requirements.txt
python memory_server.py
python memory_mcp_direct.py
```

## Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Environment Variables

See `.env.local.example`, `.env.example`, and `frontend/.env.example`.

Important runtime variables:
- `DATABASE_URL` or `DB_*` vars
- `MEMORY_API_BASE` (used by MCP proxy service, default `http://localhost:8001`)
- `CORS_ALLOW_ORIGINS`
- `ALLOWED_API_HOSTS`
- `MCP_ALLOWED_HOSTS`
- `ENFORCE_HOST_CHECK`
- `BOOTSTRAP_DEFAULT_TOKEN` (default `false`)

## Security Notes

- Do not commit real API keys, tokens, or database credentials.
- Use environment variables for all secrets.
- If this repository was ever exposed with real credentials, rotate them before publishing.

## API Summary

- `POST /api/generate-token`
- `POST /api/join-waitlist`
- `POST /memories`
- `POST /memories/search`
- `GET /memories`
- `GET /memories/{id}`
- `DELETE /memories/{id}`
- `POST /checkpoint`
- `POST /resume`

Auth token can be passed via:
- `Authorization: Bearer <token>`
- `?token=<token>` (legacy compatibility)

## License

MIT (see `LICENSE`).
