import { Link } from "react-router-dom";
import { Navigation } from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Terminal } from "lucide-react";

const NotFound = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container flex items-center justify-center py-16">
        <div className="text-center max-w-2xl">
          <div className="mb-8">
            <Terminal className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h1 className="text-6xl font-bold font-mono mb-4">404</h1>
            <h2 className="text-2xl font-semibold mb-2">Memory Not Found</h2>
            <p className="text-muted-foreground font-mono">
              The page you're looking for has been garbage collected.
            </p>
          </div>
          
          <div className="bg-muted p-6 rounded border-2 border-dashed font-mono text-left mb-8">
            <div className="text-sm space-y-1">
              <div className="text-accent-neon">$ mindmirror --help</div>
              <div className="text-muted-foreground">Available routes:</div>
              <div className="text-muted-foreground">  /           # Landing page</div>
              <div className="text-muted-foreground">  /integration # Setup guides</div>
              <div className="text-muted-foreground">  /premium    # Pricing & limits</div>
              <div className="text-muted-foreground">  /about      # Project info</div>
              <div className="text-accent-neon mt-2">$ _</div>
            </div>
          </div>
          
          <div className="space-x-4">
            <Button asChild className="bg-accent-neon text-accent-neon-foreground hover:bg-accent-neon/90">
              <Link to="/">Return Home</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/integration">View Docs</Link>
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default NotFound;