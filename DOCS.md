# MCP Memory System Documentation

Comprehensive documentation for the MCP Memory System - a multi-tenant persistent memory solution for AI assistants.

## System Overview

**MCP Memory System** is a production-ready SaaS that provides persistent memory capabilities for AI assistants through the Model Context Protocol (MCP). Users can store preferences, facts, and context that persists across AI conversations.

### Architecture

```
Frontend (Vercel) → Backend API (Render) → PostgreSQL (Supabase) → Claude Desktop (MCP)
```

**Current Production Setup:**
- **Frontend**: React/TypeScript SPA with token generation UI (usemindmirror.com)
- **Backend**: FastAPI server with PostgreSQL + pgvector (memory.usemindmirror.com)
- **MCP Server**: Direct SSE implementation for Claude Desktop integration
- **Database**: PostgreSQL with pgvector for vector similarity search

## Quick Start

### Development

```bash
# Clone and setup
git clone https://github.com/artemgetmann/mcp_memory.git
cd mcp_memory
pip install -r requirements.txt

# Start backend services
python memory_server.py      # Port 8001 (API backend)
python memory_mcp_direct.py  # Port 8000 (MCP interface)

# Start frontend (optional)
cd frontend && npm install && npm run dev  # Port 8081
```

### Production URLs
- **Backend API**: https://memory.usemindmirror.com
- **Frontend**: https://usemindmirror.com
- **MCP URL Format**: `https://memory.usemindmirror.com/sse?token=USER_TOKEN`

## Core Components

### Backend Services
- `memory_server.py` - FastAPI backend with PostgreSQL storage (port 8001)
- `memory_mcp_direct.py` - MCP server for Claude Desktop integration (port 8000)
- `start_direct.sh` - Production deployment script

### Frontend Application
- React/TypeScript SPA with token generation interface
- Token modal with copy-to-clipboard functionality
- Built with Vite, shadcn/ui, and TailwindCSS

### Database Schema
- **PostgreSQL** with pgvector extension for vector operations
- **Tables**: memories, auth_tokens, waitlist_emails
- **Vector Search**: 384-dimension embeddings using SentenceTransformers

## Key Features

### Memory Management
- **Vector Search**: Semantic similarity using all-MiniLM-L6-v2 embeddings
- **Conflict Detection**: Automatic detection of contradictory preferences (similarity > 0.65)
- **Deduplication**: Prevents storing identical or very similar memories (similarity > 0.95)
- **Memory Limits**: 25 memories per free user, unlimited for admin users

### Multi-Tenant Architecture
- **Token-based Authentication**: Each user gets a unique secure token
- **User Isolation**: Complete data separation between users
- **Premium Waitlist**: Built-in system for upgrade tracking

### MCP Integration
- **Direct SSE Protocol**: Real-time communication with Claude Desktop
- **Six Core Functions**: remember(), recall(), forget(), what_do_you_know(), checkpoint(), resume()
- **Conflict Resolution**: AI can view and resolve conflicting memories
- **Short-term Memory**: Checkpoint/resume for conversation continuity across AI sessions

## API Endpoints

### Frontend APIs
- `POST /api/generate-token` - Generate new user token with MCP URL
- `POST /api/join-waitlist` - Join premium waitlist

### Memory APIs (Token-authenticated)
- `POST /memories?token=TOKEN` - Store new memory
- `POST /memories/search?token=TOKEN` - Vector similarity search
- `GET /memories?token=TOKEN` - List user memories
- `DELETE /memories/{id}?token=TOKEN` - Delete specific memory
- `POST /checkpoint?token=TOKEN` - Save conversation checkpoint (overwrites existing)
- `POST /resume?token=TOKEN` - Retrieve saved checkpoint
- `GET /health` - System health check

## Testing

```bash
# Test core functionality
python limit_test_unique.py

# Test MCP integration
# Method 1: MCP Inspector (Quick testing)
npx @modelcontextprotocol/inspector "http://localhost:8000/sse?token=YOUR_TOKEN"

# Method 2: Claude Desktop (Production testing)
# Add to Claude Desktop config: ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "mindmirror": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8000/sse?token=YOUR_TOKEN"]
    }
  }
}

# Test memory operations
curl -X POST "http://localhost:8001/memories?token=TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I prefer working mornings", "tag": "preference"}'

# Health check
curl http://localhost:8001/health
```

## Configuration

### Environment Variables
```bash
# Backend
MEMORY_SERVER_PORT=8001
PORT=8000  # For MCP server

# Frontend
VITE_API_URL=https://memory.usemindmirror.com  # Production
VITE_API_URL=http://localhost:8001              # Development
```

### Memory Tags
Fixed set of 9 tags: `goal`, `routine`, `preference`, `constraint`, `habit`, `project`, `tool`, `identity`, `value`

### System Limits
- **Memory Limit**: 25 per free user, unlimited for admin users
- **Conflict Threshold**: 0.65 similarity for conflict detection
- **Duplicate Threshold**: 0.95 similarity blocks storage
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)

## Database Operations

```bash
# Connect to production database
psql "postgresql://REDACTED_DB_USER:[REDACTED]@REDACTED_DB_HOST:6543/postgres?sslmode=require"

# Check active users
SELECT COUNT(DISTINCT user_id) FROM auth_tokens WHERE is_active = true;

# View memory usage
SELECT tag, COUNT(*) FROM memories GROUP BY tag;

# Create admin token
INSERT INTO auth_tokens (token, user_id, user_name, is_admin) 
VALUES ('your_admin_token', 'admin_user', 'Admin User', true);
```

## Deployment

### Backend (Render)
- **Service Type**: Web Service
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `./start_direct.sh`
- **Environment**: Production PostgreSQL connection

### Frontend (Vercel)
- **Framework**: React/Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment**: `VITE_API_URL` pointing to backend
- **vercel.json**: Required for SPA routing

### Database (Supabase)
- **PostgreSQL** with pgvector extension enabled
- **Tables**: Created automatically by backend initialization
- **Backups**: Managed by Supabase

## System Status

### Production Ready Features
- ✅ Multi-tenant memory storage and retrieval
- ✅ Automatic conflict detection and grouping
- ✅ Semantic duplicate prevention
- ✅ Token-based authentication
- ✅ Memory limit enforcement
- ✅ Premium waitlist integration
- ✅ MCP integration for Claude Desktop
- ✅ Frontend token generation interface

### Performance Characteristics
- **Response Time**: <500ms for memory operations
- **Concurrent Users**: Tested up to 100+ simultaneous users
- **Memory Capacity**: 25 memories per user (configurable)
- **Vector Search**: Sub-second similarity search across all memories

## Development Patterns

1. **Always test locally first**: Use curl for API, test MCP with both Inspector (quick) and Claude Desktop (production-like)
2. **Database changes**: Test with psql before code changes
3. **Frontend integration**: Use localhost:8001 for development API calls
4. **Memory limits**: Test with limit_test_unique.py
5. **MCP changes**: Restart Claude Desktop to pick up changes

## Troubleshooting

### Common Issues
1. **MCP Connection**: Ensure token is valid and server is running
2. **Memory Limits**: Check if user has reached 25 memory limit
3. **CORS Errors**: Verify frontend domain is in CORS origins list
4. **Database Connection**: Check PostgreSQL connection string
5. **SPA Routing**: Ensure vercel.json exists for proper routing

### MCP Testing Tips
1. **Test Both Methods**: Use MCP Inspector for quick iteration, Claude Desktop for final validation
2. **Claude Desktop Setup**: Add mcp-remote config, restart Claude Desktop after changes
3. **Token Validation**: Use admin_test_token_artem_2025 for unlimited testing
4. **Connection Verification**: Test with curl to /health endpoint first before MCP testing

### Debug Commands
```bash
# Check server health
curl http://localhost:8001/health

# Test token generation
curl -X POST http://localhost:8001/api/generate-token

# View server logs
tail -f logs/memory_server.log

# Test MCP connection
npx @modelcontextprotocol/inspector "http://localhost:8000/sse?token=TOKEN"
```

## Key Files

- `memory_server.py` - Main backend API server
- `memory_mcp_direct.py` - MCP protocol implementation
- `frontend/src/api/memory.ts` - Frontend API client
- `frontend/src/components/TokenModal.tsx` - Token generation UI
- `start_direct.sh` - Production deployment script
- `CLAUDE.md` - Quick reference for AI assistants

## Future Roadmap

### Immediate (MK2)
- Enhanced conflict resolution modes
- Improved memory organization
- Advanced search capabilities
- Premium subscription features

### Long-term
- Multi-language support
- Advanced analytics
- Team/organization features
- Integration with other AI platforms

## Setup Instructions

### Simple One-URL Configuration

The MCP Memory System requires only a single URL - no system prompts needed! Memory behavior is built into the MCP server using FastMCP's instructions parameter.

**Setup Steps:**
1. Generate token at https://usemindmirror.com
2. Add to your AI tool's MCP configuration
3. Restart your AI tool

**Built-in Intelligence:** AI automatically uses memory functions proactively, detects conflicts, and stores preferences without requiring system prompts.

**Legacy Documentation:** Historical system prompt documentation is available in `docs/archive/system-prompt.md` if needed for reference.


## License

MIT License - see [LICENSE](LICENSE) for details.

---

*This documentation reflects the current production state as of the latest deployment.*