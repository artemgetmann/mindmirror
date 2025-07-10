#!/usr/bin/env python3
"""
SSE Proxy for MCP Token Authentication
Extracts tokens from URL parameters and validates against database
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx
import os
import logging
import psycopg2
import psycopg2.extras
from typing import Optional
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/proxy_sse.log'),
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
INTERNAL_MCP_URL = os.environ.get("INTERNAL_MCP_URL", "http://localhost:9000/sse")
TIMEOUT = httpx.Timeout(300.0, read=None)  # 5 min timeout for SSE streams

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
async def sse_passthrough(token: Optional[str] = Query(None)):
    """
    Proxy SSE connections with token authentication
    Extracts token from URL, validates it, and adds to header for MCP server
    """
    # Validate token parameter
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
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            logger.info(f"Proxying validated request to {INTERNAL_MCP_URL}")
            
            async with client.stream("GET", INTERNAL_MCP_URL, headers=headers) as upstream:
                logger.info(f"Upstream connection established, status: {upstream.status_code}")
                
                # Generator to stream events with token injection
                async def event_generator():
                    try:
                        buffer = b""
                        async for chunk in upstream.aiter_raw():
                            buffer += chunk
                            
                            # Process complete SSE events
                            while b"\n\n" in buffer:
                                event_end = buffer.find(b"\n\n") + 2
                                event = buffer[:event_end]
                                buffer = buffer[event_end:]
                                
                                # Parse and modify SSE event if it contains a tool call
                                modified_event = await inject_token_if_tool_call(event, token)
                                yield modified_event
                        
                        # Yield any remaining data
                        if buffer:
                            yield buffer
                            
                    except Exception as e:
                        logger.error(f"Error streaming events: {e}")
                        raise
                
                # Return streaming response
                return StreamingResponse(
                    event_generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no"  # Disable Nginx buffering
                    }
                )
                
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to upstream MCP server: {e}")
            raise HTTPException(status_code=503, detail="MCP server unavailable")
        except Exception as e:
            logger.error(f"Unexpected error in SSE proxy: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "proxy_sse"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting SSE proxy on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)