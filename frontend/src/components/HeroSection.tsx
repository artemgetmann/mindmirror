import { Button } from "@/components/ui/button";
import { ArrowRight, Zap } from "lucide-react";

export const HeroSection = () => {
  return (
    <section className="container px-4 py-24 md:py-32">
      <div className="max-w-4xl mx-auto text-left">
        {/* CLI-style subtitle */}
        <div className="mb-6">
          <p className="text-sm font-mono text-muted-foreground">
            mindmirror(1) — persistent Claude memory for obsessive developers
          </p>
        </div>

        {/* Main Headlines */}
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
          Persistent memory for{" "}
          <span className="text-primary">Claude, Windsurf, Cursor</span>{" "}
          or your own AI models.
        </h1>
        
        <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-3xl">
          Paste once. Remember forever.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-16">
          <Button 
            size="lg" 
            className="text-lg px-8 py-6 h-auto bg-accent-neon text-accent-neon-foreground hover:bg-accent-neon/90 transition-all duration-200 hover:shadow-lg hover:shadow-accent-neon/25"
          >
            Inject Token
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
          <Button 
            variant="outline" 
            size="lg" 
            className="text-lg px-8 py-6 h-auto hover:border-accent-neon hover:text-accent-neon transition-colors"
          >
            View Integration Guide
          </Button>
        </div>

        {/* Integration Preview */}
        <div className="bg-card border-2 border-dashed border-muted rounded-lg p-6 max-w-2xl">
          <div className="text-sm text-muted-foreground mb-3 font-mono">📦 Claude Snippet</div>
          <code className="block bg-muted p-4 rounded text-sm font-mono text-left overflow-x-auto">
            {`{
  "mcpServers": {
    "mindmirror": {
      "command": "npx",
      "args": ["@mindmirror/mcp-server"],
      "env": {
        "MINDMIRROR_TOKEN": "your_token_here"
      }
    }
  }
}`}
          </code>
        </div>
      </div>
    </section>
  );
};