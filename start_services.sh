#!/bin/bash

# Use hardcoded port 8000 for MCP (following MCP cloud tools pattern)
RENDER_PORT=8000
# Memory server runs internally on 8001
MEMORY_PORT=${MEMORY_SERVER_PORT:-8001}

# Start memory server in background
echo "🚀 Starting Memory Server on port $MEMORY_PORT..."
python memory_server.py &
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

# Extract token from memory server database
echo "🔍 Extracting authentication token from database..."
export AUTH_TOKEN=$(python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='REDACTED_DB_HOST',
        database='postgres',
        user='REDACTED_DB_USER',
        password='REDACTED_DB_PASSWORD',
        port=6543,
        sslmode='require'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT token FROM auth_tokens WHERE is_active = true ORDER BY created_at DESC LIMIT 1')
    result = cursor.fetchone()
    if result:
        print(result[0])
    else:
        print('no_token_found')
    conn.close()
except Exception as e:
    print(f'error: {e}')
")

if [ "$AUTH_TOKEN" = "no_token_found" ] || [ "$AUTH_TOKEN" = "error:"* ]; then
    echo "❌ Failed to extract token: $AUTH_TOKEN"
    exit 1
fi

echo "✅ Token extracted successfully"
echo "🔑 AUTH_TOKEN: $AUTH_TOKEN"

# Start MCP server with proxy on Render's assigned port
echo "🚀 Starting MCP Server on port $RENDER_PORT..."
mcp-proxy --host 0.0.0.0 --port $RENDER_PORT python memory_mcp_server.py