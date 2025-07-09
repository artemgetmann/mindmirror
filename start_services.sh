#!/bin/bash

# Use Render's assigned port or fallback to 8000 (MCP proxy - external)
RENDER_PORT=${PORT:-8000}
# Memory server runs internally on 8001
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}

# Start memory server in background and capture logs
echo "🚀 Starting Memory Server on port $MEMORY_PORT..."
python memory_server.py > memory_server.log 2>&1 &
MEMORY_PID=$!

# Wait for memory server to start and generate token
sleep 10

# Extract token from memory server logs
AUTH_TOKEN=$(grep "🔑 DEFAULT TOKEN CREATED:" memory_server.log | awk '{print $4}')
if [ -z "$AUTH_TOKEN" ]; then
    echo "❌ Failed to extract auth token from memory server logs"
    cat memory_server.log
    exit 1
fi

echo "🔑 Using token: $AUTH_TOKEN"
# Export token for MCP server
export AUTH_TOKEN

# Start MCP server with proxy on Render's assigned port
echo "🚀 Starting MCP Server on port $RENDER_PORT..."
mcp-proxy --host 0.0.0.0 --port $RENDER_PORT python memory_mcp_server.py