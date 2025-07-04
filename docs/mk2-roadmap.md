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

### Enhanced Conflict Detection
- **Semantic similarity models**: Use NLI or better embedding models for conceptual conflicts
- **Lower similarity thresholds**: Tune or make configurable below 0.65
- **Search-time conflict detection**: Check for conflicts during search, not just storage
- **Batch conflict cleanup**: Periodic guided conflict resolution sessions

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

### Session Management
**Enable cross-conversation memory persistence**

**Problem**: Each Claude Desktop chat is independent - new chats can't access previous memories
**Solution**: Add session tracking to enable cross-conversation memory access

**Implementation Details** (based on claude-memory system):
- **Session structure**: ID, name, start/end times, status, outcome
- **Auto-rotation**: Time-based session creation (4-hour intervals)
- **Cross-session search**: Search across ALL sessions, not just current
- **Session context**: Link memories to sessions while maintaining global searchability
- **Persistent storage**: All session data stored in single data store

**Key Features**:
- Automatic session naming based on time of day
- Session boundaries for organization without limiting access
- Memory persistence across conversation sessions
- Session history and outcome tracking

### Enhanced Deduplication
**Prevent semantic duplicates with different timestamps**

**Problem**: Current MD5 approach misses semantic duplicates ("I prefer email" vs "I like email communication")
**Solution**: Multi-layer deduplication using semantic similarity

**Implementation**:
1. **Semantic similarity check** (>0.95 threshold) BEFORE storage
2. **Update existing** similar memory instead of creating duplicate
3. **MD5 hash fallback** for exact text matches
4. **Real-time prevention** at storage time, not import time

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

**Problem**: No visibility into memory usage patterns
**Solution**: Track access_count, last_accessed, importance decay over time
**Why**: Enables intelligent archiving, usage-based prioritization
**Reference**: WhenMoon-afk_claude-memory-mcp (persistence.py access tracking)
**Implementation Effort**: (★★☆☆☆) - Add fields, update endpoints, decay calculation

**Implementation Details**:
- **New Fields**: `access_count`, `last_accessed`, `importance_score`
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