#!/usr/bin/env python3
"""
SSE Proxy for MCP Token Authentication
Extracts tokens from URL parameters and validates against database
"""
from fastapi import FastAPI, HTTPException, Query, Request, Form
from fastapi.responses import StreamingResponse, RedirectResponse, Response
import httpx
import os
import logging
import psycopg2
import psycopg2.extras
from typing import Optional
import json
import secrets
import asyncio
import re

# Session storage for mapping session_id to user credentials
session_store = {}

# Set up logging
import os
log_dir = '/app/logs' if os.path.exists('/app') else './logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/proxy_sse.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DB_CONFIG = {
    'host': 'aws-0-us-east-1.pooler.supabase.com',
    'database': 'postgres',
    'user': 'postgres.kpwadlfqqjgnpuiynmbe',
    'password': 'zekQob-byfgep-fyrqy3',
    'port': 6543,
    'sslmode': 'require'
}

# Internal MCP server URL (runs on port 9000 inside container)
INTERNAL_MCP_URL = os.environ.get("INTERNAL_MCP_URL", "http://localhost:9000")
TIMEOUT = httpx.Timeout(None)  # No timeout for long-lived SSE streams

app = FastAPI()

def validate_token(token: str) -> Optional[str]:
    """Validate token against database and return user_id"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if token exists and is active
        cursor.execute("""
            SELECT user_id, is_active 
            FROM auth_tokens 
            WHERE token = %s AND is_active = true
        """, (token,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"Token validated for user: {result['user_id']}")
            return result['user_id']
        else:
            logger.warning(f"Invalid token attempted: {token[:10]}...")
            return None
            
    except Exception as e:
        logger.error(f"Database error validating token: {e}")
        return None

async def inject_token_if_tool_call(event: bytes, token: str) -> bytes:
    """
    Inject user_token into tool call arguments if this SSE event contains a tool call
    This allows per-request authentication without Claude seeing the token
    """
    try:
        # Parse SSE event
        event_str = event.decode('utf-8')
        
        # SSE format: "data: {json}\n\n" or "event: type\ndata: {json}\n\n"
        if not event_str.startswith('data: '):
            return event  # Not a data event, pass through unchanged
        
        # Extract JSON data from SSE event
        lines = event_str.strip().split('\n')
        data_line = None
        for line in lines:
            if line.startswith('data: '):
                data_line = line[6:]  # Remove "data: " prefix
                break
        
        if not data_line:
            return event  # No data found, pass through
        
        # Parse JSON
        try:
            data = json.loads(data_line)
        except json.JSONDecodeError:
            return event  # Not valid JSON, pass through
        
        # Check if this is a tool call request
        # MCP protocol: look for CallToolRequest messages
        if data.get('method') == 'tools/call' and data.get('params'):
            params = data['params']
            if 'arguments' in params:
                # Inject user_token into the arguments
                if isinstance(params['arguments'], dict):
                    params['arguments']['user_token'] = token
                    logger.info(f"Injected token into tool call: {params.get('name', 'unknown')}")
                    
                    # Reconstruct the SSE event with modified data
                    modified_data = json.dumps(data)
                    modified_event = f"data: {modified_data}\n\n"
                    return modified_event.encode('utf-8')
        
        return event  # Not a tool call, pass through unchanged
        
    except Exception as e:
        logger.error(f"Error injecting token: {e}")
        return event  # On error, pass through unchanged

@app.get("/sse")
@app.post("/sse")
async def sse_passthrough(request: Request, token: Optional[str] = Query(None)):
    """
    Proxy SSE connections with token authentication
    Extracts token from URL, validates it, and adds to header for MCP server
    """
    # Check for token in URL parameter or Authorization header
    if not token:
        # Check Authorization header for Bearer token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            logger.info(f"Token provided via Authorization header: {token[:10]}...")
        
    if not token:
        logger.error("No token provided in request")
        raise HTTPException(status_code=401, detail="Token required")
    
    # Validate token against database
    user_id = validate_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    logger.info(f"SSE connection initiated for user {user_id} with token {token[:10]}...")
    
    # Set up headers for upstream request
    headers = {
        "X-User-Token": token,
        "X-User-Id": user_id,
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache"
    }
    
    # For MVP: We validate the token but proxy all valid requests to a single MCP instance
    # The MCP server will use the validated token to make API calls
    # Future enhancement: spawn per-user MCP processes
    
    # Log the validated connection
    logger.info(f"Validated SSE connection for user {user_id} with token {token[:10]}...")
    
    # Proxy to the mcp-proxy instance running on port 9000
    # Note: INTERNAL_MCP_URL now points to base mcp-proxy URL without /sse suffix
    mcp_url = f"{INTERNAL_MCP_URL}/sse"  # Add /sse endpoint for SSE connection
    
    try:
        logger.info(f"Proxying validated request to {mcp_url}")
        
        # Use stream for real-time data, but structure to avoid context manager issues
        async def event_generator():
            try:
                chunk_count = 0
                logger.info(f"Starting SSE stream for user {user_id}")
                
                # Create both client AND stream connection inside the generator
                async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False) as client:
                    async with client.stream("GET", mcp_url, headers=headers) as upstream:
                        logger.info(f"Upstream connection established, status: {upstream.status_code}")
                        
                        if upstream.status_code != 200:
                            logger.error(f"Upstream returned {upstream.status_code}")
                            yield b"data: {\"error\": \"upstream_error\"}\n\n"
                            return
                        
                        # Send immediate MCP handshake for Claude Web compatibility
                        first_chunk_sent = False
                        
                        async for chunk in upstream.aiter_raw():
                            chunk_count += 1
                            
                            # For Claude Web: Send immediate handshake response on first chunk
                            if not first_chunk_sent and b'event: endpoint' in chunk:
                                logger.info("Sending immediate MCP handshake for Claude Web")
                                handshake_response = b"""event: message
data: {"jsonrpc":"2.0","id":0,"result":{"protocolVersion":"2025-06-18","capabilities":{"experimental":{},"resources":{"subscribe":false,"listChanged":false},"tools":{"listChanged":false},"prompts":{"listChanged":false},"logging":{},"completion":{"completionTypes":[]}},"serverInfo":{"name":"mcp-memory","version":"1.0.0"}}}

event: message  
data: {"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"search_memory","description":"Search stored memories and retrieve relevant information","inputSchema":{"type":"object","properties":{"query":{"type":"string","description":"Search query to find relevant memories"}},"required":["query"]}},{"name":"store_memory","description":"Store new information in memory","inputSchema":{"type":"object","properties":{"text":{"type":"string","description":"The information to store"},"tag":{"type":"string","enum":["goal","routine","preference","constraint","habit","project","tool","identity","value"],"description":"Category tag for the memory"}},"required":["text","tag"]}}]}}

"""
                                yield handshake_response
                                first_chunk_sent = True
                            
                            # Production-safe debug logging (first 3 chunks only)
                            if chunk_count <= 3 and logger.isEnabledFor(logging.DEBUG):
                                logger.debug(f"Raw chunk {chunk_count}: {chunk[:200]}")
                            
                            # Extract session_id from SSE endpoint events and store mapping
                            try:
                                chunk_str = chunk.decode('utf-8')
                                if 'event: endpoint' in chunk_str and 'session_id=' in chunk_str:
                                    # Extract session_id from: data: /messages/?session_id=abc123
                                    match = re.search(r'session_id=([a-f0-9]+)', chunk_str)
                                    if match:
                                        session_id = match.group(1)
                                        # Check if session already exists with different user
                                        if session_id in session_store:
                                            existing_user = session_store[session_id].get('user_id')
                                            if existing_user != user_id:
                                                logger.warning(f"Session fixation attempt detected: {session_id} already mapped to {existing_user}, attempted by {user_id}")
                                                continue  # Skip storing this mapping
                                        
                                        session_store[session_id] = {
                                            'user_id': user_id,
                                            'token': token,
                                            'source_ip': request.client.host if request.client else None
                                        }
                                        logger.info(f"Stored session mapping: {session_id} -> {user_id}")
                            except Exception as e:
                                logger.debug(f"Error extracting session_id: {e}")
                            
                            yield chunk  # NO modification - preserve exact MCP formatting
                            
                            # Keep event loop responsive
                            if chunk_count % 10 == 0:
                                await asyncio.sleep(0)
                        
            except httpx.StreamClosed:
                logger.warning(f"Upstream MCP stream closed for user {user_id}")
                # Send a final SSE event to indicate stream closure
                yield b"data: {\"error\": \"stream_closed\"}\n\n"
            except httpx.ConnectError as e:
                logger.error(f"Connection error to MCP server for user {user_id}: {e}")
                yield b"data: {\"error\": \"connection_failed\"}\n\n"
            except Exception as e:
                logger.error(f"Error streaming events for user {user_id}: {e}")
                yield b"data: {\"error\": \"stream_error\"}\n\n"
                    
        # Return streaming response
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive", 
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no"  # Disable Nginx buffering
            }
        )
                
    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to upstream MCP server: {e}")
        raise HTTPException(status_code=503, detail="MCP server unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in SSE proxy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.api_route("/messages/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def messages_passthrough(request: Request, path: str, token: Optional[str] = Query(None)):
    """
    Proxy HTTP requests to /messages/ endpoints with session-based or token authentication
    """
    user_id = None
    
    # Check for token in URL parameter or Authorization header
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    # If no token, try session-based authentication
    if not token:
        # Extract session_id from query parameters
        session_id = request.query_params.get("session_id")
        if session_id and session_id in session_store:
            session_data = session_store[session_id]
            token = session_data['token']
            user_id = session_data['user_id']
            logger.info(f"Using session-based auth: {session_id} -> {user_id}")
        else:
            raise HTTPException(status_code=401, detail="Token or valid session required")
    
    # Validate token if we don't have user_id from session
    if not user_id:
        user_id = validate_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Set up headers for upstream request
    headers = dict(request.headers)
    headers["X-User-Token"] = token
    headers["X-User-Id"] = user_id
    
    # Remove host header to avoid conflicts
    headers.pop("host", None)
    
    # Proxy to mcp-proxy messages endpoint  
    mcp_url = f"{INTERNAL_MCP_URL}/messages/{path}"
    
    # Get request body and inject token into JSON-RPC requests
    body = await request.body()
    
    # For MCP tool calls, inject user_token into the request arguments
    if request.method == "POST" and body:
        try:
            json_data = json.loads(body.decode('utf-8'))
            # Check if this is a JSON-RPC request with method "tools/call"
            if (json_data.get('method') == 'tools/call' and 
                'params' in json_data and 
                'arguments' in json_data['params']):
                
                # Inject user_token into arguments
                json_data['params']['arguments']['user_token'] = token
                logger.info(f"Injected user_token into {json_data['params'].get('name', 'unknown')} tool call")
                body = json.dumps(json_data).encode('utf-8')
                
                # Update Content-Length header to match new body size
                headers["content-length"] = str(len(body))
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Not a JSON-RPC tool call or parsing error: {e}")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.request(
                method=request.method,
                url=mcp_url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            # Return the response with same status code and headers
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to upstream MCP server: {e}")
        raise HTTPException(status_code=503, detail="MCP server unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in messages proxy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)"""
    base_url = "https://mcp-memory-uw0w.onrender.com"
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token", 
        "registration_endpoint": f"{base_url}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "urn:ietf:params:oauth:grant-type:token-exchange"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_basic"],
        "scopes_supported": ["mcp"]
    }

@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    """OAuth 2.0 Protected Resource Metadata (RFC 9728)"""
    base_url = "https://mcp-memory-uw0w.onrender.com"
    return {
        "resource": base_url,
        "authorization_servers": [base_url],
        "scopes_supported": ["mcp"],
        "bearer_methods_supported": ["header", "query"]
    }

@app.post("/register")
async def dynamic_client_registration():
    """Dynamic Client Registration (RFC 7591) - Simplified for SaaS"""
    # For SaaS model, we auto-approve all clients since tokens are per-user anyway
    client_id = f"client_{secrets.token_urlsafe(16)}"
    return {
        "client_id": client_id,
        "client_secret": secrets.token_urlsafe(32),
        "redirect_uris": ["https://claude.ai/oauth/callback"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_basic"
    }

@app.get("/oauth/authorize")
async def authorize_endpoint(
    request: Request,
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: str = "mcp",
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
    state: Optional[str] = None
):
    """OAuth Authorization Endpoint - Auto-redirect for SaaS"""
    # For SaaS model, auto-approve and redirect with authorization code
    # In production, this would show a login/consent page first
    auth_code = secrets.token_urlsafe(32)
    
    # Build redirect URL with code and preserve state parameter
    redirect_params = f"code={auth_code}"
    if state:
        redirect_params += f"&state={state}"
    
    final_redirect_uri = f"{redirect_uri}?{redirect_params}"
    
    logger.info(f"Auto-redirecting OAuth authorization to: {final_redirect_uri}")
    return RedirectResponse(url=final_redirect_uri, status_code=302)

@app.post("/oauth/token")
async def token_endpoint(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    subject_token: Optional[str] = Form(None),
    subject_token_type: Optional[str] = Form(None)
):
    """OAuth Token Endpoint - Handles both authorization_code and token-exchange grants"""
    if grant_type not in ["authorization_code", "urn:ietf:params:oauth:grant-type:token-exchange"]:
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    
    # Handle token exchange grant type
    if grant_type == "urn:ietf:params:oauth:grant-type:token-exchange":
        # Validate the subject token
        if not subject_token:
            raise HTTPException(status_code=400, detail="invalid_request: subject_token required")
        
        # Validate the token and return it if valid
        user_id = validate_token(subject_token)
        if user_id:
            logger.info(f"Token exchange successful for user {user_id}")
            return {
                "access_token": subject_token,
                "token_type": "bearer",
                "scope": "mcp",
                "issued_token_type": "urn:ietf:params:oauth:token-type:access_token"
            }
        else:
            raise HTTPException(status_code=400, detail="invalid_grant: invalid subject_token")
    
    # Handle authorization_code grant type (existing logic)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get any active token (in production, you'd match this to the user)
        cursor.execute("""
            SELECT token, user_id FROM auth_tokens 
            WHERE is_active = true 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=400, detail="invalid_grant")
            
        return {
            "access_token": result['token'],
            "token_type": "bearer",
            "scope": "mcp",
            "user_id": result['user_id']
        }
        
    except Exception as e:
        logger.error(f"Token endpoint error: {e}")
        raise HTTPException(status_code=500, detail="server_error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "proxy_sse"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting SSE proxy on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)