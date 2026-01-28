#!/bin/bash

# Simplified startup script for Direct MCP implementation
# Replaces the complex proxy chain with a simple 2-service setup

# Port configuration
RENDER_PORT=${PORT:-8000}  # Main port assigned by Render (MCP+API proxy)
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}  # Memory server internal port

# Create logs directory if it doesn't exist
mkdir -p /app/logs

echo "🚀 Starting Direct MCP Memory System"
echo "📋 Configuration:"
echo "   MCP+API Proxy: Port $RENDER_PORT (external)"
echo "   Memory Server: Port $MEMORY_PORT (internal)"

# Start memory server in background
echo "🚀 Starting Memory Server on port $MEMORY_PORT..."
python memory_server.py > /app/logs/memory_server.log 2>&1 &
MEMORY_PID=$!

# Wait for memory server to initialize (ML model loading takes time)
echo "⏳ Waiting for memory server to initialize..."
sleep 15

# Check if memory server is still running
if ! kill -0 $MEMORY_PID 2>/dev/null; then
    echo "❌ Memory server process died during startup"
    echo "📋 Memory server logs:"
    cat /app/logs/memory_server.log
    exit 1
fi

# Health check for memory server (more attempts for ML model loading)
echo "🔍 Testing memory server health..."
for i in {1..15}; do
    if curl -s "http://localhost:$MEMORY_PORT/health" >/dev/null 2>&1; then
        echo "✅ Memory server health check passed"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Memory server health check failed after 15 attempts"
        echo "📋 Memory server logs:"
        tail -30 /app/logs/memory_server.log
        exit 1
    fi
    sleep 3
done

echo "✅ Memory server running successfully"

# Start MCP+API proxy on the main port (foreground)
echo "🚀 Starting MCP+API Proxy on port $RENDER_PORT..."
echo "🔗 Frontend API: https://memory.usemindmirror.com/api/generate-token"
echo "🔗 MCP URL: https://memory.usemindmirror.com/sse?token=USER_TOKEN"
echo "📋 This provides both frontend API and MCP endpoints!"

# Run in foreground so container doesn't exit
python memory_mcp_direct.py