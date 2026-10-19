import { memo, useCallback } from "react";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { MessageSquare } from "lucide-react";
import LogoutButton from "./LogoutButton";

interface NavigationProps {
    variant?: 'landing' | 'login' | 'auth' | 'app';
    isAuthenticated?: boolean;
    className?: string;
    hidden?: boolean;
}

const HeaderNavbar = memo(({
    variant = 'landing',
    isAuthenticated = false,
    className = '',
    hidden = false
}: NavigationProps) => {
    const navigate = useNavigate();

    // Authenticated app view flag 
    const isAppView = variant === "app" && isAuthenticated;

    const handleNavigate = useCallback((path: string) => {
        navigate(path);
    }, [navigate]);

    if (hidden) return null;

    return (
        <nav className={`bg-linear-to-b from-[#f8f8f6] to-[#fffeff] w-full fixed top-0 z-50 border-b border-gray-300 shadow-md shadow-black/10 ${className}`}>
            <div className="w-full">
                <div className="flex justify-between items-center h-16 w-full">
                    {/* Logo Section */}
                     <a
                         href="/"
                         className="flex items-center gap-3 cursor-pointer transition-opacity hover:opacity-80 pl-4 sm:pl-6 lg:pl-8"
                    >
                         <img src="/rs_monogram.svg" alt="Rimini Street" width={32} height={32} className="h-8 w-8" />

                        <div>
                             <span className="block font-bold text-lg tracking-tight text-black">
                                 {isAppView ? "PlatformAgent" : "Project PlatformAgent"}
                             </span>

                            <p className="text-xs text-gray-600">
                                {isAppView ? "Chat workspace" : "Evolving Virtual Assistant"}
                            </p>
                        </div>
                     </a>

                    {/* Action Buttons Section */}
                    <div className="flex items-center gap-3 pr-4 sm:pr-6 lg:pr-8 ml-auto">
                        {variant === 'landing' && !isAuthenticated && (
                            <>
                                <Button variant="ghost" asChild className="text-gray-900 hover:text-gray-800">
                                    <a href="/login">Login</a>
                                </Button>
                                <Button asChild className="w-full bg-brand hover:bg-brand/90 transition-all text-black border-0 shadow-xl">
                                    <a href="/login">Get Started</a>
                                </Button>
                            </>
                        )}

                        {variant === 'landing' && isAuthenticated && (
                            <>
                                <Button
                                    variant="ghost"
                                     onClick={() => handleNavigate("/")}
                                    className="text-gray-900 hover:text-gray-800"
                                >
                                    Chat
                                </Button>
                                <Button
                                    onClick={() => handleNavigate("/agents")}
                                    className="w-full bg-brand hover:bg-brand/90 transition-all text-black border-0 shadow-xl"
                                >
                                    <MessageSquare className="h-4 w-4" />
                                    Start Chatting
                                </Button>
                                <LogoutButton />
                            </>
                        )}

                        {variant === 'login' && (
                            <Button asChild className="w-full bg-brand hover:bg-brand/90 transition-all text-black border-0 shadow-xl">
                                <a href="/login">Get Started</a>
                            </Button>
                        )}

                        {variant === 'auth' && (
                            <Button
                                variant="ghost"
                                onClick={() => handleNavigate("/login")}
                                className="w-full bg-brand hover:bg-brand/90 transition-all text-black border-0 shadow-xl"
                            >
                                Login
                            </Button>
                        )}

                        {variant === 'app' && isAuthenticated && (
                            <>
                                <Button
                                    variant="ghost"
                                     onClick={() => navigate("/")}
                                    className="text-gray-900 hover:text-gray-800"
                                >
                                    Home
                                </Button>
                                <Button
                                    onClick={() => navigate("/agents")}
                                    className="w-full bg-brand hover:bg-brand/90 transition-all text-black border-0 shadow-xl"
                                >
                                    <MessageSquare className="h-4 w-4" />
                                    Start Chatting
                                </Button>
                                <LogoutButton />
                            </>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
});

HeaderNavbar.displayName = "HeaderNavbar";

export default HeaderNavbar;
