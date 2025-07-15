#!/usr/bin/env python3
"""
Test different message formats to see what LM Studio accepts
"""

import json
import requests

def test_message_format(format_name: str, messages: list):
    """Test a specific message format with LM Studio"""
    
    print(f"\n=== Testing {format_name} ===")
    print(f"Messages: {json.dumps(messages, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "local-model", 
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.7
            },
            timeout=15
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"].get("content", "")
                print(f"Response: {content}")
                print("✅ SUCCESS")
            else:
                print("❌ No choices in response")
        else:
            print(f"❌ ERROR: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

def run_tests():
    """Run different message format tests"""
    
    # Test 1: Standard tool role (OpenAI format)
    test_message_format("Standard Tool Role", [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are my preferences?"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"id": "call_123", "type": "function", "function": {"name": "search_memory", "arguments": '{"query": "preferences"}'}}
        ]},
        {"role": "tool", "tool_call_id": "call_123", "content": "Found 2 preferences: I like direct communication. I prefer concise responses."}
    ])
    
    # Test 2: Assistant role with tool result (alternative format)
    test_message_format("Assistant Role with Tool Info", [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are my preferences?"},
        {"role": "assistant", "content": "I found your preferences: I like direct communication. I prefer concise responses."}
    ])
    
    # Test 3: Function role (older format)
    test_message_format("Function Role", [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are my preferences?"},
        {"role": "function", "name": "search_memory", "content": "Found 2 preferences: I like direct communication. I prefer concise responses."}
    ])
    
    # Test 4: User role with function result (fallback)
    test_message_format("User Role with Function Result", [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are my preferences?"},
        {"role": "user", "content": "Function result: Found 2 preferences: I like direct communication. I prefer concise responses. Now please answer my question."}
    ])
    
    # Test 5: System role with function result
    test_message_format("System Role with Function Result", [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are my preferences?"},
        {"role": "system", "content": "MEMORY SEARCH RESULT: Found 2 preferences: I like direct communication. I prefer concise responses."},
        {"role": "assistant", "content": "Based on the memory search, here are your preferences..."}
    ])

if __name__ == "__main__":
    run_tests()