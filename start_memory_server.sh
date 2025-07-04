#!/bin/bash
# Start the memory server (HTTP API backend on port 8003)
cd /Users/user/Programming_Projects/MCP_Memory
source venv/bin/activate
python -u memory_server.py >> memory_server_logs.txt 2>&1 &