# TODO - Memory System Development




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




