#!/bin/bash

# Use Render's assigned port or fallback to 8000
RENDER_PORT=${PORT:-8000}
MEMORY_PORT=${MEMORY_SERVER_PORT:-8003}

# Start memory server in background
echo "🚀 Starting Memory Server on port $MEMORY_PORT..."
python memory_server.py &

# Wait for memory server to start
sleep 10

# Start MCP server with proxy on Render's assigned port
echo "🚀 Starting MCP Server on port $RENDER_PORT..."
mcp-proxy --host 0.0.0.0 --port $RENDER_PORT python memory_mcp_server.py