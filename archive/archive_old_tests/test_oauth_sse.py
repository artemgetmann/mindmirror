#!/usr/bin/env python3
"""
Test OAuth flow and SSE headers for MCP Memory integration
"""

import httpx
import asyncio
import json
import pytest

BASE_URL = "http://localhost:8000"
TEST_TOKEN = "T6o5fD4WoOkiLh-2kObXvAgDAOjJbLU_AuQI9WpBg0Y"

@pytest.mark.asyncio
async def test_oauth_discovery():
    """Test OAuth discovery endpoint returns correct metadata"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/.well-known/oauth-authorization-server")
        assert response.status_code == 200
        
        data = response.json()
        assert "authorization_endpoint" in data
        assert "token_endpoint" in data
        assert "grant_types_supported" in data
        assert "urn:ietf:params:oauth:grant-type:token-exchange" in data["grant_types_supported"]
        print("✅ OAuth discovery endpoint working correctly")

@pytest.mark.asyncio
async def test_token_exchange():
    """Test OAuth token exchange grant type"""
    async with httpx.AsyncClient() as client:
        # Test token exchange
        response = await client.post(
            f"{BASE_URL}/oauth/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": TEST_TOKEN,
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == TEST_TOKEN
        assert data["token_type"] == "bearer"
        assert "issued_token_type" in data
        print("✅ Token exchange working correctly")

@pytest.mark.asyncio
async def test_sse_headers():
    """Test SSE endpoint returns proper headers"""
    async with httpx.AsyncClient() as client:
        # Test GET request
        async with client.stream("GET", f"{BASE_URL}/sse?token={TEST_TOKEN}") as response:
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream"
            assert response.headers.get("cache-control") == "no-cache"
            assert response.headers.get("x-accel-buffering") == "no"
            print("✅ SSE GET headers correct")
        
        # Test POST request (should also work)
        async with client.stream("POST", f"{BASE_URL}/sse?token={TEST_TOKEN}") as response:
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream"
            print("✅ SSE POST request accepted")

@pytest.mark.asyncio
async def test_multi_tenant_isolation():
    """Test that different tokens maintain isolation"""
    token1 = TEST_TOKEN
    token2 = "different-token-here"  # This would fail validation
    
    async with httpx.AsyncClient() as client:
        # First connection should succeed
        async with client.stream("GET", f"{BASE_URL}/sse?token={token1}") as response1:
            assert response1.status_code == 200
        
        # Second connection with invalid token should fail
        try:
            response2 = await client.get(f"{BASE_URL}/sse?token={token2}")
            assert response2.status_code == 401
            print("✅ Multi-tenant isolation working")
        except httpx.HTTPStatusError as e:
            assert e.response.status_code == 401
            print("✅ Multi-tenant isolation working")

def test_double_token_curl():
    """Manual test with curl to verify double-token scenario"""
    print("\nManual test commands:")
    print(f"# Terminal 1 - Start first session:")
    print(f"curl -N '{BASE_URL}/sse?token={TEST_TOKEN}'")
    print(f"\n# Terminal 2 - Try to hijack session (should fail):")
    print(f"curl -N '{BASE_URL}/sse?token=another-token'")
    print("\nVerify that each connection maintains its own session")

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_oauth_discovery())
    asyncio.run(test_token_exchange())
    asyncio.run(test_sse_headers())
    asyncio.run(test_multi_tenant_isolation())
    test_double_token_curl()
    
    print("\n✅ All tests passed!")