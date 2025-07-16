import { Link } from "react-router-dom";

export const Footer = () => {
  return (
    <footer className="border-t bg-background">
      <div className="container px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <img 
                src="/lovable-uploads/df98b257-f966-4a4c-95ec-38a40d83c40a.png" 
                alt="MindMirror Logo" 
                className="h-6 w-6 rounded-md"
              />
              <span className="font-semibold">MindMirror</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Persistent memory for AI models.
              <br />
              Built by developers, for developers.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium mb-3">Integration</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/integration#claude" className="hover:text-foreground transition-colors">Claude</Link></li>
              <li><Link to="/integration#cursor" className="hover:text-foreground transition-colors">Cursor</Link></li>
              <li><Link to="/integration#windsurf" className="hover:text-foreground transition-colors">Windsurf</Link></li>
              <li><Link to="/integration#custom" className="hover:text-foreground transition-colors">Custom AI</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-medium mb-3">Company</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/#privacy" className="hover:text-foreground transition-colors">Privacy</Link></li>
              <li><Link to="/about" className="hover:text-foreground transition-colors">About</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t mt-8 pt-8 text-center text-sm text-muted-foreground">
          <p>&copy; 2025 MindMirror. Built by Artem with rebellion and precision.</p>
        </div>
      </div>
    </footer>
  );
};