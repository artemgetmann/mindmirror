# Local Development Files

This directory contains files specifically for local development and testing with LM Studio.

## Files

### Core Local Components
- `memory_controller.py` - Bridges LM Studio (port 1234) with MCP memory system
- `mcp_wrapper.py` - Local MCP compatibility layer (port 8002)
- `simple_memory_controller.py` - Simplified version of memory controller

### LM Studio Integration
- `lm_studio_test.py` - Test LM Studio integration
- `test_lm_studio_flow.py` - Test complete LM Studio flow

### Scripts
- `start_mcp_local.sh` - Local MCP server startup script

## Local Development Architecture

```
User Input → LM Studio (port 1234) → memory_controller.py → mcp_wrapper.py (port 8002) → memory_server.py (port 8001) → PostgreSQL + pgvector
```

## Usage

1. Start the memory server: `python ../memory_server.py`
2. Start the MCP wrapper: `python mcp_wrapper.py`
3. Start the memory controller: `python memory_controller.py`
4. Configure LM Studio on port 1234
5. Test with: `python lm_studio_test.py`

## Notes

These files are for local development only. Production deployment uses:
- `memory_server.py` (cloud deployment)
- `memory_mcp_direct.py` (direct MCP integration)
- `start_direct.sh` (service orchestration)
