#!/usr/bin/env node

/**
 * MCP-to-OpenAI Function Calling Bridge
 * 
 * This demonstrates how to connect any OpenAI-compatible API to MCP servers
 * The AI autonomously decides when to use memory tools - no manual context injection
 */

import 'dotenv/config';
import OpenAI from 'openai';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Initialize MCP Client for MindMirror
const mcpClient = new Client({
  name: "openai-mindmirror-bridge",
  version: "1.0.0"
}, {
  capabilities: {}
});

let mcpTools = [];

async function connectToMindMirror() {
  console.log('🔗 Connecting to MindMirror MCP server...');
  
  const transport = new StdioClientTransport({
    command: 'npx',
    args: [
      'mcp-remote', 
      `${process.env.MINDMIRROR_URL}?token=${process.env.MINDMIRROR_TOKEN}`
    ]
  });

  await mcpClient.connect(transport);
  console.log('✅ Connected to MindMirror');
  
  // Get available MCP tools and convert to OpenAI function format
  const tools = await mcpClient.listTools();
  console.log('📋 Available MCP tools:', tools.tools.map(t => t.name));
  
  // Convert MCP tools to OpenAI function definitions
  mcpTools = tools.tools.map(tool => ({
    type: "function",
    function: {
      name: tool.name,
      description: tool.description,
      parameters: tool.inputSchema || {
        type: "object",
        properties: {},
        required: []
      }
    }
  }));
  
  console.log('🔄 Converted to OpenAI functions:', mcpTools.map(t => t.function.name));
  return mcpTools;
}

async function callMcpTool(toolName, args) {
  try {
    console.log(`🛠️  Calling MCP tool: ${toolName} with args:`, args);
    
    const result = await mcpClient.callTool({
      name: toolName,
      arguments: args
    });
    
    // Extract the actual content from MCP response
    const content = result.content[0]?.text || JSON.stringify(result);
    console.log(`✅ MCP tool result: ${content.substring(0, 100)}...`);
    
    return content;
  } catch (error) {
    console.error(`❌ MCP tool call failed:`, error.message);
    return `Error: ${error.message}`;
  }
}

async function chatWithAutonomousMemory(userMessage, conversationHistory = []) {
  console.log(`\\n👤 User: ${userMessage}`);
  
  // Build the conversation with the new message
  const messages = [
    {
      role: "system",
      content: "You are an AI assistant with persistent memory capabilities. You have access to memory tools: store_memory, search_memory, list_memories, delete_memory. Use these tools autonomously when appropriate. When users ask about their stored information, use list_memories to show them what you know."
    },
    ...conversationHistory,
    { role: "user", content: userMessage }
  ];
  
  // Call OpenAI with memory tools available
  const completion = await openai.chat.completions.create({
    model: "gpt-3.5-turbo",
    messages: messages,
    tools: mcpTools,  // MindMirror memory tools
    tool_choice: "auto"  // Let AI decide when to use tools
  });
  
  const response = completion.choices[0].message;
  
  // Check if AI decided to use any tools
  if (response.tool_calls) {
    console.log(`🤖 AI is calling ${response.tool_calls.length} tool(s):`);
    
    // Execute each tool call the AI requested
    const toolResults = [];
    
    for (const toolCall of response.tool_calls) {
      const { name, arguments: args } = toolCall.function;
      const parsedArgs = JSON.parse(args);
      
      // Call the MCP tool
      const result = await callMcpTool(name, parsedArgs);
      
      toolResults.push({
        tool_call_id: toolCall.id,
        role: "tool",
        content: result
      });
    }
    
    // Get AI's final response after using tools
    const finalCompletion = await openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        ...messages,
        response,  // AI's message with tool calls
        ...toolResults  // Tool results
      ]
    });
    
    const finalResponse = finalCompletion.choices[0].message.content;
    console.log(`🤖 Assistant: ${finalResponse}`);
    
    return {
      response: finalResponse,
      toolsUsed: response.tool_calls.map(tc => tc.function.name),
      conversationHistory: [
        ...conversationHistory,
        { role: "user", content: userMessage },
        { role: "assistant", content: finalResponse }
      ]
    };
  } else {
    // AI didn't use any tools
    console.log(`🤖 Assistant: ${response.content}`);
    
    return {
      response: response.content,
      toolsUsed: [],
      conversationHistory: [
        ...conversationHistory,
        { role: "user", content: userMessage },
        { role: "assistant", content: response.content }
      ]
    };
  }
}

async function runBridgeDemo() {
  try {
    // Connect to MindMirror and setup tools
    await connectToMindMirror();
    
    console.log('\\n🚀 Starting OpenAI ↔ MCP Bridge Demo');
    console.log('The AI will autonomously decide when to use memory tools\\n');
    
    let conversation = [];
    
    // Test autonomous memory behavior
    const demo1 = await chatWithAutonomousMemory("Hi! I prefer working early in the morning when it's quiet.", conversation);
    conversation = demo1.conversationHistory;
    
    const demo2 = await chatWithAutonomousMemory("I also really enjoy using TypeScript for backend projects.", conversation);
    conversation = demo2.conversationHistory;
    
    const demo3 = await chatWithAutonomousMemory("What would be the best time for me to schedule a coding session?", conversation);
    conversation = demo3.conversationHistory;
    
    const demo4 = await chatWithAutonomousMemory("What programming language should I use for my next project?", conversation);
    conversation = demo4.conversationHistory;
    
    // KEY TEST: Ask AI to list memories - it should autonomously call list_memories tool
    const demo5 = await chatWithAutonomousMemory("Can you list all my stored memories?", conversation);
    conversation = demo5.conversationHistory;
    
    console.log('\\n📊 Demo Summary:');
    console.log('Demo 1 tools used:', demo1.toolsUsed);
    console.log('Demo 2 tools used:', demo2.toolsUsed);
    console.log('Demo 3 tools used:', demo3.toolsUsed);
    console.log('Demo 4 tools used:', demo4.toolsUsed);
    console.log('Demo 5 tools used:', demo5.toolsUsed);
    
    console.log('\\n✨ Bridge Demo Complete!');
    console.log('🎯 Key Success: AI autonomously decided when to store and retrieve memories');
    
  } catch (error) {
    console.error('❌ Bridge Demo Error:', error.message);
  } finally {
    await mcpClient.close();
  }
}

// Run the demo
if (import.meta.url === `file://${process.argv[1]}`) {
  runBridgeDemo();
}