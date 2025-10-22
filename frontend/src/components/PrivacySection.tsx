import { Shield, Eye, Download, Server } from "lucide-react";
import { Link } from "react-router-dom";

const privacyFeatures = [
  {
    icon: Shield,
    title: "End-to-End Security",
    description: "Your memories are stored securely on encrypted infrastructure with strict access controls"
  },
  {
    icon: Eye,
    title: "Zero Human Access", 
    description: "Your memories are only accessed through your AI model—never reviewed, read, or used by us"
  },
  {
    icon: Download,
    title: "Full Export Control",
    description: "Your memory is your own. Premium users can export all memories anytime in full"
  },
  {
    icon: Server,
    title: "Transparent Infrastructure",
    description: "Built on secure, auditable systems with clear data handling practices"
  }
];

export const PrivacySection = () => {
  return (
    <section id="privacy" className="container px-4 py-24">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Privacy-First by Design
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Your memories are yours. We built MindMirror with the same privacy standards
            we'd demand for our own AI workflows.
          </p>
          <p className="text-sm text-muted-foreground max-w-3xl mx-auto mt-4">
            For details on how we store, encrypt, and protect your data, read our{" "}
            <Link to="/privacy" className="text-accent-neon hover:underline">
              Privacy Overview
            </Link>
            .
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {privacyFeatures.map((feature, index) => (
            <div 
              key={index} 
              className="bg-card border rounded-lg p-6"
            >
              <div className="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <feature.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Privacy Statement */}
        <div className="bg-secondary/50 border rounded-lg p-8 text-center">
          <h3 className="text-lg font-semibold mb-3">Our Privacy Commitment</h3>
          <p className="text-muted-foreground max-w-3xl mx-auto">
            <strong>MindMirror stores your memories on secure infrastructure.</strong>They’re only accessed by your AI model — never reviewed, read, or used by us.

In the premium version, you’ll be able to export all your memories anytime. Until then, just ask your AI what it remembers about you — and it will tell you everything it’s stored.
          </p>
        </div>
      </div>
    </section>
  );
};