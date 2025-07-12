#!/usr/bin/env python3
"""
Direct FastAPI + MCP SDK Memory Server

A Model Context Protocol server that provides URL token authentication
and multi-tenant memory management capabilities.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from starlette.applications import Starlette
from starlette.routing import Route, Mount

# MCP SDK imports
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.types import Tool, TextContent
import mcp.types as types

# Set up logging
log_dir = '/app/logs' if os.path.exists('/app') else './logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/mcp_direct.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
MEMORY_API_BASE = "http://localhost:8001"
DB_CONFIG = {
    'host': 'REDACTED_DB_HOST',
    'database': 'postgres',
    'user': 'REDACTED_DB_USER',
    'password': 'REDACTED_DB_PASSWORD',
    'port': 6543,
    'sslmode': 'require'
}

# Valid memory tags (must match memory_server.py)
VALID_TAGS = ["goal", "routine", "preference", "constraint", "habit", "project", "tool", "identity", "value"]

# Initialize MCP server
mcp = FastMCP("memory-system")
transport = SseServerTransport("/messages/")

# Global user context storage for current session
current_user_context = {}

async def validate_token(token: str) -> Optional[str]:
    """
    Validate token against PostgreSQL database and return user_id.
    Returns user_id if valid, None if invalid.
    """
    if not token:
        return None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check if token exists and is active
        cursor.execute("""
            SELECT user_id, user_name FROM auth_tokens 
            WHERE token = %s AND is_active = true
        """, (token,))
        
        result = cursor.fetchone()
        
        if result:
            user_id = result['user_id']
            # Update last_used timestamp
            cursor.execute("""
                UPDATE auth_tokens 
                SET last_used = CURRENT_TIMESTAMP 
                WHERE token = %s
            """, (token,))
            conn.commit()
            
            logger.info(f"Token validated successfully for user: {user_id}")
            cursor.close()
            conn.close()
            return user_id
        else:
            logger.warning(f"Invalid token provided: {token[:10]}...")
            cursor.close()
            conn.close()
            return None
            
    except Exception as e:
        logger.error(f"Database error during token validation: {e}")
        return None

def create_user_http_client(token: str) -> httpx.AsyncClient:
    """Create HTTP client with user's token for memory_server API calls"""
    headers = {"Authorization": f"Bearer {token}"}
    return httpx.AsyncClient(base_url=MEMORY_API_BASE, headers=headers)

async def check_token(request: Request) -> dict:
    """
    Extract and validate token from URL parameters.
    Returns dict with user_id and token, raises HTTPException if invalid.
    """
    token = request.query_params.get("token")
    if not token:
        logger.error("No token provided in URL parameters")
        raise HTTPException(status_code=401, detail="Token required in URL parameters")
    
    user_id = await validate_token(token)
    if not user_id:
        logger.error(f"Invalid token: {token[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {"user_id": user_id, "token": token}

# MCP Tool Definitions
@mcp.tool()
async def store_memory(text: str, tag: str) -> str:
    """
    Store a new memory with conflict detection
    
    Args:
        text: The memory text to store
        tag: Memory category (goal, routine, preference, constraint, habit, project, tool, identity, value)
    """
    try:
        # Get user context (token is automatically available from session)
        if "token" not in current_user_context:
            return "Error: User not authenticated. Please reconnect with a valid token."
        
        token = current_user_context["token"]
        user_id = current_user_context["user_id"]
        
        logger.info(f"Storing memory for user {user_id}: '{text[:50]}...' (tag: {tag})")
        
        # Validate tag
        if tag not in VALID_TAGS:
            return f"Error: Invalid tag '{tag}'. Must be one of: {', '.join(VALID_TAGS)}"
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            response = await client.post("/memories", json={
                "text": text,
                "tag": tag
            })
            
            if response.status_code != 200:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"Error storing memory: {response.status_code} - {response.text}"
            
            result = response.json()
            
            # Format response including any conflicts detected
            output = f"Memory stored successfully!\n\n"
            output += f"Text: {text}\n"
            output += f"Tag: {tag}\n"
            output += f"ID: {result.get('id', 'unknown')}\n"
            
            if result.get('conflicts_detected'):
                output += f"\n⚠️ CONFLICTS DETECTED:\n"
                for conflict in result.get('conflicts', []):
                    output += f"- {conflict.get('text', 'Unknown conflict')}\n"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in store_memory: {e}")
        return f"Error storing memory: {str(e)}"

@mcp.tool()
async def search_memory(query: str, limit: int = 10, tag_filter: str = None) -> str:
    """
    Search memories by query text with conflict detection
    
    Args:
        query: Search query text
        limit: Maximum number of results to return (default: 10)
        tag_filter: Optional tag to filter results
    """
    try:
        # Get user context
        if "token" not in current_user_context:
            return "Error: User not authenticated. Please reconnect with a valid token."
        
        token = current_user_context["token"]
        user_id = current_user_context["user_id"]
        
        logger.info(f"Search request from user {user_id}: query='{query}', limit={limit}, tag_filter={tag_filter}")
        
        # Validate tag_filter if provided
        if tag_filter and tag_filter not in VALID_TAGS:
            return f"Error: Invalid tag filter '{tag_filter}'. Must be one of: {', '.join(VALID_TAGS)}"
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            search_data = {
                "query": query,
                "limit": limit
            }
            if tag_filter:
                search_data["tag_filter"] = tag_filter
            
            response = await client.post("/memories/search", json=search_data)
            
            if response.status_code != 200:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"Search failed: Memory server returned {response.status_code} error"
            
            result = response.json()
            memories = result.get("results", [])
            conflict_groups = result.get("conflict_groups", [])
            
            if not memories:
                return f"No memories found matching '{query}'"
            
            # Format results
            output = f"Found {len(memories)} memories for '{query}':\n\n"
            
            for i, memory in enumerate(memories, 1):
                timestamp = memory.get('timestamp', '')[:10] if memory.get('timestamp') else 'unknown'
                output += f"{i}. {memory.get('text', 'No text')} (ID: {memory.get('id', 'unknown')}, Tag: {memory.get('tag', 'unknown')}, {timestamp})\n"
            
            # Add conflict information if present
            if conflict_groups:
                output += f"\n⚠️ CONFLICTS DETECTED ({len(conflict_groups)} groups):\n"
                for i, group in enumerate(conflict_groups, 1):
                    output += f"Conflict Group {i}:\n"
                    for memory in group:
                        timestamp = memory.get('timestamp', '')[:10] if memory.get('timestamp') else 'unknown'
                        output += f"  - {memory.get('text', 'No text')} (ID: {memory.get('id', 'unknown')}, {timestamp})\n"
                    output += "\n"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in search_memory: {e}")
        return f"Error searching memories: {str(e)}"

@mcp.tool()
async def delete_memory(memory_id: str) -> str:
    """
    Delete a specific memory by ID
    
    Args:
        memory_id: The ID of the memory to delete
    """
    try:
        # Get user context
        if "token" not in current_user_context:
            return "Error: User not authenticated. Please reconnect with a valid token."
        
        token = current_user_context["token"]
        user_id = current_user_context["user_id"]
        
        logger.info(f"Deleting memory {memory_id} for user {user_id}")
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            response = await client.delete(f"/memories/{memory_id}")
            
            if response.status_code == 200:
                return f"Memory {memory_id} deleted successfully"
            elif response.status_code == 404:
                return f"Memory {memory_id} not found or you don't have permission to delete it"
            else:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"Failed to delete memory {memory_id}: {response.text}"
                
    except Exception as e:
        logger.error(f"Error in delete_memory: {e}")
        return f"Error deleting memory: {str(e)}"

@mcp.tool()
async def list_memories(tag: str = None, limit: int = 10) -> str:
    """
    List all memories, optionally filtered by tag
    
    Args:
        tag: Optional tag filter (goal, routine, preference, constraint, habit, project, tool, identity, value)
        limit: Maximum number of memories to return (default: 10)
    """
    try:
        # Get user context
        if "token" not in current_user_context:
            return "Error: User not authenticated. Please reconnect with a valid token."
        
        token = current_user_context["token"]
        user_id = current_user_context["user_id"]
        
        logger.info(f"Listing memories for user {user_id}: tag={tag}, limit={limit}")
        
        # Validate tag if provided
        if tag and tag not in VALID_TAGS:
            return f"Error: Invalid tag '{tag}'. Must be one of: {', '.join(VALID_TAGS)}"
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            params = {"limit": limit}
            if tag:
                params["tag"] = tag
            
            response = await client.get("/memories", params=params)
            
            if response.status_code != 200:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"Failed to list memories: Memory server returned {response.status_code} error"
            
            result = response.json()
            memories = result.get("memories", [])
            
            if not memories:
                filter_text = f" with tag '{tag}'" if tag else ""
                return f"No memories found{filter_text}"
            
            # Format results
            filter_text = f" (filtered by tag: {tag})" if tag else ""
            output = f"Your Memories{filter_text} ({len(memories)} total):\n\n"
            
            for i, memory in enumerate(memories, 1):
                timestamp = memory.get('timestamp', '')[:10] if memory.get('timestamp') else 'unknown'
                output += f"{i}. {memory.get('text', 'No text')} (ID: {memory.get('id', 'unknown')}, Tag: {memory.get('tag', 'unknown')}, {timestamp})\n"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in list_memories: {e}")
        return f"Error listing memories: {str(e)}"

async def handle_sse(request: Request):
    """Handle SSE connection with token authentication"""
    # Validate token and get user context
    user_context = await check_token(request)
    user_id = user_context["user_id"]
    token = user_context["token"]
    
    logger.info(f"SSE connection established for user: {user_id}")
    
    # Store user context for this session
    current_user_context["user_id"] = user_id
    current_user_context["token"] = token
    
    async with transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (in_stream, out_stream):
        # Initialize MCP server with user context
        initialization_options = InitializationOptions(
            server_name="memory-system",
            server_version="1.0.0",
            capabilities=mcp._mcp_server.get_capabilities()
        )
        await mcp._mcp_server.run(
            in_stream, out_stream, initialization_options
        )

# Create main FastAPI app
app = FastAPI(title="Memory MCP Server", version="1.0.0")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "server": "memory-mcp-direct"}

# Create Starlette app with SSE and message handling
sse_app = Starlette(
    routes=[
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages/", app=transport.handle_post_message)
    ]
)

# Mount the SSE app at root but after health endpoint
app.mount("/", sse_app)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting Memory MCP Direct Server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)