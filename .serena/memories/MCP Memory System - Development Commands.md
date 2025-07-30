# Development Commands & Testing

**Local Development**:
```bash
# Backend services
python memory_server.py      # Port 8001 (API)
python memory_mcp_direct.py  # Port 8000 (MCP)

# Frontend
cd frontend && npm run dev    # Port 8081
```

**Testing**:
```bash
# Core functionality
python limit_test_unique.py

# MCP testing
npx @modelcontextprotocol/inspector "http://localhost:8000/sse?token=TOKEN"

# API testing
curl -X POST "http://localhost:8001/memories?token=TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "tag": "preference"}'
```

**Frontend Commands**:
- `npm run build` - Production build
- `npm run lint` - ESLint checking
- No specific test framework detected