"""
MCP Wrapper for Memory System

This script provides a Model Context Protocol (MCP) compatible wrapper
around our memory system's REST API endpoints.

It translates between:
- add_observations → POST /memories
- search_nodes → POST /memories/search
- open_nodes → GET /memories?tag=...
"""
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import json

app = FastAPI(title="Memory System MCP Wrapper")

# Configuration
MEMORY_API_BASE = "http://localhost:8003"  # URL for memory system API

class Observation(BaseModel):
    entityName: str
    contents: List[str]

class Entity(BaseModel):
    name: str
    entityType: str
    observations: List[str]

class SearchQuery(BaseModel):
    query: str

class Response(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class ConflictResolutionRequest(BaseModel):
    memory_ids: List[str]

@app.post("/add_observations")
async def add_observations(request: Request):
    """
    Add new observations to entities in the memory system.
    MCP equivalent of add_observations.
    """
    try:
        data = await request.json()
        
        # Extract observations from MCP request
        # Handle both formats: {"observations": [...]} and direct {"entityName": ..., "contents": [...]}
        if "observations" in data:
            observations = data.get("observations", [])
        else:
            # Direct format - wrap in observations array
            observations = [data]
        
        results = []
        
        async with httpx.AsyncClient() as client:
            for obs in observations:
                entity_name = obs.get("entityName", "default_user")
                contents = obs.get("contents", [])
                
                # For each observation, create a memory in our system
                for content in contents:
                    # Use provided tag or determine from context
                    provided_tag = obs.get("tag") or data.get("tag")
                    if provided_tag:
                        tag = provided_tag
                    else:
                        # Determine tag from context using heuristics
                        tag = "preference"
                    if "routine" in content.lower():
                        tag = "routine"
                    elif "goal" in content.lower():
                        tag = "goal"
                    elif "value" in content.lower() or "believe" in content.lower():
                        tag = "value"
                    elif "identity" in content.lower() or "am a" in content.lower():
                        tag = "identity"
                    elif "tool" in content.lower() or "use" in content.lower():
                        tag = "tool"
                    elif "habit" in content.lower():
                        tag = "habit"
                    elif "constraint" in content.lower() or "can't" in content.lower():
                        tag = "constraint"
                    elif "project" in content.lower():
                        tag = "project"
                    
                    # Store the memory
                    memory_data = {
                        "text": content,
                        "tag": tag
                    }
                    
                    response = await client.post(
                        f"{MEMORY_API_BASE}/memories",
                        json=memory_data
                    )
                    
                    if response.status_code == 200:
                        results.append({
                            "entityName": entity_name,
                            "content": content,
                            "tag": tag,
                            "status": "stored"
                        })
                    else:
                        results.append({
                            "entityName": entity_name,
                            "content": content,
                            "status": "error",
                            "error": response.text
                        })
        
        return {
            "status": "success",
            "message": f"Processed {len(results)} observations",
            "results": results
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/search_nodes")
async def search_nodes(request: Request):
    """
    Search for entities in the knowledge graph based on a query.
    MCP equivalent of search_nodes.
    """
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            return {
                "status": "error",
                "message": "Query is required"
            }
        
        # Pass the query to our memory search endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MEMORY_API_BASE}/memories/search",
                json={
                    "query": query,
                    "limit": 10
                }
            )
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Error searching memories: {response.text}"
                }
            
            search_results = response.json()
            
            # Transform results to MCP format
            mcp_nodes = []
            for result in search_results.get("results", []):
                node = {
                    "name": result.get("id", "unknown"),
                    "entityType": result.get("tag", "unknown"),
                    "observations": [result.get("text", "")],
                    "similarity": result.get("similarity", 0),
                    "timestamp": result.get("timestamp", ""),
                    "last_accessed": result.get("last_accessed", "")
                }
                mcp_nodes.append(node)
            
            # Handle conflict sets if present
            if "conflict_sets" in search_results:
                conflict_sets = []
                for conflict_key, conflict_memories in search_results["conflict_sets"].items():
                    conflict_data = {
                        "primary_memory": conflict_key,
                        "conflicting_memories": [m["id"] for m in conflict_memories if m["id"] != conflict_key],
                        "message": "These memories have conflicting information. Consider using the most recent one or asking for clarification."
                    }
                    conflict_sets.append(conflict_data)
                
                return {
                    "status": "success",
                    "message": f"Found {len(mcp_nodes)} relevant memories",
                    "nodes": mcp_nodes,
                    "conflict_sets": conflict_sets
                }
            
            return {
                "status": "success",
                "message": f"Found {len(mcp_nodes)} relevant memories",
                "nodes": mcp_nodes
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/open_nodes")
async def open_nodes(request: Request):
    """
    Retrieve specific entities from the knowledge graph by their names.
    MCP equivalent of open_nodes.
    """
    try:
        data = await request.json()
        names = data.get("names", [])
        
        if not names:
            return {
                "status": "error",
                "message": "At least one node name is required"
            }
        
        # In our system, names can be either memory IDs or tags
        mcp_nodes = []
        
        async with httpx.AsyncClient() as client:
            for name in names:
                # First try to get by ID
                response = await client.get(f"{MEMORY_API_BASE}/memories/{name}")
                
                if response.status_code == 200:
                    # Found by ID
                    memory = response.json()
                    node = {
                        "name": memory.get("id", "unknown"),
                        "entityType": memory.get("tag", "unknown"),
                        "observations": [memory.get("text", "")],
                        "timestamp": memory.get("timestamp", ""),
                        "last_accessed": memory.get("last_accessed", "")
                    }
                    
                    # Handle conflict set if present
                    if "conflict_set" in memory:
                        node["conflict_set"] = memory["conflict_set"]
                        node["has_conflicts"] = True
                        
                    mcp_nodes.append(node)
                else:
                    # Try to get by tag
                    tag_response = await client.get(
                        f"{MEMORY_API_BASE}/memories", 
                        params={"tag": name, "limit": 10}
                    )
                    
                    if tag_response.status_code == 200:
                        tag_memories = tag_response.json().get("memories", [])
                        
                        for mem in tag_memories:
                            node = {
                                "name": mem.get("id", "unknown"),
                                "entityType": mem.get("tag", "unknown"),
                                "observations": [mem.get("text", "")],
                                "timestamp": mem.get("timestamp", ""),
                                "last_accessed": mem.get("last_accessed", "")
                            }
                            mcp_nodes.append(node)
        
        return {
            "status": "success",
            "message": f"Retrieved {len(mcp_nodes)} nodes",
            "nodes": mcp_nodes
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/")
async def root():
    return {
        "message": "Memory System MCP Wrapper",
        "endpoints": {
            "POST /add_observations": "Store new observations (maps to POST /memories)",
            "POST /search_nodes": "Search memories by query (maps to POST /memories/search)",
            "POST /open_nodes": "Get memories by ID or tag (maps to GET /memories/{id} or GET /memories?tag=X)"
        },
        "memory_service_url": MEMORY_API_BASE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
