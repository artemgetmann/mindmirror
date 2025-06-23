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

class MemoryItem(BaseModel):
    text: str
    tag: str
    timestamp: Optional[str] = None

class MemoryResponse(BaseModel):
    id: str
    text: str
    tag: str
    timestamp: str
    similarity: Optional[float] = None

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
    
    # Store in Chroma
    collection.add(
        embeddings=[embedding],
        documents=[memory.text],
        metadatas=[{
            "tag": memory.tag,
            "timestamp": memory.timestamp,
            "hash": memory_hash  # Store hash for future reference
        }],
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
    if results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            memory = MemoryResponse(
                id=results['ids'][0][i],
                text=doc,
                tag=results['metadatas'][0][i]['tag'],
                timestamp=results['metadatas'][0][i]['timestamp'],
                # Fix similarity calculation (cosine_distance → cosine_similarity):
                # distance is [0-2] where 0 is identical, 2 is opposite
                # normalize to proper similarity score in [0-1] range where 1 is identical
                similarity=max(0, 1 - (results['distances'][0][i] / 2))
            )
            memories.append(memory)
    
    return {
        "query": request.query,
        "results": memories,
        "count": len(memories)
    }

@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory by ID"""
    
    results = collection.get(ids=[memory_id])
    
    if not results['documents']:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return MemoryResponse(
        id=memory_id,
        text=results['documents'][0],
        tag=results['metadatas'][0]['tag'],
        timestamp=results['metadatas'][0]['timestamp']
    )

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
            memory = MemoryResponse(
                id=results['ids'][i],
                text=doc,
                tag=results['metadatas'][i]['tag'],
                timestamp=results['metadatas'][i]['timestamp']
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
            "GET /memories": "List all memories"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)