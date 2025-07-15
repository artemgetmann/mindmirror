import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const Integration = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-left mb-12">
            <h1 className="text-4xl font-bold mb-4">Integration Guide</h1>
            <p className="text-xl text-muted-foreground font-mono">
              mindmirror(1) — setup instructions for your AI tools
            </p>
          </div>

          <Tabs defaultValue="claude" className="w-full">
            <TabsList className="grid w-full grid-cols-4 mb-8">
              <TabsTrigger value="claude">Claude</TabsTrigger>
              <TabsTrigger value="cursor">Cursor</TabsTrigger>
              <TabsTrigger value="windsurf">Windsurf</TabsTrigger>
              <TabsTrigger value="custom">Custom AI</TabsTrigger>
            </TabsList>

            <TabsContent value="claude" className="space-y-6">
              <Card className="border-2 border-dashed border-muted">
                <CardHeader>
                  <CardTitle className="font-mono">🔗 Claude Setup</CardTitle>
                  <CardDescription>
                    Add MindMirror to Claude via Settings → Connectors
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">1. Open Claude Settings</h4>
                    <p className="text-sm text-muted-foreground mb-2">Navigate to Settings → Connectors</p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">2. Add MindMirror URL</h4>
                    <p className="text-sm text-muted-foreground mb-2">Paste your MindMirror URL:</p>
                    <code className="block bg-muted p-3 rounded font-mono text-sm">
                      https://memory.mindmirror.com/sse?token=YOUR_TOKEN_HERE
                    </code>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">Get Your Token</h4>
                    <Button className="bg-accent-neon text-accent-neon-foreground hover:bg-accent-neon/90">
                      Generate Token →
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="cursor" className="space-y-6">
              <Card className="border-2 border-dashed border-muted">
                <CardHeader>
                  <CardTitle className="font-mono">📦 Cursor Setup</CardTitle>
                  <CardDescription>
                    Integrate MindMirror with Cursor IDE
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">1. Open Cursor MCP Config</h4>
                    <p className="text-sm text-muted-foreground mb-2">Edit your MCP configuration file (path varies by system)</p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">2. Add MindMirror Config</h4>
                    <pre className="bg-muted p-4 rounded overflow-x-auto font-mono text-sm">
{`{
  "mcpServers": {
    "mindmirror": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://memory.mindmirror.com/sse?token=YOUR_TOKEN_HERE"
      ]
    }
  }
}`}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="windsurf" className="space-y-6">
              <Card className="border-2 border-dashed border-muted">
                <CardHeader>
                  <CardTitle className="font-mono">📦 Windsurf Setup</CardTitle>
                  <CardDescription>
                    Connect MindMirror to Windsurf
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">1. Open Windsurf MCP Config</h4>
                    <p className="text-sm text-muted-foreground mb-2">Edit the configuration file:</p>
                    <code className="block bg-muted p-2 rounded font-mono text-xs">
                      ~/.codeium/windsurf/mcp_config.json
                    </code>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">2. Add MindMirror Config</h4>
                    <pre className="bg-muted p-4 rounded overflow-x-auto font-mono text-sm">
{`{
  "mcpServers": {
    "mindmirror": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://memory.mindmirror.com/sse?token=YOUR_TOKEN_HERE"
      ]
    }
  }
}`}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="custom" className="space-y-6">
              <Card className="border-2 border-dashed border-muted">
                <CardHeader>
                  <CardTitle className="font-mono">🧩 Add MCP to Your Own AI</CardTitle>
                  <CardDescription>
                    Bridge MCP to any AI platform. Autonomous memory, not manual context injection.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="bg-blue-50 p-4 rounded border-l-4 border-blue-500">
                    <h5 className="font-semibold mb-2">🎯 Two Integration Paths</h5>
                    <ul className="text-sm space-y-1">
                      <li><strong>Track A:</strong> Interactive chat interface (OpenAI → MCP)</li>
                      <li><strong>Track B:</strong> Direct MCP integration (any platform)</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold mb-2">━━━ Track A: Interactive Chat Interface</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      Real-time chat where AI autonomously uses memory tools. No manual context injection needed.
                    </p>
                    
                    <div className="bg-gray-900 text-green-400 p-4 rounded font-mono text-sm mb-3">
                      <div className="mb-2">$ node chat_interface.js</div>
                      <div className="mb-2">🤖 Interactive Chat with MindMirror Memory</div>
                      <div className="mb-2">Type your messages below. Type "exit" to quit.</div>
                      <div className="mb-1"></div>
                      <div className="mb-1"><span className="text-blue-400">You:</span> list memories</div>
                      <div className="mb-1"><span className="text-gray-400">🛠️  AI is calling: list_memories</span></div>
                      <div className="mb-1"><span className="text-yellow-400">AI:</span> You have 5 memories stored...</div>
                      <div className="mb-1"></div>
                      <div className="mb-1"><span className="text-blue-400">You:</span> store i like vim</div>
                      <div className="mb-1"><span className="text-gray-400">🛠️  AI is calling: store_memory</span></div>
                      <div className="mb-1"><span className="text-yellow-400">AI:</span> I've stored that you like Vim!</div>
                    </div>

                    <pre className="bg-muted p-4 rounded overflow-x-auto font-mono text-sm">
{`// npm i @modelcontextprotocol/sdk openai dotenv readline
import OpenAI from 'openai';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import readline from 'readline';

const mcpClient = new Client({ name: "my-chat", version: "1.0.0" });
const transport = new StdioClientTransport({
  command: 'npx',
  args: ['mcp-remote', 'https://memory.mindmirror.com/sse?token=TOKEN']
});

await mcpClient.connect(transport);
const tools = await mcpClient.listTools();

// AI autonomously decides when to use memory tools
const completion = await openai.chat.completions.create({
  model: "gpt-3.5-turbo",
  messages: [{ role: "user", content: userInput }],
  tools: convertMcpToOpenAiTools(tools),
  tool_choice: "auto"
});`}
                    </pre>
                    <p className="text-sm text-muted-foreground mt-2">
                      <a href="https://github.com/artemis-ai/mindmirror/tree/main/examples" className="text-accent-neon hover:underline font-mono">
                        → Full interactive chat example
                      </a>
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">━━━ Track B: Direct MCP Integration</h4>
                    <p className="text-sm text-muted-foreground mb-3">Build your own MCP client for full control</p>
                    <pre className="bg-muted p-4 rounded overflow-x-auto font-mono text-sm">
{`import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const client = new Client({ name: 'my-ai', version: '1.0.0' });

const transport = new StdioClientTransport({
  command: 'npx',
  args: ['mcp-remote', 'https://memory.mindmirror.com/sse?token=TOKEN']
});

await client.connect(transport);

// Use memory tools directly
const result = await client.callTool({
  name: 'search_memory',
  arguments: { query: 'user preferences' }
});`}
                    </pre>
                  </div>
                  
                  
                  <div className="bg-gray-50 p-4 rounded border-l-4 border-accent-neon">
                    <h5 className="font-semibold mb-2">Why MCP Instead of REST?</h5>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• <strong>Autonomous AI behavior</strong> - AI decides when to use memory tools</li>
                      <li>• <strong>Universal protocol</strong> - works with Claude, OpenAI, Azure, etc.</li>
                      <li>• <strong>No manual context injection</strong> - AI searches and stores memories naturally</li>
                      <li>• <strong>Real-time interaction</strong> - streaming responses with tool calls</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Integration;