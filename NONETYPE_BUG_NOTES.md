# NoneType Bug Investigation Notes

## Summary
We encountered two related bugs in the MindMirror memory system:
1. **Original Bug**: NoneType comparison errors when searching memories
2. **New Bug**: After fixing the NoneType issue, searches without category filters started failing

## Timeline
- **Commit 900857b**: Fixed NoneType comparison bug (introduced new search bug)
- **Commit ed27a18**: Reverted the fix to restore production functionality
- **Debug Branch**: `debug-nonetype-fix` contains the broken fix for investigation

## Original NoneType Bug

### Error Message
```
I couldn't recall that: '>' not supported between instances of 'NoneType' and 'float'
```

### Cause
PostgreSQL's vector similarity calculation `1 - (embedding <=> %s::vector)` was returning NULL values when:
- The embedding column was NULL for some memories
- The vector operation failed due to incompatible dimensions

### Fix Applied (in commit 900857b)
1. Added COALESCE to SQL queries: `COALESCE(1 - (embedding <=> %s::vector), 0.0)`
2. Added NULL checks before comparisons: `if similarity is not None and similarity > threshold`
3. Updated `get_relevance_level()` to handle None values
4. Added try-catch for numpy similarity calculations

## New Bug After Fix

### Symptoms
1. **Searches without category filter fail** with validation errors
2. **Searches with category filter work** but return unexpected results (6 items instead of 10)
3. MCP Inspector shows error: "Error executing tool recall: 1 validation error for tag_filter"

### Test Cases

#### Failed Case (No Category Filter)
```
Query: "writing style tone voice"
Expected: List of memories about writing style
Actual: Validation error
```

#### Working Case (With Category Filter)
```
Query: "style"
Category: "goal"
Expected: 10 results (default limit)
Actual: 6 results
```

### Suspected Causes
1. The COALESCE changes in SQL queries might be affecting parameter binding
2. The params array manipulation for tag filtering might have been disrupted
3. Possible issue with how NULL values are handled in the search endpoint

## Code Analysis

### Changed SQL Queries
Before:
```sql
SELECT id, text, 1 - (embedding <=> %s::vector) as similarity
```

After:
```sql
SELECT id, text, COALESCE(1 - (embedding <=> %s::vector), 0.0) as similarity
```

### Parameter Handling (memory_server.py:481-489)
```python
tag_filter_sql = ""
params = [query_embedding, user_id, query_embedding, request.limit]
if request.tag_filter:
    if request.tag_filter not in VALID_TAGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tag filter. Must be one of: {VALID_TAGS}"
        )
    tag_filter_sql = "AND tag = %s"
    params.insert(2, request.tag_filter)
```

## Investigation Steps
1. Check if COALESCE affects parameter binding in psycopg2
2. Verify the params array is correctly constructed
3. Test the exact SQL queries with and without COALESCE
4. Check if the MCP layer is sending incorrect parameters
5. Review the validation error details from the MCP Inspector

## Production Status
- **Main Branch**: Reverted to working state (without NoneType fix)
- **Debug Branch**: `debug-nonetype-fix` contains the broken fix
- **Production URL**: https://memory.usemindmirror.com
- **Admin Token**: admin_test_token_artem_2025

## Next Steps
1. Set up local testing environment to reproduce the issue
2. Debug the parameter handling in the search endpoint
3. Test SQL queries directly against the database
4. Find a solution that fixes both bugs without breaking functionality
5. Consider alternative approaches to handling NULL similarity values