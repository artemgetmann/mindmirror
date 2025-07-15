# TODO - Memory System Development

> **Note**: Feature roadmap moved to `system_comparison_summary.md` for consolidated planning.


## HIGH PRIORITY: Response Sanitization (PRE-LAUNCH SECURITY)

**CRITICAL**: Hide technical implementation details from Claude Desktop before going live.

### Security Risk - Currently Exposed
```
❌ "similarity: 0.631" - reveals vector search/RAG implementation
❌ "mem_1751890084549" - exposes database ID patterns
❌ "ChromaDB returned 10 memories" - reveals backend technology  
❌ "similarity_score * 0.4 + recency_score * 0.3" - exposes algorithms
❌ "Union-Find conflict grouping" - reveals conflict detection approach
```

### Required Changes (memory_mcp_server.py)
```python
# Instead of: "similarity: 0.631" 
# Show: "relevance: high/medium/low"

# Instead of: "mem_1751890084549"
# Show: hidden or user-friendly reference

# Instead of: technical conflict metadata
# Show: "Some preferences conflict - which would you like to keep?"
```

### Implementation Strategy
1. **Add sanitization toggle** - `technical_mode = False` for production
2. **Replace similarity scores** - Map 0.8+ → "high", 0.5-0.8 → "medium", <0.5 → "low"  
3. **Hide memory IDs** - Remove from user-facing responses
4. **Simplify conflict language** - Remove technical jargon
5. **Keep debug mode** - `technical_mode = True` for development

### Business Impact
- **Prevents reverse engineering** of ChromaDB + SentenceTransformers stack
- **Hides competitive advantages** (conflict detection, similarity thresholds)
- **Protects algorithms** and implementation details
- **Professional user experience** - cleaner, less technical

**PRIORITY**: Implement before any public launch or demo

## HIGH PRIORITY: Memory Pruning Functionality Testing (PRE-LAUNCH CRITICAL)

**CRITICAL**: Test memory pruning system thoroughly before going live with real user data.

### Current Pruning Logic (NEEDS TESTING)
```python
# Current rules in memory_server.py:
# - Memories >90 days old AND not accessed in 30 days → eligible for pruning
# - Core tags (identity, value) are NEVER pruned
# - Archive endpoint identifies candidates without deleting
```

### Required Testing Before Launch
1. **Archive endpoint functionality** (`GET /memories/prune`)
   - Test with memories of different ages (30, 60, 90, 120 days)
   - Verify core tags (identity, value) are protected
   - Test last_accessed timestamp updates
   
2. **Pruning safety mechanisms**
   - Ensure no accidental deletion of important memories
   - Test edge cases: exactly 90 days, recent access updates
   - Verify core tag protection works correctly
   
3. **Real-world scenarios**
   - User goes inactive for 45 days - what gets pruned?
   - User has identity/value memories older than 90 days - are they protected?
   - Mixed memory ages with various access patterns

### Business Impact
- **Data loss prevention** - Incorrect pruning could delete valuable user memories
- **User trust** - Users need confidence their important memories are safe
- **Compliance** - Data retention policies must work correctly
- **Performance** - Pruning affects database size and search performance

### Implementation Status
- ✅ Pruning logic implemented in memory_server.py
- ❌ **NOT TESTED** with real data scenarios
- ❌ **NOT VALIDATED** core tag protection
- ❌ **NOT VERIFIED** last_accessed timestamp behavior

**ACTION REQUIRED**: Run comprehensive pruning tests before any production deployment or real user onboarding.

**PRIORITY**: CRITICAL - Test before any public launch or demo


## Bugs to Fix

### DateTime Deprecation Warning
- **File**: `memory_server.py` lines 88, 110, 140
- **Issue**: Using deprecated `datetime.utcnow()` instead of timezone-aware `datetime.now(datetime.UTC)`
- **Impact**: DeprecationWarning messages in logs, future Python compatibility issues
- **Error Messages**:
  ```
  DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  ```
- **Note**: Memory timestamps appear to work correctly, but need to update to modern datetime API for future-proofing


## FUTURE ENHANCEMENT: Token Endpoint

**Feature**: Add `/token` endpoint to memory server for easy token retrieval

### Implementation
```python
@app.get("/token")
async def get_current_token():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM auth_tokens WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"token": result[0]}
    else:
        return {"error": "No active token found"}
```

### Benefits
- **Easy token access**: `curl https://mcp-memory-uw0w.onrender.com/token`
- **No need to check deployment logs** - always accessible
- **Claude Desktop configuration** - get token anytime for setup
- **Debugging and development** - useful for troubleshooting
- **User-friendly** - no need to parse logs or check console output

### Priority
- **Low** - Current approach (token in deployment logs) works for now
- **Enhancement** - Would improve developer experience and user onboarding
- **Consider** - Add when user onboarding becomes more frequent

## Implementation Notes

- Consider whether to implement these features in our current ChromaDB system OR fork WhenMoon's architecture
- Our conflict detection system remains unique and valuable
- WhenMoon system uses JSON file storage vs our ChromaDB vector database



## Deferred Installation Tasks

### MCP Probe Installation (September 2025)
- **When**: After macOS 26 official release (September 2025)
- **Why Deferred**: Current macOS 26 pre-release has compatibility issues with Homebrew/Xcode
- **Installation Commands**:
  ```bash
  # Option 1: One-liner installer
  curl -fsSL https://raw.githubusercontent.com/conikeec/mcp-probe/master/install.sh | bash
  
  # Option 2: Homebrew (if available)
  brew tap conikeec/tap
  brew install mcp-probe
  
  # Option 3: Cargo (if Rust installed)
  cargo install mcp-cli
  ```
- **Purpose**: Ultra-fast MCP server testing with TUI interface for rapid development iteration
- **Alternative**: Continue using Claude Desktop testing (Inspector has compatibility issues with our server type)

