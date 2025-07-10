#!/bin/bash

# Port configuration
RENDER_PORT=${PORT:-8000}  # Main port assigned by Render
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}  # Memory server internal port
MCP_PORT=9000  # MCP proxy internal port

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

# Start MCP proxy with memory_mcp_server on internal port
echo "🚀 Starting MCP Server on port $MCP_PORT..."
export INTERNAL_MCP_URL="http://localhost:$MCP_PORT/sse"
mcp-proxy --host 0.0.0.0 --port $MCP_PORT python memory_mcp_server.py >> /app/logs/mcp_proxy.log 2>&1 &
MCP_PID=$!

# Wait for MCP proxy to initialize
echo "⏳ Waiting for MCP proxy to initialize..."
sleep 5

# Check if MCP proxy is still running
if ! kill -0 $MCP_PID 2>/dev/null; then
    echo "❌ MCP proxy process died during startup"
    exit 1
fi

echo "✅ MCP proxy running successfully"

# Start SSE proxy on Render's main port
echo "🚀 Starting SSE Proxy on port $RENDER_PORT..."
python proxy_sse.py