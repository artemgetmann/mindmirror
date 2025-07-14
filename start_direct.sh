#!/bin/bash

# Simplified startup script for Direct MCP implementation
# Replaces the complex proxy chain with a simple 2-service setup

# Port configuration
RENDER_PORT=${PORT:-8000}  # Main port assigned by Render (Direct MCP Server)
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}  # Memory server internal port

# Create logs directory if it doesn't exist
mkdir -p /app/logs

echo "🚀 Starting Direct MCP Memory System"
echo "📋 Configuration:"
echo "   Memory Server: Port $MEMORY_PORT (internal)"
echo "   Direct MCP Server: Port $RENDER_PORT (external)"

# Start memory server in background
echo "🚀 Starting Memory Server on port $MEMORY_PORT..."
python memory_server.py > /app/logs/memory_server.log 2>&1 &
MEMORY_PID=$!

# Wait for memory server to initialize
echo "⏳ Waiting for memory server to initialize..."
sleep 8

# Check if memory server is still running
if ! kill -0 $MEMORY_PID 2>/dev/null; then
    echo "❌ Memory server process died during startup"
    echo "📋 Memory server logs:"
    cat /app/logs/memory_server.log
    exit 1
fi

# Quick health check for memory server
echo "🔍 Testing memory server health..."
for i in {1..5}; do
    if curl -s "http://localhost:$MEMORY_PORT/health" >/dev/null 2>&1; then
        echo "✅ Memory server health check passed"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "❌ Memory server health check failed after 5 attempts"
        echo "📋 Memory server logs:"
        tail -20 /app/logs/memory_server.log
        exit 1
    fi
    sleep 2
done

echo "✅ Memory server running successfully"

# Start Direct MCP Server on the main port (foreground)
echo "🚀 Starting Direct MCP Server on port $RENDER_PORT..."
echo "🔗 URL: https://your-app.onrender.com/sse?token=USER_TOKEN"
echo "📋 This provides URL token authentication without chat pasting!"

# Run in foreground so container doesn't exit
python memory_mcp_direct.py