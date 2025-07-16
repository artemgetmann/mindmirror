# CLAUDE.md

Development guidance for the MCP Memory System - a production-ready persistent memory SaaS for AI assistants.

## Current Architecture (Production)

```
Frontend (Vercel) → Backend API (Render) → PostgreSQL (Supabase) → Claude Desktop (MCP)
```

**Services:**
- `memory_server.py` - FastAPI backend with PostgreSQL + pgvector (port 8001)
- `memory_mcp_direct.py` - MCP server for Claude Desktop integration (port 8000)
- Frontend React/TypeScript SPA with token generation UI

## Quick Development Setup

```bash
# Start backend services
python memory_server.py      # API backend (port 8001)
python memory_mcp_direct.py  # MCP interface (port 8000)

# Start frontend (optional)
cd frontend && npm run dev    # Port 8081
```

## Key API Endpoints

### Frontend APIs
- `POST /api/generate-token` - Generate new user token with MCP URL
- `POST /api/join-waitlist` - Premium waitlist signup

### Memory APIs (Token-authenticated)
- `POST /memories?token=TOKEN` - Store memory with conflict detection
- `POST /memories/search?token=TOKEN` - Vector similarity search  
- `GET /memories?token=TOKEN` - List user memories
- `DELETE /memories/{id}?token=TOKEN` - Delete specific memory

## Development Testing

```bash
# Test token generation
curl -X POST http://localhost:8001/api/generate-token

# Test memory storage
curl -X POST "http://localhost:8001/memories?token=TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I prefer working mornings", "tag": "preference"}'

# Test MCP integration
npx @modelcontextprotocol/inspector "http://localhost:8000/sse?token=TOKEN"

# Test memory limits
python limit_test_unique.py
```

## Database Operations

```bash
# Connect to production database
psql "postgresql://REDACTED_DB_USER:REDACTED_DB_PASSWORD@REDACTED_DB_HOST:6543/postgres?sslmode=require"

# Check active users
SELECT COUNT(DISTINCT user_id) FROM auth_tokens WHERE is_active = true;

# View memory usage
SELECT tag, COUNT(*) FROM memories GROUP BY tag;
```

## System Configuration

### Memory Limits
- **Free Users**: 25 memories maximum
- **Admin Users**: Unlimited (is_admin = true in auth_tokens)
- **Premium**: Unlimited (planned feature)

### Similarity Thresholds
- **Conflict Detection**: 0.65 similarity triggers conflict flagging
- **Duplicate Prevention**: 0.95 similarity blocks storage
- **Vector Model**: SentenceTransformers all-MiniLM-L6-v2 (384 dimensions)

### Memory Tags
Fixed set: `goal`, `routine`, `preference`, `constraint`, `habit`, `project`, `tool`, `identity`, `value`

## MCP Integration

### Four Core Functions (Claude Desktop)
- `remember(text, category)` - Store new memory
- `recall(query, limit, category_filter)` - Search memories
- `forget(information_id)` - Delete specific memory  
- `what_do_you_know(category, limit)` - List all memories

### Token Authentication
- Each user gets unique token via frontend
- MCP URL format: `https://mcp-memory-uw0w.onrender.com/sse?token=USER_TOKEN`
- Token validates against PostgreSQL auth_tokens table

## Production URLs

- **Backend API**: https://mcp-memory-uw0w.onrender.com
- **Frontend**: https://usemindmirror.com (deploying to Vercel)
- **Health Check**: https://mcp-memory-uw0w.onrender.com/health

## Development Patterns

1. **Always test locally first**: Use curl for API, MCP Inspector for MCP
2. **Database changes**: Test with psql before code changes
3. **Frontend integration**: Use localhost:8001 for development API calls
4. **Memory limits**: Test with limit_test_unique.py
5. **MCP changes**: Restart Claude Desktop to pick up changes

## Key Files

- `memory_server.py` - Main backend API server
- `memory_mcp_direct.py` - MCP protocol implementation
- `frontend/src/api/memory.ts` - Frontend API client
- `frontend/src/components/TokenModal.tsx` - Token generation UI
- `start_direct.sh` - Production deployment script
- `DOCS.md` - Comprehensive documentation

---

*For detailed documentation, see [DOCS.md](DOCS.md)*