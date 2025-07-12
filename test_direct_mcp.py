#!/usr/bin/env python3
"""
Test script for the direct MCP server implementation
"""
import asyncio
import httpx
import json

async def test_memory_server_connection():
    """Test if memory_server.py is running and accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/health")
            if response.status_code == 200:
                print("✅ Memory server is running on port 8001")
                return True
            else:
                print(f"❌ Memory server returned {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to memory server: {e}")
        return False

async def test_token_validation():
    """Test token validation against PostgreSQL"""
    # This would require importing the validation function
    # For now, just check if we can import the module
    try:
        import sys
        sys.path.append('/Users/user/Programming_Projects/MCP_Memory')
        from memory_mcp_direct import validate_token
        
        # Test with a sample token (this will likely fail but shouldn't crash)
        result = await validate_token("test_token")
        print(f"✅ Token validation function works (result: {result})")
        return True
    except Exception as e:
        print(f"❌ Token validation error: {e}")
        return False

async def test_mcp_server_startup():
    """Test if the MCP server can start up"""
    try:
        # Try to import the main module
        import sys
        sys.path.append('/Users/user/Programming_Projects/MCP_Memory')
        import memory_mcp_direct
        
        print("✅ MCP direct server module imports successfully")
        return True
    except Exception as e:
        print(f"❌ MCP server import error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing Direct MCP Server Implementation\n")
    
    tests = [
        ("Memory Server Connection", test_memory_server_connection),
        ("Token Validation", test_token_validation),
        ("MCP Server Startup", test_mcp_server_startup)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        result = await test_func()
        results.append(result)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("="*50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready to test with Claude Desktop.")
    else:
        print("⚠️ Some tests failed. Check the issues above.")

if __name__ == "__main__":
    asyncio.run(main())