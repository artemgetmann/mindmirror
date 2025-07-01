#!/usr/bin/env python3
"""
Memory Controller - Connects LLM function calls to MCP memory system

This controller creates a bridge between:
1. Local LLM with function-calling (LM Studio on port 1234)
2. MCP memory wrapper (on port 8002)

The flow:
- User input → sent to LLM
- LLM may call memory functions (search/store)
- Controller executes actual API calls to MCP
- Results returned to LLM to complete its response
"""

import os
import sys
import json
import requests
import argparse
from typing import Dict, List, Any, Optional

# Configuration
LLM_BASE_URL = "http://localhost:1234/v1"
OPENAI_API_URL = f"{LLM_BASE_URL}/chat/completions"
MCP_URL = "http://localhost:8002"
MODEL_NAME = "local-model"  # LM Studio doesn't need actual model name
LLM_KEY = "sk-local"  # any value works for LM Studio
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LLM_KEY}"
}

# Define memory functions for function-calling
MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search for relevant information in user memory using semantic search",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant memories"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "user_preferences",
            "description": "Store a new user preference or observation",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_info": {
                        "type": "string",
                        "description": "The preference or fact to remember about the user"
                    }
                },
                "required": ["new_info"]
            }
        }
    }
]

class MemoryController:
    """Controller for bridging LLM function calls with MCP memory system"""
    
    def __init__(self, verbose: bool = False):
        """Initialize the controller"""
        self.verbose = verbose
        self.messages = [{
            "role": "system",
            "content": (
                "IMPORTANT: You are an assistant with access to ONLY these two functions:\n"
                "1. search_memory - Use this to find user preferences\n"
                "2. user_preferences - Use this to store user preferences\n\n"
                
                "CRITICAL RULES FOR CAPTURING PREFERENCES:\n"
                "- When the user says 'I prefer X' → call user_preferences with {new_info: 'X'}\n"
                "- When the user says 'Actually, I prefer Y' → call user_preferences with {new_info: 'Y'}\n"
                "- When the user contradicts a previous preference → call user_preferences\n\n"
                
                "CRITICAL RULES FOR HANDLING CONFLICTS:\n"
                "1. ALWAYS check search_memory responses for 'clear_conflicts' field\n"
                "2. If clear_conflicts exists, you MUST start your response with:\n"
                "   'I notice conflicting preferences about [topic]:' followed by the conflicting preferences\n"
                "3. List each conflicting preference with its timestamp:\n"
                "   * Preference X (from date Y)\n"
                "   * Preference Z (from date W)\n"
                "4. EXPLICITLY ASK which preference the user wants to keep\n\n"
                
                "CRITICAL RULES FOR PROVIDING ADVICE:\n"
                "- When the user asks 'How should I...' always call search_memory with the query\n"
                "- Use the most recent preference if there are no conflicts\n"
                "- If there are conflicts and the user hasn't clarified, ask which preference to use\n"
                "- NEVER give contradicting advice - be clear about which preference you're following\n\n"
                
                "DO NOT store guidance or suggestions as user preferences.\n"
                "DO NOT attempt to use any other tools like write_email, email_guidelines, etc.\n"
                "ONLY use search_memory and user_preferences as described above."
            )
        }]
    
    def log(self, message: str):
        """Print a log message if verbose mode is on"""
        if self.verbose:
            print(f"[LOG] {message}")
    
    def search_memory(self, query: str) -> Dict[str, Any]:
        """Search for memories related to a query"""
        try:
            response = requests.post(
                f"{MCP_URL}/search_nodes",
                json={"query": query},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # MCP wrapper already processes conflicts into the correct format
            # No need to reprocess them here - they're ready for formatting
            
            self.log(f"Search result: {json.dumps(result)[:200]}...")
            return result
        except Exception as e:
            self.log(f"Error searching memory: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def format_tool_result_for_llm(self, tool_result: Dict[str, Any]) -> str:
        """Convert complex tool results into clean, readable text for LM Studio"""
        try:
            # Handle error cases
            if "error" in tool_result:
                return f"Error: {tool_result['error']}"
            
            # Handle search results with conflicts (from MCP wrapper format)
            if "conflict_sets" in tool_result and tool_result["conflict_sets"]:
                conflicts_text = "🚨 CONFLICTING PREFERENCES DETECTED:\n\n"
                
                # Get nodes for reference
                nodes = tool_result.get("nodes", [])
                node_map = {node.get("name"): node for node in nodes}
                
                # Track unique preference texts to avoid duplicates
                seen_preferences = set()
                conflict_groups = []
                
                # Process conflict sets to find actual conflicting preference texts
                for conflict_set in tool_result["conflict_sets"]:
                    primary_id = conflict_set.get("primary_memory", "")
                    conflicting_ids = conflict_set.get("conflicting_memories", [])
                    
                    # Get texts for this conflict group
                    conflict_texts = []
                    all_ids = [primary_id] + conflicting_ids
                    
                    for mem_id in all_ids:
                        if mem_id in node_map:
                            node = node_map[mem_id]
                            text = node.get("observations", [""])[0] if node.get("observations") else ""
                            timestamp = node.get("timestamp", "").split("T")[0] if node.get("timestamp") else "unknown"
                            if text and text not in seen_preferences:
                                conflict_texts.append((text, timestamp))
                                seen_preferences.add(text)
                    
                    if len(conflict_texts) > 1:  # Only add if we have actual different texts
                        conflict_groups.append(conflict_texts)
                
                # Format conflicts for display
                if conflict_groups:
                    conflicts_text += "I found conflicting communication preferences:\n\n"
                    for i, group in enumerate(conflict_groups[:2], 1):  # Limit to top 2 conflicts
                        conflicts_text += f"Conflict #{i}:\n"
                        for text, date in group:
                            conflicts_text += f"  • \"{text}\" (from {date})\n"
                        conflicts_text += "\n"
                    
                    conflicts_text += "❓ PLEASE ASK THE USER: Which preference should I keep and use going forward?"
                    return conflicts_text
            
            # Handle search results without conflicts (MCP wrapper format)
            if "nodes" in tool_result and tool_result["nodes"]:
                nodes = tool_result["nodes"]
                if len(nodes) == 0:
                    return "No relevant memories found."
                
                result_text = f"Found {len(nodes)} relevant memories:\n\n"
                for i, node in enumerate(nodes[:5], 1):  # Limit to top 5
                    text = node.get("observations", [""])[0] if node.get("observations") else ""
                    tag = node.get("entityType", "")
                    date = node.get("timestamp", "").split("T")[0] if node.get("timestamp") else "unknown date"
                    if text:
                        result_text += f"{i}. {text} (tag: {tag}, from: {date})\n"
                
                if len(nodes) > 5:
                    result_text += f"\n... and {len(nodes) - 5} more memories"
                
                return result_text
            
            # Handle storage confirmations
            if "status" in tool_result:
                if tool_result["status"] == "success":
                    return "✅ Preference stored successfully!"
                elif tool_result["status"] == "error":
                    return f"❌ Error: {tool_result.get('message', 'Unknown error')}"
            
            # Default fallback - return a simple summary
            return f"Tool executed. Status: {tool_result.get('status', 'completed')}"
            
        except Exception as e:
            return f"Error formatting result: {str(e)}"
    
    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate API call based on the tool name"""
        self.log(f"Executing tool: {tool_name} with args: {tool_args}")
        
        try:
            if tool_name == "search_memory":
                return self.search_memory(tool_args.get("query", ""))
            
            elif tool_name == "user_preferences":
                # Don't store LLM guidance as preferences
                info = tool_args.get("new_info", "")
                if info.startswith("Here's") or info.startswith("Here is") or info.startswith("Based on"):
                    self.log(f"Skipping storing LLM guidance: {info[:50]}...")
                    return {"status": "error", "message": "Cannot store LLM guidance as preferences"}
                
                # Clean up the preference text
                if info.lower().startswith("remember that"):
                    info = info[len("remember that"):].strip()
                
                # Call MCP add observations endpoint
                response = requests.post(
                    f"{MCP_URL}/add_observations",
                    json={
                        "entityName": "user",
                        "contents": [info],
                        "tag": "preference"
                    },
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                self.log(f"Store result: {json.dumps(result)[:200]}...")
                return result
                
            # Handle any other tools LM Studio might try to call by redirecting to appropriate memory functions
            elif tool_name in ["write_email", "email_guidelines", "write_email_guidelines"]:
                # Redirect to search_memory
                self.log(f"Redirecting {tool_name} to search_memory")
                response = requests.post(
                    f"{MCP_URL}/search_nodes",
                    json={"query": "email writing preferences"},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                return result
            else:
                self.log(f"Unknown tool: {tool_name}, forcing memory search")
                # Default to memory search with the tool name as query
                response = requests.post(
                    f"{MCP_URL}/search_nodes",
                    json={"query": tool_name},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                return result
        
        except Exception as e:
            self.log(f"Error executing tool {tool_name}: {str(e)}")
            return {"error": str(e)}
    
    def call_llm(self, user_input: str) -> str:
        """Process user input through LLM with function calls"""
        # Add user message to conversation
        self.messages.append({"role": "user", "content": user_input})
        
        # Check for explicit preference statements and force tool usage
        force_preference_storage = False
        force_memory_search = False
        preference_text = ""
        search_query = ""
        
        # Detect questions for search and preferences for storage
        is_question = user_input.strip().endswith("?") or user_input.lower().startswith("how") or user_input.lower().startswith("what") or user_input.lower().startswith("when") or user_input.lower().startswith("why") or user_input.lower().startswith("where") or user_input.lower().startswith("who") or user_input.lower().startswith("which")
        
        # For questions, use memory search
        if is_question:
            force_memory_search = True
            search_query = user_input
            self.log(f"Question detected: {search_query}")
        # For preference statements, store them
        elif any(pattern in user_input.lower() for pattern in [
            "i prefer", "i like", "i want", "i need", "i don't like", 
            "actually, i", "actually i", "i would rather", "i'd rather",
            "i don't want", "instead, i"]):
            force_preference_storage = True
            preference_text = user_input
            self.log(f"Direct preference detected: {preference_text}")
            
        # Log thinking state first
        self.log("Thinking...")
        
        try:
            # If we detected a direct preference statement, force tool usage
            if force_preference_storage:
                # Execute the user_preferences tool directly
                result = self.execute_tool("user_preferences", {"new_info": preference_text})
                self.log(f"Forced preference storage: {preference_text}")
                
            # If we detected a question, force memory search
            if force_memory_search:
                # Execute the search_memory tool directly
                result = self.execute_tool("search_memory", {"query": search_query})
                self.log(f"Forced memory search: {search_query}")
            
            # LLM API call
            response = requests.post(
                OPENAI_API_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": self.messages,
                    "tools": MEMORY_TOOLS
                },
                headers=HEADERS,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract the message
            if "choices" not in result or not result["choices"]:
                raise Exception("Invalid response format from LLM")
                
            message = result["choices"][0]["message"]
            
            # Check for tool calls
            if "tool_calls" in message and message["tool_calls"]:
                # Process each tool call
                for tool_call in message["tool_calls"]:
                    tool_id = tool_call.get("id", "unknown")
                    function_data = tool_call.get("function", {})
                    tool_name = function_data.get("name", "")
                    
                    try:
                        # Parse arguments
                        tool_args = json.loads(function_data.get("arguments", "{}"))
                        
                        # Execute the tool
                        tool_result = self.execute_tool(tool_name, tool_args)
                        self.log(f"Tool {tool_name} returned: {json.dumps(tool_result)[:300]}...")
                        
                        # Format the result as clean text for LM Studio
                        formatted_result = self.format_tool_result_for_llm(tool_result)
                        self.log(f"Formatted result for LLM: {formatted_result[:200]}...")
                        
                        # Add tool result to messages
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": formatted_result
                        })
                        
                    except json.JSONDecodeError:
                        self.log(f"Invalid tool arguments: {function_data.get('arguments', '')}")
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_id, 
                            "content": json.dumps({"error": "Invalid arguments"})
                        })
                
                # Second LLM call to process tool results
                response = requests.post(
                    OPENAI_API_URL,
                    headers=HEADERS,
                    json={
                        "model": MODEL_NAME,
                        "messages": self.messages,
                    },
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                if "choices" not in result or not result["choices"]:
                    raise Exception("Invalid response format from second LLM call")
                    
                message = result["choices"][0]["message"]
            
            # Add assistant's response to messages
            self.messages.append({
                "role": "assistant",
                "content": message.get("content", "")
            })
            
            return message.get("content", "")
            
        except Exception as e:
            error_msg = f"Error calling LLM: {str(e)}"
            self.log(error_msg)
            return error_msg
    
    def chat_loop(self):
        """Run an interactive chat loop"""
        print("\n=== Memory-Enabled Assistant ===")
        print("Type 'exit' to quit\n")
        
        try:
            while True:
                try:
                    user_input = input("\nYou: ")
                    if not user_input:
                        continue
                        
                    if user_input.lower() in ("exit", "quit", "bye"):
                        print("\nGoodbye!")
                        break
                        
                    print("\nThinking...")
                    response = self.call_llm(user_input)
                    print(f"\nAssistant: {response}")
                    
                except EOFError:
                    print("\nInput stream ended. Exiting.")
                    break
                except KeyboardInterrupt:
                    print("\nInterrupted. Exiting.")
                    break
                except Exception as e:
                    print(f"\nError processing input: {str(e)}")
                    
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            return

def main():
    """Main entry point"""
    # Declare globals at the beginning
    global LLM_BASE_URL, MCP_URL, OPENAI_API_URL, HEADERS
    
    parser = argparse.ArgumentParser(description="Memory Controller")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--llm-url", 
        default=LLM_BASE_URL,
        help=f"LLM API base URL (default: {LLM_BASE_URL})"
    )
    parser.add_argument(
        "--mcp-url", 
        default=MCP_URL,
        help=f"MCP memory API URL (default: {MCP_URL})"
    )
    args = parser.parse_args()
    
    # Update global URLs if provided
    LLM_BASE_URL = args.llm_url
    MCP_URL = args.mcp_url
    
    # Create and run the controller
    controller = MemoryController(verbose=args.verbose)
    controller.chat_loop()

if __name__ == "__main__":
    main()
