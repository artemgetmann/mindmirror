import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { TokenModal } from "@/components/TokenModal";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Menu } from "lucide-react";
import { useState } from "react";

export const Navigation = () => {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  
  const isActive = (path: string) => location.pathname === path;
  
  const navigationItems = [
    { path: "/#how-it-works", label: "How it works" },
    { path: "/integration", label: "Integration" },
    { path: "/premium", label: "Premium" },
    { path: "/about", label: "About" }
  ];
  
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur-sm supports-[backdrop-filter]:bg-background/60">
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
          {navigationItems.map((item) => (
            <Link 
              key={item.path}
              to={item.path} 
              className={`text-sm transition-colors hover:text-accent-neon ${
                isActive(item.path) ? 'text-foreground' : 'text-muted-foreground'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        
        <div className="flex items-center space-x-4">
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
          
          {/* Mobile menu */}
          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
              <Button 
                variant="outline" 
                size="sm" 
                className="md:hidden p-2"
                aria-label="Open menu"
              >
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
              <nav className="flex flex-col space-y-6 mt-6">
                {navigationItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`text-lg transition-colors hover:text-accent-neon ${
                      isActive(item.path) ? 'text-foreground' : 'text-muted-foreground'
                    }`}
                    onClick={() => setIsOpen(false)}
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
};