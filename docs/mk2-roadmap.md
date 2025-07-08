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

### Memory Type System ⭐⭐⭐
**Move beyond fixed tags to flexible memory types**

**Problem**: Our 9 fixed tags are rigid
**Solution**: Flexible memory types (conversation, fact, entity, reflection, code)
**Why**: Better content structure, type-specific processing
**Reference**: WhenMoon-afk_claude-memory-mcp (utils/schema.py memory types)
**Implementation Effort**: (★★★☆☆) - Schema flexibility, validation updates, UI changes

**Implementation Details**:
- **Type System**: Replace fixed tags with user-defined + system-suggested types
- **Validation**: Schema validation for type-specific fields
- **Migration**: Automatic mapping from current tags to new type system
- **Processing**: Type-specific search and relevance algorithms

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

### Claude Desktop Response Sanitization ⭐
**Hide technical implementation details from users**

**Problem**: Claude Desktop sees technical details that may not be user-friendly
**Solution**: Toggle between technical mode (current) vs user-friendly mode
**Why**: Better user experience, cleaner interface for non-developers

**Current Technical Details Exposed**:
- Similarity scores (reveals RAG/vector search implementation)
- Memory IDs (technical database identifiers)  
- Internal conflict detection metadata
- ChromaDB structure and technical details

**Consider for MK2**:
- Hide similarity scores and show "relevance" instead
- Remove memory IDs from user-facing responses
- Simplify conflict presentation without technical details
- Maintain debugging mode for development/troubleshooting