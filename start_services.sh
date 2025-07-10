#!/bin/bash

# Use hardcoded port 8000 for MCP (following MCP cloud tools pattern)
RENDER_PORT=8000
# Memory server runs internally on 8001
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Start memory server in background with logging
echo "🚀 Starting Memory Server on port $MEMORY_PORT..."
python memory_server.py >> /app/logs/memory_server.log 2>&1 &
MEMORY_PID=$!

# Wait for memory server to initialize
echo "⏳ Waiting for memory server to initialize..."
sleep 10

# Check if memory server is still running
if ! kill -0 $MEMORY_PID 2>/dev/null; then
    echo "❌ Memory server process died during startup"
    exit 1
fi

echo "✅ Memory server running successfully"

# Start MCP server with proxy on Render's assigned port
echo "🚀 Starting MCP Server on port $RENDER_PORT..."
mcp-proxy --host 0.0.0.0 --port $RENDER_PORT python memory_mcp_server.py