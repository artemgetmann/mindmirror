#!/bin/bash

# Use Render's assigned port or fallback to 8000 (MCP proxy - external)
RENDER_PORT=${PORT:-8000}
# Memory server runs internally on 8001
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}

# Start memory server in background
echo "🚀 Starting Memory Server on port $MEMORY_PORT..."
python memory_server.py &
MEMORY_PID=$!

# Wait for memory server to start and create token file
sleep 10

# Read token from file
if [ -f "/tmp/auth_token.txt" ]; then
    AUTH_TOKEN=$(cat /tmp/auth_token.txt)
    echo "🔑 Using token: $AUTH_TOKEN"
    # Export token for MCP server
    export AUTH_TOKEN
else
    echo "❌ Failed to find auth token file"
    exit 1
fi

# Start MCP server with proxy on Render's assigned port
echo "🚀 Starting MCP Server on port $RENDER_PORT..."
mcp-proxy --host 0.0.0.0 --port $RENDER_PORT python memory_mcp_server.py