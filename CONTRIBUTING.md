# Contributing

## Setup

1. Fork and clone the repository.
2. Create a branch from `main`.
3. Configure `.env` from `.env.example`.
4. Install dependencies:
   - Backend: `pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`

## Development Rules

- Keep secrets out of commits.
- Keep changes focused and reviewable.
- Add or update docs for behavior/config changes.
- Prefer small PRs with clear scope.

## Validation Before PR

Run at minimum:

```bash
python3 -m py_compile memory_server.py memory_mcp_direct.py
```

If frontend changes:

```bash
cd frontend && npm run build
```

## Pull Request Checklist

- [ ] No secrets/tokens/credentials committed
- [ ] No generated artifacts committed (`logs/`, `*.db`, `node_modules/`, `.DS_Store`)
- [ ] Docs updated where relevant
- [ ] Behavior tested locally
