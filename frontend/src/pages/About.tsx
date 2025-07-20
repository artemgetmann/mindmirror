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
              The most advanced AI memory system in the world. Built because I was tired of re-explaining everything in every chat.
            </p>
          </div>

          <Card className="border-2 border-dashed border-gray-300 bg-gray-50 mb-8">
            <CardHeader>
              <CardTitle className="font-mono text-lg">━━━ Watch: MindMirror in Action ━━━</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                <iframe
                  className="absolute top-0 left-0 w-full h-full rounded-lg"
                  src="https://www.youtube.com/embed/R36RkMoCoa8?rel=0"
                  title="MindMirror Demo Video"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            </CardContent>
          </Card>

          <div className="space-y-8">
            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg">━━━ Founder Problem ━━━</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  Every AI chat felt like starting from scratch. Same tools. Same goals. Same repetition. Claude has no long-term memory across chats. Claude Code doesn't either. Cursor forgets. The ChatGPT and Anthropic APIs are stateless. Windsurf starts fresh.
                </p>
                <p className="text-muted-foreground">
                  None of these tools retain memory — and even when some do, it's very basic and nothing syncs across tools. You build up memory in one tool, then switch platforms and everything is gone. That's the real problem.
                </p>
                <p className="text-muted-foreground">
                  Here's the deeper issue: how do you even build custom tools with AI if there's no memory? I believe you can't build truly effective AI solutions without it. That's the exact wall I hit when I tried. I wanted to build smarter agents — but APIs were stateless.
                </p>
                <p className="text-muted-foreground">
                  MindMirror fixes that. You can now build multiple AI applications — a robot with Claude, a drone with OpenAI — and they can all share the same memory backend. One universal memory layer. Plug and play.
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