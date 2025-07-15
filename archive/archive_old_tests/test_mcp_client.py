"""
Test Client for MCP Memory Wrapper

This script simulates how an LLM would interact with our memory system
through the MCP wrapper interface. It demonstrates:

1. Adding observations via add_observations
2. Searching memories via search_nodes  
3. Opening specific memories via open_nodes
4. Handling conflict sets appropriately

Run this after starting both:
- memory_server.py (port 8003)
- mcp_wrapper.py (port 8002)
"""
import requests
import json
import time
from datetime import datetime, timedelta
import sys

# Configuration
MCP_BASE_URL = "http://localhost:8002"
MEMORY_BASE_URL = "http://localhost:8003"  # Updated port for memory service

def print_json(data):
    """Print JSON data with pretty formatting"""
    print(json.dumps(data, indent=2))

def check_services():
    """Check if required services are running"""
    try:
        memory_response = requests.get(f"{MEMORY_BASE_URL}/health", timeout=2)
        wrapper_response = requests.get(f"{MCP_BASE_URL}/", timeout=2)
        
        if memory_response.status_code == 200 and wrapper_response.status_code == 200:
            print("✅ Both services are running!")
            print(f"Memory service: {MEMORY_BASE_URL}")
            print(f"MCP wrapper: {MCP_BASE_URL}")
            return True
        else:
            print("❌ Services check failed!")
            if memory_response.status_code != 200:
                print("Memory service is not responding correctly")
            if wrapper_response.status_code != 200:
                print("MCP wrapper is not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Error connecting to services: {e}")
        print("Make sure both memory_server.py and mcp_wrapper.py are running")
        return False

def add_test_memories():
    """Add test memories including conflicting ones"""
    print("\n=== Adding Test Memories ===\n")
    
    # Test observations with some conflicts
    observations = {
        "observations": [
            {
                "entityName": "test_user",
                "contents": [
                    "Prefers fast, blunt communication without fluff",
                    "Always makes time for morning exercise routine",
                    "Values direct feedback over politeness"
                ]
            },
            {
                "entityName": "test_user",
                "contents": [
                    "Likes to communicate with lots of detail and explanation",
                    "Works on coding projects in Python and JavaScript",
                    "Prefers to be called by first name only"
                ]
            }
        ]
    }
    
    response = requests.post(
        f"{MCP_BASE_URL}/add_observations",
        json=observations
    )
    
    if response.status_code == 200:
        print("✅ Successfully added test memories")
        print_json(response.json())
    else:
        print(f"❌ Failed to add memories: {response.status_code}")
        print(response.text)
        return False
    
    return True

def test_search_without_conflicts():
    """Test searching for memories without conflicts"""
    print("\n=== Searching Memories (No Conflicts) ===\n")
    
    # This search should match memories without conflicts
    search_data = {
        "query": "What projects does the user work on?"
    }
    
    response = requests.post(
        f"{MCP_BASE_URL}/search_nodes",
        json=search_data
    )
    
    if response.status_code == 200:
        print("✅ Search completed successfully")
        result = response.json()
        print_json(result)
        
        # Check if we got expected results
        if "nodes" in result and len(result["nodes"]) > 0:
            print(f"Found {len(result['nodes'])} memories")
            return True
        else:
            print("❌ No memories found in search results")
            return False
    else:
        print(f"❌ Search failed: {response.status_code}")
        print(response.text)
        return False

def test_search_with_conflicts():
    """Test searching for memories with known conflicts"""
    print("\n=== Searching Memories (With Conflicts) ===\n")
    
    # This search should match memories with conflicts
    search_data = {
        "query": "How does the user prefer to communicate?"
    }
    
    response = requests.post(
        f"{MCP_BASE_URL}/search_nodes",
        json=search_data
    )
    
    if response.status_code == 200:
        print("✅ Search completed successfully")
        result = response.json()
        print_json(result)
        
        # Check if we got conflict sets
        if "conflict_sets" in result:
            print(f"✅ Found {len(result['conflict_sets'])} conflict sets")
            
            # Simulate LLM conflict resolution
            print("\n=== Simulated LLM Conflict Resolution ===\n")
            print("System: Response contains conflict_sets, I'll pick the most recent item or ask for clarification.")
            
            # In real LLM this would be date comparison logic
            print("LLM: I found conflicting information about your communication preferences:")
            for node in result["nodes"]:
                print(f"- {node['observations'][0]} ({node['timestamp']})")
            
            print("\nLLM: Since these conflict, I'll use the most recent information or ask:")
            print("'I notice you've given different communication preferences. Do you prefer blunt, direct communication or detailed explanations?'")
            
            return True
        else:
            print("❓ No conflict sets found - check if conflicts were correctly flagged")
            return False
    else:
        print(f"❌ Search failed: {response.status_code}")
        print(response.text)
        return False

def test_open_nodes():
    """Test opening specific nodes by name"""
    print("\n=== Opening Nodes by Tag ===\n")
    
    # This should retrieve all memories with preference tag
    open_data = {
        "names": ["preference"]
    }
    
    response = requests.post(
        f"{MCP_BASE_URL}/open_nodes",
        json=open_data
    )
    
    if response.status_code == 200:
        print("✅ Open nodes completed successfully")
        result = response.json()
        print_json(result)
        
        # Check if we got preferences
        if "nodes" in result and len(result["nodes"]) > 0:
            print(f"Found {len(result['nodes'])} preference memories")
            return True
        else:
            print("❌ No preference memories found")
            return False
    else:
        print(f"❌ Open nodes failed: {response.status_code}")
        print(response.text)
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print("\n🧪 Running MCP Client Tests 🧪\n")
    
    if not check_services():
        return False
    
    results = []
    results.append(("Add Test Memories", add_test_memories()))
    
    # Short pause to ensure memories are indexed
    time.sleep(1)
    
    results.append(("Search Without Conflicts", test_search_without_conflicts()))
    results.append(("Search With Conflicts", test_search_with_conflicts()))
    results.append(("Open Nodes", test_open_nodes()))
    
    # Print summary
    print("\n=== Test Results Summary ===\n")
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! MCP integration looks good.")
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
