#!/usr/bin/env python3
"""
Debug script to test tool result formatting and message flow
"""

import json
import requests
from memory_controller import MemoryController

def test_tool_result_formatting():
    """Test how tool results are being formatted"""
    
    controller = MemoryController(verbose=True)
    
    # Test search memory result
    test_search_result = {
        "status": "success",
        "message": "Found 2 relevant memories",
        "nodes": [
            {
                "name": "mem_123",
                "entityType": "preference",
                "observations": ["I prefer direct communication"],
                "timestamp": "2024-01-01T00:00:00Z",
                "similarity": 0.85
            },
            {
                "name": "mem_456", 
                "entityType": "preference",
                "observations": ["I like concise responses"],
                "timestamp": "2024-01-02T00:00:00Z",
                "similarity": 0.72
            }
        ]
    }
    
    # Test conflict result
    test_conflict_result = {
        "status": "success",
        "message": "Found conflicting preferences",
        "nodes": [
            {
                "name": "mem_789",
                "entityType": "preference", 
                "observations": ["I prefer detailed explanations"],
                "timestamp": "2024-01-03T00:00:00Z"
            }
        ],
        "conflict_sets": [
            {
                "primary_memory": "mem_123",
                "conflicting_memories": ["mem_789"],
                "message": "Conflicting communication preferences"
            }
        ]
    }
    
    print("=== Testing Normal Search Result ===")
    formatted_normal = controller.format_tool_result_for_llm(test_search_result)
    print(f"Formatted result:\n{formatted_normal}")
    print(f"Length: {len(formatted_normal)} characters")
    
    print("\n=== Testing Conflict Result ===")
    formatted_conflict = controller.format_tool_result_for_llm(test_conflict_result)
    print(f"Formatted result:\n{formatted_conflict}")
    print(f"Length: {len(formatted_conflict)} characters")
    
    print("\n=== Testing JSON Serialization ===")
    try:
        json_normal = json.dumps(test_search_result, indent=2)
        print("Normal result JSON serializes OK")
    except Exception as e:
        print(f"Normal result JSON error: {e}")
    
    try:
        json_conflict = json.dumps(test_conflict_result, indent=2)  
        print("Conflict result JSON serializes OK")
    except Exception as e:
        print(f"Conflict result JSON error: {e}")

def test_direct_mcp_call():
    """Test calling MCP wrapper directly"""
    
    print("\n=== Testing Direct MCP Call ===")
    try:
        response = requests.post(
            "http://localhost:8002/search_nodes",
            json={"query": "communication preferences"},
            timeout=10
        )
        
        print(f"MCP Response Status: {response.status_code}")
        print(f"MCP Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"MCP Response Data: {json.dumps(result, indent=2)}")
        else:
            print(f"MCP Response Text: {response.text}")
            
    except Exception as e:
        print(f"MCP Call Error: {e}")

def test_lm_studio_message_format():
    """Test the exact message format sent to LM Studio"""
    
    print("\n=== Testing LM Studio Message Format ===")
    
    # Simulate the message structure that would be sent
    messages = [
        {"role": "system", "content": "You have access to memory functions."},
        {"role": "user", "content": "What are my communication preferences?"},
        {"role": "assistant", "content": "", "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "arguments": '{"query": "communication preferences"}'
                }
            }
        ]},
        {"role": "tool", "tool_call_id": "call_123", "content": "Found 2 relevant memories:\n\n1. I prefer direct communication (tag: preference, from: 2024-01-01)\n2. I like concise responses (tag: preference, from: 2024-01-02)"}
    ]
    
    print("Messages that would be sent to LM Studio:")
    for i, msg in enumerate(messages):
        print(f"Message {i}: {json.dumps(msg, indent=2)}")

if __name__ == "__main__":
    test_tool_result_formatting()
    test_direct_mcp_call()
    test_lm_studio_message_format()