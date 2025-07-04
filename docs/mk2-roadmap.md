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

### Claude Desktop Response Sanitization
**Brainstorm whether to Sanitize Claude Desktop Responses to Hide Infra Details (e.g. Similarity, RAG)**

Current issue: Claude Desktop sees technical implementation details that may not be user-friendly:
- Similarity scores (reveals RAG/vector search implementation)
- Memory IDs (technical database identifiers)  
- Internal conflict detection metadata
- ChromaDB structure and technical details

Consider for MK2:
- Toggle between technical mode (current) vs user-friendly mode
- Hide similarity scores and show "relevance" instead
- Remove memory IDs from user-facing responses
- Simplify conflict presentation without technical details
- Maintain debugging mode for development/troubleshooting