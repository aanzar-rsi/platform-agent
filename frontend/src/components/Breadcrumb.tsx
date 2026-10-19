import { useNavigate } from "react-router";
import { ChevronRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";

interface BreadcrumbItem {
  label: string;
  path: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // Show breadcrumb when scrolling up or at the top
      if (currentScrollY < lastScrollY || currentScrollY < 10) {
        setIsVisible(true);
      } 
      // Hide breadcrumb when scrolling down (but only after scrolling past a threshold)
      else if (currentScrollY > lastScrollY && currentScrollY > 100) {
        setIsVisible(false);
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const handleBack = () => {
    if (items.length > 1) {
      // Navigate to the previous breadcrumb item
      navigate(items[items.length - 2].path);
    } else {
      navigate("/");
    }
  };

  return (
    <nav aria-label="Breadcrumb" 
      className={`fixed top-16 left-0 right-0 z-40 bg-[#f8f8f6] transition-transform duration-300 ${
        isVisible ? 'translate-y-0' : '-translate-y-full'
      }`}
    >
      <div className="w-full">
        <div className="flex items-center gap-2 pl-4 sm:pl-6 lg:pl-8 py-3">
          <Button
            aria-label="Go to previous page"
            variant="ghost"
            size="icon"
            onClick={handleBack}
            className="h-7 w-7 hover:bg-[#171717]/10 text-[#171717]"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
           <div className="flex items-center gap-2 text-sm">
            {items.map((item, index) => {
              const isLast = index === items.length - 1;
              return (
                <div key={item.path} className="flex items-center gap-2">
                  {index > 0 && (
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  )}
                  {isLast ? (
                    <span aria-current="page" className="text-[#171717] font-semibold">{item.label}</span>
                  ) : (
                    <a
                      href={item.path}
                      onClick={(event) => {
                        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
                        event.preventDefault();
                        navigate(item.path, item.path === "/agents/mcp-config" || item.path === "/mcp-config" ? { replace: true, state: { reset: true } } : undefined);
                      }}
                      className="text-gray-600 hover:text-[#171717]"
                    >
                      {item.label}
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
