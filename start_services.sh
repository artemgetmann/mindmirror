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
export MCP_TRACE=1

# First, verify mcp-proxy is installed and working
echo "🔍 Checking mcp-proxy installation..."
if ! command -v mcp-proxy &> /dev/null; then
    echo "❌ mcp-proxy not found in PATH"
    echo "Available commands:"
    ls -la /root/.local/bin/ | grep mcp || echo "No mcp commands found"
    exit 1
fi

echo "✅ mcp-proxy found at: $(which mcp-proxy)"
echo "📋 mcp-proxy version:"
mcp-proxy --help | head -5 || echo "Failed to get mcp-proxy help"

# Start mcp-proxy with detailed logging
echo "🚀 Starting mcp-proxy on port $MCP_PORT..."
echo "Command: mcp-proxy --sse-host 0.0.0.0 --sse-port $MCP_PORT -- python memory_mcp_server.py"

# Don't redirect to background immediately - capture startup output
mcp-proxy --sse-host 0.0.0.0 --sse-port $MCP_PORT -- python memory_mcp_server.py > /app/logs/mcp_proxy.log 2>&1 &
MCP_PID=$!

echo "📊 MCP proxy started with PID: $MCP_PID"

# Wait and check multiple times
for i in {1..10}; do
    echo "⏳ Waiting for MCP proxy to initialize... ($i/10)"
    sleep 1
    
    # Check if process is still running
    if ! kill -0 $MCP_PID 2>/dev/null; then
        echo "❌ MCP proxy process died during startup (attempt $i)"
        echo "📋 Last few lines of mcp-proxy log:"
        tail -20 /app/logs/mcp_proxy.log || echo "No log file found"
        exit 1
    fi
    
    # Check if port is bound
    if netstat -ln 2>/dev/null | grep ":$MCP_PORT " >/dev/null; then
        echo "✅ Port $MCP_PORT is bound!"
        break
    fi
    
    if [ $i -eq 10 ]; then
        echo "⚠️ Port $MCP_PORT not bound after 10 seconds"
        echo "📋 Current mcp-proxy log:"
        cat /app/logs/mcp_proxy.log || echo "No log file found"
        echo "📊 Port status:"
        netstat -ln | grep ":$MCP_PORT " || echo "Port $MCP_PORT not found in netstat"
    fi
done

echo "✅ MCP proxy initialization complete"

# Start SSE proxy on Render's main port
echo "🚀 Starting SSE Proxy on port $RENDER_PORT..."
python proxy_sse.py