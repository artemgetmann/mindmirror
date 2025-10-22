import { Clock, ArrowLeftRight, TrendingDown } from "lucide-react";

const benefits = [
  {
    icon: Clock,
    title: "Never forgets — even years later",
    description: "MindMirror keeps your context alive. Your AI can recall people, projects, or preferences from a year ago — instantly."
  },
  {
    icon: ArrowLeftRight,
    title: "Portable memory",
    description: "Your data isn't locked to one model. Plug it into Claude, Cursor, Windsurf, or your own AI — your memory moves with you."
  },
  {
    icon: TrendingDown,
    title: "Smarter recall, lower cost",
    description: "Only the ten most relevant memories are retrieved per query — optimized for performance and API cost."
  }
];

export const WhyItMattersSection = () => {
  return (
    <section className="container px-4 py-24 bg-secondary/30">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Why Persistent Memory Matters
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            AI memory isn't just a feature — it's the foundation for truly intelligent, AGI-like systems
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {benefits.map((benefit, index) => (
            <div
              key={index}
              className="bg-card border-2 border-dashed border-muted rounded-lg p-6"
            >
              <div className="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <benefit.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2 font-mono">{benefit.title}</h3>
              <p className="text-muted-foreground">{benefit.description}</p>
            </div>
          ))}
        </div>

        <div className="text-center">
          <p className="text-lg text-muted-foreground">
            Try MindMirror free — your AI should remember you.
          </p>
        </div>
      </div>
    </section>
  );
};
