# MK2 Roadmap

## Current MVP Assessment

The system successfully handles core memory and conflict resolution use cases:
- ✅ Memory storage, search, and retrieval working reliably
- ✅ Dual conflict detection (automatic + LLM semantic reasoning)
- ✅ Conflict resolution via delete_memory tool
- ✅ Non-blocking workflow allows brain-dumping without interruption
- ✅ Ready for real-world testing and user feedback

## Conflict Detection Architecture

The system uses **two separate conflict detection mechanisms**:

1. **Storage-time detection**: Checks similarity > 0.65 when storing new memories, flags both memories with `has_conflicts` metadata
2. **Search-time display**: Shows conflict sets for memories that have the `has_conflicts` flag
3. **LLM semantic reasoning**: Catches conceptual conflicts the automatic system misses (like "detailed vs brief communication")

**Key insight**: Search returns top N results regardless of similarity threshold (explaining 0.3 similarity scores). Conflicts are detected at storage time, not search time.

## MK2 Planned Improvements

### Conflict Resolution Modes (User Toggle)
Add `conflict_resolution_mode` setting to give users control over their preferred workflow:

- **`"immediate"`** - Stop and ask user to resolve conflicts before storing new memory
  - Best for: Precision users who want clean database
  - UX: "You previously said X, now you're saying Y. Which should I keep?"
  
- **`"deferred"`** - Current behavior, store and flag conflicts for later resolution
  - Best for: Brain-dumpers who don't want workflow interruption
  - UX: Continue conversation, surface conflicts during search
  
- **`"auto_replace"`** - Automatically replace older conflicting memory with new one
  - Best for: Quick users updating preferences frequently
  - UX: Seamless updates, show notification of replacement

### ✅ Enhanced Conflict Detection (COMPLETED)
**✅ IMPLEMENTED**: 
- Semantic similarity working with SentenceTransformers embeddings detecting conceptual conflicts
- 0.65 similarity threshold proven effective in stress testing (Test 4 validated perfect conflict detection)
- Union-Find conflict grouping organizes complex conflict sets into clean groups
- Search-time conflict detection working - conflicts surface during search with clean presentation
- Natural language conflict cleanup demonstrated in Test 6 edge case handling

### User Experience Improvements
- **Conflict prevention**: Ask before storing obvious duplicates
- **Guided resolution workflows**: UI/prompts to help users resolve complex conflicts
- **Conflict analytics**: Show conflict patterns and help users understand their preferences
- **Memory organization**: Categories, folders, or hierarchical organization

### Security & Privacy Considerations
- **Configurable log levels**: DEBUG/INFO/ERROR modes for production
- **Log rotation and retention policies**: Automatic cleanup of old logs
- **Privacy options**: Toggle for query logging in production environments
- **Data sanitization**: Option to disable detailed logging for sensitive deployments

### Deployment Considerations
- **Port configuration**: Currently hardcoded to port 8003 for memory server
  - May conflict with cloud deployment platforms (Render, Railway, etc.)
  - Consider environment variable PORT for dynamic assignment
  - Update MCP server configuration to use dynamic ports
- **Service orchestration**: Multiple services (memory server + MCP server) need coordination
- **Health checks**: Current `/health` endpoint ready for load balancers

### Export/Import System
**Enable data portability and backup/restore workflows**

**Problem**: Users can't migrate between systems or share memory sets
**Solution**: Add export/import endpoints with multiple format support

**Implementation Details** (based on claude-memory system):
- **Export formats**: JSON, YAML, CSV, Markdown
- **Filtering options**: By date range, memory types, tags
- **Data structure preservation**: Complete schema compatibility
- **Sanitization**: Option to remove sensitive information
- **Round-trip compatibility**: Export → Import with no data loss

**API Endpoints**:
- `GET /export?format=json&types=preference,goal&from=2025-01-01`
- `POST /import` with file upload and merge/replace modes
- `GET /export/schema` for format documentation

### Session Management ⭐⭐⭐⭐⭐ (NEEDS EXPLORATION)
**Enable cross-conversation awareness and relationship detection**

**Current Status**: We have basic memory persistence across chats (memories stored in database persist between Claude Desktop conversations), but this is NOT true session management.

**What We Have**: Cross-session memory access - new chats can search previously stored memories
**What We're Missing**: ChatGPT-style cross-conversation context awareness where AI understands when topics in different chats are related without explicit memory storage

**Research Needed**: 
- How to implement conversation relationship detection
- Cross-chat context synthesis and proactive context bridging  
- Session metadata tracking (themes, outcomes, continuation patterns)
- "This seems related to what we discussed yesterday about X" capabilities

**Implementation Details** (research required):
- **Conversation fingerprinting**: Detect topic similarity across different chats
- **Context bridging**: Reference previous conversations without explicit memory storage
- **Session metadata**: Track conversation themes, outcomes, continuation patterns
- **Proactive awareness**: Surface related previous conversations automatically

### ✅ Enhanced Deduplication (COMPLETED)
**Prevent semantic duplicates with different timestamps**

**✅ IMPLEMENTED**: System now uses semantic similarity check (>0.95 threshold) BEFORE storage to prevent duplicates. Test 6 validated this prevents duplicate proliferation ("I like working in the mornings" blocked at 0.9556 similarity). Real-time prevention working at storage time with graceful user feedback.

### Search Precision Improvements ⭐⭐⭐
**Improve recall of semantically related but keyword-distant memories**

**Problem**: Important memories don't surface in relevant searches due to keyword/semantic gaps
- Example: Query "writing style preferences communication" doesn't return memory about "signature phrases and patterns: 'Look...', 'What about...'"
- Core writing style memories surface correctly, but specific phrase patterns get missed
- Search works for 90%+ of cases but misses nuanced relationships

**Solution Options**:
1. **Query expansion**: Auto-expand "writing style" → ["phrases", "patterns", "signature", "voice", "tone"]
2. **Multi-query strategy**: Run multiple targeted searches and merge results
3. **Semantic keyword mapping**: Map concepts to related terms
4. **Tag-aware search**: Weight memories by relevance to query domain

**Research First**: Check GitHub open source memory systems to see how they solved similar issues
- WhenMoon memory system approach to query expansion and semantic mapping
- Obsidian/Logseq search precision techniques
- ChromaDB/Pinecone query enhancement strategies  
- RAG systems with multi-query approaches
- Learn existing patterns before implementing custom solution

**Implementation Effort**: ⭐⭐⭐ (4-6 hours) - Query expansion + multi-search strategy
**Impact**: Makes product feel significantly smarter and more comprehensive
**Priority**: Post-MVP polish - good for v1.1 after user feedback

### Advanced Relevance Scoring
**Improve search results with multi-factor scoring**

**Problem**: Current search only uses similarity scores, ignoring usage patterns and recency
**Solution**: Combined scoring algorithm balancing similarity, recency, and importance

**Implementation** (based on WhenMoon system, lines 3091-3119):
```python
relevance_score = (
    similarity_score * 0.4 +     # Semantic relevance
    recency_score * 0.3 +        # How recent the memory is
    importance_score * 0.3       # Based on access frequency
)
```

**Benefits**: 
- Recent memories rank higher even with lower similarity
- Frequently accessed memories get priority
- More practical, usage-based results

**Note**: Our current approach relies on Claude to evaluate timestamp relevance. This provides algorithmic intelligence for more consistent ranking.

### Multi-Tier Memory System ⭐⭐⭐⭐⭐
**Enable intelligent memory lifecycle management**

**Problem**: Our system treats all memories equally - no lifecycle management
**Solution**: Short-term → Long-term → Archived tiers with automatic promotion/demotion  
**Why**: Enables intelligent memory management, better performance, natural forgetting
**Reference**: WhenMoon-afk_claude-memory-mcp (domains/manager.py, domains/temporal.py)
**Implementation Effort**: (★★★☆☆) - Database schema changes, promotion logic, tier management

**Implementation Details**:
- **Tier Structure**: Short-term (0-7 days), Long-term (7-90 days), Archived (90+ days)
- **Promotion Logic**: Access frequency, relevance scores, manual user flagging
- **Performance**: Query optimization to search active tiers first
- **Storage**: Add `tier` field to memory schema, background promotion jobs

### Access Tracking & Importance ⭐⭐⭐
**Enable usage-based memory prioritization**

**Current Status**: Basic `last_accessed` timestamp tracking implemented and working
**Still Needed**: Full importance scoring system with decay algorithm

**Problem**: No comprehensive visibility into memory usage patterns
**Solution**: Track access_count, last_accessed, importance decay over time
**Why**: Enables intelligent archiving, usage-based prioritization
**Reference**: WhenMoon-afk_claude-memory-mcp (persistence.py access tracking)
**Implementation Effort**: (★★☆☆☆) - Add fields, update endpoints, decay calculation

**Implementation Details**:
- **New Fields**: `access_count`, `importance_score` (we have `last_accessed`)
- **Auto-update**: Increment access_count on each retrieval
- **Decay Algorithm**: `importance = base_importance * (1 - age_factor) * access_multiplier`
- **Query Integration**: Use importance in relevance scoring algorithm

**Core Memory Identification** (Obsidian-style second brain):
- **Access count display**: Show AI how many times each memory has been accessed
- **Core memory detection**: Memories with high access counts become "core memories"
- **Reinforcement learning**: Frequently accessed memories get priority in search results
- **Usage patterns**: AI can identify which memories are most important to the user
- **Implementation**: Add `access_count` field, increment on each recall/search, display to AI
- **Benefits**: Mimics human memory reinforcement where frequently accessed information is easier to recall

### Memory Type System ⭐⭐⭐
**Move beyond fixed tags to flexible memory types**

**Current Limitation**: Hard-coded 9 fixed tags with strict validation
```python
# memory_server.py lines 47-50
VALID_TAGS = ["goal", "routine", "preference", "constraint", "habit", "project", "tool", "identity", "value"]

# Rigid validation (line 82-86)
if memory.tag not in VALID_TAGS:
    raise HTTPException(status_code=400, detail=f"Invalid tag. Must be one of: {VALID_TAGS}")
```

**Problem**: Users need domain-specific categorization (e.g., `meeting_notes`, `book_highlights`, `health_data`, `patient_notes`)

**WhenMoon's Approach**: Flexible, user-defined memory types
- **Base Types**: `conversation`, `fact`, `entity`, `reflection`, `code`
- **User-Defined**: Custom types created dynamically 
- **Hierarchical**: Type relationships and inheritance
- **Schema Validation**: Type-specific field requirements
- **Processing**: Type-aware search and relevance algorithms

**Implementation Strategy**:
1. **Phase 1**: Add `custom_type` field alongside existing tags for backward compatibility
2. **Phase 2**: Replace VALID_TAGS validation with flexible type registry  
3. **Phase 3**: Migration utility to convert fixed tags to flexible types
4. **Phase 4**: Type-specific processing and schema validation

**Technical Details**:
- **Database**: Add `memory_type` field, keep `tag` for migration
- **Validation**: Replace hard list with type registry + user creation API
- **API**: `POST /memory-types` for custom type creation
- **Migration**: `goal` → `personal_goal`, `habit` → `daily_habit`, etc.
- **Backward Compatibility**: Accept both old tags and new types during transition

**Implementation Effort**: (★★★☆☆) - Database migration, validation rewrite, type management system

### CLI Helper Wrapper ⭐⭐
**Improve development and testing workflow**

**Problem**: Testing and development requires manual API calls
**Solution**: Thin Click/Typer wrapper for `mcpmem search/store/list` commands
**Why**: Faster development workflow, easier debugging
**Implementation Effort**: (★☆☆☆☆) - Simple CLI wrapper over existing API

**Implementation Details**:
- **Commands**: `mcpmem search "query"`, `mcpmem store "text" --tag preference`
- **Output**: Pretty-printed results, JSON option for scripting
- **Configuration**: Connect to local/remote memory server
- **Integration**: Use existing FastAPI endpoints, no new logic

### Auto-Archive System ⭐⭐
**Automatic cleanup of old, unused memories**

**Problem**: No automatic cleanup of old, unused memories
**Solution**: Nightly job: `WHERE age>90d AND last_access>30d → archived=true`
**Why**: Prevents database bloat, maintains performance
**Reference**: WhenMoon-afk_claude-memory-mcp archival logic
**Implementation Effort**: (★★☆☆☆) - Background job, archive endpoint, cleanup logic

**Implementation Details**:
- **Criteria**: Configurable age and access thresholds
- **Safety**: Never auto-archive `identity` or `value` tagged memories
- **Recovery**: Archived memories searchable but with lower priority
- **Monitoring**: Archive statistics and undo capability

---

## 🧠 HIGH PRIORITY: Strategic Decision – Memory Extraction

**Question**: Should users be able to extract their memories? This is a critical call with implications for trust, lock-in, architecture, and future interoperability.

---

### ⚖️ The Dilemma

**FOR Extraction**:
- ✅ **User empowerment** — Builds trust through data ownership and transparency
- ✅ **Competitive parity** — ChatGPT allows "Tell me everything you know about me"
- ✅ **MCP-agnostic future** — Users can use memory outside MCP-native tools (e.g., ChatGPT web, Tesla, or future local AI systems)
- ✅ **AI continuity across models** — One memory across Claude, GPT, Gemini, etc.
- ✅ **Portability as a feature** — Makes MindMirror a source of truth, not just a service

**AGAINST Extraction**:
- ❌ **Reduces stickiness** — Users can migrate away easily
- ❌ **Leaks architecture** — Naive exports could reveal ChromaDB layout or internal tagging logic
- ❌ **Loss of moat** — Makes it easier to reverse-engineer or replicate approach
- ❌ **Ecosystem control** — Lock-in via API token keeps users in the MCP-based universe

---

### 🎯 Strategic Framing

**Short-term MVP** (✅ shipping today):
- No full export needed
- AI model can already respond with: "Here's what I remember about you" via `list_memory`, `search_memory`, or `get_memory`

**Mid-term Premium Plan** (⚙️ optional):
- Offer **Basic Memory Export** as JSON, using a sanitized schema:
  - No internal DB structure revealed
  - Just top-level objects: tag, key, value, timestamp
  - Example:
    ```json
    {
      "tag": "goal",
      "key": "2025_vision", 
      "value": "Build AGI infrastructure",
      "updated": "2025-07-15T13:42Z"
    }
    ```

**Future Dev/Enterprise Plan** (🔓 optional):
- Offer **Full Export** or SDK sync (e.g., `GET /export/full`)
- Or add **MCP Mirror Mode**: stream memory to developer's DB via webhook or plugin
- All behind auth walls or usage tiers

---

### 🤖 Key Research Questions

1. **MCP ecosystem maturity**
   - Will non-MCP systems adopt external memory interfaces soon?
   - Is MindMirror memory a bridge or a destination?

2. **ChatGPT behavior**
   - How transparent is OpenAI about memory data?
   - Can we beat them on usability + trust?

3. **Export Format Design**
   - Can we decouple export from DB implementation?
   - Is a "memory object schema" standardizable?

4. **Security implications**
   - Can exports be digitally signed or encrypted if needed?

---

### 🧩 Final Recommendation

**✅ YES, allow memory extraction** — but with phased control:

| Phase | Export Format | Audience | Risks | Benefit |
|-------|---------------|----------|-------|---------|
| MVP | None | All users | None | Simplicity, fast shipping |
| Premium | Sanitized JSON | Pro/power users | Low | Trust, portability, goodwill |
| Developer | Full JSON/API | Devs/enterprises | Medium | Dev flexibility |

---

### 🧠 Why This Works

- **You build trust** without revealing internals
- **You avoid overengineering** the MVP
- **You future-proof** MindMirror as a memory layer, not a walled garden
- **You retain the option** to tier access, throttle export, or monetize sync

---

**Implementation options**:
- An export schema spec
- Code for `GET /export/basic`
- A memory signing or encryption flow
- Text for privacy/legal UX copy ("you own your data")

---

## 🔍 STRATEGIC RESEARCH: Competitive Memory Systems Analysis

**Question**: Should we research other memory systems on the market to understand their features and potentially implement superior approaches, or focus purely on our own vision?

**Philosophy**: "You don't know what you don't know" - but we should research intelligently, not copy blindly.

### Research Approach

**✅ DO**:
- **Survey existing solutions** to understand the problem space landscape
- **Analyze their design decisions** from first principles: What problem were they solving? Why did they choose this approach?
- **Identify gaps or better solutions** based on our unique understanding
- **Learn patterns and anti-patterns** without copying implementations

**❌ DON'T**:
- Rush to implement features just because competitors have them
- Copy solutions without understanding the underlying problem
- Let feature parity drive product direction
- Waste time on features that don't align with our core value proposition

### Key Research Questions

1. **Problem Understanding**:
   - What specific memory/context problems are other systems trying to solve?
   - Are their problems the same as ours, or different user segments?
   - What constraints led them to their current architecture?

2. **Design Trade-offs**:
   - Why did they choose their conflict resolution approach?
   - How do they handle memory organization and search?
   - What are the performance vs. accuracy trade-offs they made?

3. **Better Solutions**:
   - Given our MCP-first architecture, can we solve their problems more elegantly?
   - Are there fundamental improvements possible with our tech stack?
   - What would we build differently knowing what we know now?

### Research Methodology

**Phase 1: Problem Space Mapping**
- Catalog existing memory systems (ChatGPT Memory, Mem.ai, NotionAI, etc.)
- Document their core value propositions and target use cases
- Identify common problems they're all trying to solve

**Phase 2: First Principles Analysis**
- For each interesting feature: Why does it exist? What problem does it solve?
- Could we solve the same problem better with our architecture?
- What are the real user needs vs. implementation artifacts?

**Phase 3: Strategic Decision**
- Which problems align with our vision and user base?
- What can we build uniquely well that others can't?
- Where should we innovate vs. adopt proven patterns?

**Implementation Timeline**: Research phase before building new features - investment in understanding pays dividends in building the right things.

