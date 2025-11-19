import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Check } from "lucide-react";
import { useState } from "react";
import { memoryApi } from "@/api/memory";
import { useToast } from "@/hooks/use-toast";

const Premium = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleWaitlistSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !email.includes('@')) {
      toast({
        title: "Invalid email",
        description: "Please enter a valid email address.",
        variant: "destructive"
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await memoryApi.joinWaitlist({ email });
      toast({
        title: "Success!",
        description: "You've been added to the premium waitlist.",
      });
      setEmail("");
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to join waitlist",
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-left mb-12">
            <h1 className="text-4xl font-bold mb-2 font-mono">
              mindmirror(1) — Premium
            </h1>
            <p className="text-sm text-muted-foreground font-mono mb-4">
              Unlimited memory. Advanced features. Full export control.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <Card className="border-2 border-muted">
              <CardHeader>
                <CardTitle className="font-mono">Free Tier</CardTitle>
                <CardDescription>Good for testing and light usage</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">25 memory entries</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Basic memory persistence</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Standard conflict detection</span>
                  </div>
                </div>
                <div className="text-2xl font-bold">$0</div>
              </CardContent>
            </Card>

            <Card className="border-2 border-accent-neon bg-accent-neon/5">
              <CardHeader>
                <CardTitle className="font-mono text-accent-neon">Premium Tier</CardTitle>
                <CardDescription>For obsessive developers who need everything</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-accent-neon" />
                    <span className="text-sm">Unlimited memory entries</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-accent-neon" />
                    <span className="text-sm">Full memory export (JSON/CSV)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-accent-neon" />
                    <span className="text-sm">Advanced search & filtering</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-accent-neon" />
                    <span className="text-sm">Memory analytics dashboard</span>
                  </div>
                </div>
                <div className="text-2xl font-bold">Coming Soon</div>
              </CardContent>
            </Card>
          </div>

          <Card className="border-2 border-dashed border-muted">
            <CardHeader>
              <CardTitle className="font-mono">Join the Premium Waitlist</CardTitle>
              <CardDescription>
                Be the first to know when Premium launches. No spam, just updates.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleWaitlistSubmit} className="space-y-4">
                <div className="grid gap-2">
                  <Label htmlFor="email" className="font-mono">Email Address</Label>
                  <Input 
                    id="email" 
                    type="email" 
                    placeholder="your@email.com"
                    className="font-mono"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <Button 
                  type="submit"
                  className="bg-accent-neon text-accent-neon-foreground hover:bg-accent-neon/90 font-mono"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Joining..." : "Join Waitlist →"}
                </Button>
                <p className="text-xs text-muted-foreground">
                  Early access + 50% discount for first 100 developers
                </p>
              </form>
            </CardContent>
          </Card>

          <div className="mt-12 text-center">
            <h3 className="text-lg font-semibold mb-4 font-mono">Hit the limit?</h3>
            <p className="text-muted-foreground mb-4">
              Your current memory usage will be displayed here once you generate a token.
            </p>
            <div className="bg-muted p-4 rounded border-2 border-dashed font-mono text-sm">
              Memory Usage: -- / 25 entries
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Premium;