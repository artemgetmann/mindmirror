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

### Environment Setup
```bash
# Python 3.8+ required
pip install -r requirements.txt

# LM Studio configuration
export OPENAI_API_KEY=sk-local
export OPENAI_API_BASE=http://localhost:1234/v1
```

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