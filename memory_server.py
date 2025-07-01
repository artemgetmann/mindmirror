"""
Minimal Viable Memory System (v0)
Cloud-based vector memory with FastAPI + SentenceTransformers + Chroma
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
from datetime import datetime
from typing import List, Optional
import json
import os
import hashlib
from datetime import datetime, timedelta

app = FastAPI(title="Memory System v0")

# Initialize embedding model and vector store
model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="memories")

# Create memory hash cache for deduplication
memory_hashes = set()

# Load existing memory hashes on startup
try:
    existing_memories = collection.get()
    if existing_memories and 'metadatas' in existing_memories and existing_memories['metadatas']:
        for metadata in existing_memories['metadatas']:
            if 'hash' in metadata:
                memory_hashes.add(metadata['hash'])
            else:
                # For backwards compatibility with memories stored before hash implementation
                text = existing_memories['documents'][existing_memories['metadatas'].index(metadata)].strip().lower()
                tag = metadata['tag']
                memory_hash = hashlib.md5(f"{text}:{tag}".encode()).hexdigest()
                memory_hashes.add(memory_hash)
                
    print(f"Loaded {len(memory_hashes)} memory hashes for deduplication")
except Exception as e:
    print(f"Error loading memory hashes: {e}")

# Fixed tag set
VALID_TAGS = [
    "goal", "routine", "preference", "constraint", 
    "habit", "project", "tool", "identity", "value"
]

# Constants for pruning logic
ARCHIVE_AGE_DAYS = 90  # Archive memories older than 90 days
ACCESS_THRESHOLD_DAYS = 30  # Archive if not accessed in last 30 days
CORE_TAGS = ["identity", "value"]  # Never prune these core memories
SIMILARITY_THRESHOLD = 0.65  # Threshold for conflict detection

class MemoryItem(BaseModel):
    text: str
    tag: str
    timestamp: Optional[str] = None
    last_accessed: Optional[str] = None

class MemoryResponse(BaseModel):
    id: str
    text: str
    tag: str
    timestamp: str
    similarity: Optional[float] = None
    last_accessed: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    tag_filter: Optional[str] = None

@app.post("/memories")
async def store_memory(memory: MemoryItem):
    """Store a new memory item"""
    
    # Validate tag
    if memory.tag not in VALID_TAGS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid tag. Must be one of: {VALID_TAGS}"
        )
    
    # Generate timestamp if not provided
    if not memory.timestamp:
        memory.timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Check for duplicates using hash of text+tag
    memory_text_normalized = memory.text.strip().lower()
    memory_hash = hashlib.md5(f"{memory_text_normalized}:{memory.tag}".encode()).hexdigest()
    
    if memory_hash in memory_hashes:
        # Memory already exists, return without storing
        return {
            "status": "skipped",
            "reason": "duplicate",
            "text": memory.text,
            "tag": memory.tag
        }
    
    # Add to hash set
    memory_hashes.add(memory_hash)
    
    # Generate embedding
    embedding = model.encode(memory.text).tolist()
    
    # Create unique ID
    memory_id = f"mem_{int(datetime.utcnow().timestamp() * 1000)}"
    
    # Check for conflicts with existing memories (same tag, high similarity)
    conflicts = []
    SIMILARITY_THRESHOLD = 0.65  # Lowered threshold for potential conflicts - was 0.8 initially
    print(f"Checking for conflicts with similarity threshold {SIMILARITY_THRESHOLD}...")
    
    # Search for memories with same tag
    if collection.count() > 0:  # Skip conflict check for first memory
        # Use embedding to search for similar memories with same tag
        similar_results = collection.query(
            query_embeddings=[embedding],
            n_results=5,  # Check top 5 similar memories
            where={"tag": memory.tag}
        )
        
        # Check if any meets similarity threshold
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
    last_accessed = memory.last_accessed or current_time
    
    # Prepare metadata with conflict info if any
    metadata = {
        "tag": memory.tag,
        "timestamp": memory.timestamp,
        "hash": memory_hash,  # Store hash for future reference
        "last_accessed": last_accessed
    }
    
    # Add conflict flags and IDs if conflicts exist
    if conflicts:
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
                
                # Update the conflict's metadata
                collection.update(ids=[conflict_id], metadatas=[conflict_metadata])
    
    # Store in Chroma
    collection.add(
        embeddings=[embedding],
        documents=[memory.text],
        metadatas=[metadata],
        ids=[memory_id]
    )
    
    return {
        "id": memory_id,
        "text": memory.text,
        "tag": memory.tag,
        "timestamp": memory.timestamp,
        "status": "stored"
    }

@app.post("/memories/search")
async def search_memories(request: SearchRequest):
    """Search memories by query text"""
    
    # Generate query embedding
    query_embedding = model.encode(request.query).tolist()
    
    # Build where clause for tag filtering
    where_clause = None
    if request.tag_filter:
        if request.tag_filter not in VALID_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tag filter. Must be one of: {VALID_TAGS}"
            )
        where_clause = {"tag": request.tag_filter}
    
    # Search in Chroma
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=request.limit,
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
            
            memory = MemoryResponse(
                id=memory_id,
                text=doc,
                tag=metadata['tag'],
                timestamp=metadata['timestamp'],
                last_accessed=current_time,
                # Fix similarity calculation (cosine_distance → cosine_similarity):
                # distance is [0-2] where 0 is identical, 2 is opposite
                # normalize to proper similarity score in [0-1] range where 1 is identical
                similarity=max(0, 1 - (results['distances'][0][i] / 2))
            )
            memories.append(memory)
            
            # Check for conflicts and build conflict sets
            if "has_conflicts" in metadata and metadata["has_conflicts"]:
                # This memory has conflicts, retrieve the conflict IDs
                conflict_ids = json.loads(metadata.get("conflict_ids", "[]"))
                
                # Create or update conflict set for this memory
                if memory_id not in conflict_sets:
                    conflict_sets[memory_id] = [dict(memory)]
                
                # Fetch and add conflicting memories if not already in results
                for conflict_id in conflict_ids:
                    if conflict_id not in [m['id'] if isinstance(m, dict) else m.id for m in memories]:
                        conflict_result = collection.get(ids=[conflict_id])
                        if conflict_result['documents'] and conflict_result['documents'][0]:
                            conflict_metadata = conflict_result['metadatas'][0]
                            
                            conflict_memory = MemoryResponse(
                                id=conflict_id,
                                text=conflict_result['documents'][0],
                                tag=conflict_metadata['tag'],
                                timestamp=conflict_metadata['timestamp'],
                                last_accessed=conflict_metadata.get('last_accessed', conflict_metadata['timestamp'])
                            )
                            
                            # Add to conflict set
                            conflict_sets[memory_id].append(dict(conflict_memory))
    
    # Build final response
    response = {
        "query": request.query,
        "results": memories,
        "count": len(memories)
    }
    
    # Debug: print conflict detection information
    print(f"\nDEBUG: Found {len(results['ids'])} results total")
    print(f"DEBUG: Built {len(memories)} memory responses")
    print(f"DEBUG: Identified {len(conflict_sets)} conflict sets")
    
    # Add conflict sets if any exist
    if conflict_sets:
        print(f"DEBUG: Adding conflict sets to response: {conflict_sets}")
        response["conflict_sets"] = conflict_sets
    else:
        # Manually check for conflicts among the returned results
        print("DEBUG: No conflict sets detected, performing manual conflict check")
        manual_conflict_sets = {}
        
        # Check each memory for conflicts
        for memory in memories:
            memory_id = memory['id']
            metadata_result = collection.get(ids=[memory_id])
            
            if metadata_result['metadatas'] and len(metadata_result['metadatas']) > 0:
                metadata = metadata_result['metadatas'][0]
                
                if metadata.get('has_conflicts', False) and 'conflict_ids' in metadata:
                    conflict_ids = json.loads(metadata['conflict_ids'])
                    print(f"DEBUG: Memory {memory_id} has conflicts with: {conflict_ids}")
                    
                    # Create conflict set
                    if memory_id not in manual_conflict_sets:
                        manual_conflict_sets[memory_id] = [memory]
                    
                    # Add conflicting memories
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
                            
                            manual_conflict_sets[memory_id].append(conflict_memory)
        
        # Add manual conflict sets to response
        if manual_conflict_sets:
            print(f"DEBUG: Adding manually detected conflict sets: {list(manual_conflict_sets.keys())}")
            response["conflict_sets"] = manual_conflict_sets
    
    return response

@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory by ID"""
    
    results = collection.get(ids=[memory_id])
    
    if not results['documents']:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    metadata = results['metadatas'][0]
    
    # Update last_accessed timestamp
    current_time = datetime.utcnow().isoformat() + "Z"
    metadata["last_accessed"] = current_time
    collection.update(ids=[memory_id], metadatas=[metadata])
    
    memory = MemoryResponse(
        id=memory_id,
        text=results['documents'][0],
        tag=metadata['tag'],
        timestamp=metadata['timestamp'],
        last_accessed=current_time
    )
    
    response_data = dict(memory)
    
    # Check if this memory has conflicts
    if "has_conflicts" in metadata and metadata["has_conflicts"] and "conflict_ids" in metadata:
        conflict_ids = json.loads(metadata["conflict_ids"])
        conflict_set = [response_data]
        
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
        
        response_data["conflict_set"] = conflict_set
    
    return response_data

@app.get("/memories")
async def list_memories(tag: Optional[str] = None, limit: int = 10):
    """List all memories, optionally filtered by tag"""
    
    where_clause = None
    if tag:
        if tag not in VALID_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tag. Must be one of: {VALID_TAGS}"
            )
        where_clause = {"tag": tag}
    
    results = collection.get(where=where_clause, limit=limit)
    
    memories = []
    if results['documents']:
        for i, doc in enumerate(results['documents']):
            metadata = results['metadatas'][i]
            memory = MemoryResponse(
                id=results['ids'][i],
                text=doc,
                tag=metadata['tag'],
                timestamp=metadata['timestamp'],
                last_accessed=metadata.get('last_accessed', metadata['timestamp'])
            )
            memories.append(memory)
    
    return {
        "memories": memories,
        "count": len(memories)
    }

@app.get("/")
async def root():
    return {
        "message": "Memory System v0",
        "valid_tags": VALID_TAGS,
        "endpoints": {
            "POST /memories": "Store a memory",
            "POST /memories/search": "Search memories",
            "GET /memories/{id}": "Get specific memory",
            "GET /memories": "List all memories",
            "GET /memories/prune": "Identify and archive old unused memories"
        },
        "features": {
            "deduplication": "Prevents storing exact duplicates (text+tag)",
            "conflict_detection": "Identifies similar memories with same tag that might conflict (cosine sim > 0.65)",
            "conflict_sets": "Groups potentially conflicting memories for client-side resolution",
            "pruning": "Archives old, unused, non-core memories (age > 90 days, not accessed in 30 days)"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/memories/prune")
async def prune_memories():
    """Identify memories for pruning based on age, access time, and importance"""
    
    now = datetime.utcnow()
    archive_cutoff = now - timedelta(days=ARCHIVE_AGE_DAYS)
    access_cutoff = now - timedelta(days=ACCESS_THRESHOLD_DAYS)
    
    # Format cutoff dates for display
    cutoff_info = {
        "archive_cutoff": archive_cutoff.isoformat() + "Z",
        "access_cutoff": access_cutoff.isoformat() + "Z",
        "archive_age_days": ARCHIVE_AGE_DAYS,
        "access_threshold_days": ACCESS_THRESHOLD_DAYS,
        "core_tags": CORE_TAGS
    }
    
    # Get all memories
    results = collection.get()
    memories = []
    
    # Split into categories
    to_prune = []
    kept = []
    
    if results['documents']:
        for i, doc in enumerate(results['documents']):
            memory_id = results['ids'][i]
            metadata = results['metadatas'][i]
            
            memory = {
                "id": memory_id,
                "text": doc,
                "tag": metadata['tag'],
                "timestamp": metadata['timestamp'],
                "last_accessed": metadata.get('last_accessed', metadata['timestamp'])
            }
            memories.append(memory)
            
            # Skip core memories
            if metadata['tag'] in CORE_TAGS:
                kept.append(memory)
                continue
            
            # Check timestamp
            timestamp = datetime.fromisoformat(metadata["timestamp"].rstrip("Z"))
            
            # Check last_accessed (if available)
            last_accessed = None
            if "last_accessed" in metadata:
                last_accessed = datetime.fromisoformat(metadata["last_accessed"].rstrip("Z"))
            else:
                # If no last_accessed, use timestamp
                last_accessed = timestamp
            
            # Apply pruning logic
            if timestamp < archive_cutoff and last_accessed < access_cutoff:
                # Mark for pruning
                to_prune.append(memory)
                
                # Update metadata to indicate archived status
                metadata["archived"] = True
                metadata["archive_date"] = datetime.utcnow().isoformat() + "Z"
                metadata["archive_reason"] = "age_and_access"
                
                # Update metadata in collection
                collection.update(
                    ids=[memory_id],
                    metadatas=[metadata]
                )
            else:
                kept.append(memory)
    
    # Return pruning results
    return {
        "cutoff_info": cutoff_info,
        "total_memories": len(memories),
        "pruned_count": len(to_prune),
        "kept_count": len(kept),
        "pruned_memories": to_prune
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)