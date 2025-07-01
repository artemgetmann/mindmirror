#!/usr/bin/env python3
"""
Test script to debug the exact LM Studio flow that's failing
"""

import json
import requests
from typing import List, Dict, Any

def test_lm_studio_function_calling():
    """Test the exact function calling flow with LM Studio"""
    
    # Define the tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_memory",
                "description": "Search for relevant information in user memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    # Initial messages
    messages = [
        {
            "role": "system",
            "content": "You have access to a search_memory function. When the user asks about their preferences, use this function to search their memory."
        },
        {
            "role": "user", 
            "content": "What are my communication preferences?"
        }
    ]
    
    print("=== Step 1: Initial LM Studio Call ===")
    print(f"Sending messages: {json.dumps(messages, indent=2)}")
    print(f"Sending tools: {json.dumps(tools, indent=2)}")
    
    try:
        # First call to LM Studio
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "local-model",
                "messages": messages,
                "tools": tools,
                "max_tokens": 1024,
                "temperature": 0.7
            },
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return
        
        result = response.json()
        print(f"LM Studio response: {json.dumps(result, indent=2)}")
        
        # Check if tool calls were made
        if "choices" in result and result["choices"]:
            message = result["choices"][0]["message"]
            
            if "tool_calls" in message and message["tool_calls"]:
                print("\n=== Step 2: Tool Calls Detected ===")
                
                # Process each tool call
                for tool_call in message["tool_calls"]:
                    tool_id = tool_call.get("id", "unknown")
                    function_data = tool_call.get("function", {})
                    tool_name = function_data.get("name", "")
                    
                    print(f"Tool call ID: {tool_id}")
                    print(f"Tool name: {tool_name}")
                    print(f"Tool arguments: {function_data.get('arguments', '')}")
                    
                    # Execute the tool call
                    if tool_name == "search_memory":
                        try:
                            args = json.loads(function_data.get("arguments", "{}"))
                            query = args.get("query", "")
                            
                            print(f"\n=== Step 3: Executing Memory Search ===")
                            print(f"Query: {query}")
                            
                            # Call MCP wrapper
                            mcp_response = requests.post(
                                "http://localhost:8002/search_nodes",
                                json={"query": query},
                                timeout=10
                            )
                            
                            print(f"MCP response status: {mcp_response.status_code}")
                            
                            if mcp_response.status_code == 200:
                                mcp_result = mcp_response.json()
                                print(f"MCP result: {json.dumps(mcp_result, indent=2)}")
                                
                                # Format result for LM Studio
                                if "nodes" in mcp_result and mcp_result["nodes"]:
                                    tool_result = f"Found {len(mcp_result['nodes'])} memories:\n"
                                    for i, node in enumerate(mcp_result["nodes"][:3], 1):
                                        text = node.get("observations", [""])[0]
                                        tag = node.get("entityType", "")
                                        tool_result += f"{i}. {text} (tag: {tag})\n"
                                else:
                                    tool_result = "No relevant memories found."
                                
                                print(f"\n=== Step 4: Formatted Tool Result ===")
                                print(f"Tool result: {tool_result}")
                                
                                # Add tool result to messages
                                messages.append({
                                    "role": "assistant",
                                    "content": message.get("content", ""),
                                    "tool_calls": message["tool_calls"]
                                })
                                
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_id,
                                    "content": tool_result
                                })
                                
                                print(f"\n=== Step 5: Updated Messages ===")
                                print(f"Messages: {json.dumps(messages, indent=2)}")
                                
                                # Second call to LM Studio
                                print(f"\n=== Step 6: Second LM Studio Call ===")
                                final_response = requests.post(
                                    "http://localhost:1234/v1/chat/completions",
                                    headers={"Content-Type": "application/json"},
                                    json={
                                        "model": "local-model",
                                        "messages": messages,
                                        "max_tokens": 1024,
                                        "temperature": 0.7
                                    },
                                    timeout=30
                                )
                                
                                print(f"Final response status: {final_response.status_code}")
                                
                                if final_response.status_code == 200:
                                    final_result = final_response.json()
                                    print(f"Final LM Studio response: {json.dumps(final_result, indent=2)}")
                                    
                                    if "choices" in final_result and final_result["choices"]:
                                        final_message = final_result["choices"][0]["message"]
                                        print(f"\n=== FINAL ANSWER ===")
                                        print(f"Assistant: {final_message.get('content', '')}")
                                else:
                                    print(f"Final response error: {final_response.text}")
                            else:
                                print(f"MCP error: {mcp_response.text}")
                                
                        except json.JSONDecodeError as e:
                            print(f"JSON parsing error: {e}")
                        except Exception as e:
                            print(f"Tool execution error: {e}")
            else:
                print("No tool calls in response")
                print(f"Direct response: {message.get('content', '')}")
        else:
            print("No choices in response")
            
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_lm_studio_function_calling()