"""
Quick demo of Memory System v0 improvements
Shows deduplication, positive similarity scores, and performance metrics
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def divider(title):
    """Print a section divider with title"""
    print(f"\n{'=' * 60}")
    print(f" 🔍 {title}")
    print(f"{'=' * 60}")

def demo_deduplication():
    """Demonstrate deduplication logic"""
    divider("DEDUPLICATION DEMO")
    
    # Try storing the same memory twice
    memory = {
        "text": "This is a test memory for deduplication demo",
        "tag": "preference"
    }
    
    print("Storing first memory...")
    response = requests.post(f"{BASE_URL}/memories", json=memory)
    first_result = response.json()
    print(f"Result: {json.dumps(first_result, indent=2)}")
    
    print("\nTrying to store exact same memory again...")
    response = requests.post(f"{BASE_URL}/memories", json=memory)
    second_result = response.json()
    print(f"Result: {json.dumps(second_result, indent=2)}")
    
    # Different tag, same text
    memory["tag"] = "value"
    print("\nTrying to store same text with different tag...")
    response = requests.post(f"{BASE_URL}/memories", json=memory)
    third_result = response.json()
    print(f"Result: {json.dumps(third_result, indent=2)}")
    
    # Slight variation of text
    memory["text"] = "This is a test memory for deduplication demo (variant)"
    memory["tag"] = "preference"
    print("\nTrying to store slightly different text...")
    response = requests.post(f"{BASE_URL}/memories", json=memory)
    fourth_result = response.json()
    print(f"Result: {json.dumps(fourth_result, indent=2)}")

def demo_positive_similarity():
    """Demonstrate positive similarity scores"""
    divider("POSITIVE SIMILARITY SCORES DEMO")
    
    print("Searching for 'What are the user's preferences?'")
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/memories/search", 
        json={"query": "What are the user's preferences?", "limit": 3}
    )
    duration = time.time() - start
    
    results = response.json()
    print(f"Found {len(results['results'])} results in {duration:.3f} seconds")
    
    for i, result in enumerate(results['results']):
        print(f"\nResult {i+1}:")
        print(f"  Text: {result['text']}")
        print(f"  Tag: {result['tag']}")
        print(f"  Similarity: {result['similarity']:.3f}")  # Should be positive!
        
    return results

def demo_performance():
    """Demonstrate search and response performance"""
    divider("PERFORMANCE METRICS DEMO")
    
    # Test queries with different complexity
    queries = [
        "What programming languages does the user know?",
        "What are the user's communication preferences?",
        "How does the user approach problem-solving?"
    ]
    
    for i, query in enumerate(queries):
        print(f"\nQuery {i+1}: '{query}'")
        
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/memories/search", 
            json={"query": query, "limit": 5}
        )
        duration = time.time() - start
        
        results = response.json()
        print(f"Found {len(results['results'])} results in {duration:.3f}s")
        
        if results['results']:
            top_result = results['results'][0]
            print(f"Top result: [{top_result['tag']}] {top_result['text']} (sim: {top_result['similarity']:.3f})")
    
    # Test tag filtering performance
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/memories/search", 
        json={"query": "anything", "tag_filter": "preference", "limit": 3}
    )
    tag_duration = time.time() - start
    
    print(f"\nTag filtered search completed in {tag_duration:.3f}s")

def check_memory_stats():
    """Get overall memory statistics"""
    divider("MEMORY SYSTEM STATS")
    
    # Check memory counts by tag
    counts = {}
    for tag in ["goal", "routine", "preference", "constraint", 
               "habit", "project", "tool", "identity", "value"]:
        response = requests.get(f"{BASE_URL}/memories?tag={tag}")
        if response.status_code == 200:
            counts[tag] = len(response.json()['memories'])
    
    print("Memory counts by tag:")
    for tag, count in counts.items():
        print(f"  {tag}: {count}")
    
    # Check server health
    response = requests.get(f"{BASE_URL}/health")
    print(f"\nServer health: {response.json()['status']}")

if __name__ == "__main__":
    print("🧠 Memory System v0 Quick Demo")
    
    # Run demos
    demo_deduplication()
    demo_positive_similarity()
    demo_performance()
    check_memory_stats()