#!/usr/bin/env python3
"""
Simplified Memory Controller - Returns raw JSON instead of formatted text
"""

import json
import requests
from typing import Dict, Any

class SimpleMemoryController:
    """Simplified controller that returns raw JSON to LM Studio"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.mcp_url = "http://localhost:8002"
    
    def log(self, message: str):
        if self.verbose:
            print(f"[DEBUG] {message}")
    
    def search_memory(self, query: str) -> str:
        """Search memory and return simple JSON string"""
        try:
            response = requests.post(
                f"{self.mcp_url}/search_nodes",
                json={"query": query},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            self.log(f"Raw MCP response: {json.dumps(result, indent=2)}")
            
            # Return simplified JSON string
            if "nodes" in result and result["nodes"]:
                simplified = {
                    "found_memories": len(result["nodes"]),
                    "memories": []
                }
                
                for node in result["nodes"][:3]:  # Limit to 3 results
                    memory = {
                        "text": node.get("observations", [""])[0],
                        "tag": node.get("entityType", ""),
                        "date": node.get("timestamp", "").split("T")[0]
                    }
                    simplified["memories"].append(memory)
                
                # Check for conflicts
                if "conflict_sets" in result and result["conflict_sets"]:
                    simplified["has_conflicts"] = True
                    simplified["conflict_count"] = len(result["conflict_sets"])
                
                return json.dumps(simplified)
            else:
                return json.dumps({"found_memories": 0, "message": "No memories found"})
                
        except Exception as e:
            self.log(f"Search error: {e}")
            return json.dumps({"error": str(e)})
    
    def store_memory(self, text: str) -> str:
        """Store memory and return simple confirmation"""
        try:
            response = requests.post(
                f"{self.mcp_url}/add_observations",
                json={
                    "entityName": "user",
                    "contents": [text],
                    "tag": "preference"
                },
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            return json.dumps({"status": "stored", "text": text})
            
        except Exception as e:
            return json.dumps({"error": str(e)})

def test_simple_controller():
    """Test the simplified controller"""
    controller = SimpleMemoryController(verbose=True)
    
    print("=== Testing Simplified Memory Search ===")
    result = controller.search_memory("communication preferences")
    print(f"Search result: {result}")
    
    print("\n=== Testing Memory Storage ===")
    store_result = controller.store_memory("I prefer concise responses")
    print(f"Store result: {store_result}")

if __name__ == "__main__":
    test_simple_controller()