import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { TokenModal } from "@/components/TokenModal";

export const Navigation = () => {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;
  
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center space-x-2">
          <img 
            src="/lovable-uploads/df98b257-f966-4a4c-95ec-38a40d83c40a.png" 
            alt="MindMirror Logo" 
            className="h-8 w-8 rounded-md"
          />
          <span className="font-semibold text-lg">MindMirror</span>
        </Link>
        
        <nav className="hidden md:flex items-center space-x-6">
          <Link 
            to="/#how-it-works" 
            className={`text-sm transition-colors hover:text-accent-neon ${
              isActive('/') ? 'text-foreground' : 'text-muted-foreground'
            }`}
          >
            How it works
          </Link>
          <Link 
            to="/integration" 
            className={`text-sm transition-colors hover:text-accent-neon ${
              isActive('/integration') ? 'text-foreground' : 'text-muted-foreground'
            }`}
          >
            Integration
          </Link>
          <Link 
            to="/premium" 
            className={`text-sm transition-colors hover:text-accent-neon ${
              isActive('/premium') ? 'text-foreground' : 'text-muted-foreground'
            }`}
          >
            Premium
          </Link>
          <Link 
            to="/about" 
            className={`text-sm transition-colors hover:text-accent-neon ${
              isActive('/about') ? 'text-foreground' : 'text-muted-foreground'
            }`}
          >
            About
          </Link>
        </nav>
        
        <TokenModal
          trigger={
            <Button 
              variant="outline" 
              size="sm"
              className="hover:bg-accent-neon hover:text-accent-neon-foreground hover:border-accent-neon transition-all duration-200"
            >
              Inject Token
            </Button>
          }
        />
      </div>
    </header>
  );
};