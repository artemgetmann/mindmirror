import { Brain, Lock, Zap, Code, Users, Download, GitBranch } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Intelligent Memory",
    description: "Not chat logs. Just the stuff that drives better, more personal suggestions"
  },
  {
    icon: GitBranch,
    title: "Smart Conflict Resolution",
    description: "Humans evolve. When preferences conflict, MindMirror helps you choose—never silently overwrites"
  },
  {
    icon: Zap,
    title: "Zero-Friction Setup",
    description: "Paste one URL, done. No complex configurations or API juggling"
  },
  {
    icon: Lock,
    title: "Privacy-First",
    description: "Secure by design. Only your AI uses your memories — never reviewed or read by us"
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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
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

        {/* YouTube Shorts Demo Video */}
        <div className="mt-24">
          <h3 className="text-2xl md:text-3xl font-bold text-center mb-8 font-mono">
            ━━━ Watch: MindMirror in Action ━━━
          </h3>
          <div className="max-w-md mx-auto">
            <div className="border-2 border-dashed border-gray-300 bg-gray-50 rounded-lg p-6">
              <div 
                className="relative overflow-hidden rounded-lg"
                style={{ paddingBottom: '177.78%' }}
              >
                <iframe
                  className="absolute top-0 left-0 w-full h-full"
                  src="https://www.youtube.com/embed/83PucS986fE?rel=0"
                  title="MindMirror Demo"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};