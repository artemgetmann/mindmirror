import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, Lock, Eye, Download, DollarSign, Server } from "lucide-react";

const Privacy = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-left mb-12">
            <h1 className="text-4xl font-bold mb-4 font-mono">Privacy Overview</h1>
            <p className="text-lg text-muted-foreground">
              At MindMirror, your data isn't a product — it's your memory.
              We treat it with the same level of care we demand for our own AI workflows.
            </p>
          </div>

          <div className="space-y-8">
            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Secure by Design
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  All communication between your AI and MindMirror is encrypted in transit (TLS) and stored securely using modern encryption standards.
                </p>
                <p className="text-muted-foreground">
                  We're working toward full end-to-end encryption so that even we can't view user data — only your AI can.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  Zero Human Access
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  Your memories aren't reviewed, read, or sold.
                </p>
                <p className="text-muted-foreground">
                  Access is restricted to your AI instance and integration token.
                </p>
                <p className="text-muted-foreground">
                  Administrative visibility exists only for debugging and will be phased out once client-side encryption is active.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  Transparent Infrastructure
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  MindMirror runs on state-of-the-art U.S. cloud infrastructure with audited data centers and strict access controls.
                </p>
                <p className="text-muted-foreground">
                  We log every system-level access and plan to open-audit our privacy stack in future releases.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg flex items-center gap-2">
                  <Download className="h-5 w-5" />
                  Full Export & Deletion Control
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  All users can delete their memories anytime.
                </p>
                <p className="text-muted-foreground">
                  Premium users can also export all data in full.
                </p>
                <p className="text-muted-foreground">
                  We don't retain residual backups beyond the minimal operational window.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg flex items-center gap-2">
                  <DollarSign className="h-5 w-5" />
                  No Data Monetization
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  MindMirror has a clear subscription-based model.
                </p>
                <p className="text-muted-foreground">
                  It's not a free product — which means we have no need to sell or analyze your data.
                </p>
                <p className="text-muted-foreground">
                  Your memories exist to serve you, not our business model.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
              <CardHeader>
                <CardTitle className="font-mono text-lg flex items-center gap-2">
                  <Lock className="h-5 w-5" />
                  Our Commitment
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  AI shouldn't just be smart — it should be trustworthy.
                </p>
                <p className="text-muted-foreground">
                  We're building a system where your AI remembers what matters to you, not to us.
                </p>
                <p className="text-muted-foreground">
                  For questions, reach out on{" "}
                  <a href="https://github.com/artemgetmann" target="_blank" rel="noopener noreferrer" className="text-accent-neon hover:underline">
                    GitHub
                  </a>
                  ,{" "}
                  <a href="https://x.com/artemgetman_" target="_blank" rel="noopener noreferrer" className="text-accent-neon hover:underline">
                    Twitter
                  </a>
                  , or{" "}
                  <a href="https://www.reddit.com/user/artemgetman/" target="_blank" rel="noopener noreferrer" className="text-accent-neon hover:underline">
                    Reddit
                  </a>
                  .
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

export default Privacy;
