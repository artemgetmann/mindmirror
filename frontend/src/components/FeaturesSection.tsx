import { Brain, Lock, Zap, Code, Users, Download } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Intelligent Memory",
    description: "Your AI remembers preferences, habits, and context across all conversations"
  },
  {
    icon: Zap,
    title: "Zero-Friction Setup",
    description: "Paste one URL, done. No complex configurations or API juggling"
  },
  {
    icon: Lock,
    title: "Privacy-First",
    description: "Your memories are encrypted and only accessible through your AI model"
  }
];

export const FeaturesSection = () => {
  return (
    <section id="how-it-works" className="container px-4 py-24">
      <div className="max-w-6xl mx-auto">
        <div className="text-left mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            How MindMirror Works
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl font-mono">
            Simple, secure, and powerful memory for your AI conversations
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div 
              key={index} 
              className="p-6 rounded-lg border-2 border-dashed border-muted bg-card hover:bg-secondary/50 transition-colors"
            >
              <div className="mb-4">
                <feature.icon className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-2 font-mono">{feature.title}</h3>
              <p className="text-muted-foreground text-sm">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};