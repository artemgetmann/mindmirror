"""
Memory System Demo Tutorial
Step-by-step demonstration of how the memory system works
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def divider(title):
    """Print a section divider"""
    print(f"\n{'=' * 70}")
    print(f" 📘 {title}")
    print(f"{'=' * 70}")

def print_response(response):
    """Pretty print API response"""
    try:
        print(f"\nResponse (Status: {response.status_code}):")
        print(f"{json.dumps(response.json(), indent=2)}")
    except:
        print(f"Raw response: {response.text}")

def demo_add_memory():
    """Demonstration of adding memories with different tags"""
    divider("ADDING MEMORIES DEMO")
    print("Let's add different types of memories and see how they're handled")
    
    # In this system, tags need to be specified manually when adding a memory
    print("\n🔹 STEP 1: Adding a preference memory")
    print("Here, we explicitly set the tag to 'preference'")
    memory1 = {
        "text": "Prefers dark mode in code editors",
        "tag": "preference"
    }
    
    print("\nStoring preference memory...")
    response = requests.post(f"{BASE_URL}/memories", json=memory1)
    print_response(response)
    
    # Example of adding a different tag type
    print("\n🔹 STEP 2: Adding a goal memory")
    print("Now we explicitly set the tag to 'goal'")
    memory2 = {
        "text": "Build a simpler memory system with fewer components",
        "tag": "goal"
    }
    
    print("\nStoring goal memory...")
    response = requests.post(f"{BASE_URL}/memories", json=memory2)
    print_response(response)
    
    # Example of invalid tag
    print("\n🔹 STEP 3: Trying to add memory with invalid tag")
    print("The system only accepts these tags:")
    print("  goal, routine, preference, constraint, habit, project, tool, identity, value")
    memory3 = {
        "text": "Let's see what happens with an invalid tag",
        "tag": "invalid_tag"
    }
    
    print("\nAttempting to store with invalid tag...")
    response = requests.post(f"{BASE_URL}/memories", json=memory3)
    print_response(response)
    
    print("\n➡️ KEY INSIGHT: Tags are NOT automatically assigned.")
    print("   The system requires you to specify the tag when storing a memory.")
    print("   In a full production system, an AI model would need to classify the text")
    print("   and determine the appropriate tag before storage.")

def demo_duplicate_handling():
    """Demonstration of duplicate memory handling"""
    divider("DUPLICATE HANDLING DEMO")
    print("Let's see how the system handles duplicates")
    
    memory = {
        "text": "Prefers to work in early morning hours",
        "tag": "preference"
    }
    
    print("\n🔹 STEP 1: Adding a new memory")
    print("Storing a new memory...")
    response = requests.post(f"{BASE_URL}/memories", json=memory)
    print_response(response)
    
    print("\n🔹 STEP 2: Trying to add exact duplicate")
    print("Storing the exact same memory again...")
    response = requests.post(f"{BASE_URL}/memories", json=memory)
    print_response(response)
    
    print("\n🔹 STEP 3: Trying same text with different tag")
    memory["tag"] = "habit"
    print("Storing same text but tagged as 'habit'...")
    response = requests.post(f"{BASE_URL}/memories", json=memory)
    print_response(response)
    
    print("\n➡️ KEY INSIGHT: Deduplication is based on exact text + tag combination.")
    print("   Same text with different tags IS allowed (could represent different aspects)")
    print("   Slight variations in text are also allowed")

def demo_memory_search():
    """Demonstration of memory search and retrieval"""
    divider("MEMORY SEARCH DEMO")
    print("Let's see how vector search finds relevant memories")
    
    # First, add some varied memories to search
    memories = [
        {"text": "Prefers using Terminal over GUI tools", "tag": "preference"},
        {"text": "Has experience with React and TypeScript", "tag": "identity"},
        {"text": "Wants to improve code testing practices", "tag": "goal"},
        {"text": "Uses VSCode as primary editor", "tag": "tool"}
    ]
    
    print("\n🔹 STEP 1: Adding some varied memories to search")
    for memory in memories:
        response = requests.post(f"{BASE_URL}/memories", json=memory)
        print(f"Added: {memory['text']} [{memory['tag']}]")
    
    # Simple semantic search
    print("\n🔹 STEP 2: Simple semantic search")
    query1 = "What development environment does the user prefer?"
    print(f"Query: '{query1}'")
    print("Searching...")
    
    response = requests.post(f"{BASE_URL}/memories/search", 
                            json={"query": query1, "limit": 3})
    print_response(response)
    
    # Search with tag filter
    print("\n🔹 STEP 3: Search with tag filter")
    query2 = "What technologies does the user know?"
    print(f"Query: '{query2}' (filtered to identity tag)")
    print("Searching with tag filter...")
    
    response = requests.post(f"{BASE_URL}/memories/search", 
                            json={"query": query2, "tag_filter": "identity", "limit": 3})
    print_response(response)
    
    print("\n➡️ KEY INSIGHT: Semantic search finds related memories based on meaning")
    print("   Query about 'development environment' finds memories about editors and terminals")
    print("   Tag filters limit search to specific categories")
    print("   Similarity scores show how closely the memory matches the query")

def demo_similar_but_different():
    """Demonstration of similar memories with slightly different wording"""
    divider("SIMILAR MEMORIES DEMO")
    print("Let's see how slightly different wording affects search")
    
    # Add similar memories with different wording
    memories = [
        {"text": "Prefers clean, minimal code with no fluff", "tag": "preference"},
        {"text": "Likes concise coding style without unnecessary comments", "tag": "preference"},
        {"text": "Values brevity and directness in communication", "tag": "value"}
    ]
    
    print("\n🔹 STEP 1: Adding memories with similar meaning but different wording")
    for memory in memories:
        response = requests.post(f"{BASE_URL}/memories", json=memory)
        print(f"Added: {memory['text']} [{memory['tag']}]")
    
    # Search with semantically related query
    print("\n🔹 STEP 2: Search with semantically related query")
    query = "Does the user like verbose code with lots of comments?"
    print(f"Query: '{query}'")
    
    response = requests.post(f"{BASE_URL}/memories/search", 
                           json={"query": query, "limit": 3})
    print_response(response)
    
    print("\n➡️ KEY INSIGHT: Semantic search finds related concepts")
    print("   Query about 'verbose code' finds memories about 'minimal code'")
    print("   This works because the embeddings capture meaning, not just keywords")

def demo_mcp_integration():
    """Explain how MCP integration would work"""
    divider("MCP INTEGRATION EXPLANATION")
    print("Here's how this would work as an MCP server:")
    
    print("\n🔹 MCP Endpoints would map to memory operations:")
    print("  • add_observations() → POST /memories")
    print("  • search_nodes() → POST /memories/search")
    print("  • open_nodes() → GET /memories/{id} or GET /memories?tag=X")
    
    print("\n🔹 Flow for storing memories:")
    print("  1. AI receives info from user: 'I prefer dark mode'")
    print("  2. AI decides this is a preference (requires AI classification)")
    print("  3. AI calls add_observations with entity='user', content='Prefers dark mode'")
    print("  4. MCP server translates to POST /memories with tag='preference'")
    print("  5. Memory stored in vector database")
    
    print("\n🔹 Flow for retrieving memories:")
    print("  1. User asks: 'What theme should I use?'")
    print("  2. AI calls search_nodes with query='user interface preferences'")
    print("  3. MCP server translates to POST /memories/search")
    print("  4. Vector search finds semantic matches")
    print("  5. AI receives 'Prefers dark mode' and includes in response")
    
    print("\n➡️ KEY INSIGHT: For MCP integration, you need:")
    print("   1. Tag classification: AI must determine correct tag for observations")
    print("   2. Entity mapping: Map between MCP entities and your tag system")
    print("   3. Query translation: Convert MCP queries to effective vector searches")

def run_demo():
    """Run the complete demonstration"""
    print("🧠 Memory System Step-by-Step Demo")
    print("A clear walkthrough of how the system works")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Memory server not responding. Start server before running demo.")
            return
    except:
        print("❌ Cannot connect to server at http://localhost:8000")
        print("   Please start the memory server first with: python memory_server.py")
        return
    
    print("✅ Memory server is running\n")
    
    # Run each demo section
    demo_add_memory()
    demo_duplicate_handling()
    demo_memory_search()
    demo_similar_but_different()
    demo_mcp_integration()
    
    print("\n🎓 Demo complete! You now understand how the memory system works.")
    print("The key points to remember:")
    print("1. Tags must be explicitly assigned (no auto-classification yet)")
    print("2. Semantic search finds relevant memories based on meaning")
    print("3. Deduplication prevents exact duplicates (text + tag)")
    print("4. Integration with MCP requires tag classification logic")

if __name__ == "__main__":
    run_demo()