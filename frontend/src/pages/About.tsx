import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Github, Twitter, Globe } from "lucide-react";

const About = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-left mb-12">
            <h1 className="text-4xl font-bold mb-2 font-mono">mindmirror(1) — Persistent memory for AI</h1>
            <p className="text-sm text-muted-foreground font-mono">
              AI shouldn't forget. This one doesn't.
            </p>
          </div>

          <div className="space-y-8">
            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg">━━━ Founder Problem ━━━</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  Every AI chat felt like Groundhog Day. Same tools. Same goals. Same repetition. I got tired of reminding my assistants who I was.
                </p>
                <p className="text-muted-foreground">
                  The memory fragmentation across different AI models made it even worse. ChatGPT has its own memory. Claude either doesn't have memory or forces you to manually inject it. Different tools remember different things. Switching between models felt like starting from scratch every time.
                </p>
                <p className="text-muted-foreground">
                  I wanted one shared memory layer across all my AI systems—Claude, Cursor, Windsurf, or any custom-built model—without the constant overhead of rebuilding context.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg">━━━ What It Is ━━━</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  MindMirror is a persistent memory server for AI models. It integrates seamlessly with Claude, Cursor, Windsurf, and your custom AI tools.
                </p>
                <p className="text-muted-foreground">
                  MindMirror stores structured, searchable memories—not raw chat logs. It's plug-and-play: inject one token, and your AI assistant instantly gains persistent recall, across any conversation and any compatible model.
                </p>
                <p className="text-muted-foreground">
                  No more manual setup, no more repetitive context injections. Just one URL, one memory, everywhere.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg">━━━ Built by Artem ━━━</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  MindMirror wasn't built by a startup team or a corporate initiative. It started out of pure frustration.
                </p>
                <p className="text-muted-foreground">
                  I didn't want to rebuild memory every time I switched AI tools. So I built one persistent memory system that works seamlessly across them all.
                </p>
                <p className="text-muted-foreground">
                  MindMirror is designed specifically for developers and power users who need sharper, memory-driven AI workflows—not fancy marketing demos.
                </p>
                
                <div className="flex space-x-4 pt-4">
                  <a href="https://github.com/artemgetmann" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2 text-muted-foreground hover:text-accent-neon transition-colors">
                    <Github className="h-4 w-4" />
                    <span className="font-mono text-sm">GitHub</span>
                  </a>
                  <a href="https://x.com/artemgetman_" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2 text-muted-foreground hover:text-accent-neon transition-colors">
                    <Twitter className="h-4 w-4" />
                    <span className="font-mono text-sm">Twitter</span>
                  </a>
                  <a href="https://www.reddit.com/user/artemgetman/" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2 text-muted-foreground hover:text-accent-neon transition-colors">
                    <Globe className="h-4 w-4" />
                    <span className="font-mono text-sm">Reddit</span>
                  </a>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg">━━━ Mission & Call to Action ━━━</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  If you care about building better, sharper AI tools—or pushing toward true AGI—MindMirror is built for you.
                </p>
                <p className="text-muted-foreground">
                  Persistent, structured memory is step zero for real intelligence. MindMirror saves you time, reduces friction, and helps you build smarter tools faster.
                </p>
                <p className="text-muted-foreground">
                  Join the waitlist if you want early access, or just use it today.
                </p>
                <p className="text-muted-foreground">
                  I hope it brings real value to your workflow—and helps push my AGI research forward.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50 mt-8">
              <CardHeader>
                <CardTitle className="font-mono text-lg">━━━ Smart Conflict Resolution ━━━</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  <strong>Humans evolve. Our preferences change. Our memory system does too.</strong>
                </p>
                <p className="text-muted-foreground">
                  Today you might prefer VS Code. Tomorrow you might prefer Vim. Most AI systems break when preferences conflict—MindMirror embraces this reality.
                </p>
                <p className="text-muted-foreground">
                  Our advanced conflict detection automatically identifies when new information contradicts stored memories. Instead of silently overwriting or ignoring conflicts, MindMirror surfaces them intelligently, letting you choose which preferences to keep.
                </p>
                <p className="text-muted-foreground">
                  <strong>We're not binary creatures.</strong> We constantly evolve our thoughts, habits, and preferences. Your AI memory should evolve with you, not against you.
                </p>
                <p className="text-muted-foreground">
                  This is what makes MindMirror different from simple storage—it understands that human memory is complex, contextual, and constantly changing.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50 mt-8">
              <CardHeader>
                <CardTitle className="font-mono text-lg">━━━ Under the Hood ━━━</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  MindMirror uses a token-based memory namespace, isolated by user, usable with Claude, Cursor, Windsurf, or any AI tool that supports MCP protocol or external context injection.
                </p>
                <p className="text-muted-foreground">
                  No login, no accounts — just persistent memory through a single URL.
                </p>
                <p className="text-muted-foreground">
                  Want integration help? <a href="/integration" className="text-accent-neon hover:underline font-mono">See integration guide</a>.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default About;