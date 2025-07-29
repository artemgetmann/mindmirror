"""
Minimal Viable Memory System (v0)
Cloud-based vector memory with FastAPI + SentenceTransformers + Chroma
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from datetime import datetime
from typing import List, Optional
import json
import os
import hashlib
from datetime import datetime, timedelta, timezone
import numpy as np
from numpy.linalg import norm
import psycopg2
import psycopg2.extras
import secrets
from contextlib import asynccontextmanager
import logging

# Set up logging
log_dir = '/app/logs' if os.path.exists('/app') else './logs'
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/memory_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
DB_CONFIG = {
    'host': 'aws-0-us-east-1.pooler.supabase.com',
    'database': 'postgres',
    'user': 'postgres.kpwadlfqqjgnpuiynmbe',
    'password': 'zekQob-byfgep-fyrqy3',
    'port': 6543,
    'sslmode': 'require'
}
security = HTTPBearer(auto_error=False)

# Database initialization
def init_auth_db():
    """Initialize authentication database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id SERIAL PRIMARY KEY,
            token TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            user_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT true,
            is_admin BOOLEAN DEFAULT false
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_token ON auth_tokens(token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_active ON auth_tokens(is_active)")
    
    # Add is_admin column if it doesn't exist (for existing databases)
    cursor.execute("""
        ALTER TABLE auth_tokens 
        ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false
    """)
    
    # Create waitlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waitlist_emails (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            token_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (token_used) REFERENCES auth_tokens(token)
        )
    """)
    
    # Create default token if none exists
    cursor.execute("SELECT COUNT(*) FROM auth_tokens WHERE is_active = true")
    if cursor.fetchone()[0] == 0:
        default_token = secrets.token_urlsafe(32)
        cursor.execute("""
            INSERT INTO auth_tokens (token, user_id, user_name) 
            VALUES (%s, %s, %s)
        """, (default_token, "default_user", "Default User"))
        
        logger.info(f"🔑 DEFAULT TOKEN CREATED: {default_token}")
        logger.info(f"🔗 Use this URL: http://localhost:{os.getenv('MEMORY_SERVER_PORT', '8001')}/memories?token={default_token}")
        # Also write to file for local development
        with open("/tmp/auth_token.txt", "w") as f:
            f.write(default_token)
    
    conn.commit()
    cursor.close()
    conn.close()

# Initialize auth database
init_auth_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Memory Server starting up...")
    yield
    # Shutdown
    logger.info("🛑 Memory Server shutting down...")

app = FastAPI(title="Memory System v0", lifespan=lifespan)

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:5174",  # Alternative dev port
    "http://localhost:8081",  # Frontend dev server
    "https://usemindmirror.com",  # Production domain
    "https://www.usemindmirror.com",  # Production with www
    "https://memory.usemindmirror.com",  # Memory subdomain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embedding model (pre-downloaded during build)
logger.info("🔄 Loading pre-downloaded embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create memory hash cache for deduplication
memory_hashes = set()

# Load existing memory hashes on startup
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT metadata->>'hash' as hash FROM memories WHERE metadata->>'hash' IS NOT NULL")
    hashes = cursor.fetchall()
    for (hash_val,) in hashes:
        memory_hashes.add(hash_val)
    cursor.close()
    conn.close()
    logger.info(f"Loaded {len(memory_hashes)} memory hashes for deduplication")
except Exception as e:
    logger.error(f"Error loading memory hashes: {e}")

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

# Authentication functions
def get_user_from_token(token: str) -> Optional[str]:
    """Get user_id from token"""
    logger.info(f"Validating token: {token[:10]}...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id FROM auth_tokens 
            WHERE token = %s AND is_active = true
        """, (token,))
        
        result = cursor.fetchone()
        
        if result:
            # Update last_used timestamp
            cursor.execute("""
                UPDATE auth_tokens 
                SET last_used = CURRENT_TIMESTAMP 
                WHERE token = %s
            """, (token,))
            conn.commit()
            logger.info(f"Token validated successfully for user: {result[0]}")
        else:
            logger.warning(f"Token validation failed for token: {token[:10]}...")
        
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Database error during token validation: {e}")
        return None

def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user from token (URL param or Authorization header)"""
    # Validate host to ensure memory limits are enforced
    host = request.headers.get("host", "")
    allowed_hosts = [
        "memory.usemindmirror.com",
        "localhost:8001", 
        "localhost:8000",
        "127.0.0.1:8001",
        "127.0.0.1:8000"
    ]
    
    if host not in allowed_hosts:
        logger.warning(f"Memory access denied from unauthorized host: {host}")
        raise HTTPException(
            status_code=403, 
            detail=f"Memory access restricted. Please use https://memory.usemindmirror.com"
        )
    
    token = None
    
    # Check URL parameter first (Zapier-style)
    if "token" in request.query_params:
        token = request.query_params["token"]
        logger.info(f"Token provided via URL parameter: {token[:10]}...")
    
    # Check Authorization header as fallback
    elif credentials:
        token = credentials.credentials
        logger.info(f"Token provided via Authorization header: {token[:10]}...")
    
    if not token:
        logger.warning("No authentication token provided")
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    user_id = get_user_from_token(token)
    if not user_id:
        logger.warning(f"Authentication failed for token: {token[:10]}...")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    logger.info(f"Request authenticated for user: {user_id}")
    return user_id

class MemoryItem(BaseModel):
    text: str
    tag: str
    timestamp: Optional[str] = None
    last_accessed: Optional[str] = None

class TokenGenerationRequest(BaseModel):
    """Request model for generating a new auth token"""
    user_name: Optional[str] = None

class TokenGenerationResponse(BaseModel):
    """Response model for token generation"""
    token: str
    user_id: str
    url: str
    memory_limit: int = 25
    memories_used: int = 0

class WaitlistRequest(BaseModel):
    """Request model for joining premium waitlist"""
    email: str

class WaitlistResponse(BaseModel):
    """Response model for waitlist signup"""
    message: str
    email: str

class MemoryResponse(BaseModel):
    id: str
    text: str
    tag: str
    timestamp: str
    similarity: Optional[float] = None
    last_accessed: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    tag_filter: Optional[str] = None

class CheckpointRequest(BaseModel):
    content: str
    title: Optional[str] = None

class CheckpointResponse(BaseModel):
    status: str
    overwrote: bool
    previous_checkpoint_time: Optional[str] = None
    id: int

class ResumeResponse(BaseModel):
    exists: bool
    content: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[str] = None
    id: Optional[int] = None

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

@app.post("/memories")
async def store_memory(memory: MemoryItem, user_id: str = Depends(get_current_user)):
    """Store a new memory item"""
    
    logger.info(f"Storing memory for user {user_id}: '{memory.text[:50]}...' (tag: {memory.tag})")
    
    # Validate tag
    if memory.tag not in VALID_TAGS:
        logger.error(f"Invalid tag '{memory.tag}' provided by user {user_id}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid tag. Must be one of: {VALID_TAGS}"
        )
    
    # Generate timestamp if not provided
    if not memory.timestamp:
        memory.timestamp = datetime.now(timezone.utc).isoformat() + "Z"
    
    # Check for duplicates using hash of text+tag
    memory_text_normalized = memory.text.strip().lower()
    memory_hash = hashlib.md5(f"{memory_text_normalized}:{memory.tag}".encode()).hexdigest()
    
    if memory_hash in memory_hashes:
        # Memory already exists, return without storing
        logger.info(f"Duplicate memory detected for user {user_id}: hash {memory_hash[:10]}...")
        return {
            "status": "skipped",
            "reason": "duplicate",
            "text": memory.text,
            "tag": memory.tag
        }
    
    # Add to hash set
    memory_hashes.add(memory_hash)
    
    # Check memory limit (except for admin users)
    MEMORY_LIMIT = 25
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user is admin
    cursor.execute("""
        SELECT is_admin FROM auth_tokens 
        WHERE user_id = %s AND is_active = true
        LIMIT 1
    """, (user_id,))
    admin_result = cursor.fetchone()
    is_admin = admin_result[0] if admin_result and admin_result[0] else False
    
    if not is_admin:
        # Check current memory count
        cursor.execute("""
            SELECT COUNT(*) FROM memories WHERE user_id = %s
        """, (user_id,))
        memory_count = cursor.fetchone()[0]
        
        if memory_count >= MEMORY_LIMIT:
            cursor.close()
            conn.close()
            logger.info(f"Memory limit reached for user {user_id}: {memory_count}/{MEMORY_LIMIT}")
            return {
                "error": "Memory limit reached. Upgrade to premium to store more.",
                "premium_link": "https://usemindmirror.com/premium",
                "memories_used": memory_count,
                "memory_limit": MEMORY_LIMIT
            }
    
    # Generate embedding
    embedding = model.encode(memory.text).tolist()
    
    # Check for semantic duplicates (similarity > 0.95) before storing
    DUPLICATE_THRESHOLD = 0.95
    
    # Check for similar memories with same tag
    cursor.execute("""
        SELECT id, text, COALESCE(1 - (embedding <=> %s::vector), 0.0) as similarity
        FROM memories 
        WHERE user_id = %s AND tag = %s
        ORDER BY embedding <=> %s::vector
        LIMIT 3
    """, (embedding, user_id, memory.tag, embedding))
    
    similar_memories = cursor.fetchall()
    for mem_id, mem_text, similarity in similar_memories:
        if similarity is not None and similarity > DUPLICATE_THRESHOLD:
            cursor.close()
            conn.close()
            logger.info(f"Semantic duplicate detected for user {user_id}: '{memory.text}' too similar to '{mem_text}' (similarity: {similarity:.4f})")
            return {"status": "duplicate", "message": f"Memory too similar to existing memory {mem_id}", "similarity": similarity}
    
    # Create unique ID
    memory_id = f"mem_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    
    # Check for conflicts with existing memories (same tag, high similarity)
    conflicts = []
    SIMILARITY_THRESHOLD = 0.65  # Lowered threshold for potential conflicts - was 0.8 initially
    logger.info(f"Checking for conflicts for user {user_id} with similarity threshold {SIMILARITY_THRESHOLD}...")
    
    # Search for memories with same tag for conflict detection
    cursor.execute("""
        SELECT id, text, COALESCE(1 - (embedding <=> %s::vector), 0.0) as similarity
        FROM memories 
        WHERE user_id = %s AND tag = %s
        ORDER BY embedding <=> %s::vector
        LIMIT 5
    """, (embedding, user_id, memory.tag, embedding))
    
    conflict_candidates = cursor.fetchall()
    for conflict_id, conflict_text, similarity in conflict_candidates:
        similarity_str = f"{similarity:.4f}" if similarity is not None else "None"
        logger.info(f"Similarity check for user {user_id} with '{conflict_text}': {similarity_str}")
        if similarity is not None and similarity >= SIMILARITY_THRESHOLD:
            logger.info(f"Conflict detected for user {user_id}: {conflict_id} (similarity: {similarity:.4f})")
            conflicts.append(conflict_id)
    
    # Set last_accessed timestamp
    current_time = datetime.now(timezone.utc).isoformat() + "Z"
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
            cursor.execute("SELECT metadata FROM memories WHERE id = %s", (conflict_id,))
            result = cursor.fetchone()
            if result:
                conflict_metadata = result[0]
                
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
                cursor.execute("UPDATE memories SET metadata = %s WHERE id = %s", (json.dumps(conflict_metadata), conflict_id))
    
    # Store in PostgreSQL
    cursor.execute("""
        INSERT INTO memories (id, user_id, text, tag, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (memory_id, user_id, memory.text, memory.tag, embedding, json.dumps(metadata)))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"Memory stored successfully for user {user_id}: ID {memory_id}, {len(conflicts)} conflicts detected")
    
    return {
        "id": memory_id,
        "text": memory.text,
        "tag": memory.tag,
        "timestamp": memory.timestamp,
        "status": "stored"
    }

def keyword_search(query: str, user_id: str, limit: int, tag_filter: str = None, exclude_ids: set = None):
    """
    Fallback keyword search using PostgreSQL ILIKE for text matching
    Returns list of MemoryResponse objects with artificial similarity scores
    """
    # Extract keywords from query (split on spaces, remove common words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = [word.strip().lower() for word in query.split() if word.strip().lower() not in stop_words and len(word.strip()) > 2]
    
    if not keywords:
        return []
    
    # Build ILIKE conditions for each keyword
    like_conditions = []
    params = [user_id]
    
    for keyword in keywords:
        like_conditions.append("text ILIKE %s")
        params.append(f"%{keyword}%")
    
    # Build tag filter
    tag_filter_sql = ""
    if tag_filter:
        tag_filter_sql = "AND tag = %s"
        params.append(tag_filter)
    
    # Build exclude IDs filter
    exclude_filter_sql = ""
    if exclude_ids:
        exclude_placeholders = ','.join(['%s'] * len(exclude_ids))
        exclude_filter_sql = f"AND id NOT IN ({exclude_placeholders})"
        params.extend(exclude_ids)
    
    params.append(limit)
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Execute keyword search
    where_clause = f"WHERE user_id = %s AND ({' OR '.join(like_conditions)}) {tag_filter_sql} {exclude_filter_sql}"
    cursor.execute(f"""
        SELECT id, text, tag, metadata, created_at
        FROM memories 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s
    """, params)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Convert to MemoryResponse objects with artificial similarity scores
    memories = []
    for i, row in enumerate(results):
        metadata = row['metadata']
        # Assign decreasing similarity scores (0.7 to 0.6) to compete with weaker semantic matches
        artificial_similarity = 0.7 - (i * 0.03)  # 0.7, 0.67, 0.64, 0.61, etc.
        
        memory = MemoryResponse(
            id=row['id'],
            text=row['text'],
            tag=row['tag'],
            timestamp=metadata['timestamp'],
            last_accessed=metadata.get('last_accessed', metadata['timestamp']),
            similarity=artificial_similarity
        )
        memories.append(memory)
    
    return memories

@app.post("/memories/search")
async def search_memories(request: SearchRequest, user_id: str = Depends(get_current_user)):
    """Hybrid search: semantic search with keyword fallback"""
    
    logger.info(f"Search request from user {user_id}: query='{request.query}', limit={request.limit}, tag_filter={request.tag_filter}")
    
    # Generate query embedding
    query_embedding = model.encode(request.query).tolist()
    
    # Build where clause for tag filtering
    tag_filter_sql = ""
    params = [query_embedding, user_id, query_embedding, request.limit]
    if request.tag_filter:
        if request.tag_filter not in VALID_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tag filter. Must be one of: {VALID_TAGS}"
            )
        tag_filter_sql = "AND tag = %s"
        params.insert(2, request.tag_filter)
    
    # Log search parameters
    logger.info(f"Search SQL params - user_id: {user_id}, limit: {request.limit}, tag_filter: {request.tag_filter}")
    logger.info(f"SQL will use LIMIT: {params[-1]}")
    
    # Search in PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute(f"""
        SELECT id, text, tag, metadata, created_at,
               COALESCE(1 - (embedding <=> %s::vector), 0.0) as similarity
        FROM memories 
        WHERE user_id = %s {tag_filter_sql}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, params)
    
    results = cursor.fetchall()
    
    # Log raw search results  
    total_results = len(results)
    logger.info(f"Semantic search results for user {user_id}: found {total_results} memories from database")
    logger.info(f"Query was: '{request.query}' with limit {request.limit}")
    if total_results > 0:
        similarities = [row['similarity'] for row in results[:3]]
        logger.info(f"Top 3 similarities: {similarities}")
        # Log first result for debugging
        logger.info(f"First result: {results[0]['text'][:50]}... (similarity: {results[0]['similarity']})")
    
    # Hybrid search: add keyword fallback if semantic search returned fewer than requested results
    if total_results < request.limit:
        remaining_slots = request.limit - total_results
        semantic_ids = {row['id'] for row in results}
        
        logger.info(f"Semantic search returned {total_results} < {request.limit} requested. Running keyword fallback for {remaining_slots} more results.")
        
        # Run keyword search for remaining slots, excluding already found IDs
        keyword_results = keyword_search(
            query=request.query,
            user_id=user_id,
            limit=remaining_slots,
            tag_filter=request.tag_filter,
            exclude_ids=semantic_ids
        )
        
        if keyword_results:
            logger.info(f"Keyword fallback found {len(keyword_results)} additional memories")
            # Convert MemoryResponse objects back to dict format to match semantic results
            for memory in keyword_results:
                result_dict = {
                    'id': memory.id,
                    'text': memory.text,
                    'tag': memory.tag,
                    'similarity': memory.similarity,
                    'metadata': {
                        'timestamp': memory.timestamp,
                        'last_accessed': memory.last_accessed,
                        'tag': memory.tag
                    },
                    'created_at': memory.timestamp  # Use timestamp as created_at
                }
                results.append(result_dict)
        else:
            logger.info("Keyword fallback found no additional memories")
    
    # Update total count after hybrid search
    total_hybrid_results = len(results)
    logger.info(f"Total hybrid search results: {total_hybrid_results} memories (semantic: {total_results}, keyword: {total_hybrid_results - total_results})")
    
    # Sort all results by similarity and timestamp (composite sort for recency tiebreaking)
    if results:
        results.sort(key=lambda x: (x.get('similarity', 0.0), x.get('created_at', '')), reverse=True)
        top_created = results[0].get('created_at', 'unknown')
        if hasattr(top_created, 'strftime'):
            top_created_str = top_created.strftime('%Y-%m-%d')
        elif isinstance(top_created, str):
            top_created_str = top_created[:10]
        else:
            top_created_str = str(top_created)[:10]
        logger.info(f"Sorted hybrid results by similarity+timestamp - top result: similarity={results[0].get('similarity', 0.0):.3f}, created={top_created_str}")
    
    # Format response
    memories = []
    conflict_sets = {}
    
    if results:
        # First pass - create all memories
        for row in results:
            metadata = row['metadata']
            memory_id = row['id']
            
            # Update last_accessed timestamp
            current_time = datetime.now(timezone.utc).isoformat() + "Z"
            metadata["last_accessed"] = current_time
            cursor.execute("UPDATE memories SET metadata = %s WHERE id = %s", (json.dumps(metadata), memory_id))
            
            memory = MemoryResponse(
                id=memory_id,
                text=row['text'],
                tag=row['tag'],
                timestamp=metadata['timestamp'],
                last_accessed=current_time,
                similarity=row['similarity']
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
                        cursor.execute("SELECT id, text, tag, metadata FROM memories WHERE id = %s", (conflict_id,))
                        conflict_result = cursor.fetchone()
                        if conflict_result:
                            conflict_metadata = conflict_result['metadata']
                            
                            conflict_memory = MemoryResponse(
                                id=conflict_id,
                                text=conflict_result['text'],
                                tag=conflict_result['tag'],
                                timestamp=conflict_metadata['timestamp'],
                                last_accessed=conflict_metadata.get('last_accessed', conflict_metadata['timestamp'])
                            )
                            
                            # Add to conflict set
                            conflict_sets[memory_id].append(dict(conflict_memory))
    
    # Apply semantic deduplication to conflict sets
    for memory_id, conflicts in conflict_sets.items():
        if len(conflicts) > 1:
            # Extract embeddings for similarity calculation
            unique_conflicts = []
            
            for conflict in conflicts:
                # Check if this conflict is semantically similar to any existing unique conflict
                is_duplicate = False
                conflict_embedding = model.encode([conflict['text']])
                
                for unique_conflict in unique_conflicts:
                    unique_embedding = model.encode([unique_conflict['text']])
                    
                    # Calculate cosine similarity between embeddings
                    
                    # Flatten embeddings for calculation
                    emb1 = conflict_embedding[0]
                    emb2 = unique_embedding[0]
                    
                    # Calculate cosine similarity
                    try:
                        similarity = np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))
                    except (ZeroDivisionError, ValueError):
                        similarity = 0.0
                    
                    # If similarity > 0.95, it's a duplicate
                    if similarity is not None and similarity > 0.95:
                        is_duplicate = True
                        # Keep the more recent one
                        if conflict['timestamp'] > unique_conflict['timestamp']:
                            unique_conflicts.remove(unique_conflict)
                            unique_conflicts.append(conflict)
                        break
                
                # If not a duplicate, add to unique conflicts
                if not is_duplicate:
                    unique_conflicts.append(conflict)
            
            # Sort unique conflicts by timestamp (most recent first)
            unique_conflicts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Update conflict set with deduplicated conflicts
            conflict_sets[memory_id] = unique_conflicts
    
    # Close database connection
    conn.commit()
    cursor.close()
    conn.close()
    
    # Build initial response
    response = {
        "query": request.query,
        "results": memories,
        "count": len(memories)
    }
    
    # Server-side conflict message formatting will be added after conflict groups are built
    
    # Group overlapping conflict sets using Union-Find for transitive merging
    class UnionFind:
        def __init__(self):
            self.parent = {}
            self.rank = {}
        
        def find(self, x):
            if x not in self.parent:
                self.parent[x] = x
                self.rank[x] = 0
            if self.parent[x] != x:
                self.parent[x] = self.find(self.parent[x])  # Path compression
            return self.parent[x]
        
        def union(self, x, y):
            px, py = self.find(x), self.find(y)
            if px == py:
                return
            # Union by rank for efficiency
            if self.rank[px] < self.rank[py]:
                px, py = py, px
            self.parent[py] = px
            if self.rank[px] == self.rank[py]:
                self.rank[px] += 1
        
        def get_groups(self):
            groups = {}
            for x in self.parent:
                root = self.find(x)
                if root not in groups:
                    groups[root] = []
                groups[root].append(x)
            return list(groups.values())
    
    # Build conflict groups using Union-Find
    if conflict_sets:
        uf = UnionFind()
        
        # Union memories that appear in the same conflict set
        for memory_id, conflicts in conflict_sets.items():
            memory_ids_in_set = {memory_id}
            for conflict in conflicts:
                memory_ids_in_set.add(conflict['id'])
            
            # Union all memories in this conflict set
            memory_list = list(memory_ids_in_set)
            for i in range(len(memory_list)):
                for j in range(i + 1, len(memory_list)):
                    uf.union(memory_list[i], memory_list[j])
        
        # Get unified conflict groups
        memory_groups = uf.get_groups()
        
        # Filter out singleton groups (groups with only 1 memory = no real conflicts)
        meaningful_groups = [group for group in memory_groups if len(group) >= 2]
        
        # Build final conflict groups with memory objects
        conflict_groups = []
        for group in meaningful_groups:
            group_memories = []
            for memory_id in group:
                # Find memory object from original results or conflict sets
                memory_obj = None
                
                # First check if it's in the main results
                for memory in memories:
                    if (isinstance(memory, dict) and memory['id'] == memory_id) or \
                       (hasattr(memory, 'id') and memory.id == memory_id):
                        memory_obj = dict(memory) if not isinstance(memory, dict) else memory
                        break
                
                # If not found, look in conflict sets
                if memory_obj is None:
                    for conflicts in conflict_sets.values():
                        for conflict in conflicts:
                            if conflict['id'] == memory_id:
                                memory_obj = conflict
                                break
                        if memory_obj:
                            break
                
                if memory_obj:
                    group_memories.append(memory_obj)
            
            # Sort group by timestamp (most recent first) and add to conflict groups
            group_memories.sort(key=lambda x: x['timestamp'], reverse=True)
            conflict_groups.append(group_memories)
        
        # Replace individual conflict_sets with unified conflict_groups
        if conflict_groups:
            response["conflict_groups"] = conflict_groups
            logger.info(f"Unified conflict groups for user {user_id}: {len(conflict_groups)} groups created from {len(conflict_sets)} individual sets")
            for i, group in enumerate(conflict_groups):
                logger.info(f"- Group {i+1}: {len(group)} memories ({', '.join([m['text'][:30] + '...' for m in group])})")
        else:
            # Keep original conflict_sets if no meaningful groups found
            response["conflict_sets"] = conflict_sets
    else:
        # No conflicts detected, keep original structure
        response["conflict_sets"] = conflict_sets
    
    # Debug: log conflict detection information
    logger.info(f"Debug for user {user_id}: ChromaDB returned {total_results} memories, built {len(memories)} responses")
    
    # Log memory content details
    if memories:
        logger.info(f"Memory details for user {user_id}:")
        for memory in memories:
            memory_dict = memory if isinstance(memory, dict) else dict(memory)
            text_snippet = memory_dict['text'][:50] + "..." if len(memory_dict['text']) > 50 else memory_dict['text']
            similarity = memory_dict.get('similarity', 'N/A')
            
            # Extract short dates from timestamps
            created_date = "unknown"
            accessed_date = "unknown"
            
            if 'timestamp' in memory_dict and memory_dict['timestamp']:
                try:
                    # Convert "2025-07-01T14:40:19.175601Z" to "07-01"
                    created_date = memory_dict['timestamp'].split('T')[0][5:]  # Take YYYY-MM-DD, extract MM-DD
                except:
                    created_date = "unknown"
                    
            if 'last_accessed' in memory_dict and memory_dict['last_accessed']:
                try:
                    # Convert "2025-07-03T14:37:18.063049Z" to "07-03"
                    accessed_date = memory_dict['last_accessed'].split('T')[0][5:]  # Take YYYY-MM-DD, extract MM-DD
                except:
                    accessed_date = "unknown"
            
            logger.info(f"- {memory_dict['id']}: \"{text_snippet}\" ({memory_dict['tag']}, sim: {similarity:.3f}, ts: {created_date}, accessed: {accessed_date})")
    else:
        logger.info(f"No memories returned for user {user_id}")
    
    logger.info(f"Debug for user {user_id}: Identified {len(conflict_sets)} conflict sets")
    
    # Add conflict sets if any exist
    if conflict_sets:
        # Clean conflict summary logging
        conflict_summaries = []
        for memory_id, conflicts in conflict_sets.items():
            conflict_count = len(conflicts) - 1  # Subtract 1 because it includes the original memory
            if conflicts:
                main_memory = conflicts[0]
                text_snippet = main_memory['text'][:50] + "..." if len(main_memory['text']) > 50 else main_memory['text']
                conflict_summaries.append(f"{memory_id}: '{text_snippet}' ({conflict_count} conflicts)")
        
        logger.info(f"Conflict sets for user {user_id}: {len(conflict_sets)} sets detected")
        for summary in conflict_summaries:
            logger.info(f"- {summary}")
    else:
        # Manually check for conflicts among the returned results
        logger.info(f"Debug for user {user_id}: No conflict sets detected, performing manual conflict check")
        manual_conflict_sets = {}
        
        # Check each memory for conflicts
        conn2 = get_db_connection()
        cursor2 = conn2.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        for memory in memories:
            memory_id = memory['id'] if isinstance(memory, dict) else memory.id
            cursor2.execute("SELECT metadata FROM memories WHERE id = %s", (memory_id,))
            result = cursor2.fetchone()
            
            if result:
                metadata = result['metadata']
                
                if metadata.get('has_conflicts', False) and 'conflict_ids' in metadata:
                    conflict_ids = json.loads(metadata['conflict_ids'])
                    logger.info(f"Debug for user {user_id}: Memory {memory_id} has conflicts with: {conflict_ids}")
                    
                    # Create conflict set
                    if memory_id not in manual_conflict_sets:
                        manual_conflict_sets[memory_id] = [memory]
                    
                    # Add conflicting memories
                    for conflict_id in conflict_ids:
                        cursor2.execute("SELECT id, text, tag, metadata FROM memories WHERE id = %s", (conflict_id,))
                        conflict_result = cursor2.fetchone()
                        if conflict_result:
                            conflict_metadata = conflict_result['metadata']
                            
                            conflict_memory = {
                                "id": conflict_id,
                                "text": conflict_result['text'],
                                "tag": conflict_result['tag'],
                                "timestamp": conflict_metadata['timestamp'],
                                "last_accessed": conflict_metadata.get('last_accessed', conflict_metadata['timestamp'])
                            }
                            
                            manual_conflict_sets[memory_id].append(conflict_memory)
        
        cursor2.close()
        conn2.close()
        
        # Add manual conflict sets to response (only if no conflict groups were created)
        if manual_conflict_sets and "conflict_groups" not in response:
            logger.info(f"Debug for user {user_id}: Adding manually detected conflict sets: {list(manual_conflict_sets.keys())}")
            response["conflict_sets"] = manual_conflict_sets
    

    # Log final response summary
    if "conflict_groups" in response:
        conflict_count = len(response["conflict_groups"])
        logger.info(f"Search response for user {user_id}: returning {len(memories)} memories with {conflict_count} conflict groups")
    else:
        conflict_count = len(response.get("conflict_sets", {}))
        logger.info(f"Search response for user {user_id}: returning {len(memories)} memories with {conflict_count} conflict sets")
    
    return response

@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str, user_id: str = Depends(get_current_user)):
    """Get a specific memory by ID"""
    
    logger.info(f"Getting memory {memory_id} for user {user_id}")
    
    # Get memory from PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT id, text, tag, metadata FROM memories WHERE id = %s AND user_id = %s", (memory_id, user_id))
    result = cursor.fetchone()
    
    if not result:
        cursor.close()
        conn.close()
        logger.warning(f"Memory {memory_id} not found for user {user_id}")
        raise HTTPException(status_code=404, detail="Memory not found")
    
    metadata = result['metadata']
    
    # Update last_accessed timestamp
    current_time = datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    metadata["last_accessed"] = current_time
    cursor.execute("UPDATE memories SET metadata = %s WHERE id = %s", (json.dumps(metadata), memory_id))
    
    memory = MemoryResponse(
        id=memory_id,
        text=result['text'],
        tag=result['tag'],
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
            cursor.execute("SELECT id, text, tag, metadata FROM memories WHERE id = %s", (conflict_id,))
            conflict_result = cursor.fetchone()
            if conflict_result:
                conflict_metadata = conflict_result['metadata']
                
                conflict_memory = {
                    "id": conflict_id,
                    "text": conflict_result['text'],
                    "tag": conflict_result['tag'],
                    "timestamp": conflict_metadata['timestamp'],
                    "last_accessed": conflict_metadata.get('last_accessed', conflict_metadata['timestamp'])
                }
                
                conflict_set.append(conflict_memory)
        
        response_data["conflict_set"] = conflict_set
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return response_data

@app.get("/memories")
async def list_memories(tag: Optional[str] = None, limit: int = 10, user_id: str = Depends(get_current_user)):
    """List all memories, optionally filtered by tag"""
    
    logger.info(f"Listing memories for user {user_id}: tag={tag}, limit={limit}")
    
    tag_filter_sql = ""
    params = [user_id, limit]
    if tag:
        if tag not in VALID_TAGS:
            logger.error(f"Invalid tag '{tag}' provided by user {user_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tag. Must be one of: {VALID_TAGS}"
            )
        tag_filter_sql = "AND tag = %s"
        params.insert(1, tag)
    
    # Get memories from PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute(f"""
        SELECT id, text, tag, metadata, created_at
        FROM memories 
        WHERE user_id = %s {tag_filter_sql}
        ORDER BY created_at DESC
        LIMIT %s
    """, params)
    
    results = cursor.fetchall()
    
    memories = []
    for row in results:
        metadata = row['metadata']
        memory = MemoryResponse(
            id=row['id'],
            text=row['text'],
            tag=row['tag'],
            timestamp=metadata['timestamp'],
            last_accessed=metadata.get('last_accessed', metadata['timestamp'])
        )
        memories.append(memory)
    
    cursor.close()
    conn.close()
    
    logger.info(f"Returning {len(memories)} memories for user {user_id}")
    
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
            "DELETE /memories/{id}": "Delete specific memory",
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

@app.post("/api/generate-token", response_model=TokenGenerationResponse)
async def generate_token(request: TokenGenerationRequest):
    """Generate a new authentication token for a user"""
    try:
        # Generate secure token
        new_token = secrets.token_urlsafe(32)
        
        # Generate unique user ID
        user_id = f"user_{secrets.token_hex(8)}"
        user_name = request.user_name or f"User {user_id[-8:]}"
        
        # Store token in database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO auth_tokens (token, user_id, user_name) 
            VALUES (%s, %s, %s)
            RETURNING id
        """, (new_token, user_id, user_name))
        
        # Get memory count for this user (should be 0 for new users)
        cursor.execute("""
            SELECT COUNT(*) FROM memories WHERE user_id = %s
        """, (user_id,))
        memory_count = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Determine the domain based on environment
        domain = os.getenv('MEMORY_DOMAIN', 'memory.usemindmirror.com')
        if domain == 'localhost':
            domain = f"localhost:{os.getenv('PORT', '8000')}"
        
        # Create the MCP URL
        mcp_url = f"https://{domain}/sse?token={new_token}"
        
        logger.info(f"Generated new token for user {user_id}")
        
        return TokenGenerationResponse(
            token=new_token,
            user_id=user_id,
            url=mcp_url,
            memory_limit=25,
            memories_used=memory_count
        )
        
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate token")

@app.post("/api/join-waitlist", response_model=WaitlistResponse)
async def join_waitlist(request: WaitlistRequest):
    """Add email to premium waitlist"""
    try:
        # Basic email validation
        if "@" not in request.email or "." not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Try to insert email (will fail if duplicate due to UNIQUE constraint)
        cursor.execute("""
            INSERT INTO waitlist_emails (email) 
            VALUES (%s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (request.email.lower(),))
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"New email added to waitlist: {request.email}")
            message = "Successfully joined the premium waitlist!"
        else:
            logger.info(f"Email already on waitlist: {request.email}")
            message = "Email already on waitlist."
        
        return WaitlistResponse(
            message=message,
            email=request.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining waitlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to join waitlist")

@app.post("/checkpoint", response_model=CheckpointResponse)
async def store_checkpoint(request: CheckpointRequest, user_id: str = Depends(get_current_user)):
    """Store current conversation context for later continuation"""
    
    logger.info(f"Storing checkpoint for user {user_id}: '{request.content[:50]}...'")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check if user already has a checkpoint
        cursor.execute("""
            SELECT id, created_at FROM short_term_memories WHERE user_id = %s
        """, (user_id,))
        
        existing = cursor.fetchone()
        overwrote = existing is not None
        previous_time = existing['created_at'].isoformat() if existing else None
        
        # Insert or update checkpoint (UPSERT)
        cursor.execute("""
            INSERT INTO short_term_memories (user_id, title, content, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                created_at = EXCLUDED.created_at
            RETURNING id
        """, (user_id, request.title, request.content))
        
        result = cursor.fetchone()
        checkpoint_id = result['id']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Checkpoint stored successfully for user {user_id}: ID {checkpoint_id}, overwrote: {overwrote}")
        
        return CheckpointResponse(
            status="ok",
            overwrote=overwrote,
            previous_checkpoint_time=previous_time,
            id=checkpoint_id
        )
        
    except Exception as e:
        logger.error(f"Error storing checkpoint for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store checkpoint: {str(e)}")

@app.post("/resume", response_model=ResumeResponse)
async def resume_checkpoint(user_id: str = Depends(get_current_user)):
    """Retrieve the most recent conversation checkpoint"""
    
    logger.info(f"Retrieving checkpoint for user {user_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT id, title, content, created_at 
            FROM short_term_memories 
            WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"Checkpoint found for user {user_id}: ID {result['id']}")
            return ResumeResponse(
                exists=True,
                content=result['content'],
                title=result['title'],
                created_at=result['created_at'].isoformat(),
                id=result['id']
            )
        else:
            logger.info(f"No checkpoint found for user {user_id}")
            return ResumeResponse(exists=False)
            
    except Exception as e:
        logger.error(f"Error retrieving checkpoint for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve checkpoint: {str(e)}")

@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str, user_id: str = Depends(get_current_user)):
    """Delete a specific memory by ID"""
    
    logger.info(f"Deleting memory {memory_id} for user {user_id}")
    
    try:
        # Get memory from PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # First check if memory exists
        cursor.execute("SELECT id, text, tag, metadata FROM memories WHERE id = %s AND user_id = %s", (memory_id, user_id))
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            logger.warning(f"Memory {memory_id} not found for deletion by user {user_id}")
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Get memory details for logging
        memory_text = result['text']
        metadata = result['metadata']
        memory_tag = result['tag']
        
        # Remove hash from memory_hashes set for deduplication tracking
        if 'hash' in metadata:
            memory_hash = metadata['hash']
            memory_hashes.discard(memory_hash)
        else:
            # For backwards compatibility with memories stored before hash implementation
            memory_text_normalized = memory_text.strip().lower()
            memory_hash = hashlib.md5(f"{memory_text_normalized}:{memory_tag}".encode()).hexdigest()
            memory_hashes.discard(memory_hash)
        
        # Handle conflict cleanup - remove this memory from other memories' conflict lists
        if metadata.get('has_conflicts', False) and 'conflict_ids' in metadata:
            conflict_ids = json.loads(metadata['conflict_ids'])
            
            for conflict_id in conflict_ids:
                try:
                    # Get the conflicting memory
                    cursor.execute("SELECT metadata FROM memories WHERE id = %s", (conflict_id,))
                    conflict_result = cursor.fetchone()
                    if conflict_result:
                        conflict_metadata = conflict_result['metadata']
                        
                        # Remove this memory from its conflict list
                        if 'conflict_ids' in conflict_metadata:
                            existing_conflicts = json.loads(conflict_metadata['conflict_ids'])
                            if memory_id in existing_conflicts:
                                existing_conflicts.remove(memory_id)
                                
                                # Update or remove conflict info
                                if existing_conflicts:
                                    conflict_metadata['conflict_ids'] = json.dumps(existing_conflicts)
                                else:
                                    # No more conflicts, remove conflict flags
                                    conflict_metadata['has_conflicts'] = False
                                    del conflict_metadata['conflict_ids']
                                
                                # Update the conflicting memory
                                cursor.execute("UPDATE memories SET metadata = %s WHERE id = %s", (json.dumps(conflict_metadata), conflict_id))
                except Exception as e:
                    logger.warning(f"Warning for user {user_id}: Error updating conflict for memory {conflict_id}: {e}")
        
        # Delete the memory from PostgreSQL
        cursor.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log the deletion
        logger.info(f"Memory deleted for user {user_id}: {memory_id} - '{memory_text}' (tag: {memory_tag})")
        
        return {
            "status": "deleted",
            "id": memory_id,
            "text": memory_text,
            "tag": memory_tag,
            "timestamp": metadata.get('timestamp')
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete memory: {str(e)}"
        )

@app.get("/memories/prune")
async def prune_memories(user_id: str = Depends(get_current_user)):
    """Identify memories for pruning based on age, access time, and importance"""
    
    logger.info(f"Pruning memories for user {user_id}")
    
    now = datetime.now(datetime.timezone.utc)
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
    
    # Get memories from PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT id, text, tag, metadata, created_at FROM memories WHERE user_id = %s", (user_id,))
    results = cursor.fetchall()
    
    memories = []
    
    # Split into categories
    to_prune = []
    kept = []
    
    for row in results:
        memory_id = row['id']
        metadata = row['metadata']
        
        memory = {
            "id": memory_id,
            "text": row['text'],
            "tag": row['tag'],
            "timestamp": metadata['timestamp'],
            "last_accessed": metadata.get('last_accessed', metadata['timestamp'])
        }
        memories.append(memory)
        
        # Skip core memories
        if row['tag'] in CORE_TAGS:
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
            metadata["archive_date"] = datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            metadata["archive_reason"] = "age_and_access"
            
            # Update metadata in database
            cursor.execute("UPDATE memories SET metadata = %s WHERE id = %s", (json.dumps(metadata), memory_id))
        else:
            kept.append(memory)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Return pruning results
    logger.info(f"Pruning complete for user {user_id}: {len(to_prune)} memories pruned, {len(kept)} kept")
    
    return {
        "cutoff_info": cutoff_info,
        "total_memories": len(memories),
        "pruned_count": len(to_prune),
        "kept_count": len(kept),
        "pruned_memories": to_prune
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MEMORY_SERVER_PORT", "8001"))
    logger.info(f"🚀 Memory Server starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)