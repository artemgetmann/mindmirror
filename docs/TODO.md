# TODO - Memory System Development

> **Note**: Feature roadmap moved to `system_comparison_summary.md` for consolidated planning.

## HIGH PRIORITY: Strategic Decision - Memory Extraction

**Question**: Should users be able to extract all their memories? Critical business/technical decision needed.

### The Dilemma
**FOR Extraction:**
- ✅ **User empowerment** - Data portability, trust, control
- ✅ **Competitive parity** - ChatGPT allows "tell me everything you know about me"  
- ✅ **Flexibility selling point** - Take memory anywhere, future-proof against non-MCP systems
- ✅ **Tesla/car AI scenario** - What if autonomous vehicles don't support MCP?
- ✅ **ChatGPT web limitation** - No MCP support, users need export to use with ChatGPT

**AGAINST Extraction:**
- ❌ **Customer stickiness** - Users can migrate to competitors easily
- ❌ **Reveals architecture** - Export format exposes ChromaDB structure, implementation details
- ❌ **Competitive advantage loss** - Easier reverse engineering
- ❌ **MCP lock-in alternative** - Keep users in our ecosystem, they use API keys with our server

### Strategic Questions
1. **MCP adoption bet**: Will MCP become standard? Timeline unclear
2. **Lock-in vs empowerment**: Proprietary control vs user trust?
3. **Technical exposure**: Can we export memories WITHOUT revealing system architecture?
4. **Competitive positioning**: How does ChatGPT handle this? What's our differentiation?

### Research Needed
- **Second opinion**: Consult another AI for strategic analysis
- **Competitor analysis**: How do other memory systems handle extraction?
- **MCP timeline**: When will major platforms (ChatGPT, Tesla, etc.) adopt MCP?
- **Technical sanitization**: Export format that hides implementation details?

### Potential Solutions
- **Tiered extraction**: Basic export (sanitized) vs full export (premium/developer)
- **API-only access**: Users keep data in our system, access via API keys
- **Format flexibility**: Multiple export formats for different use cases
- **Gradual rollout**: Test with power users first

**DECISION NEEDED**: This affects product roadmap, pricing strategy, and technical architecture.

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