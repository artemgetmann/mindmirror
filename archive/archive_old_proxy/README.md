# Archived Proxy Implementation

This directory contains the old proxy-based MCP implementation that was replaced by the direct FastAPI + MCP SDK approach.

## Archived Files:
- `proxy_sse.py` - SSE proxy that attempted to intercept tokens from URLs
- `memory_mcp_server.py` - MCP server using stdio transport with session management
- `start_services.sh` - Complex startup script for 3-service proxy chain

## Why Replaced:
The proxy approach had several issues:
1. Complex 3-service architecture (Memory Server → mcp-proxy → SSE proxy)
2. SSE handshake problems preventing tool discovery in Claude Desktop
3. Complex session management and token forwarding
4. Difficult to debug and maintain

## New Implementation:
The replacement `memory_mcp_direct.py` provides:
- Direct FastAPI + MCP SDK integration
- URL token authentication without proxy complexity
- Simplified 2-service architecture
- Better error handling and logging
- Easier debugging and maintenance

## Historical Context:
These files represent the evolution from working chat-based token auth to attempting URL-based token auth via proxying, which led to the final direct implementation solution.