import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Copy, Check, Loader2, AlertCircle } from 'lucide-react';
import { memoryApi, TokenGenerationResponse } from '@/api/memory';
import { Link } from 'react-router-dom';

interface TokenModalProps {
  trigger: React.ReactNode;
}

export const TokenModal: React.FC<TokenModalProps> = ({ trigger }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [userName, setUserName] = useState('');
  const [tokenData, setTokenData] = useState<TokenGenerationResponse | null>(null);
  const [copiedToken, setCopiedToken] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateToken = async () => {
    if (isGenerating) return;
    
    setIsGenerating(true);
    setError(null);

    try {
      const response = await memoryApi.generateToken({
        user_name: userName.trim() || undefined
      });

      setTokenData(response);
      
      // Store token in localStorage for future reference
      localStorage.setItem('mcp_memory_token', response.token);
      localStorage.setItem('mcp_memory_url', response.url);
      
      toast.success('Token generated successfully!');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate token';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = async (text: string, type: 'token' | 'url') => {
    try {
      await navigator.clipboard.writeText(text);
      
      if (type === 'token') {
        setCopiedToken(true);
        setTimeout(() => setCopiedToken(false), 2000);
      } else {
        setCopiedUrl(true);
        setTimeout(() => setCopiedUrl(false), 2000);
      }
      
      toast.success(`${type === 'token' ? 'Token' : 'URL'} copied to clipboard!`);
    } catch (err) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    // Reset form after a brief delay to avoid flashing
    setTimeout(() => {
      setUserName('');
      setTokenData(null);
      setCopiedToken(false);
      setCopiedUrl(false);
      setError(null);
    }, 200);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild onClick={() => setIsOpen(true)}>
        {trigger}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Generate Your Memory Token</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {!tokenData ? (
            // Token generation form
            <div className="space-y-4">
              <div>
                <Label htmlFor="userName">Your Name (Optional)</Label>
                <Input
                  id="userName"
                  type="text"
                  placeholder="Enter your name"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  disabled={isGenerating}
                />
                <p className="text-sm text-muted-foreground mt-1">
                  This helps identify your token in logs
                </p>
              </div>

              {error && (
                <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                  <AlertCircle className="h-4 w-4 text-destructive" />
                  <span className="text-sm text-destructive">{error}</span>
                </div>
              )}

              <Button 
                onClick={handleGenerateToken}
                disabled={isGenerating}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating Token...
                  </>
                ) : (
                  'Generate Token'
                )}
              </Button>
            </div>
          ) : (
            // Token display
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Your Memory Token</CardTitle>
                  <CardDescription>
                    Use this token to connect your AI to long-term memory
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="token">Token</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        id="token"
                        type="text"
                        value={tokenData.token}
                        readOnly
                        className="font-mono text-sm"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(tokenData.token, 'token')}
                      >
                        {copiedToken ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="url">MCP URL</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        id="url"
                        type="text"
                        value={tokenData.url}
                        readOnly
                        className="font-mono text-sm"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(tokenData.url, 'url')}
                      >
                        {copiedUrl ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  <div className="bg-muted p-3 rounded-lg">
                    <p className="text-sm font-medium">Memory Usage</p>
                    <p className="text-sm text-muted-foreground">
                      {tokenData.memories_used} of {tokenData.memory_limit} memories used
                    </p>
                    <p className="text-[10px] text-muted-foreground/60 mt-1.5">
                      25 memories free forever. Full trial coming soon.
                    </p>
                  </div>
                </CardContent>
              </Card>

              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-2">Next Steps:</h4>
                <ol className="text-sm text-blue-800 space-y-1">
                  <li>1. <strong>Add system prompt</strong> - Required for proactive memory usage</li>
                  <li>2. Copy the MCP URL above</li>
                  <li>3. Add URL to your AI tool (Claude, Cursor, Windsurf, etc.)</li>
                  <li>4. <Link to="/integration" className="text-blue-600 hover:underline font-medium" onClick={handleClose}>Follow complete setup guide with system prompt</Link></li>
                  <li>5. Start using proactive long-term memory!</li>
                </ol>
                <div className="mt-3 p-2 bg-amber-100 border border-amber-300 rounded text-xs text-amber-800">
                  <strong>⚠️ Important:</strong> System prompts are essential for proactive behavior. Without them, your AI won't automatically use memory functions.
                </div>
              </div>

              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  onClick={handleClose}
                  className="flex-1"
                >
                  Done
                </Button>
                <Button 
                  variant="outline" 
                  asChild
                  className="flex-1"
                >
                  <Link to="/integration" onClick={handleClose}>
                    Setup Guide
                  </Link>
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};