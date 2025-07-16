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
from fastapi.middleware.cors import CORSMiddleware
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

def get_relevance_level(similarity: float) -> str:
    """Convert similarity score to user-friendly relevance level"""
    if similarity >= 0.8:
        return "high"
    elif similarity >= 0.5:
        return "medium"
    else:
        return "low"

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
async def remember(text: str, category: str) -> str:
    """
    Store information for future reference
    
    Args:
        text: The information to remember
        category: Information type (goal, routine, preference, constraint, habit, project, tool, identity, value)
    """
    try:
        # Get user context (token is automatically available from session)
        if "token" not in current_user_context:
            return "I need to authenticate first. Please reconnect with a valid token."
        
        token = current_user_context["token"]
        user_id = current_user_context["user_id"]
        
        logger.info(f"Storing memory for user {user_id}: '{text[:50]}...' (tag: {category})")
        
        # Validate category
        if category not in VALID_TAGS:
            return f"I don't recognize the category '{category}'. Please use one of: {', '.join(VALID_TAGS)}"
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            response = await client.post("/memories", json={
                "text": text,
                "tag": category
            })
            
            if response.status_code != 200:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"I couldn't remember that: {response.text}"
            
            result = response.json()
            
            # Check for memory limit error
            if result.get('error'):
                logger.info(f"Memory limit reached for user {user_id}: {result}")
                error_msg = f"❌ {result.get('error')}\n\n"
                
                if result.get('premium_link'):
                    error_msg += f"Sign up for premium at: {result.get('premium_link')}\n\n"
                
                if result.get('memories_used') and result.get('memory_limit'):
                    error_msg += f"You've used {result.get('memories_used')}/{result.get('memory_limit')} memories.\n\n"
                
                error_msg += f"This would have been: {text}"
                return error_msg
            
            # Format response including any conflicts detected
            output = f"I'll remember that!\n\n"
            output += f"Information: {text}\n"
            output += f"Category: {category}\n"
            output += f"Memory ID: {result.get('id', 'unknown')}\n"
            
            if result.get('conflicts_detected'):
                output += f"\n⚠️ I noticed this conflicts with something I already know:\n"
                for conflict in result.get('conflicts', []):
                    output += f"- {conflict.get('text', 'Unknown conflict')}\n"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in remember: {e}")
        return f"I couldn't remember that: {str(e)}"

@mcp.tool()
async def recall(query: str, limit: int = 10, category_filter: str = None) -> str:
    """
    Find previously stored information
    
    Args:
        query: What you're looking for
        limit: Maximum number of results to return (default: 10)
        category_filter: Optional category to filter results
    """
    try:
        # Get user context
        if "token" not in current_user_context:
            return "I need to authenticate first. Please reconnect with a valid token."
        
        token = current_user_context["token"]
        user_id = current_user_context["user_id"]
        
        logger.info(f"Search request from user {user_id}: query='{query}', limit={limit}, category_filter={category_filter}")
        
        # Validate category_filter if provided
        if category_filter and category_filter not in VALID_TAGS:
            return f"I don't recognize the category '{category_filter}'. Please use one of: {', '.join(VALID_TAGS)}"
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            search_data = {
                "query": query,
                "limit": limit
            }
            if category_filter:
                search_data["tag_filter"] = category_filter
            
            response = await client.post("/memories/search", json=search_data)
            
            if response.status_code != 200:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"I couldn't search for that: {response.text}"
            
            result = response.json()
            memories = result.get("results", [])
            conflict_groups = result.get("conflict_groups", [])
            
            if not memories:
                return f"I don't recall anything about '{query}'"
            
            # Format results
            output = f"I remember {len(memories)} things about '{query}':\n\n"
            
            for i, memory in enumerate(memories, 1):
                created = memory.get('timestamp', '')[:10] if memory.get('timestamp') else 'unknown'
                last_accessed = memory.get('last_accessed', '')[:10] if memory.get('last_accessed') else 'unknown'
                similarity = memory.get('similarity', 0.0)
                relevance = get_relevance_level(similarity)
                output += f"{i}. {memory.get('text', 'No text')} (ID: {memory.get('id', 'unknown')}, Tag: {memory.get('tag', 'unknown')}, Relevance: {relevance}, Created: {created}, Last accessed: {last_accessed})\n"
            
            # Add conflict information if present
            if conflict_groups:
                output += f"\n⚠️ I remember some conflicting information ({len(conflict_groups)} groups):\n"
                for i, group in enumerate(conflict_groups, 1):
                    output += f"Conflict Group {i}:\n"
                    for memory in group:
                        created = memory.get('timestamp', '')[:10] if memory.get('timestamp') else 'unknown'
                        last_accessed = memory.get('last_accessed', '')[:10] if memory.get('last_accessed') else 'unknown'
                        similarity = memory.get('similarity', 0.0)
                        relevance = get_relevance_level(similarity)
                        output += f"  - {memory.get('text', 'No text')} (ID: {memory.get('id', 'unknown')}, Relevance: {relevance}, Created: {created}, Last accessed: {last_accessed})\n"
                    output += "\n"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in recall: {e}")
        return f"I couldn't recall that: {str(e)}"

@mcp.tool()
async def forget(information_id: str) -> str:
    """
    Remove specific information from memory
    
    Args:
        information_id: The ID of the information to forget
    """
    try:
        # Get user context
        if "token" not in current_user_context:
            return "I need to authenticate first. Please reconnect with a valid token."
        
        token = current_user_context["token"]
        user_id = current_user_context["user_id"]
        
        logger.info(f"Forgetting information {information_id} for user {user_id}")
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            response = await client.delete(f"/memories/{information_id}")
            
            if response.status_code == 200:
                return f"I've forgotten that information"
            elif response.status_code == 404:
                return f"I don't have that information or you don't have permission to remove it"
            else:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"I couldn't forget that: {response.text}"
                
    except Exception as e:
        logger.error(f"Error in forget: {e}")
        return f"I couldn't forget that: {str(e)}"

@mcp.tool()
async def what_do_you_know(category: str = None, limit: int = 1000) -> str:
    """
    Show what information you have stored
    
    Args:
        category: Optional category filter (goal, routine, preference, constraint, habit, project, tool, identity, value)
        limit: Maximum number of items to return (default: 1000)
    """
    try:
        # Get user context
        if "token" not in current_user_context:
            return "I need to authenticate first. Please reconnect with a valid token."
        
        token = current_user_context["token"]
        user_id = current_user_context["user_id"]
        
        logger.info(f"Listing memories for user {user_id}: category={category}, limit={limit}")
        
        # Validate category if provided
        if category and category not in VALID_TAGS:
            return f"I don't recognize the category '{category}'. Please use one of: {', '.join(VALID_TAGS)}"
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            params = {"limit": limit}
            if category:
                params["tag"] = category
            
            response = await client.get("/memories", params=params)
            
            if response.status_code != 200:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"I couldn't access what I know: {response.text}"
            
            result = response.json()
            memories = result.get("memories", [])
            
            if not memories:
                filter_text = f" in category '{category}'" if category else ""
                return f"I don't know anything{filter_text}"
            
            # Format results
            filter_text = f" (category: {category})" if category else ""
            output = f"Here's what I know{filter_text} ({len(memories)} total):\n\n"
            
            for i, memory in enumerate(memories, 1):
                created = memory.get('timestamp', '')[:10] if memory.get('timestamp') else 'unknown'
                last_accessed = memory.get('last_accessed', '')[:10] if memory.get('last_accessed') else 'unknown'
                output += f"{i}. {memory.get('text', 'No text')} (ID: {memory.get('id', 'unknown')}, Tag: {memory.get('tag', 'unknown')}, Created: {created}, Last accessed: {last_accessed})\n"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in what_do_you_know: {e}")
        return f"I couldn't access what I know: {str(e)}"

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
        # Use the correct MCP SDK pattern from documentation
        await mcp._mcp_server.run(
            in_stream, 
            out_stream, 
            mcp._mcp_server.create_initialization_options()
        )

# Create main FastAPI app
app = FastAPI(title="Memory MCP Server", version="1.0.0")

# Configure CORS for frontend access
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:5174",  # Alternative dev port
    "http://localhost:8081",  # Frontend dev server
    "https://usemindmirror.com",  # Production domain
    "https://www.usemindmirror.com",  # Production with www
    "https://memory.usemindmirror.com",  # Memory subdomain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "server": "memory-mcp-direct"}

# API Proxy Routes - Forward to internal memory server
@app.post("/api/generate-token")
async def proxy_generate_token(request: Request):
    """Proxy token generation to internal memory server"""
    import httpx
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MEMORY_API_BASE}/api/generate-token",
            content=body,
            headers={"content-type": "application/json"}
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

@app.post("/api/join-waitlist")
async def proxy_join_waitlist(request: Request):
    """Proxy waitlist signup to internal memory server"""
    import httpx
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MEMORY_API_BASE}/api/join-waitlist",
            content=body,
            headers={"content-type": "application/json"}
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

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