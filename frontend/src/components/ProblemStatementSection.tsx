import { XCircle, CheckCircle } from "lucide-react";

export const ProblemStatementSection = () => {
  return (
    <section className="container px-4 py-24 bg-secondary/30">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-card border-2 border-dashed border-muted rounded-lg p-8">
            <div className="h-12 w-12 bg-destructive/10 rounded-lg flex items-center justify-center mb-4">
              <XCircle className="h-6 w-6 text-destructive" />
            </div>
            <h3 className="text-2xl font-bold mb-4 font-mono">The Problem</h3>
            <p className="text-muted-foreground text-lg leading-relaxed">
              LLM APIs don't remember anything.
              <br /><br />
              Every developer hacks their own storage, embeddings, and retrieval logic.
            </p>
          </div>
          <div className="bg-card border-2 border-dashed border-muted rounded-lg p-8">
            <div className="h-12 w-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <CheckCircle className="h-6 w-6 text-primary" />
            </div>
            <h3 className="text-2xl font-bold mb-4 font-mono">The Fix</h3>
            <p className="text-muted-foreground text-lg leading-relaxed">
              MindMirror gives you a unified memory backend: store, retrieve, search, and share context between agents without building infra.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
