# MindMirror Examples

Examples showing how to add persistent memory to your own AI systems using the Model Context Protocol (MCP).

## Interactive Chat Interface (Recommended)

**File:** `chat_interface.js`

Real-time chat interface that demonstrates autonomous AI memory behavior. The AI decides when to use memory tools based on natural language queries.

### What it demonstrates

- ✅ **Autonomous tool usage** - AI decides when to call memory tools
- ✅ **Natural language interface** - "what do you know" → AI calls `what_do_you_know`
- ✅ **Real-time interaction** - streaming responses with tool calls
- ✅ **Persistent memory** - stores and retrieves user preferences

### Example interaction

```bash
$ npm start

🤖 Interactive Chat with MindMirror Memory
Type your messages below. Type "exit" to quit.

You: what do you know about me?
🛠️  AI is calling: what_do_you_know  
AI: Here's what I know (4 total): ...

You: remember i like vim
🛠️  AI is calling: remember
AI: I'll remember that!

You: what are my preferences?
🛠️  AI is calling: recall
AI: I remember 3 things about your preferences: working mornings, TypeScript, Vim...
```

### Key insight

The AI **autonomously decides** when to use memory tools. No manual context injection - just natural conversation.

## Bridge Implementation (For Developers)

**File:** `openai_mcp_bridge.js`

Reference implementation showing how to convert MCP tools to OpenAI function calls. Useful for understanding the bridge architecture.

### What it demonstrates

- ✅ **MCP to OpenAI function calling** conversion
- ✅ **Programmatic testing** of autonomous behavior
- ✅ **Error handling** and fallback mechanisms
- ✅ **Tool call execution** flow

### Usage

```bash
npm run bridge
```

## Setup

1. **Install dependencies:**
   ```bash
   cd examples/
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and MindMirror token
   ```

3. **Run examples:**
   ```bash
   npm start          # Interactive chat interface
   npm run chat       # Same as above
   npm run bridge     # Bridge implementation demo
   ```

## Architecture

```
Your AI App → MCP Client → mcp-remote → MindMirror Server
              ↑
         Standard MCP protocol
```

### How it works

1. **Connect** to MindMirror via MCP protocol using `mcp-remote`
2. **List tools** available from MindMirror server (`remember`, `recall`, `what_do_you_know`, `forget`)
3. **Convert** MCP tools to OpenAI function definitions
4. **Let AI decide** when to use memory tools based on user input
5. **Execute** tool calls via MCP client when AI requests them

## Key Features

- **Autonomous AI behavior** - AI decides when memory is needed
- **Universal protocol** - works with any AI platform that supports function calling
- **No manual context injection** - AI searches and stores memories naturally
- **Real-time streaming** - see tool calls as they happen
- **Persistent memory** - data stored across conversations

## Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
MINDMIRROR_TOKEN=your_mindmirror_token_here
MINDMIRROR_URL=https://memory.usemindmirror.com/sse

# Optional
MINDMIRROR_URL=https://memory.usemindmirror.com/sse  # Default production URL
```

## Integration with Your AI

To add MindMirror memory to your own AI system:

1. **Install MCP client**: `npm i @modelcontextprotocol/sdk`
2. **Connect to MindMirror**: Use `mcp-remote` with your token
3. **Convert tools**: Map MCP tools to your AI's function calling format
4. **Let AI decide**: Set `tool_choice: "auto"` and let AI use memory naturally

The AI will autonomously call memory tools when appropriate - no manual prompting needed.