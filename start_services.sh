#!/bin/bash

# Start memory server in background
echo "🚀 Starting Memory Server on port $MEMORY_SERVER_PORT..."
python memory_server.py &

# Wait for memory server to start
sleep 5

# Start MCP server with proxy
echo "🚀 Starting MCP Server on port $PORT..."
mcp-proxy --host 0.0.0.0 --port $PORT python memory_mcp_server.py