import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { Infinity, Zap, Download, Crown } from "lucide-react";

export const PremiumWaitlistSection = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsSubmitting(true);
    
    // Simulate API call for now
    setTimeout(() => {
      toast({
        title: "You're on the list!",
        description: "We'll notify you when MindMirror Premium launches.",
      });
      setEmail("");
      setIsSubmitting(false);
    }, 1000);
  };

  const premiumFeatures = [
    {
      icon: Infinity,
      title: "Unlimited Memory",
      description: "No storage limits on your AI's memory capacity"
    },
    {
      icon: Zap,
      title: "Advanced Features",
      description: "Priority processing and enhanced memory algorithms"
    },
    {
      icon: Download,
      title: "Full Export Control", 
      description: "Download all your memories anytime, in any format"
    },
    {
      icon: Crown,
      title: "Priority Support",
      description: "Direct access to our engineering team"
    }
  ];

  return (
    <section className="container px-4 py-24">
      <div className="max-w-4xl mx-auto text-center">
        <div className="mb-12">
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary rounded-full px-4 py-2 text-sm mb-6">
            <Crown className="h-4 w-4" />
            <span>Premium Coming Soon</span>
          </div>
          
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Hit the limit? Join the Premium Waitlist.
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            MindMirror Premium: Unlimited memory, advanced features, and complete export control.
          </p>
        </div>

        {/* Premium Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {premiumFeatures.map((feature, index) => (
            <div key={index} className="bg-card border rounded-lg p-6 text-left">
              <div className="h-10 w-10 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Waitlist Form */}
        <div className="bg-card border rounded-lg p-8 max-w-md mx-auto">
          <h3 className="text-lg font-semibold mb-4">Join the Premium Waitlist</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full"
            />
            <Button 
              type="submit" 
              className="w-full" 
              disabled={isSubmitting}
            >
              {isSubmitting ? "Joining..." : "Join Waitlist"}
            </Button>
          </form>
          <p className="text-xs text-muted-foreground mt-3">
            We'll notify you when premium features are available.
          </p>
        </div>
      </div>
    </section>
  );
};