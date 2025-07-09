#!/bin/bash

# Use Render's assigned port or fallback to 8000 (MCP proxy - external)
RENDER_PORT=${PORT:-8000}
# Memory server runs internally on 8001
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}

# Start memory server and extract token using process substitution
echo "🚀 Starting Memory Server on port $MEMORY_PORT and extracting token..."

# Use process substitution to capture token directly from stdout
AUTH_TOKEN=$(python memory_server.py 2>&1 | grep "DEFAULT TOKEN CREATED:" | awk '{print $4}')

if [ -n "$AUTH_TOKEN" ]; then
    echo "🔑 Token captured: $AUTH_TOKEN"
    export AUTH_TOKEN
else
    echo "❌ Failed to capture token from memory server"
    
    # Fallback: Try named pipe approach
    echo "🔄 Trying fallback method with named pipe..."
    mkfifo /tmp/token_pipe
    python memory_server.py > /tmp/token_pipe 2>&1 &
    MEMORY_PID=$!
    
    # Extract token from pipe
    AUTH_TOKEN=$(grep "DEFAULT TOKEN CREATED:" /tmp/token_pipe | awk '{print $4}')
    rm /tmp/token_pipe
    
    if [ -n "$AUTH_TOKEN" ]; then
        echo "🔑 Token captured via fallback: $AUTH_TOKEN"
        export AUTH_TOKEN
    else
        echo "❌ Failed to capture token with both methods"
        exit 1
    fi
fi

# Start MCP server with proxy on Render's assigned port
echo "🚀 Starting MCP Server on port $RENDER_PORT..."
mcp-proxy --host 0.0.0.0 --port $RENDER_PORT python memory_mcp_server.py