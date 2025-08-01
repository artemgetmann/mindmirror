# TODO - Memory System Development

## URGENT FIXES

### 1. Forget Function Missing Memory Content (HIGH PRIORITY)
**Problem**: When users delete memories via MCP, the response only shows the memory ID (e.g., "I've forgotten that information") without displaying what was actually deleted. This makes it impossible for users to verify they deleted the correct memory.

**Solution**: Update the `forget` function in `memory_mcp_direct.py` to:
- Fetch the memory content before deletion
- Return both the ID and the text of the deleted memory
- Format: "I've forgotten: '[memory text]' (ID: mem_123...)"

make When the AI forgets memories using the MCP server, there is no indication of what memory it's forgetting. There's just the information ID and the memory ID, but there's no information about what memory is actually being deleted. And that's not user-friendly. We want users to see what actual memory is being deleted, so that when they click Accept, they know that they're deleting the right thing and not the wrong thing. I think that should be done in this way.


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

### Improve Conflict Detection for Conceptual Opposites
**Problem**: Current conflict detection uses 0.65 similarity threshold, which misses conceptual opposites with lower semantic similarity scores.

**Example**: "User prefers collaborative team environments" vs "User prefers working alone without interruptions" has similarity 0.609 (below 0.65 threshold), so they're not detected as conflicts despite being semantically opposite.

**Solution Options**:
1. **Lower similarity threshold** from 0.65 to 0.55-0.60 to catch more conceptual conflicts
2. **Add semantic contradiction detection** using NLP to identify opposing concepts (team/alone, morning/evening, etc.)
3. **Manual conflict keywords** - flag specific opposing term pairs automatically

**Current Status**: Works well for time preferences (morning/afternoon/evening) but misses conceptual opposites with lower similarity scores.

**Priority**: Medium - improves conflict detection accuracy for better user experience

### Improve Conflict Presentation and User Action Clarity
**Problem**: When conflicts are detected, Claude shows the conflicting memories but doesn't clearly instruct the user on what to do next or present conflicts with enough detail.

**Current Behavior**: 
- Shows: "⚠️ I remember some conflicting information (1 groups):" 
- Lists conflicts with IDs and dates
- But doesn't explicitly tell user what action to take

**Desired Behavior**:
```
⚠️ I remember some conflicting information (1 groups): 
IMPORTANT: Tell the user the exact conflicts with created date, relevance, and ask which they would like to keep. Present user with the exact word-for-word conflicts - don't assume user saw them in the response.

Conflict Group 1:
- "User prefers working alone only" (ID: mem_123, Created: July 29, 2025, Relevance: low)
- "User prefers working alone without interruptions" (ID: mem_456, Created: July 29, 2025, Relevance: low)

Which of these conflicting memories would you like to keep? I can delete the others for you.
```

**Solution**: Update MCP server conflict presentation to:
1. Always present exact conflict text word-for-word 
2. Include human-readable dates (July 29, 2025 instead of 2025-07-29)
3. Explicitly ask user which memory to keep
4. Offer to delete the unwanted conflicts
5. Don't assume user can see the conflicts in the technical response

**Priority**: Medium-High - improves user experience and conflict resolution workflow





