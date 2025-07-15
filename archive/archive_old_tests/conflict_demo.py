"""
Conflict Detection Demo

This script demonstrates the core conflict detection logic for memory systems.
It uses direct ChromaDB and SentenceTransformers access rather than FastAPI.
"""
from sentence_transformers import SentenceTransformer
import chromadb
from datetime import datetime
import json
import time
import hashlib

# Initialize embedding model and vector store
print("Initializing model and ChromaDB...")
model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="memories")

def clear_text():
    """Clear console text for better readability"""
    print("\033c", end="")

def print_header(text):
    """Print a formatted header"""
    print(f"\n\033[1;36m{text}\033[0m")
    print("=" * 50)

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))

def store_memory(text, tag):
    """Store a memory with conflict detection"""
    # Generate timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Generate embedding
    embedding = model.encode(text).tolist()
    
    # Generate memory ID
    memory_id = f"mem_{int(datetime.utcnow().timestamp() * 1000)}"
    
    # Check for conflicts with existing memories (same tag, high similarity)
    print(f"Checking for conflicts with tag '{tag}' and similarity threshold 0.65...")
    conflicts = []
    SIMILARITY_THRESHOLD = 0.65
    
    # Search for memories with same tag
    if collection.count() > 0:  # Skip conflict check for first memory
        similar_results = collection.query(
            query_embeddings=[embedding],
            n_results=5,
            where={"tag": tag}
        )
        
        if similar_results['distances'] and similar_results['distances'][0]:
            for i, distance in enumerate(similar_results['distances'][0]):
                # Convert distance to similarity (0-1 range)
                similarity = max(0, 1 - (distance / 2))
                conflict_id = similar_results['ids'][0][i]
                conflict_text = similar_results['documents'][0][i]
                print(f"Similarity with '{conflict_text}': {similarity:.4f}")
                
                if similarity >= SIMILARITY_THRESHOLD:
                    print(f"CONFLICT DETECTED: {conflict_id} (similarity: {similarity:.4f})")
                    conflicts.append(conflict_id)
    
    # Set last_accessed timestamp
    current_time = datetime.utcnow().isoformat() + "Z"
    
    # Prepare metadata with conflict info if any
    metadata = {
        "tag": tag,
        "timestamp": timestamp,
        "last_accessed": current_time,
        "hash": hashlib.md5(f"{text.strip().lower()}:{tag}".encode()).hexdigest()
    }
    
    # Add conflict flags and IDs if conflicts exist
    if conflicts:
        print(f"Adding conflict metadata for {len(conflicts)} conflicts")
        metadata["has_conflicts"] = True
        metadata["conflict_ids"] = json.dumps(conflicts)
        
        # Update the conflicting memories to point back to this one
        for conflict_id in conflicts:
            # Get existing metadata for the conflict
            conflict_result = collection.get(ids=[conflict_id])
            if conflict_result['metadatas'] and conflict_result['metadatas'][0]:
                conflict_metadata = conflict_result['metadatas'][0]
                
                # Update conflict info
                conflict_metadata["has_conflicts"] = True
                
                # Add this memory ID to the conflict's list of conflicts
                if "conflict_ids" in conflict_metadata:
                    existing_conflicts = json.loads(conflict_metadata["conflict_ids"])
                    if memory_id not in existing_conflicts:
                        existing_conflicts.append(memory_id)
                        conflict_metadata["conflict_ids"] = json.dumps(existing_conflicts)
                else:
                    conflict_metadata["conflict_ids"] = json.dumps([memory_id])
                
                print(f"Updating conflict metadata for {conflict_id}")
                # Update the conflict's metadata
                collection.update(ids=[conflict_id], metadatas=[conflict_metadata])
    
    # Store in Chroma
    collection.add(
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata],
        ids=[memory_id]
    )
    
    return {
        "id": memory_id,
        "text": text,
        "tag": tag,
        "timestamp": timestamp,
        "has_conflicts": len(conflicts) > 0,
        "conflict_ids": conflicts if conflicts else None
    }

def get_memory(memory_id):
    """Get a specific memory by ID with conflicts"""
    results = collection.get(ids=[memory_id])
    
    if not results['documents']:
        return {"error": "Memory not found"}
    
    metadata = results['metadatas'][0]
    
    # Update last_accessed timestamp
    current_time = datetime.utcnow().isoformat() + "Z"
    metadata["last_accessed"] = current_time
    collection.update(ids=[memory_id], metadatas=[metadata])
    
    response = {
        "id": memory_id,
        "text": results['documents'][0],
        "tag": metadata['tag'],
        "timestamp": metadata['timestamp'],
        "last_accessed": current_time
    }
    
    # Check if this memory has conflicts
    if "has_conflicts" in metadata and metadata["has_conflicts"] and "conflict_ids" in metadata:
        conflict_ids = json.loads(metadata["conflict_ids"])
        conflict_set = [response.copy()]
        
        # Fetch all conflicting memories
        for conflict_id in conflict_ids:
            conflict_result = collection.get(ids=[conflict_id])
            if conflict_result['documents'] and conflict_result['documents'][0]:
                conflict_metadata = conflict_result['metadatas'][0]
                
                conflict_memory = {
                    "id": conflict_id,
                    "text": conflict_result['documents'][0],
                    "tag": conflict_metadata['tag'],
                    "timestamp": conflict_metadata['timestamp'],
                    "last_accessed": conflict_metadata.get('last_accessed', conflict_metadata['timestamp'])
                }
                
                conflict_set.append(conflict_memory)
        
        response["conflict_set"] = conflict_set
    
    return response

def search_memories(query, tag_filter=None, limit=5):
    """Search memories by query text"""
    query_embedding = model.encode(query).tolist()
    
    # Build where clause for tag filtering
    where_clause = None
    if tag_filter:
        where_clause = {"tag": tag_filter}
    
    # Search in Chroma
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where=where_clause
    )
    
    # Format response
    memories = []
    conflict_sets = {}
    
    if results['documents'] and results['documents'][0]:
        # First pass - create all memories
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            memory_id = results['ids'][0][i]
            
            # Update last_accessed timestamp
            current_time = datetime.utcnow().isoformat() + "Z"
            metadata["last_accessed"] = current_time
            collection.update(ids=[memory_id], metadatas=[metadata])
            
            memory = {
                "id": memory_id,
                "text": doc,
                "tag": metadata['tag'],
                "timestamp": metadata['timestamp'],
                "last_accessed": current_time,
                "similarity": max(0, 1 - (results['distances'][0][i] / 2))
            }
            memories.append(memory)
            
            # Check for conflicts and build conflict sets
            if "has_conflicts" in metadata and metadata["has_conflicts"]:
                # This memory has conflicts, retrieve the conflict IDs
                conflict_ids = json.loads(metadata.get("conflict_ids", "[]"))
                
                # Create or update conflict set for this memory
                if memory_id not in conflict_sets:
                    conflict_sets[memory_id] = [memory.copy()]
                
                # Fetch and add conflicting memories if not already in results
                for conflict_id in conflict_ids:
                    if conflict_id not in [m["id"] for m in memories]:
                        conflict_result = collection.get(ids=[conflict_id])
                        if conflict_result['documents'] and conflict_result['documents'][0]:
                            conflict_metadata = conflict_result['metadatas'][0]
                            
                            conflict_memory = {
                                "id": conflict_id,
                                "text": conflict_result['documents'][0],
                                "tag": conflict_metadata['tag'],
                                "timestamp": conflict_metadata['timestamp'],
                                "last_accessed": conflict_metadata.get('last_accessed', conflict_metadata['timestamp'])
                            }
                            
                            # Add to conflict set
                            conflict_sets[memory_id].append(conflict_memory)
    
    # Build final response
    response = {
        "query": query,
        "results": memories,
        "count": len(memories)
    }
    
    # Add conflict sets if any exist
    if conflict_sets:
        response["conflict_sets"] = conflict_sets
    
    return response

def main():
    """Run the conflict detection demo"""
    clear_text()
    print_header("🔍 CONFLICT DETECTION DEMO")
    
    # Add first memory
    print_header("Step 1: Adding a preference memory")
    current_time = datetime.utcnow().isoformat()
    memory1 = store_memory(
        f"I prefer working at night (demo: {current_time})",
        "preference"
    )
    print("Response:")
    print_json(memory1)
    first_memory_id = memory1["id"]
    
    time.sleep(1)  # Short pause
    
    # Add conflicting memory
    print_header("Step 2: Adding a conflicting memory")
    memory2 = store_memory(
        f"I prefer working in the mornings (demo: {current_time})",
        "preference"
    )
    print("Response:")
    print_json(memory2)
    second_memory_id = memory2["id"]
    
    time.sleep(1)  # Short pause
    
    # Get first memory to check conflict_set
    print_header("Step 3: Retrieving first memory to check for conflict_set")
    memory1_result = get_memory(first_memory_id)
    print("First memory with conflicts:")
    print_json(memory1_result)
    
    # Search memories
    print_header("Step 4: Searching for memories")
    time_marker = current_time.split("T")[1][:8]  # Extract time portion (HH:MM:SS)
    search_results = search_memories(
        f"When do I work best? {time_marker}",
        tag_filter="preference", 
        limit=5
    )
    print("Search results:")
    print_json(search_results)
    
    # Print conclusion
    print_header("Test Results")
    
    if "conflict_set" in memory1_result:
        print("✅ Direct memory retrieval correctly includes conflict_set")
        print(f"   Found {len(memory1_result['conflict_set'])} memories in conflict set")
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
