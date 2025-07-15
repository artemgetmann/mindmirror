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
              <TabsTrigger value="claude">Claude Desktop</TabsTrigger>
              <TabsTrigger value="cursor">Cursor</TabsTrigger>
              <TabsTrigger value="windsurf">Windsurf</TabsTrigger>
              <TabsTrigger value="custom">Custom AI</TabsTrigger>
            </TabsList>

            <TabsContent value="claude" className="space-y-6">
              <Card className="border-2 border-dashed border-muted">
                <CardHeader>
                  <CardTitle className="font-mono">📦 Claude Desktop Setup</CardTitle>
                  <CardDescription>
                    Add MindMirror to your Claude Desktop configuration
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">1. Open Claude Desktop Settings</h4>
                    <p className="text-sm text-muted-foreground mb-2">Navigate to:</p>
                    <code className="block bg-muted p-2 rounded font-mono text-sm">
                      ~/.claude_desktop_config.json
                    </code>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">2. Add MindMirror Tool</h4>
                    <pre className="bg-muted p-4 rounded overflow-x-auto font-mono text-sm">
{`{
  "tools": {
    "mindmirror": {
      "url": "https://api.mindmirror.ai/your-token-here",
      "description": "Persistent memory for Claude"
    }
  }
}`}
                    </pre>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">3. Generate Your Token</h4>
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
                    <h4 className="font-semibold mb-2">1. Open Cursor Settings</h4>
                    <p className="text-sm text-muted-foreground mb-2">Go to Settings → AI Models</p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">2. Add Custom Tool</h4>
                    <pre className="bg-muted p-4 rounded overflow-x-auto font-mono text-sm">
{`// Add to your cursor settings
"ai.tools": {
  "mindmirror": {
    "endpoint": "https://api.mindmirror.ai/your-token-here",
    "description": "Memory persistence"
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
                    <h4 className="font-semibold mb-2">1. Access Windsurf Configuration</h4>
                    <p className="text-sm text-muted-foreground">Navigate to your Windsurf settings panel</p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">2. Add External Tool</h4>
                    <p className="text-sm text-muted-foreground mb-2">Paste your MindMirror URL:</p>
                    <code className="block bg-muted p-2 rounded font-mono text-sm">
                      https://api.mindmirror.ai/your-token-here
                    </code>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="custom" className="space-y-6">
              <Card className="border-2 border-dashed border-muted">
                <CardHeader>
                  <CardTitle className="font-mono">📦 Custom AI Setup</CardTitle>
                  <CardDescription>
                    Integrate with your own AI implementation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">API Endpoint</h4>
                    <code className="block bg-muted p-2 rounded font-mono text-sm">
                      GET/POST https://api.mindmirror.ai/memory/{`{token}`}
                    </code>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-2">Example Implementation</h4>
                    <pre className="bg-muted p-4 rounded overflow-x-auto font-mono text-sm">
{`// Store memory
await fetch('https://api.mindmirror.ai/memory/your-token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    memory: "User prefers dark mode",
    context: "UI preferences"
  })
});

// Retrieve memory
const response = await fetch('https://api.mindmirror.ai/memory/your-token');
const memories = await response.json();`}
                    </pre>
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