# Memory System v0

Minimal viable memory system with vector search and fixed tags.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python memory_server.py

# Test in another terminal
python test_client.py
```

## API Endpoints

- `POST /memories` - Store memory
- `POST /memories/search` - Search memories  
- `GET /memories` - List all memories
- `GET /health` - Health check

## Test Case

The MVP test stores "Prefers blunt, fast communication" and retrieves it via search query "What do you know about my communication style?"

Must pass 10 consecutive roundtrips to validate the system.

## Tags

Fixed set: `goal`, `routine`, `preference`, `constraint`, `habit`, `project`, `tool`, `identity`, `value`

## Tests and Validation

### What the tests actually proved

#### conflict_demo.py

**What it tested:** Write-time flagging + read-time surfacing of conflicts

**What it showed:**
- Similar memories (sim > 0.65) got has_conflicts=true and conflict_ids metadata.
- Retrieval and search return a conflict_set array so the caller can see all contradictory preferences.
- **Meaning:** the server now detects and packages conflicts; no LLM needed yet.

#### pruning_demo.py

**What it tested:** Age/usage pruning filter

**What it showed:** 
- Ran with 641 memories; none met both ">90 days old **and** not accessed in 30 days" → 0 pruned.
- Logic executes without touching protected identity/value tags.

#### Other script tests

**What they tested:** Manual tag validation, deduplication, semantic search

**What they showed:** All earlier guarantees still hold. Backend logic is sound; nothing broke.

## Integration Plan

### MCP Integration Approach

**Minimal viable approach:**
1. **Expose the three REST endpoints** already mapped in the demo
   - POST /memories (add)
   - POST /memories/search (vector + conflict_set)
   - GET /memories?tag=X (open by tag)

2. **Add a thin MCP wrapper** (Flask/FastAPI) that translates:
   - add_observations → POST /memories
   - search_nodes → POST /memories/search
   - open_nodes → GET /memories?tag=…

3. **Hook a local LLM** with a system prompt:
   ```
   If response contains conflict_set, pick the most recent item
   or ask the user to clarify.
   ```

4. Keep calls cheap: context only, no embeddings—server already does the heavy work.

5. **Mock test** first: drive the MCP wrapper with a simple Python client that simulates LLM questions.

## Implementation Roadmap

1. **Integrate conflict + pruning code into memory_server.py**
2. **Add MCP-compatible REST wrapper**
3. **Write a tiny client** that:
   - sends add_observations
   - asks search_nodes
   - prints conflict_set handling
4. **Swap the client** from stub to real LLM when satisfied
5. **Only after that** decide if a dedicated "memory-arbiter" LLM is needed
