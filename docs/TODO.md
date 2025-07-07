# TODO - Memory System Development

> **Note**: Feature roadmap moved to `system_comparison_summary.md` for consolidated planning.

## Current Testing

### System Validation
- **TODO**: Continue with stress tests 4-7 (refer to docs/stress_tests.md)
- Tests 1-3 completed successfully: Memory overload, conflict creation, multi-tag stress
- Remaining: Contradiction bomb, search stress, edge cases, real-world scenarios

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

## Implementation Notes

- Consider whether to implement these features in our current ChromaDB system OR fork WhenMoon's architecture
- Our conflict detection system remains unique and valuable
- WhenMoon system uses JSON file storage vs our ChromaDB vector database