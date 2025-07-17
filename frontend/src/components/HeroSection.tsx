import { Button } from "@/components/ui/button";
import { TokenModal } from "@/components/TokenModal";
import { ArrowRight, Zap } from "lucide-react";
import { Link } from "react-router-dom";

export const HeroSection = () => {
  return (
    <section className="container px-4 py-24 md:py-32">
      <div className="max-w-4xl mx-auto text-left">
        {/* CLI-style subtitle */}
        <div className="mb-6">
          <p className="text-sm font-mono text-muted-foreground">
            mindmirror(1) — Give AI the ability to never forget anything about you
          </p>
        </div>

        {/* Main Headlines */}
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
          Persistent memory for{" "}
          <span className="text-primary">Claude, Windsurf, Cursor</span>{" "}
          or your own AI models
        </h1>
        
        <p className="text-xl md:text-2xl text-muted-foreground mb-6 max-w-3xl">
          The World's Most Advanced AI Memory System!
        </p>
        
        <p className="text-lg text-muted-foreground mb-12 max-w-3xl">
          Just paste one URL and your AI will remember everything across chats. No more repeating your preferences, goals, or project setup — your AI just remembers
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-16">
          <TokenModal
            trigger={
              <Button 
                size="lg" 
                className="text-lg px-8 py-6 h-auto bg-accent-neon text-accent-neon-foreground hover:bg-accent-neon/90 transition-all duration-200 hover:shadow-lg hover:shadow-accent-neon/25"
              >
                Inject Token
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            }
          />
          <Button 
            variant="outline" 
            size="lg" 
            asChild
            className="text-lg px-8 py-6 h-auto hover:border-accent-neon hover:text-accent-neon transition-colors"
          >
            <Link to="/integration">
              View Integration Guide
            </Link>
          </Button>
        </div>

        {/* Integration Preview */}
        <div className="bg-card border-2 border-dashed border-muted rounded-lg p-6 max-w-3xl">
          <div className="text-sm text-muted-foreground mb-3 font-mono">🔗 Add to Claude:</div>
          <code className="block bg-muted p-4 rounded text-sm font-mono text-left overflow-x-auto">
            https://memory.usemindmirror.com/sse?token=••••••••••••••••••••••••••••••••••••••••••••••••
          </code>
          <div className="text-xs text-muted-foreground mt-2 font-mono">
            Get your personal token above ↑
          </div>
        </div>
      </div>
    </section>
  );
};