#!/usr/bin/env python3
"""
Memory MCP Server

A Model Context Protocol server that provides memory management capabilities.
Connects to our existing memory system via HTTP API.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# Configuration
MEMORY_API_BASE = "http://localhost:8003"

# Initialize the MCP server
server = Server("memory-server")

# HTTP client for API calls
http_client = None

async def setup_http_client():
    """Initialize HTTP client"""
    global http_client
    http_client = httpx.AsyncClient(base_url=MEMORY_API_BASE)

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available memory resources"""
    return [
        Resource(
            uri="memory://memories",
            name="Stored Memories",
            description="All stored memories in the system",
            mimeType="application/json",
        ),
        Resource(
            uri="memory://search",
            name="Memory Search",
            description="Search through stored memories",
            mimeType="application/json",
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read memory resources"""
    if uri == "memory://memories":
        try:
            response = await http_client.get("/memories")
            return json.dumps(response.json(), indent=2)
        except Exception as e:
            return f"Error reading memories: {str(e)}"
    
    elif uri == "memory://search":
        return json.dumps({
            "info": "Use the search_memory tool to search through memories",
            "example": "Call search_memory with a query string"
        }, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available memory tools"""
    return [
        Tool(
            name="store_memory",
            description="Store a new memory with automatic conflict detection",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The memory text to store"
                    },
                    "tag": {
                        "type": "string",
                        "enum": ["goal", "routine", "preference", "constraint", "habit", "project", "tool", "identity", "value"],
                        "description": "Category tag for the memory"
                    }
                },
                "required": ["text", "tag"]
            }
        ),
        Tool(
            name="search_memory",
            description="Search through stored memories using semantic similarity",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding relevant memories"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="delete_memory",
            description="Delete a specific memory by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The ID of the memory to delete"
                    }
                },
                "required": ["memory_id"]
            }
        ),
        Tool(
            name="list_memories",
            description="List all stored memories, optionally filtered by tag",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "enum": ["goal", "routine", "preference", "constraint", "habit", "project", "tool", "identity", "value"],
                        "description": "Optional tag filter"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Execute memory tools"""
    
    try:
        if name == "store_memory":
            text = arguments.get("text")
            tag = arguments.get("tag")
            
            # Call memory API to store
            response = await http_client.post("/memories", json={
                "text": text,
                "tag": tag
            })
            
            result = response.json()
            
            # Format response including any conflicts detected
            output = f"Memory stored successfully!\n\n"
            output += f"Text: {text}\n"
            output += f"Tag: {tag}\n"
            output += f"ID: {result.get('id', 'unknown')}\n"
            
            if result.get('conflicts_detected'):
                output += f"\n⚠️ CONFLICTS DETECTED:\n"
                for conflict in result.get('conflicts', []):
                    output += f"- {conflict.get('text', 'Unknown conflict')}\n"
            
            return [types.TextContent(type="text", text=output)]
        
        elif name == "search_memory":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            
            response = await http_client.post("/memories/search", json={
                "query": query,
                "limit": limit
            })
            
            result = response.json()
            memories = result.get("results", [])  # Fixed: memory server returns "results" not "memories" 
            conflict_groups = result.get("conflict_groups", [])
            
            output = f"Search Results for: '{query}'\n"
            output += f"Found {len(memories)} memories\n\n"
            
            # Show memories
            for i, memory in enumerate(memories, 1):
                output += f"{i}. [{memory.get('tag', 'unknown')}] {memory.get('text', '')}\n"
                output += f"   ID: {memory.get('id', 'unknown')} | Similarity: {memory.get('similarity', 0):.3f}\n\n"
            
            # Show conflicts if any
            if conflict_groups:
                output += "⚠️ CONFLICTS DETECTED:\n\n"
                for i, group in enumerate(conflict_groups, 1):
                    output += f"Conflict Group {i}:\n"
                    for memory in group:
                        timestamp = memory.get('timestamp', '')[:10] if memory.get('timestamp') else 'unknown'  # Just date part
                        output += f"  - {memory.get('text', 'No text')} (ID: {memory.get('id', 'unknown')}, {timestamp})\n"
                    output += "\n"
            
            return [types.TextContent(type="text", text=output)]
        
        elif name == "delete_memory":
            memory_id = arguments.get("memory_id")
            
            response = await http_client.delete(f"/memories/{memory_id}")
            
            if response.status_code == 200:
                return [types.TextContent(type="text", text=f"Memory {memory_id} deleted successfully")]
            else:
                return [types.TextContent(type="text", text=f"Failed to delete memory {memory_id}: {response.text}")]
        
        elif name == "list_memories":
            tag = arguments.get("tag")
            
            params = {}
            if tag:
                params["tag"] = tag
            
            response = await http_client.get("/memories", params=params)
            result = response.json()
            memories = result.get("memories", [])
            
            output = f"All Memories"
            if tag:
                output += f" (filtered by tag: {tag})"
            output += f"\nTotal: {len(memories)}\n\n"
            
            for i, memory in enumerate(memories, 1):
                output += f"{i}. [{memory.get('tag', 'unknown')}] {memory.get('text', '')}\n"
                output += f"   ID: {memory.get('id', 'unknown')} | Created: {memory.get('timestamp', 'unknown')}\n\n"
            
            return [types.TextContent(type="text", text=output)]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

async def main():
    """Main entry point"""
    # Setup HTTP client
    await setup_http_client()
    
    # Run the server using the transport
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, InitializationOptions(
            server_name="memory-server",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        ))

if __name__ == "__main__":
    asyncio.run(main())