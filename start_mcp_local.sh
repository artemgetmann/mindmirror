#!/bin/bash

# Read the current auth token from file
if [ -f "/tmp/auth_token.txt" ]; then
    export AUTH_TOKEN=$(cat /tmp/auth_token.txt)
    echo "🔑 Using token: $AUTH_TOKEN"
else
    echo "❌ No auth token found. Make sure memory server is running."
    exit 1
fi

# Start the MCP server with the token using virtual environment
cd /Users/user/Programming_Projects/MCP_Memory
/Users/user/Programming_Projects/MCP_Memory/venv/bin/python memory_mcp_server.py