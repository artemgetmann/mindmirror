#!/bin/bash

# Use Render's assigned port or fallback to 8000 (MCP proxy - external)
RENDER_PORT=${PORT:-8000}
# Memory server runs internally on 8001
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}

# Start memory server in background
echo "🚀 Starting Memory Server on port $MEMORY_PORT..."
python memory_server.py &
MEMORY_PID=$!

# Wait for memory server to initialize and create database
echo "⏳ Waiting for memory server to initialize..."
sleep 10

# Query token directly from database (most reliable method)
echo "🔍 Querying token from database..."
AUTH_TOKEN=$(python -c "
import sqlite3
try:
    conn = sqlite3.connect('auth_tokens.db')
    cursor = conn.cursor()
    cursor.execute('SELECT token FROM auth_tokens WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    print(result[0] if result else '')
except Exception as e:
    print('')
")

if [ -n "$AUTH_TOKEN" ]; then
    export AUTH_TOKEN
    echo "🔑 Token captured: $AUTH_TOKEN"
    echo "🔗 Claude Desktop URL: https://mcp-memory-uw0w.onrender.com/sse?token=$AUTH_TOKEN"
else
    echo "❌ Failed to capture token from database"
    exit 1
fi

# Start MCP server with proxy on Render's assigned port
echo "🚀 Starting MCP Server on port $RENDER_PORT..."
mcp-proxy --host 0.0.0.0 --port $RENDER_PORT python memory_mcp_server.py