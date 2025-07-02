"""
Manual Conflict Detection API Test

This script tests the conflict detection logic by directly using the core functions from memory_server.py
without running the actual server. This bypasses any port conflict issues.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import from memory_server.py
sys.path.append(str(Path(__file__).parent))

# Import functions from memory_server.py
from sentence_transformers import SentenceTransformer
import chromadb
from memory_server import MemoryItem, SearchRequest  # Import models
import memory_server  # Import the module

# Helper function to print results nicely
def print_formatted_json(data):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2))

def test_conflict_detection():
    """Test conflict detection in memory_server.py directly"""
    print("\n===== Testing Conflict Detection =====\n")
    
    # Initialize memory server components (same as in memory_server.py)
    print("Initializing models and database...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="memories")
    
    # Create two conflicting memories
    print("\nStep 1: Creating conflicting memories...")
    
    # First memory
    memory1 = MemoryItem(
        text="Prefers direct and concise communication",
        tag="preference"
    )
    
    # Add first memory
    print("\nAdding first memory...")
    result1 = memory_server.add_memory(memory1, model, collection)
    print(f"Memory 1 result: {result1}")
    
    # Second memory - potentially conflicting
    memory2 = MemoryItem(
        text="Likes detailed explanations with examples",
        tag="preference"  # Same tag, conflicting content
    )
    
    # Add second memory
    print("\nAdding second memory...")
    result2 = memory_server.add_memory(memory2, model, collection)
    print(f"Memory 2 result: {result2}")
    
    # Create a neutral memory with different tag
    memory3 = MemoryItem(
        text="Works on Python and JavaScript projects",
        tag="project"
    )
    
    # Add neutral memory
    print("\nAdding neutral memory (different tag)...")
    result3 = memory_server.add_memory(memory3, model, collection)
    print(f"Memory 3 result: {result3}")
    
    # Search for communication preferences
    print("\nStep 2: Searching for communication preferences (should find conflicts)...")
    search_request = SearchRequest(
        query="How does the user prefer to communicate?",
        limit=10,
        tags=["preference"]  # Optional: filter by tag
    )
    
    # Perform search
    search_result = memory_server.search_memories(search_request, model, collection)
    print("\nSearch Results (Communication Preferences):")
    print_formatted_json(search_result)
    
    # Check for conflict sets
    if "conflict_sets" in search_result:
        print(f"\n✅ SUCCESS: Found {len(search_result['conflict_sets'])} conflict sets")
        for key, conflicts in search_result["conflict_sets"].items():
            print(f"\nConflict set for '{key}':")
            for conflict in conflicts:
                print(f"- '{conflict['text']}' (tag: {conflict['tag']})")
    else:
        print("\n❌ FAILURE: No conflict sets found in search results")
        print("Debug info:")
        for result in search_result["results"]:
            print(f"- {result['id']}: '{result['text']}', tag: {result['tag']}")
            
            # Check metadata manually
            metadata_result = collection.get(ids=[result['id']])
            metadata = metadata_result['metadatas'][0] if metadata_result['metadatas'] else {}
            print(f"  Metadata: has_conflicts={metadata.get('has_conflicts', False)}")
            if 'conflict_ids' in metadata:
                print(f"  Conflict IDs: {metadata['conflict_ids']}")
    
    # Search for projects
    print("\nStep 3: Searching for projects (should NOT find conflicts)...")
    project_request = SearchRequest(
        query="What projects does the user work on?",
        limit=10,
        tags=["project"]  # Optional: filter by tag
    )
    
    # Perform projects search
    project_result = memory_server.search_memories(project_request, model, collection)
    print("\nSearch Results (Projects):")
    print_formatted_json(project_result)
    
    return search_result, project_result

if __name__ == "__main__":
    test_conflict_detection()
