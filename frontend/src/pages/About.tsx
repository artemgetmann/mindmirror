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
            <h1 className="text-4xl font-bold mb-4">About MindMirror</h1>
            <p className="text-xl text-muted-foreground font-mono">
              Why persistent memory matters for AI development
            </p>
          </div>

          <div className="space-y-8">
            <Card className="border-2 border-dashed border-muted">
              <CardHeader>
                <CardTitle className="font-mono">The Problem</CardTitle>
                <CardDescription>Every conversation starts from zero</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  Current AI models have no persistent memory across sessions. Every time you start 
                  a new conversation with Claude, Cursor, or any AI tool, you're starting from scratch. 
                  The AI doesn't remember your preferences, your codebase patterns, your workflow, 
                  or the context from previous interactions.
                </p>
                <p className="text-muted-foreground">
                  For developers and power users who rely on AI as a daily tool, this is frustrating 
                  and inefficient. You end up repeating the same context, explaining the same 
                  preferences, and re-establishing the same working relationships over and over.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-muted">
              <CardHeader>
                <CardTitle className="font-mono">The Vision</CardTitle>
                <CardDescription>AI that truly knows you</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  MindMirror bridges this gap by providing persistent, user-specific memory for AI models. 
                  Instead of starting fresh every time, your AI assistant remembers your coding style, 
                  your project preferences, your communication patterns, and the context of your work.
                </p>
                <p className="text-muted-foreground">
                  This isn't about training custom models or complex setups. It's about simple, 
                  token-based memory that any AI tool can access through a single URL. 
                  Paste once, remember forever.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-muted">
              <CardHeader>
                <CardTitle className="font-mono">Built by Artem</CardTitle>
                <CardDescription>A developer frustrated with forgetful AI</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  MindMirror was born out of personal frustration. As a developer who uses AI tools 
                  daily for coding, writing, and problem-solving, I got tired of repeating myself 
                  in every new conversation.
                </p>
                <p className="text-muted-foreground">
                  I wanted an AI that remembered my coding conventions, my project structures, 
                  my communication style, and the ongoing context of my work. Since no one else 
                  was building this simple solution, I built it myself.
                </p>
                <p className="text-muted-foreground">
                  MindMirror is designed by a developer, for developers. It's minimalist, 
                  technical, and focused on solving one problem really well: giving AI the 
                  memory it should have had from the beginning.
                </p>
                
                <div className="flex space-x-4 pt-4">
                  <a href="#" className="flex items-center space-x-2 text-muted-foreground hover:text-accent-neon transition-colors">
                    <Github className="h-4 w-4" />
                    <span className="font-mono text-sm">GitHub</span>
                  </a>
                  <a href="#" className="flex items-center space-x-2 text-muted-foreground hover:text-accent-neon transition-colors">
                    <Twitter className="h-4 w-4" />
                    <span className="font-mono text-sm">Twitter</span>
                  </a>
                  <a href="#" className="flex items-center space-x-2 text-muted-foreground hover:text-accent-neon transition-colors">
                    <Globe className="h-4 w-4" />
                    <span className="font-mono text-sm">Website</span>
                  </a>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-muted">
              <CardHeader>
                <CardTitle className="font-mono">Technical Details</CardTitle>
                <CardDescription>How MindMirror works under the hood</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2 font-mono">Token-Based Authentication</h4>
                  <p className="text-sm text-muted-foreground">
                    Each user gets a unique token that serves as both authentication and memory namespace. 
                    No accounts, no passwords, just a simple token.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2 font-mono">RESTful API</h4>
                  <p className="text-sm text-muted-foreground">
                    Simple GET/POST endpoints that any AI tool can integrate with. 
                    Store memories, retrieve context, search by keywords.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2 font-mono">Privacy by Design</h4>
                  <p className="text-sm text-muted-foreground">
                    Your memories are encrypted, isolated by token, and never accessed by humans. 
                    Premium users will have full export capabilities.
                  </p>
                </div>
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