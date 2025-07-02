"""
Conflict Detection Test Script

Tests the conflict detection logic in the memory system:
1. Add a memory
2. Add a contradictory memory with same tag
3. Check that conflict_sets are properly returned in search results
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"

def clear_text():
    """Clear console text for better readability"""
    print("\033c", end="")

def print_header(text):
    """Print a formatted header"""
    print(f"\n\033[1;36m{text}\033[0m")
    print("="*50)

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))

def main():
    """Run the conflict detection test"""
    clear_text()
    print_header("🔍 CONFLICT DETECTION TEST")
    
    # 1. Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server not running. Please start the server first.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the server first.")
        return
    
    # 2. Add first memory with timestamp to ensure uniqueness
    print_header("Step 1: Adding first memory")
    current_time = datetime.utcnow().isoformat()
    memory1 = {
        "text": f"I prefer working at night (test: {current_time})",
        "tag": "preference",
        "timestamp": current_time + "Z"
    }
    
    response = requests.post(f"{BASE_URL}/memories", json=memory1)
    print("Response (Status: {}):".format(response.status_code))
    first_memory = response.json()
    print_json(first_memory)
    # Handle possible duplicate case
    if "id" in first_memory:
        first_memory_id = first_memory["id"]
    else:
        print("⚠️ First memory appears to be a duplicate, using a search to find latest")
        # Search for the memory to get its ID
        find_request = {
            "query": current_time,
            "limit": 1,
            "tag_filter": "preference"
        }
        find_response = requests.post(f"{BASE_URL}/memories/search", json=find_request)
        results = find_response.json()
        if results["count"] > 0:
            first_memory_id = results["results"][0]["id"]
            print(f"Found memory with ID: {first_memory_id}")
        else:
            print("❌ Could not find the first memory")
            return
    
    # 3. Add conflicting memory (using same timestamp base to keep it close in time)
    print_header("Step 2: Adding conflicting memory")
    memory2 = {
        "text": f"I prefer working in the mornings (test: {current_time})",
        "tag": "preference", 
        "timestamp": current_time + "Z"
    }
    
    print("Adding conflicting memory...")
    response = requests.post(f"{BASE_URL}/memories", json=memory2)
    print("Response (Status: {}):".format(response.status_code))
    second_memory = response.json() 
    print_json(second_memory)
    # Handle possible duplicate case
    if "id" in second_memory:
        second_memory_id = second_memory["id"]
    else:
        print("⚠️ Second memory appears to be a duplicate, using a search to find it")
        # Search for the memory to get its ID
        find_request = {
            "query": current_time,
            "limit": 5,
            "tag_filter": "preference"
        }
        find_response = requests.post(f"{BASE_URL}/memories/search", json=find_request)
        results = find_response.json()
        if results["count"] > 1:
            # Take the one that's not the first_memory_id
            for result in results["results"]:
                if result["id"] != first_memory_id:
                    second_memory_id = result["id"]
                    print(f"Found second memory with ID: {second_memory_id}")
                    break
        if not 'second_memory_id' in locals():
            print("❌ Could not find the second memory")
            return
    
    # 4. Retrieve first memory directly to check conflict_set
    print_header("Step 3: Retrieving first memory to check for conflict_set")
    response = requests.get(f"{BASE_URL}/memories/{first_memory_id}")
    print("Response (Status: {}):".format(response.status_code))
    memory_with_conflicts = response.json()
    print_json(memory_with_conflicts)
    
    # 5. Search for memories to check conflict_sets in search
    print_header("Step 4: Searching for our test memories")
    # Use part of the timestamp to find exactly our test memories
    time_marker = current_time.split("T")[1][:8]  # Extract time portion (HH:MM:SS)
    search_request = {
        "query": f"When do I work best? {time_marker}",
        "limit": 5,
        "tag_filter": "preference"
    }
    
    response = requests.post(f"{BASE_URL}/memories/search", json=search_request)
    print("Response (Status: {}):".format(response.status_code))
    search_results = response.json()
    print_json(search_results)
    
    # 6. Print conclusion
    print_header("Test Results")
    
    if "conflict_set" in memory_with_conflicts:
        print("✅ Direct memory retrieval correctly includes conflict_set")
        print(f"   Found {len(memory_with_conflicts['conflict_set'])} memories in conflict set")
    else:
        print("❌ Direct memory retrieval does not include conflict_set")
    
    if "conflict_sets" in search_results:
        print("✅ Search results correctly include conflict_sets")
        print(f"   Found {len(search_results['conflict_sets'])} conflict sets")
        
        # Explanation for usage with LLM
        print("\n🤖 LLM Conflict Resolution:")
        print("When a memory response contains conflict_sets, the LLM should:")
        print("1. Identify that contradictory memories exist")
        print("2. Choose the most relevant one based on context or recency")
        print("3. Consider asking the user which preference is current")
    else:
        print("❌ Search results do not include conflict_sets")

if __name__ == "__main__":
    main()
