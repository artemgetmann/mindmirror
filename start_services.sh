#!/bin/bash

# Use Render's assigned port or fallback to 8000 (MCP proxy - external)
RENDER_PORT=${PORT:-8000}
# Memory server runs internally on 8001
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}

# Start memory server and extract token using named pipe
echo "🚀 Starting Memory Server on port $MEMORY_PORT and extracting token..."

# Create named pipe for token communication
mkfifo /tmp/token_pipe

# Start memory server in background, tee output to pipe
python memory_server.py 2>&1 | tee /tmp/token_pipe &
MEMORY_PID=$!

# Extract token with timeout (non-blocking)
timeout 15 grep -m 1 "DEFAULT TOKEN CREATED:" /tmp/token_pipe | awk '{print $4}' > /tmp/extracted_token &
GREP_PID=$!

# Wait for token extraction or timeout
wait $GREP_PID
AUTH_TOKEN=$(cat /tmp/extracted_token 2>/dev/null)

# Cleanup pipes
rm -f /tmp/token_pipe /tmp/extracted_token

if [ -n "$AUTH_TOKEN" ]; then
    export AUTH_TOKEN
    echo "🔑 Token captured: $AUTH_TOKEN"
    echo "🔗 Claude Desktop URL: https://mcp-memory-uw0w.onrender.com/sse?token=$AUTH_TOKEN"
else
    echo "❌ Failed to capture token"
    exit 1
fi

# Start MCP server with proxy on Render's assigned port
echo "🚀 Starting MCP Server on port $RENDER_PORT..."
mcp-proxy --host 0.0.0.0 --port $RENDER_PORT python memory_mcp_server.py