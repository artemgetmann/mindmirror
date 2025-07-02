"""
API Conflict Test

This script tests the conflict detection logic by making direct HTTP requests to 
the memory_server API endpoints. This helps us verify that conflict sets are properly
surfaced in API responses without needing to go through the MCP wrapper.
"""

import requests
import json
from datetime import datetime
import time

# Configuration
API_BASE = "http://localhost:8003"  # Use the port we updated in memory_server.py

def print_formatted_json(data):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2))

def test_api_conflict_detection():
    """Test conflict detection through API calls"""
    print("\n===== Testing API Conflict Detection =====\n")
    
    # Check if API is running
    try:
        health_response = requests.get(f"{API_BASE}/health")
        if health_response.status_code != 200:
            print(f"❌ API not running at {API_BASE}")
            print(f"Status code: {health_response.status_code}")
            return False
        
        print(f"✅ API is running at {API_BASE}")
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        print(f"Make sure the memory server is running on port {API_BASE.split(':')[-1]}")
        return False
    
    # Step 1: Add first memory
    print("\nStep 1: Adding first communication preference memory...")
    memory1 = {
        "text": "Prefers direct communication with minimal details",
        "tag": "preference"
    }
    
    response1 = requests.post(f"{API_BASE}/memories", json=memory1)
    if response1.status_code == 200:
        print("✅ First memory added successfully")
        result1 = response1.json()
        print_formatted_json(result1)
    else:
        print(f"❌ Failed to add first memory: {response1.text}")
        return False
    
    # Short pause between adding memories
    time.sleep(1)
    
    # Step 2: Add conflicting memory
    print("\nStep 2: Adding conflicting communication preference memory...")
    memory2 = {
        "text": "Likes detailed and comprehensive communication",
        "tag": "preference"  # Same tag, conflicting content
    }
    
    response2 = requests.post(f"{API_BASE}/memories", json=memory2)
    if response2.status_code == 200:
        print("✅ Second (conflicting) memory added successfully")
        result2 = response2.json()
        print_formatted_json(result2)
    else:
        print(f"❌ Failed to add second memory: {response2.text}")
        return False
    
    # Short pause between operations
    time.sleep(1)
    
    # Step 3: Search for memories and check for conflict sets
    print("\nStep 3: Searching for communication preferences...")
    search_request = {
        "query": "How does the user prefer to communicate?",
        "limit": 10
    }
    
    search_response = requests.post(f"{API_BASE}/memories/search", json=search_request)
    if search_response.status_code == 200:
        print("✅ Search completed successfully")
        search_results = search_response.json()
        
        # Print full results for debugging
        print("\nSearch Results:")
        print_formatted_json(search_results)
        
        # Check for conflict sets
        if "conflict_sets" in search_results:
            print(f"\n✅ SUCCESS: Found {len(search_results['conflict_sets'])} conflict sets in API response")
            for key, conflicts in search_results["conflict_sets"].items():
                print(f"\nConflict set for '{key}':")
                for conflict in conflicts:
                    print(f"- '{conflict['text']}' (tag: {conflict['tag']})")
        else:
            print("\n❌ FAILURE: No conflict sets found in API response")
            print("This suggests the conflict detection logic is not properly surfacing conflicts")
            print("Debugging info:")
            print(f"Results count: {search_results['count']}")
            if "results" in search_results:
                for result in search_results["results"]:
                    print(f"- {result['id']}: '{result['text']}', tag: {result['tag']}")
    else:
        print(f"❌ Failed to search memories: {search_response.text}")
        return False
    
    return search_results

if __name__ == "__main__":
    results = test_api_conflict_detection()
    
    if not results:
        print("\n❌ Test failed - see errors above")
    elif "conflict_sets" in results:
        print("\n🎉 Test passed! Conflict sets are properly surfaced in API responses")
    else:
        print("\n⚠️ Test completed but conflict sets were not found in the response")
        print("Check the memory_server.py implementation of conflict detection")
