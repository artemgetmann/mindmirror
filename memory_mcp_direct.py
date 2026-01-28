#!/usr/bin/env python3
"""
Direct FastAPI + MCP SDK Memory Server

A Model Context Protocol server that provides URL token authentication
and multi-tenant memory management capabilities.
"""

import asyncio
import contextvars
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
from mcp.server.transport_security import TransportSecuritySettings
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

# Initialize MCP server with minimal global policy
mcp = FastMCP(
    name="mindmirror",
    stateless_http=True,  # Enable stateless mode for serverless/Streamable HTTP
    streamable_http_path="/",  # Mount at root so we control the path when mounting
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "localhost",
            "localhost:8000",
            "localhost:8001",
            "localhost:8002",
            "127.0.0.1",
            "127.0.0.1:8000",
            "127.0.0.1:8001",
            "127.0.0.1:8002",
            "mcp-memory-uw0w.onrender.com",
            "memory.usemindmirror.com",
        ],
    ),
    instructions="""
GLOBAL POLICY (embedded, minimal)

Identity:
You are an AI assistant with persistent memory. Tools available: recall, remember, what_do_you_know, forget, checkpoint, resume. Do not invent or call undefined tools.

Guardrails:
• Before any personal advice or recommendations: call recall().
• If recall() returns conflicts: present the conflict information to user and ask which preference to follow. Only call forget() if user explicitly requests deletion.
• Storing:
  - If user explicitly states a preference ("I prefer X"), store it immediately.
  - For non‑explicit info, ask permission before remember(). Never store AI‑suggested ideas as user preferences.
• Transparency: when giving advice, state which stored preference you used; when asked about stored information, call what_do_you_know() and present the response.
• Context handoff: use checkpoint() when user wants to continue conversation elsewhere ("save this for later", switching to another AI); use resume() when user references previous work without context ("continue our discussion", "where did we leave off").
"""
)
transport = SseServerTransport("/messages/")

# Thread-safe per-request context (replaces global dict for concurrent user safety)
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('user_id', default='')
user_token_var: contextvars.ContextVar[str] = contextvars.ContextVar('token', default='')

def get_relevance_level(similarity: float) -> str:
    """Convert similarity score to user-friendly relevance level"""
    if similarity is None:
        return "unknown"
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
    return httpx.AsyncClient(base_url=MEMORY_API_BASE, headers=headers, timeout=30.0)

async def check_token(request: Request) -> dict:
    """
    Extract and validate token from Authorization header or URL parameters.
    Returns dict with user_id and token, raises HTTPException if invalid.
    """
    token = None
    
    # Check Authorization header first (new MCP spec requirement)
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        logger.info(f"Token provided via Authorization header: {token[:10]}...")
    
    # Fallback to URL parameter for backward compatibility
    elif "token" in request.query_params:
        token = request.query_params.get("token")
        logger.info(f"Token provided via URL parameter: {token[:10]}...")
    
    if not token:
        logger.error("No token provided in Authorization header or URL parameters")
        raise HTTPException(status_code=401, detail="Token required in Authorization header or URL parameters")
    
    user_id = await validate_token(token)
    if not user_id:
        logger.error(f"Invalid token: {token[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Set thread-safe context vars for this request
    user_id_var.set(user_id)
    user_token_var.set(token)

    return {"user_id": user_id, "token": token}

# MCP Tool Definitions
@mcp.tool()
async def remember(text: str, category: str) -> str:
    """
    Store user preferences, facts, and context.
    
    CRITICAL CAPTURE RULES:
    • When user says "I prefer X" → remember("User prefers X", category="preference")
    • When user says "Actually, I prefer Y" → remember("User prefers Y", category="preference")  
    • If user contradicts previous preference → store the new preference

    MEMORY CATEGORIES: goal, routine, preference, constraint, habit, project, tool, identity, value

    PROACTIVE MEMORY SUGGESTIONS (ask permission first):
    • Unique workflow/process → "Would you like me to remember this workflow for future reference?"
    • Repeated behaviors → "I notice you mention this approach often - should I store this for you?"
    • Problem-solving methods → "This seems like a useful technique - want me to remember it?"
    • Domain knowledge → "Should I remember this approach for next time?"

    PROACTIVE STORAGE MAPPING (with user permission):
    • Unique workflows/processes → 'routine' or 'tool'
    • Repeated behaviors → 'habit'  
    • Problem-solving methods → 'tool'
    • Personal approaches → 'routine'
    • Domain knowledge → 'tool' or 'project'

    IMPORTANT: Always ASK before storing non-explicit information. Don't store AI-generated suggestions as user preferences.
    
    Args:
        text: The information to remember
        category: Information type (goal, routine, preference, constraint, habit, project, tool, identity, value)
    """
    try:
        # Get user context from thread-safe context vars
        token = user_token_var.get()
        user_id = user_id_var.get()
        if not token:
            return "Authentication required. Please reconnect with a valid token."

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
    Search stored information. ALWAYS call this BEFORE giving personal advice or recommendations.
    
    WHEN TO USE PROACTIVELY (without user asking):
    • Questions starting with "How should I..." or "What's the best way to..."
    • Questions about "my preferences", "my habits", "my routines", "my goals"  
    • Questions that assume previous knowledge or context
    • Questions using "I" or "my" that might reference stored information
    • Before giving advice or recommendations about personal topics
    • When user asks about something they might have mentioned before

    CRITICAL: Use the most recent preference if no conflicts. If conflicts exist, present them 
    to user and ask which preference to follow.
    
    Args:
        query: What you're looking for
        limit: Maximum number of results to return (default: 10)
        category_filter: Optional category to filter results
    """
    try:
        # Get user context from thread-safe context vars
        token = user_token_var.get()
        user_id = user_id_var.get()
        if not token:
            return "Authentication required. Please reconnect with a valid token."

        # Convert empty string to None for optional parameters
        if category_filter == "":
            category_filter = None
            
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
            
            logger.info(f"Making request to {MEMORY_API_BASE}/memories/search with data: {search_data}")
            response = await client.post("/memories/search", json=search_data)
            logger.info(f"Response status: {response.status_code}")
            
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
                similarity = memory.get('similarity', 0.0) or 0.0
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
                        similarity = memory.get('similarity', 0.0) or 0.0
                        relevance = get_relevance_level(similarity)
                        output += f"  - {memory.get('text', 'No text')} (ID: {memory.get('id', 'unknown')}, Relevance: {relevance}, Created: {created}, Last accessed: {last_accessed})\n"
                    output += "\n"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in recall: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return f"I couldn't recall that: {str(e)}"

@mcp.tool()
async def forget(information_id: str) -> str:
    """
    Remove specific memories by ID.
    
    CONFLICT RESOLUTION:
    Use this after identifying conflicts via recall() and after user explicitly asks to delete 
    specific memories. Always show what you're forgetting before deletion.
    
    USAGE:
    • Only call when user explicitly requests deletion
    • Never auto-delete conflicting memories without user consent
    • Always confirm what will be deleted before proceeding
    
    Args:
        information_id: The ID of the information to forget
    """
    try:
        # Get user context from thread-safe context vars
        token = user_token_var.get()
        user_id = user_id_var.get()
        if not token:
            return "Authentication required. Please reconnect with a valid token."

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
    Browse all stored memories to understand the full scope of stored information.
    
    USAGE:
    • Use when user asks what you know about them
    • Use before making comprehensive recommendations to understand context
    • Helps provide personalized advice based on complete memory picture
    • Present the formatted response from server (includes timestamps/relevance)
    
    Args:
        category: Optional category filter (goal, routine, preference, constraint, habit, project, tool, identity, value)
        limit: Maximum number of items to return (default: 1000)
    """
    try:
        # Get user context from thread-safe context vars
        token = user_token_var.get()
        user_id = user_id_var.get()
        if not token:
            return "Authentication required. Please reconnect with a valid token."

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

@mcp.tool()
async def checkpoint(text: str, title: str = None) -> str:
    """
    Save current conversation context for later continuation.
    
    SUMMARY INSTRUCTIONS: Create a detailed summary that allows another AI 
    (or a new chat) with ZERO prior context to understand exactly what was 
    discussed, what was accomplished, and what remains to be done.
    
    USE THIS WHEN THE USER:
    - Wants to continue this conversation in a new chat
    - Is switching to another AI model/platform  
    - Asks to "save where we left off" or similar
    - Needs to pause and resume this discussion later
    
    CRITICAL: This overwrites existing checkpoints. When you see "⚠️" and overwrite 
    warning in the response, you MUST immediately tell the user: "I overwrote your 
    previous checkpoint from [DATE]. Let me know if this wasn't what you intended." 
    DO NOT proceed without informing the user about the overwrite.
    
    Args:
        text: The conversation summary/context to save
        title: Optional title for the checkpoint
    """
    try:
        # Get user context from thread-safe context vars
        token = user_token_var.get()
        user_id = user_id_var.get()
        if not token:
            return "Authentication required. Please reconnect with a valid token."

        logger.info(f"Storing checkpoint for user {user_id}: '{text[:50]}...'")
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            response = await client.post("/checkpoint", json={
                "content": text,
                "title": title
            })
            
            if response.status_code != 200:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"I couldn't save the checkpoint: {response.text}"
            
            result = response.json()
            
            # Handle overwrite warning FIRST - make it the primary message
            if result.get('overwrote', False):
                prev_time = result.get('previous_checkpoint_time', '')
                if prev_time:
                    # Format datetime for user display
                    try:
                        from datetime import datetime
                        prev_date = datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
                        formatted_date = prev_date.strftime('%B %d, %Y at %I:%M %p')
                        output = f"⚠️ IMPORTANT: I overwrote your previous checkpoint from {formatted_date}. Was this what you intended?\n\n"
                    except:
                        output = f"⚠️ IMPORTANT: I overwrote your previous checkpoint. Let me know if this wasn't what you intended.\n\n"
                else:
                    output = f"⚠️ IMPORTANT: I overwrote your previous checkpoint. Let me know if this wasn't what you intended.\n\n"
            else:
                output = ""
            
            # Then add success details
            output += f"✅ Checkpoint saved successfully!\n\n"
            output += f"Content: {text[:100]}{'...' if len(text) > 100 else ''}\n"
            if title:
                output += f"Title: {title}\n"
            output += f"Checkpoint ID: {result.get('id', 'unknown')}"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in checkpoint: {e}")
        return f"I couldn't save the checkpoint: {str(e)}"

@mcp.tool()
async def resume() -> str:
    """
    Retrieve the most recent conversation checkpoint to continue where you left off.
    
    USE THIS WHEN:
    - User explicitly asks to "continue from before" or "resume our discussion"
    - User references previous work WITHOUT context ("how's that feature coming along?")
    - User seems confused about lost context ("wait, what were we working on?")
    - User mentions "last time" or "earlier" without providing details
    
    DO NOT use automatically at conversation start. Only check for checkpoints
    when there's a clear signal the user wants to continue something.
    
    Returns the saved context with metadata, or indicates no checkpoint exists.
    """
    try:
        # Get user context from thread-safe context vars
        token = user_token_var.get()
        user_id = user_id_var.get()
        if not token:
            return "Authentication required. Please reconnect with a valid token."

        logger.info(f"Retrieving checkpoint for user {user_id}")
        
        # Create HTTP client with user's token
        async with create_user_http_client(token) as client:
            response = await client.post("/resume")
            
            if response.status_code != 200:
                logger.error(f"Memory server error: {response.status_code} - {response.text}")
                return f"I couldn't retrieve the checkpoint: {response.text}"
            
            result = response.json()
            
            if not result.get('exists', False):
                return "I don't have any saved checkpoint to resume from."
            
            # Format response with checkpoint content
            output = f"📋 Found your saved checkpoint:\n\n"
            
            if result.get('title'):
                output += f"**{result['title']}**\n\n"
            
            output += f"{result.get('content', 'No content available')}\n\n"
            
            # Add metadata
            created_at = result.get('created_at', '')
            if created_at:
                try:
                    from datetime import datetime
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = created_date.strftime('%B %d, %Y at %I:%M %p')
                    output += f"*Saved on {formatted_date}*\n"
                except:
                    output += f"*Saved: {created_at[:16]}*\n"
            
            output += f"*Checkpoint ID: {result.get('id', 'unknown')}*"
            
            return output
            
    except Exception as e:
        logger.error(f"Error in resume: {e}")
        return f"I couldn't retrieve the checkpoint: {str(e)}"

async def handle_sse_options(request: Request):
    """Handle OPTIONS preflight for SSE endpoint"""
    origin = request.headers.get("origin", "")
    
    # Define allowed origins for MCP clients
    allowed_origins = [
        "https://claude.ai",
        "http://localhost:5173",
        "http://localhost:8081",
        "https://usemindmirror.com",
        "https://www.usemindmirror.com",
        "https://memory.usemindmirror.com"
    ]
    
    headers = {
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, MCP-Protocol-Version, mcp-session-id",
        "Access-Control-Expose-Headers": "MCP-Protocol-Version, mcp-session-id",
        "MCP-Protocol-Version": "2025-06-18"
    }
    
    if origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
    
    return Response(
        status_code=204,
        headers=headers
    )

async def handle_sse(request: Request):
    """Handle SSE connection with token authentication"""
    # Handle OPTIONS preflight
    if request.method == "OPTIONS":
        return await handle_sse_options(request)
    
    # Validate token and get user context
    user_context = await check_token(request)
    user_id = user_context["user_id"]
    token = user_context["token"]
    
    logger.info(f"SSE connection established for user: {user_id}")

    # Context vars already set by check_token(), no additional action needed
    
    # Set response headers with MCP protocol version
    response_headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "MCP-Protocol-Version": "2025-06-18"
    }
    
    # Set CORS headers
    origin = request.headers.get("origin", "")
    allowed_origins = [
        "https://claude.ai",
        "http://localhost:5173",
        "http://localhost:8081",
        "https://usemindmirror.com",
        "https://www.usemindmirror.com",
        "https://memory.usemindmirror.com"
    ]
    
    if origin in allowed_origins:
        response_headers["Access-Control-Allow-Origin"] = origin
        response_headers["Access-Control-Allow-Credentials"] = "true"
    
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

# Lifespan handler for MCP session manager (required for Streamable HTTP)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP session manager on startup"""
    async with mcp.session_manager.run():
        logger.info("MCP session manager started")
        yield
    logger.info("MCP session manager stopped")

# Create main FastAPI app with lifespan
# redirect_slashes=False prevents 307 redirect from /mcp to /mcp/ which breaks MCP clients
app = FastAPI(title="Memory MCP Server", version="2.0.0", lifespan=lifespan, redirect_slashes=False)

# Configure CORS for frontend access
origins = [
    "https://claude.ai",  # Claude web app - NEW MCP CLIENT
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
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "MCP-Protocol-Version", "mcp-session-id"],
    expose_headers=["MCP-Protocol-Version", "mcp-session-id"]
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

class MCPProtocolMiddleware:
    """Middleware to add MCP protocol headers to responses"""
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Handle OPTIONS preflight for any endpoint
            if scope["method"] == "OPTIONS":
                origin = ""
                for header_name, header_value in scope.get("headers", []):
                    if header_name == b"origin":
                        origin = header_value.decode()
                        break
                
                allowed_origins = [
                    "https://claude.ai",
                    "http://localhost:5173",
                    "http://localhost:8081", 
                    "https://usemindmirror.com",
                    "https://www.usemindmirror.com",
                    "https://memory.usemindmirror.com"
                ]
                
                headers = [
                    (b"access-control-allow-methods", b"GET, POST, DELETE, OPTIONS"),
                    (b"access-control-allow-headers", b"Content-Type, Authorization, MCP-Protocol-Version, mcp-session-id"),
                    (b"access-control-expose-headers", b"MCP-Protocol-Version, mcp-session-id"),
                    (b"mcp-protocol-version", b"2025-06-18")
                ]
                
                if origin in allowed_origins:
                    headers.append((b"access-control-allow-origin", origin.encode()))
                
                await send({
                    "type": "http.response.start",
                    "status": 204,
                    "headers": headers
                })
                await send({"type": "http.response.body", "body": b""})
                return
        
        # Wrap the send function to add headers to responses
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                # Add MCP protocol version header
                headers = list(message.get("headers", []))
                headers.append((b"mcp-protocol-version", b"2025-06-18"))
                
                # Add CORS headers
                origin = ""
                for header_name, header_value in scope.get("headers", []):
                    if header_name == b"origin":
                        origin = header_value.decode()
                        break
                
                allowed_origins = [
                    "https://claude.ai",
                    "http://localhost:5173",
                    "http://localhost:8081",
                    "https://usemindmirror.com", 
                    "https://www.usemindmirror.com",
                    "https://memory.usemindmirror.com"
                ]
                
                if origin in allowed_origins:
                    headers.append((b"access-control-allow-origin", origin.encode()))
                    headers.append((b"access-control-allow-credentials", b"true"))
                
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_with_headers)


class TokenAuthMiddleware:
    """Extract token from query param or header and set context vars for Streamable HTTP"""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract token from query string
            query_string = scope.get("query_string", b"").decode()
            params = dict(p.split("=", 1) for p in query_string.split("&") if "=" in p)
            token = params.get("token")

            # Or from Authorization header
            if not token:
                for name, value in scope.get("headers", []):
                    if name == b"authorization":
                        auth = value.decode()
                        if auth.startswith("Bearer "):
                            token = auth[7:]
                        break

            if token:
                user_id = await validate_token(token)
                if user_id:
                    user_id_var.set(user_id)
                    user_token_var.set(token)
                    logger.info(f"TokenAuthMiddleware: authenticated user {user_id}")

        await self.app(scope, receive, send)


# Create Streamable HTTP app (path configured via streamable_http_path in constructor)
streamable_app = mcp.streamable_http_app()
streamable_with_auth = TokenAuthMiddleware(streamable_app)

# Create SSE app (legacy, backward compatible) - custom routes for our auth
sse_app = Starlette(
    routes=[
        Route("/", handle_sse, methods=["GET", "OPTIONS"]),  # Will be at /sse
        Mount("/messages/", app=MCPProtocolMiddleware(transport.handle_post_message))
    ]
)

# Handle /mcp without trailing slash - redirect to /mcp/ preserving query params
from starlette.responses import RedirectResponse

@app.api_route("/mcp", methods=["GET", "POST", "DELETE", "OPTIONS"])
async def mcp_redirect(request: Request):
    """Redirect /mcp to /mcp/ preserving query params"""
    query_string = request.url.query
    redirect_url = "/mcp/" + ("?" + query_string if query_string else "")
    return RedirectResponse(url=redirect_url, status_code=307)

# Mount both transports at their respective paths
app.mount("/mcp", streamable_with_auth)  # Streamable HTTP at /mcp/
app.mount("/sse", sse_app)  # SSE at /sse and /sse/messages

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting Memory MCP Direct Server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)