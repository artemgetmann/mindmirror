"""
Test client for Memory System v0
Tests the MVP roundtrip: store memory -> search memory
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_communication_preference_roundtrip():
    """Test case: store and retrieve communication preference"""
    
    print("🧪 Testing communication preference roundtrip...")
    
    # Step 1: Store memory
    memory_data = {
        "text": "Prefers blunt, fast communication",
        "tag": "preference"
    }
    
    print(f"📝 Storing: {memory_data['text']}")
    response = requests.post(f"{BASE_URL}/memories", json=memory_data)
    
    if response.status_code != 200:
        print(f"❌ Store failed: {response.text}")
        return False
    
    store_result = response.json()
    print(f"✅ Stored with ID: {store_result['id']}")
    
    # Step 2: Search for memory
    search_data = {
        "query": "What do you know about my communication style?",
        "limit": 3
    }
    
    print(f"🔍 Searching: {search_data['query']}")
    response = requests.post(f"{BASE_URL}/memories/search", json=search_data)
    
    if response.status_code != 200:
        print(f"❌ Search failed: {response.text}")
        return False
    
    search_result = response.json()
    
    if search_result['count'] == 0:
        print("❌ No memories found")
        return False
    
    # Check if our memory was retrieved
    found = False
    for memory in search_result['results']:
        if "blunt" in memory['text'].lower() or "fast" in memory['text'].lower():
            found = True
            print(f"✅ Found memory: {memory['text']} (similarity: {memory['similarity']:.3f})")
            break
    
    if not found:
        print("❌ Communication preference not retrieved")
        return False
    
    print("🎉 Roundtrip test PASSED!")
    return True

def test_multiple_roundtrips():
    """Run the test 10 times to validate consistency"""
    print("\n🔄 Running 10 consecutive roundtrip tests...")
    
    success_count = 0
    for i in range(10):
        print(f"\n--- Test {i+1}/10 ---")
        if test_communication_preference_roundtrip():
            success_count += 1
        else:
            print(f"❌ Test {i+1} failed")
            break
    
    print(f"\n📊 Results: {success_count}/10 tests passed")
    
    if success_count == 10:
        print("🚀 MVP TEST PASSED! Memory system is ready.")
        return True
    else:
        print("💥 MVP test failed. Need to fix issues.")
        return False

def list_all_memories():
    """List all stored memories"""
    print("\n📋 All stored memories:")
    response = requests.get(f"{BASE_URL}/memories")
    
    if response.status_code != 200:
        print(f"❌ Failed to list memories: {response.text}")
        return
    
    result = response.json()
    for memory in result['memories']:
        print(f"  • [{memory['tag']}] {memory['text']} ({memory['timestamp']})")

def check_server_health():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print("❌ Server health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Run: python memory_server.py")
        return False

if __name__ == "__main__":
    print("🧠 Memory System v0 Test Client")
    print("=" * 40)
    
    # Check server health first
    if not check_server_health():
        exit(1)
    
    # List existing memories
    list_all_memories()
    
    # Run single test
    if test_communication_preference_roundtrip():
        # Run multiple tests if single test passes
        test_multiple_roundtrips()