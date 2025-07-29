# TODO - Memory System Development

## URGENT FIXES

### 1. Forget Function Missing Memory Content (HIGH PRIORITY)
**Problem**: When users delete memories via MCP, the response only shows the memory ID (e.g., "I've forgotten that information") without displaying what was actually deleted. This makes it impossible for users to verify they deleted the correct memory.

**Solution**: Update the `forget` function in `memory_mcp_direct.py` to:
- Fetch the memory content before deletion
- Return both the ID and the text of the deleted memory
- Format: "I've forgotten: '[memory text]' (ID: mem_123...)"

**Impact**: User confidence and safety - prevents accidental deletion of important memories

### 2. Scalability Considerations (MEDIUM PRIORITY)
**Brainstorm**: As users accumulate hundreds/thousands of memories, consider:
- **Search performance**: Current vector search may slow down with large datasets
  - Consider indexing strategies for pgvector
  - Implement pagination for search results
  - Add query caching for frequent searches
- **Memory management**: 
  - Implement memory categories/folders for organization
  - Add bulk operations (delete multiple, export, etc.)
  - Consider memory archiving vs deletion
- **Storage optimization**:
  - Monitor embedding storage size (384 dimensions per memory)
  - Consider compression strategies
  - Plan for database sharding if needed
- **UI/UX for large memory sets**:
  - Better filtering and sorting options
  - Memory visualization/timeline views
  - Search within results

**Note**: Not critical until we have active users, but important to plan architecture for scale




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

## MEDIUM PRIORITY: UX Improvements

### Remove System Prompt Requirement
**Goal**: Eliminate the need for users to add system prompts to Claude Desktop settings

**Current Problem**: 
- Users need to setup MCP URL + add system prompt to Claude Desktop
- Creates friction for non-technical users  
- Two-step setup instead of "paste one URL and done"

**Solution**: Move all system prompt guidance into MCP function docstrings
- Enhance each function description with proactive usage guidelines
- Make functions self-explanatory so AI knows when/how to use them
- Test behavior consistency with/without system prompt

**Benefits**:
- ✅ True "one URL setup" experience
- ✅ Reduces onboarding friction significantly
- ✅ Better UX for non-technical users
- ✅ System already works without system prompt

**Implementation Status**:
- ✅ Current MCP functions work without system prompt
- ❌ Function descriptions need enhancement with proactive guidance
- ❌ Need to test AI behavior consistency
- ❌ Remove system prompt from DOCS.md once verified

**Priority**: Medium-High (good UX improvement, easy win with current small user base)

**Timing**: Should do now while user base is small (~10 users) for easy communication




