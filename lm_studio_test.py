#!/usr/bin/env python3
"""
Simple script to test LM Studio with existing MCP memory system.
"""

import os
import requests
import json

# You can use your existing MCP wrapper directly
MEMORY_MCP_URL = "http://localhost:8002"

# System prompt with instructions for memory handling
SYSTEM_PROMPT = """
You have access to an MCP memory server at http://localhost:8002.

When a user question matches memories or preferences, you should:
- Check memory by calling: POST /search_nodes with {"query": user's question}
- If conflict_sets are returned, acknowledge conflicts and ask for clarification
- Process response and use memory data in your answer

When the user shares a new fact or preference, store it by:
- Calling: POST /add_observations with {"entityName": "user", "contents": ["user's fact"]}

Important: Include the actual curl commands in your response when you use memory functions.
"""

def call_lm_studio(messages):
    """Make a request to LM Studio's OpenAI-compatible API"""
    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": "local-model",
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
        },
    )
    return response.json()

def main():
    """Test the system with sample queries"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    print("\n=== LM Studio + MCP Memory Test ===\n")
    print("Type 'exit' to quit\n")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ("exit", "quit", "bye"):
            break
            
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        try:
            print("\nWaiting for LM Studio response...")
            result = call_lm_studio(messages)
            
            if "choices" in result and result["choices"]:
                assistant_message = result["choices"][0]["message"]["content"]
                print(f"\nLM Studio: {assistant_message}")
                
                # Add assistant message to history
                messages.append({"role": "assistant", "content": assistant_message})
            else:
                print("\nError: Unexpected response format from LM Studio")
                print(f"Response: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
