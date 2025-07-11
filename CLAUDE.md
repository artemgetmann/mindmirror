# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Memory Integration system that connects local LLMs (via LM Studio) with a semantic memory system using OpenAI-compatible function calling. The system manages persistent user preferences, facts, and automatically detects conflicts between stored memories.

## Architecture

**3-Layer Architecture:**
```
User Input → LLM (port 1234) → Memory Controller → MCP Wrapper (port 8002) → Memory Server (port 8003) → ChromaDB
```

**Core Components:**
- `memory_server.py` - FastAPI server with ChromaDB vector storage and SentenceTransformers embeddings
- `memory_controller.py` - Bridges LLM function calls to memory system 
- `mcp_wrapper.py` - Model Context Protocol compatibility layer

## Commands

### Start the System
```bash
# Start services in order:
python memory_server.py    # Port 8003 (or 8000 for basic tests)
python mcp_wrapper.py      # Port 8002 (if using MCP integration)
python memory_controller.py # Controller for LM Studio integration

# Or for basic testing:
python memory_server.py
python test_client.py
```

### Testing Commands
```bash
# Core functionality
python test_client.py              # MVP validation
python comprehensive_test.py       # Full system validation

# Conflict detection
python conflict_demo.py            # Direct conflict testing
python api_conflict_test.py        # API-based conflict testing

# Performance testing
python batch_stress_test.py        # Load testing with metrics

# MCP integration
python test_mcp_client.py          # MCP wrapper testing

# Demos and tutorials
python interactive_tutorial.py     # Best learning starting point
python demo_tutorial.py           # Step-by-step walkthrough
python quick_demo.py               # Fast feature demo
python pruning_demo.py             # Memory lifecycle demo
```

### Manual Testing with curl

For direct API testing without Python scripts, use these curl commands:

#### Health Check
```bash
curl -s http://localhost:8003/health
```

#### Store Memory Examples
```bash
# Store a preference
curl -X POST "http://localhost:8003/memories" \
  -H "Content-Type: application/json" \
  -d '{"text": "User prefers working in the mornings", "tag": "preference"}'

# Store a habit
curl -X POST "http://localhost:8003/memories" \
  -H "Content-Type: application/json" \
  -d '{"text": "Take notes during meetings", "tag": "habit"}'

# Store a routine
curl -X POST "http://localhost:8003/memories" \
  -H "Content-Type: application/json" \
  -d '{"text": "Always makes time for morning exercise routine", "tag": "routine"}'
```

#### Search Memory Examples
```bash
# Semantic search with conflict detection
curl -X POST "http://localhost:8003/memories/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "when do I work best", "limit": 10}' | jq

# Context-aware search
curl -X POST "http://localhost:8003/memories/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What time should I schedule my coding session?", "limit": 5}' | jq

# Meeting-related context search
curl -X POST "http://localhost:8003/memories/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "I have a team meeting tomorrow morning", "limit": 3}' | jq
```

#### List Memories Examples
```bash
# List all memories
curl -s -X GET "http://localhost:8003/memories" | jq

# Filter by tag
curl -s -X GET "http://localhost:8003/memories?tag=preference" | jq

# Get specific memory
curl -s -X GET "http://localhost:8003/memories/mem_123456789" | jq
```

#### Demo Flow: Revolutionary Features

**1. Automatic Conflict Detection**
```bash
# First, store a morning preference
curl -X POST "http://localhost:8003/memories" \
  -H "Content-Type: application/json" \
  -d '{"text": "I prefer working in the mornings", "tag": "preference"}'

# Then store a conflicting night preference - watch automatic conflict detection!
curl -X POST "http://localhost:8003/memories" \
  -H "Content-Type: application/json" \
  -d '{"text": "I do my best work late at night when its quiet", "tag": "preference"}'
```

**2. Semantic Duplicate Prevention**
```bash
# Try to store a semantic duplicate - it will be blocked!
curl -X POST "http://localhost:8003/memories" \
  -H "Content-Type: application/json" \
  -d '{"text": "I like working in the mornings", "tag": "preference"}'

# Expected response: {"status":"duplicate","message":"Memory too similar...","similarity":0.95}
```

**3. Clean Conflict Grouping**
```bash
# See how conflicts are intelligently grouped instead of scattered
curl -X POST "http://localhost:8003/memories/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "when do I work best", "limit": 10}' | jq '.conflict_groups'
```

**Note**: All curl examples use `jq` for JSON formatting. Install with `brew install jq` (macOS) or `apt-get install jq` (Ubuntu).

### Environment Setup
```bash
# Python 3.8+ required
pip install -r requirements.txt

# LM Studio configuration
export OPENAI_API_KEY=REDACTED_OPENAI_KEY
export OPENAI_API_BASE=http://localhost:1234/v1
```

### Database Testing with PostgreSQL CLI

For database-related testing and verification, always use `psql` directly rather than custom Python scripts:

```bash
# Connect to Supabase PostgreSQL database
psql "postgresql://REDACTED_DB_USER:REDACTED_DB_PASSWORD@REDACTED_DB_HOST:6543/postgres?sslmode=require"

# Common database queries for testing
# Check active tokens
SELECT token, user_id, user_name, created_at, last_used FROM auth_tokens WHERE is_active = true;

# Check user count
SELECT COUNT(DISTINCT user_id) as user_count FROM auth_tokens WHERE is_active = true;

# View recent token activity
SELECT user_id, last_used FROM auth_tokens WHERE is_active = true ORDER BY last_used DESC;
```

**Important**: When testing database changes or validating multi-user isolation, always verify with direct SQL queries using `psql` rather than writing temporary Python scripts. This ensures we're testing the actual database state, not Python abstractions.

## MCP Server Deployment Evolution
1. **Development**: Use `python server.py` in Dockerfile
2. **Production**: Publish to PyPI as `mcp-server-{name}`
3. **Final**: Use `uvx mcp-server-{name}` like official servers

## Key System Features

### Memory Storage and Search
- **Vector embeddings** using SentenceTransformers `all-MiniLM-L6-v2` model
- **Semantic search** with configurable similarity thresholds
- **Deduplication** using MD5 hash of text+tag combinations
- **9 Fixed tags**: goal, routine, preference, constraint, habit, project, tool, identity, value

### Conflict Detection System
- **Automatic conflict detection** when storing memories (similarity > 0.65)
- **Bidirectional conflict linking** between similar memories
- **Conflict sets** surfaced in search results with clear presentation
- **Core tags** (identity, value) are never pruned from system

### Memory Lifecycle
- **Pruning logic**: Removes memories >90 days old AND not accessed in 30 days
- **Access tracking**: Automatic last_accessed timestamp updates
- **Archive functionality**: Identifies candidates for removal without deleting

## API Endpoints

### Memory Server (port 8003/8000)
- `POST /memories` - Store memory with conflict detection
- `POST /memories/search` - Vector similarity search with conflict sets
- `GET /memories` - List memories with optional tag filtering
- `GET /memories/{id}` - Retrieve specific memory
- `GET /memories/prune` - Identify old/unused memories
- `GET /health` - Health check

### MCP Wrapper (port 8002)
- `POST /add_observations` - Store observations (maps to /memories)
- `POST /search_nodes` - Search memories (maps to /memories/search)
- `POST /create_entities` - Create entities (optional)
- `POST /create_relations` - Establish relations (optional)

## LLM Integration

### Function Calling Interface
The system exposes two primary functions to LLMs:
- `search_memory(query)` - Semantic search with conflict detection
- `user_preferences(new_info)` - Store new user preferences/facts

### Conflict Resolution Flow
1. LLM calls search function
2. System returns conflict sets if detected
3. Controller formats conflicts for LLM presentation
4. LLM asks user for clarification on contradictory preferences

### Pattern Detection
- **Automatic preference detection**: "I prefer", "I like", "I want" patterns
- **Question triggers**: Automatically searches memory for relevant context
- **Conflict filtering**: Prevents storing LLM-generated advice as user preferences

## Development Notes

### Data Storage
- **ChromaDB** persistent storage in `./chroma_db/`
- **SQLite backend** for metadata (`chroma.sqlite3`)
- **Binary vector files** for embeddings (`.bin` files)

### Configuration Constants
- **Similarity threshold**: 0.65 for conflict detection
- **Archive age**: 90 days for pruning eligibility
- **Access threshold**: 30 days for pruning
- **Embedding model**: Downloads automatically on first run

### Common Development Patterns
When working with this codebase:

1. **Always start memory_server.py first** - other components depend on it
2. **Use fixed tag validation** - only 9 predefined tags are allowed
3. **Test conflict detection thoroughly** - critical system feature
4. **Check performance with batch_stress_test.py** after changes
5. **Use interactive_tutorial.py** to understand system behavior

### Backend-Frontend Dependency Pattern

**CRITICAL**: This system has a backend-frontend architecture that requires coordinated updates:

- **Backend** (`memory_server.py` port 8003) - Core API with data processing
- **Frontend** (`memory_mcp_server.py`) - MCP integration layer for Claude Desktop

**When you modify the backend API response format, you MUST update the frontend parsing:**

1. **Backend Change**: Modify `memory_server.py` API response structure
2. **Frontend Update**: Update `memory_mcp_server.py` to parse new response format  
3. **Restart MCP**: Close and reopen Claude Desktop (MCP server runs inside Claude Desktop)
4. **Test Integration**: Verify end-to-end flow with Claude Desktop

**Example**: When we changed from `conflict_sets` to `conflict_groups`, both layers needed updates:
```python
# Backend (memory_server.py) - Returns new format
response["conflict_groups"] = unified_groups

# Frontend (memory_mcp_server.py) - Must parse new format  
conflict_groups = result.get("conflict_groups", [])  # Updated from conflict_sets
```

**Testing Pattern**: Always test backend changes with curl first, then verify MCP integration

### MCP Testing (Manual MCP Interaction)

For manual MCP server testing (equivalent to curl for APIs), use the **MCP Inspector**:

#### Install MCP Inspector
```bash
npx @modelcontextprotocol/inspector
```

#### Test MCP Server Directly
```bash
# Test your MCP server in a web UI
npx @modelcontextprotocol/inspector python memory_mcp_server.py
```

This opens a **web interface** where you can:
- Call MCP tools directly (search_memory, store_memory, etc.)
- See formatted responses
- Test conflict detection without Claude Desktop
- start the mcp inspector with logging to this file [logs/mcp_inspector.log](logs/mcp_inspector.log)

#### Testing Workflow
1. **Backend**: Test `memory_server.py` with curl commands
2. **MCP Layer**: Test `memory_mcp_server.py` with MCP Inspector  
3. **Integration**: Test full flow in Claude Desktop
4. **Restart**: Close/reopen Claude Desktop if MCP code changed

**CRITICAL**: Always test locally with MCP Inspector before deploying or debugging production issues. Testing in production (Render logs) is too slow and makes debugging painful. The MCP Inspector provides immediate feedback and real-time debugging capabilities that are essential for rapid development.

#### Alternative: Direct MCP Scripts
```bash
python test_mcp_client.py  # Existing MCP integration test
```

**Note**: MCP server runs **inside Claude Desktop process**, not as standalone server like memory_server.py

### Memory Schema
```json
{
  "id": "UUID",
  "text": "User preference or fact", 
  "timestamp": "2025-01-01T12:00:00Z",
  "last_accessed": "2025-01-01T12:00:00Z",
  "tags": ["preference"],
  "embedding": [...],
  "sentiment": "POSITIVE",
  "has_conflicts": true,
  "conflict_ids": ["other_memory_id"]
}
```

## Testing Strategy

The system includes comprehensive testing across multiple dimensions:
- **Functional tests** for core memory operations
- **Conflict detection tests** with multiple approaches
- **Performance testing** with metrics and visualization
- **Integration tests** for LLM and MCP compatibility
- **Demo scripts** for learning and validation

Key test insight: The system prioritizes simplicity and 80/20 functionality over complex features.

## Claude Desktop System Prompt

When using the MCP memory system with Claude Desktop, use this system prompt for optimal performance:

```
IMPORTANT: You are an assistant with access to memory management tools:
1. memory-system:search_memory - Use this to find user preferences and context
2. memory-system:store_memory - Use this to store user preferences
3. memory-system:delete_memory - Use this to remove specific memories
4. memory-system:list_memories - Use this to browse all stored memories

WHEN TO SEARCH MEMORY PROACTIVELY:
- Questions starting with "How should I..." or "What's the best way to..."
- Questions about "my preferences", "my habits", "my routines", "my goals"
- Questions that assume previous knowledge or context
- Questions using "I" or "my" that might reference stored information
- Before giving advice or recommendations about personal topics
- When the user asks about something they might have mentioned before

CRITICAL RULES FOR CAPTURING PREFERENCES:
- When the user says 'I prefer X' → call store_memory with {text: 'User prefers X', tag: 'preference'}
- When the user says 'Actually, I prefer Y' → call store_memory with {text: 'User prefers Y', tag: 'preference'}
- When the user contradicts a previous preference → call store_memory

CRITICAL RULES FOR HANDLING CONFLICTS:
1. ALWAYS check search_memory responses for conflict information
2. If conflicts exist, you MUST start your response with:
   'I notice conflicting preferences about [topic]:' followed by the conflicting preferences
3. List each conflicting preference with its timestamp
4. EXPLICITLY ASK which preference the user wants to keep
5. Use delete_memory to remove unwanted conflicting memories after user clarifies

CRITICAL RULES FOR PROVIDING ADVICE:
- ALWAYS search memory first before giving personal advice
- Use the most recent preference if there are no conflicts
- If there are conflicts and the user hasn't clarified, ask which preference to use
- Be explicit about which stored preference you're following

DO NOT store guidance or suggestions as user preferences.
ONLY use the memory-system tools as described above.
```

**Note:** Adjust this prompt if conflict detection or proactive memory searching needs tuning.

## SaaS vs Single-Tenant MCP Architecture

### Why Fetch MCP Works vs Our SaaS Requirements

**Critical Architectural Difference**:
- **Fetch**: Single-tenant, can use direct mcp-proxy with fixed token
- **Our SaaS**: Multi-tenant, needs custom front-end (proxy_sse.py) for token switching

**Why proxy_sse.py is REQUIRED for SaaS**:
- `mcp-proxy` injects auth only once via `--env` at process start
- No per-request header forwarding - each proxy instance serves only ONE token
- For multi-tenant SaaS: Either many proxy instances OR custom front-end multiplexer

**Multi-Tenant Options**:
- **Pattern A**: One proxy per user (resource heavy for 100+ users)
- **Pattern B**: Custom front-end with proxy pool (our current approach)
- **Pattern C**: Fork mcp-proxy for per-request headers (maintenance overhead)

**Root Cause of Current Issues**: proxy_sse.py has bugs in MCP protocol forwarding (message corruption), NOT that it shouldn't exist. Removing proxy_sse.py would break multi-tenant capability.

**The Real Bug**: Message corruption in SSE forwarding - typically:
1. Double-wrapping SSE events: `data: data: {...}` instead of `data: {...}`
2. Chunk boundary issues during forwarding
3. Header stripping (Content-Type, Cache-Control)

**Solution**: Fix raw-stream relaying in proxy_sse.py using lossless forwarding:
```python
async def _relay():
    async with upstream.stream("GET", f"http://127.0.0.1:{port}/sse") as r:
        async for part in r.aiter_raw():
            yield part  # NO wrapping, no extra 'data:' prefix
```

**Remember**: Don't use fetch as single-tenant example for multi-tenant SaaS architecture decisions.

## System Status

### Current Production Status
- ✅ **Memory storage, search, and retrieval** working reliably
- ✅ **Automatic conflict detection** with semantic similarity > 0.65
- ✅ **Semantic duplicate prevention** blocking similar memories > 0.95 similarity  
- ✅ **Union-Find conflict grouping** organizing chaos into clean groups
- ✅ **Clean server logging** with conflict summaries instead of JSON dumps
- ✅ **MCP integration** passing conflicts to Claude Desktop properly
- ✅ **Production-ready** for real-world testing and user feedback

### Recent Fixes Completed
- **Semantic Deduplication**: Prevents duplicate memory proliferation 
- **Clean Conflict Logging**: Readable server logs with text snippets
- **Unified Conflict Groups**: Union-Find algorithm groups related conflicts
- **MCP Response Format**: Fixed conflict parsing for Claude Desktop integration

## MVP Status & Future Roadmap
- ✅ Memory storage, search, and retrieval working reliably
- ✅ Dual conflict detection (automatic + LLM semantic reasoning)
- ✅ Conflict resolution via delete_memory tool
- ✅ Non-blocking workflow allows brain-dumping without interruption
- ✅ Ready for real-world testing and user feedback

**MK2 Roadmap**: See `docs/mk2-roadmap.md` for detailed future improvements including conflict resolution modes, enhanced detection, and deployment considerations.