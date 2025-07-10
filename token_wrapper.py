#!/usr/bin/env python3
"""
Token Wrapper for MCP Proxy
Extracts authentication tokens from SSE URLs and passes them to MCP server subprocess
"""
import os
import sys
import subprocess
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/token_wrapper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_token_from_environment():
    """Extract token from various environment sources"""
    # Check if token was passed via environment (from Render dashboard)
    token_sources = [
        'USER_TOKEN',
        'AUTH_TOKEN', 
        'API_ACCESS_TOKEN',
        'MCP_TOKEN',
        'TOKEN'
    ]
    
    for source in token_sources:
        token = os.environ.get(source)
        if token:
            logger.info(f"Found token from environment variable {source}: {token[:10]}...")
            return token
    
    return None

def monitor_for_sse_token():
    """
    Monitor the mcp-proxy logs for SSE connections with tokens
    This is a fallback approach since mcp-proxy doesn't pass URL params directly
    """
    # For now, we'll rely on environment variables
    # In the future, we could implement log monitoring if needed
    return None

def main():
    """Main wrapper function"""
    logger.info("🔧 Token Wrapper starting...")
    
    # Create logs directory
    os.makedirs('/app/logs', exist_ok=True)
    
    # Extract token from available sources
    token = extract_token_from_environment()
    
    if not token:
        logger.warning("⚠️ No token found in environment variables")
        logger.info("Available environment variables:")
        for key, value in os.environ.items():
            if any(word in key.lower() for word in ['token', 'auth', 'api', 'key']):
                logger.info(f"  {key} = {value[:10]}..." if len(value) > 10 else f"  {key} = {value}")
    else:
        logger.info(f"✅ Token extracted successfully: {token[:10]}...")
    
    # Set up environment for mcp-proxy subprocess
    env = os.environ.copy()
    if token:
        env['USER_TOKEN'] = token
        env['API_ACCESS_TOKEN'] = token  # mcp-proxy standard
        logger.info("🔑 Token set in environment for subprocess")
    
    # Build mcp-proxy command
    mcp_proxy_cmd = [
        'mcp-proxy',
        '--host', '0.0.0.0',
        '--port', str(os.environ.get('PORT', '8000')),
        '--pass-environment',  # Pass all environment variables to subprocess
        'python', 'memory_mcp_server.py'
    ]
    
    logger.info(f"🚀 Starting mcp-proxy with command: {' '.join(mcp_proxy_cmd)}")
    
    # Start mcp-proxy with token in environment
    try:
        subprocess.run(mcp_proxy_cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ mcp-proxy failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        logger.info("🛑 Token wrapper interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()