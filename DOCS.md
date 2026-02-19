# Technical Documentation

## Hosted Deployment

- Frontend: https://usemindmirror.com
- Backend API: https://memory.usemindmirror.com

## Services

- `memory_server.py` (default port `8001`): core memory + auth API.
- `memory_mcp_direct.py` (default port `8000`): MCP transport and tool layer, proxies frontend APIs to `memory_server.py`.
- `start_direct.sh`: starts both services for container/runtime environments.

## Data Model

`memory_server.py` initializes required tables on startup:

- `auth_tokens`
- `waitlist_emails`
- `memories` (pgvector `vector(384)`)
- `short_term_memories`

Required PostgreSQL extension:
- `vector`

## Memory Semantics

- Fixed categories: `goal`, `routine`, `preference`, `constraint`, `habit`, `project`, `tool`, `identity`, `value`
- Duplicate threshold: semantic similarity `> 0.95` blocks inserts
- Conflict threshold: semantic similarity `>= 0.65` flags possible conflicts
- Default memory limit: `25` for non-admin users (`auth_tokens.is_admin = false`)

## API Endpoints

### Public utility
- `GET /health`
- `GET /` (service metadata)

### Auth and onboarding
- `POST /api/generate-token`
- `POST /api/join-waitlist`

### Token-authenticated memory APIs
- `POST /memories`
- `POST /memories/search`
- `GET /memories`
- `GET /memories/{memory_id}`
- `DELETE /memories/{memory_id}`
- `GET /memories/prune`
- `POST /checkpoint`
- `POST /resume`

## MCP Endpoints

`memory_mcp_direct.py` exposes:
- Streamable HTTP transport at `/mcp/` (redirect from `/mcp`)
- SSE transport at `/sse/` with POST messages at `/sse/messages/` (redirect from `/sse`)

## Recommended Agent System Prompt

Use this for assistants that connect to MindMirror MCP tools:

```text
IMPORTANT: You have access to memory tools:
- remember(text, category)
- recall(query, limit, category_filter)
- forget(information_id)
- what_do_you_know(category, limit)
- checkpoint(text, title)
- resume()

Use recall proactively before personal recommendations and preference-based advice.
If conflicting preferences exist, explicitly show the conflict and ask which one to follow.
Only call forget after user explicitly asks to delete specific memories.

When user explicitly states preferences (e.g. "I prefer X"), store them with remember.
For non-explicit patterns or inferred behaviors, ask permission before storing.

Memory categories: goal, routine, preference, constraint, habit, project, tool, identity, value.

Use checkpoint when user wants to continue later or in another AI tool.
Use resume when user asks to continue previous work without context.
If checkpoint output indicates overwrite warning, tell the user clearly.
```

Full UI version of this prompt also exists in:
- `frontend/src/pages/Integration.tsx`

## Configuration

Use `.env.local.example` as the template and `.env.local` (gitignored) for real machine-only credentials.

Recommended startup command:

```bash
docker compose --env-file .env.local up --build
```

### Required
- `DATABASE_URL` OR `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

### Optional
- `DB_PORT` (default `5432`)
- `DB_SSLMODE` (default `require`)
- `MEMORY_API_BASE` (default `http://localhost:8001`)
- `CORS_ALLOW_ORIGINS` (comma-separated)
- `ALLOWED_API_HOSTS` (comma-separated)
- `MCP_ALLOWED_HOSTS` (comma-separated)
- `ENFORCE_HOST_CHECK` (`true`/`false`)
- `BOOTSTRAP_DEFAULT_TOKEN` (`true`/`false`)

## Local Validation Checklist

1. `python3 -m py_compile memory_server.py memory_mcp_direct.py`
2. Start both services.
3. `curl` health endpoints.
4. Generate token via `/api/generate-token`.
5. Store/search/delete a test memory.
6. Exercise MCP endpoint with a client (Claude, mcp-remote, or inspector).

## Open Source Hygiene

- Keep credentials out of source control.
- Never commit runtime logs, databases, or local package installs.
- Use `examples/.env.example` and `frontend/.env.example` placeholders only.
