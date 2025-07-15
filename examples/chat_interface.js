#!/usr/bin/env node

/**
 * Interactive Chat Interface with MindMirror Memory
 * 
 * Real-time chat where AI autonomously uses memory tools
 * Run: node chat_interface.js
 */

import 'dotenv/config';
import OpenAI from 'openai';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import readline from 'readline';

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Initialize MCP Client for MindMirror
const mcpClient = new Client({
  name: "interactive-chat-mindmirror",
  version: "1.0.0"
}, {
  capabilities: {}
});

let mcpTools = [];
let conversationHistory = [];

// Create readline interface for chat
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

async function connectToMindMirror() {
  console.log('🔗 Connecting to MindMirror...');
  
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
  try {
    // Add a small delay to ensure connection is fully established
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const tools = await mcpClient.listTools();
    console.log('🛠️  Available tools:', tools.tools.map(t => t.name).join(', '));
    
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
    
    return mcpTools;
  } catch (error) {
    console.error('❌ Failed to list tools:', error.message);
    console.log('🔄 Using known MindMirror tools as fallback');
    // Fallback: define tools manually based on what we know MindMirror supports
    mcpTools = [
      {
        type: "function",
        function: {
          name: "store_memory",
          description: "Store a new memory",
          parameters: {
            type: "object",
            properties: {
              text: { type: "string", description: "The memory text to store" },
              tag: { type: "string", description: "The memory tag (preference, habit, etc.)" }
            },
            required: ["text", "tag"]
          }
        }
      },
      {
        type: "function",
        function: {
          name: "search_memory",
          description: "Search for memories",
          parameters: {
            type: "object",
            properties: {
              query: { type: "string", description: "Search query" }
            },
            required: ["query"]
          }
        }
      },
      {
        type: "function",
        function: {
          name: "list_memories",
          description: "List all stored memories",
          parameters: {
            type: "object",
            properties: {},
            required: []
          }
        }
      },
      {
        type: "function",
        function: {
          name: "delete_memory",
          description: "Delete a specific memory",
          parameters: {
            type: "object",
            properties: {
              memory_id: { type: "string", description: "The ID of the memory to delete" }
            },
            required: ["memory_id"]
          }
        }
      }
    ];
    
    console.log('🛠️  Using fallback tool definitions');
    return mcpTools;
  }
}

async function callMcpTool(toolName, args) {
  try {
    console.log(`🛠️  AI is calling: ${toolName}`);
    
    const result = await mcpClient.callTool({
      name: toolName,
      arguments: args
    });
    
    // Extract the actual content from MCP response
    const content = result.content[0]?.text || JSON.stringify(result);
    return content;
  } catch (error) {
    console.error(`❌ Tool call failed:`, error.message);
    return `Error: ${error.message}`;
  }
}

async function chatWithAI(userMessage) {
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
    
    // Update conversation history
    conversationHistory.push(
      { role: "user", content: userMessage },
      { role: "assistant", content: finalResponse }
    );
    
    return finalResponse;
  } else {
    // AI didn't use any tools
    const aiResponse = response.content;
    
    // Update conversation history
    conversationHistory.push(
      { role: "user", content: userMessage },
      { role: "assistant", content: aiResponse }
    );
    
    return aiResponse;
  }
}

async function startInteractiveChat() {
  try {
    // Connect to MindMirror and setup tools
    await connectToMindMirror();
    
    console.log('\n🤖 Interactive Chat with MindMirror Memory');
    console.log('Type your messages below. The AI will autonomously use memory tools when needed.');
    console.log('Type "exit" to quit.\n');
    
    // Main chat loop
    const askQuestion = () => {
      rl.question('You: ', async (input) => {
        if (input.toLowerCase() === 'exit') {
          console.log('\n👋 Goodbye!');
          await mcpClient.close();
          rl.close();
          return;
        }
        
        if (input.trim() === '') {
          askQuestion();
          return;
        }
        
        try {
          const aiResponse = await chatWithAI(input);
          console.log(`AI: ${aiResponse}\n`);
        } catch (error) {
          console.error('❌ Error:', error.message);
        }
        
        askQuestion();
      });
    };
    
    askQuestion();
    
  } catch (error) {
    console.error('❌ Setup Error:', error.message);
    rl.close();
  }
}

// Handle cleanup on exit
process.on('SIGINT', async () => {
  console.log('\n👋 Goodbye!');
  await mcpClient.close();
  rl.close();
  process.exit(0);
});

// Start the interactive chat
if (import.meta.url === `file://${process.argv[1]}`) {
  startInteractiveChat();
}