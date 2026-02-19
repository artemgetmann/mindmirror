# CLAUDE.md

Agent-facing reference for this repository.

## What This Repo Is

MCP-backed persistent memory service:
- `memory_server.py` for storage/search/auth APIs
- `memory_mcp_direct.py` for MCP transport + tool exposure
- `frontend/` for token generation and integration UX

## Local Run

Default workflow (preferred for agents and local development):

```bash
cp .env.local.example .env.local
$EDITOR .env.local
docker compose --env-file .env.local up --build
```

Optional direct process workflow:

```bash
cp .env.example .env
pip install -r requirements.txt
python memory_server.py
python memory_mcp_direct.py
```

## Required Environment

Either:
- `DATABASE_URL`

Or:
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

## Important Safety Rules

- Do not hardcode credentials or tokens in source code.
- Do not commit logs, local databases, cache files, or `node_modules`.
- Prefer `Authorization: Bearer` token auth; query token is legacy-compatible.

## Quick Checks

```bash
python3 -m py_compile memory_server.py memory_mcp_direct.py
curl http://localhost:8001/health
curl http://localhost:8000/health
```
