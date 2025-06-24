"""
Direct Conflict Test

This script directly tests the core conflict detection logic 
by interacting with the Chroma DB directly, without requiring
any server to be running. This allows us to:

1. Verify conflict detection works at the DB level
2. Debug conflict set generation
3. Simulate the search workflow to confirm conflicts are properly surfaced

Run this script with the virtual environment activated.
"""

from sentence_transformers import SentenceTransformer
import chromadb
import json
from datetime import datetime
import hashlib
import time

# Initialize embedding model and vector store
print("Initializing models and database...")
model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="memories")

# Constants
SIMILARITY_THRESHOLD = 0.65  # Same threshold used in memory_server.py

def add_memory(text, tag, verbose=False):
    """Add a memory to the collection"""
    
    # Generate timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Check for duplicates 
    memory_text_normalized = text.strip().lower()
    memory_hash = hashlib.md5(f"{memory_text_normalized}:{tag}".encode()).hexdigest()
    
    # Generate embedding
    embedding = model.encode(text).tolist()
    
    # Create unique ID
    memory_id = f"mem_{int(datetime.utcnow().timestamp() * 1000)}"
    
    # Check for conflicts with existing memories (same tag, high similarity)
    conflicts = []
    if verbose:
        print(f"Checking for conflicts with similarity threshold {SIMILARITY_THRESHOLD}...")
    
    # Search for memories with same tag
    if collection.count() > 0:  # Skip conflict check for first memory
        # Use embedding to search for similar memories with same tag
        similar_results = collection.query(
            query_embeddings=[embedding],
            n_results=5,  # Check top 5 similar memories
            where={"tag": tag}
        )
        
        # Check if any meets similarity threshold
        if similar_results['distances'] and similar_results['distances'][0]:
            for i, distance in enumerate(similar_results['distances'][0]):
                # Convert distance to cosine similarity (1 - distance)
                similarity = 1 - distance
                if similarity > SIMILARITY_THRESHOLD:
                    similar_id = similar_results['ids'][0][i]
                    if verbose:
                        print(f"Found similar memory {similar_id} with similarity {similarity}")
                    conflicts.append(similar_id)
    
    # Prepare metadata
    metadata = {
        "tag": tag,
        "timestamp": timestamp,
        "last_accessed": timestamp,
        "hash": memory_hash
    }
    
    # Add conflict metadata if conflicts found
    if conflicts:
        metadata["has_conflicts"] = True
        metadata["conflict_ids"] = json.dumps(conflicts)
        
        # Update metadata of conflicting memories to reference this one
        for conflict_id in conflicts:
            conflict_metadata = collection.get(ids=[conflict_id])['metadatas'][0]
            
            # Get existing conflicts or initialize empty array
            existing_conflicts = []
            if "has_conflicts" in conflict_metadata and "conflict_ids" in conflict_metadata:
                existing_conflicts = json.loads(conflict_metadata["conflict_ids"])
            
            # Add this memory to the conflicts
            existing_conflicts.append(memory_id)
            
            # Update conflict metadata
            conflict_metadata["has_conflicts"] = True
            conflict_metadata["conflict_ids"] = json.dumps(existing_conflicts)
            
            # Update in collection
            collection.update(
                ids=[conflict_id],
                metadatas=[conflict_metadata]
            )
            
            if verbose:
                print(f"Updated conflict metadata for {conflict_id}")
    
    # Store the memory
    collection.add(
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata],
        ids=[memory_id]
    )
    
    if verbose:
        print(f"Added memory {memory_id}: {text} (tag: {tag})")
        if conflicts:
            print(f"Memory has conflicts with: {conflicts}")
    
    return memory_id

def search_memories(query, limit=5, tag_filter=None, verbose=False):
    """Search memories by query text"""
    
    if verbose:
        print(f"Searching for '{query}' with tag filter '{tag_filter}'")
    
    # Generate embedding for query
    query_embedding = model.encode(query).tolist()
    
    # Prepare where clause for tag filtering
    where_clause = None
    if tag_filter:
        where_clause = {"tag": tag_filter}
    
    # Search collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where=where_clause
    )
    
    # Process results
    memories = []
    conflict_sets = {}
    
    if verbose:
        print(f"Found {len(results['ids'][0])} results")
    
    if results['ids']:
        for i, memory_id in enumerate(results['ids'][0]):
            distance = results['distances'][0][i]
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            
            # Convert distance to similarity
            similarity = 1 - distance
            
            # Create memory response object
            memory = {
                "id": memory_id,
                "text": document,
                "tag": metadata['tag'],
                "timestamp": metadata['timestamp'],
                "similarity": similarity,
                "last_accessed": metadata.get('last_accessed', metadata['timestamp'])
            }
            
            memories.append(memory)
            
            # Check for conflicts
            if metadata.get('has_conflicts', False) and 'conflict_ids' in metadata:
                if verbose:
                    print(f"Memory {memory_id} has conflicts")
                
                conflict_ids = json.loads(metadata['conflict_ids'])
                
                # Create conflict set
                conflict_sets[memory_id] = [memory]
                
                # Get conflicting memories
                for conflict_id in conflict_ids:
                    conflict_result = collection.get(ids=[conflict_id])
                    
                    if conflict_result['ids']:
                        conflict_metadata = conflict_result['metadatas'][0]
                        conflict_document = conflict_result['documents'][0]
                        
                        conflict_memory = {
                            "id": conflict_id,
                            "text": conflict_document,
                            "tag": conflict_metadata['tag'],
                            "timestamp": conflict_metadata['timestamp'],
                            "last_accessed": conflict_metadata.get('last_accessed', conflict_metadata['timestamp'])
                        }
                        
                        conflict_sets[memory_id].append(conflict_memory)
            
            # Update last_accessed timestamp
            current_time = datetime.utcnow().isoformat() + "Z"
            metadata["last_accessed"] = current_time
            collection.update(ids=[memory_id], metadatas=[metadata])
    
    # Build response
    response = {
        "query": query,
        "results": memories,
        "count": len(memories)
    }
    
    if conflict_sets:
        if verbose:
            print(f"Found {len(conflict_sets)} conflict sets")
            for key, conflicts in conflict_sets.items():
                print(f"  - Conflict set for {key}: {len(conflicts)} conflicts")
                for conflict in conflicts:
                    print(f"      '{conflict['text']}' ({conflict['id']})")
        
        response["conflict_sets"] = conflict_sets
    
    return response

def run_conflict_test():
    """Run a test of the conflict detection and surfacing"""
    print("\n=== Running Direct Conflict Test ===\n")
    
    print("Step 1: Adding test memories with conflicts...")
    
    # Clear any test memories from previous runs
    print("\nStep 2: Adding conflicting communication preferences...")
    mem1 = add_memory("Prefers fast, blunt communication without fluff", "preference", verbose=True)
    
    # Short pause between adds
    time.sleep(0.5)
    
    mem2 = add_memory("Likes to communicate with lots of detail and explanation", "preference", verbose=True)
    
    print("\nStep 3: Adding non-conflicting memories...")
    mem3 = add_memory("Works on coding projects in Python and JavaScript", "project", verbose=True)
    
    print("\nStep 4: Searching for communication preferences (with conflicts)...")
    search_results = search_memories(
        "How does the user prefer to communicate?", 
        limit=5,
        verbose=True
    )
    
    print("\n=== Search Results ===")
    print(json.dumps(search_results, indent=2))
    
    print("\nStep 5: Searching for projects (without conflicts)...")
    project_results = search_memories(
        "What coding projects does the user work on?", 
        limit=5,
        verbose=True
    )
    
    print("\n=== Project Search Results ===")
    print(json.dumps(project_results, indent=2))
    
    return search_results, project_results

if __name__ == "__main__":
    search_results, project_results = run_conflict_test()
    
    # Final summary
    print("\n=== Test Summary ===")
    
    conflict_test = "conflict_sets" in search_results and len(search_results["conflict_sets"]) > 0
    print(f"Conflict Detection: {'✅ PASS' if conflict_test else '❌ FAIL'}")
    
    if not conflict_test:
        print("\n⚠️ Conflict sets not detected in search results.")
        print("Debugging suggestions:")
        print("1. Check similarity threshold (currently {SIMILARITY_THRESHOLD})")
        print("2. Verify conflict metadata is being properly stored")
        print("3. Confirm conflict_sets are being included in the response")
    else:
        print(f"✅ Successfully detected {len(search_results['conflict_sets'])} conflict sets")
        
        # Show the conflicting memories
        for key, conflicts in search_results["conflict_sets"].items():
            print(f"\nConflict set for '{key}':")
            for conflict in conflicts:
                print(f"- '{conflict['text']}' ({conflict['id']})")
        
        print("\n🎉 Conflict detection is working correctly!")
