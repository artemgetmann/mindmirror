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

### MCP Inspector Compatibility Research (September 2025)
- **Issue**: Official MCP Inspector fails to connect with our low-level MCP server implementation
- **Error**: "Connection Error - Check if your MCP server is running and proxy token is correct"
- **Root Cause**: Inspector expects FastMCP servers, not low-level Server class via stdio transport
- **Current Workaround**: Claude Desktop testing works perfectly (proven with conflict resolution workflow)
- **Research Questions**:
  - How to configure Inspector for low-level MCP servers?
  - Alternative MCP testing tools compatible with our architecture?
  - Benefits of refactoring to FastMCP vs keeping current implementation?
- **Priority**: Low (current testing workflow is sufficient)

## Implementation Notes

- Consider whether to implement these features in our current ChromaDB system OR fork WhenMoon's architecture
- Our conflict detection system remains unique and valuable
- WhenMoon system uses JSON file storage vs our ChromaDB vector database