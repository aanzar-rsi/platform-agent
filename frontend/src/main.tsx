import { AuthProvider } from "@/hooks/AuthProvider";
import { StrictMode, Suspense, lazy, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes, useLocation, Navigate, useSearchParams } from "react-router";
import "./index.css";
import ProtectedRoute from "./components/ProtectedRoute.tsx";
import { applyAppTheme } from "@/lib/theme";
import { Toaster } from "@/components/ui/sonner";
import { InstrumentationProvider } from "@/instrumentation.tsx";


const LoginPage = lazy(() => import("./pages/Login.tsx"));
const SignupPage = lazy(() => import("./pages/Signup.tsx"));
const NotFound = lazy(() => import("./pages/NotFound.tsx"));
const ChatInterface = lazy(() => import("./components/ChatInterface.tsx"));

function RouteSyncer() {
  const location = useLocation();
  useEffect(() => {
    window.parent.postMessage(
      { type: "iframe-route-change", path: location.pathname },
      "*",
    );
  }, [location.pathname]);

  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.data?.type === "navigate") {
        if (event.data.direction === "back") window.history.back();
        if (event.data.direction === "forward") window.history.forward();
      }
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  // Always reset document scroll on route change (prevents stacked-page scroll bleed)
  useEffect(() => {
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }, [location.pathname, location.search]);

  // If a previous route shell was left in the DOM (HMR / stale mount), remove it.
  // React should only keep one page under the router; extras cause Memory→Chat stacking.
  useEffect(() => {
    const root = document.getElementById("root");
    if (!root) return;

    const onChat = location.pathname.startsWith("/agents");
    const shells = Array.from(root.querySelectorAll<HTMLElement>(":scope div.h-screen.flex.flex-col"));
    for (const el of shells) {
      // Only remove chat shells when we are NOT on chat
      if (onChat) continue;
      const looksLikeChat =
        !!el.querySelector("[class*='ChatSidebar'], .h-full.flex.flex-col") &&
        (el.textContent?.includes("New Chat") || el.textContent?.includes("Platform Agent"));
      if (!looksLikeChat) continue;
      // Don't remove if this node is inside the current route's expected tree wrongly —
      // chat shells are always the outer h-screen wrapper from ChatInterface.
      if (el.parentElement === root || root.contains(el)) {
        // Only detach if it's a direct leftover sibling of the active page, not the active page itself
        const pageRoots = Array.from(root.children);
        // Walk up to find topmost page-ish ancestor under root
        let top: HTMLElement | null = el;
        while (top.parentElement && top.parentElement !== root) {
          top = top.parentElement as HTMLElement;
        }
        if (top && top.parentElement === root && pageRoots.length > 1) {
          // Prefer removing the chat shell when another min-h-screen/h-screen page exists
          const hasOtherPage = pageRoots.some((c) => {
            if (c === top) return false;
            const cls = c.classList;
            return (
              cls.contains("min-h-screen") ||
              cls.contains("h-screen") ||
              cls.contains("h-dvh")
            );
          });
          if (hasOtherPage) {
            top.remove();
          }
        }
      }
    }
  }, [location.pathname]);

  return null;
}

function ExperienceRedirect() {
  const [params] = useSearchParams();
  const next = new URLSearchParams(params);
  next.set("tab", "experiences");
  return <Navigate to={`/agents/memory?${next}`} replace />;
}

function LegacyWorkspaceRedirect({ view }: { view: string }) {
  const { search } = useLocation();
  return <Navigate to={`/agents/${view}${search}`} replace />;
}

function LegacyChatRouteRedirect() {
  const { pathname, search } = useLocation();
  const nextPath = pathname.replace(/^\/chat\b/, "/agents");
  return <Navigate to={`${nextPath}${search}`} replace />;
}

function PageMetadata() {
  const { pathname } = useLocation();
  useEffect(() => {
    const pages: Record<string, [string, string]> = {
      "/": ["Chat | PlatformAgent", "Start or continue a conversation in PlatformAgent."],
      "/login": ["Sign in | PlatformAgent", "Sign in to PlatformAgent to access your conversations, memory, and tool integrations."],
      "/signup": ["Sign up | PlatformAgent", "Create your PlatformAgent account. This page is currently a mock sign-up flow."],
      "/agents": ["Chat | PlatformAgent", "Start or continue a conversation in PlatformAgent."],
      "/agents/settings": ["Settings | PlatformAgent", "Manage your PlatformAgent preferences, models, memory, and tools."],
      "/agents/mcp-config": ["MCP Config | PlatformAgent", "Configure and manage Model Context Protocol servers and tools."],
      "/agents/memory": ["Memory | PlatformAgent", "Explore your memory and experiences in PlatformAgent."],
      "/agents/playground": ["Playground | PlatformAgent", "Explore tool creation in the PlatformAgent playground."],
    };
    const [title, description] = pages[pathname] ?? (pathname.startsWith("/agents/")
      ? pages["/agents"]
      : pathname === "/auth" ? pages["/login"]
      : pathname === "/experience" ? pages["/agents/memory"]
      : ["Page not found | PlatformAgent", "This page could not be found. Return to the PlatformAgent homepage."]);
    document.title = title;
    document.querySelector('meta[name="description"]')?.setAttribute("content", description);
  }, [pathname]);
  return null;
}

// Single consistent theme across browsers (ignore stale light/dark/system localStorage).
applyAppTheme();

const rootEl = document.getElementById("root")!;
// HMR can call this module twice and leave a second page tree under #root (Memory + Chat stacked).
const existingRoot = (globalThis as unknown as { __evaReactRoot?: ReturnType<typeof createRoot> })
  .__evaReactRoot;
const prerendered = rootEl.hasChildNodes();
if (!existingRoot && prerendered) rootEl.replaceChildren();
const app = (
  <StrictMode>
    <InstrumentationProvider>
      <AuthProvider>
        <BrowserRouter>
          <RouteSyncer />
          <PageMetadata />
          <Suspense fallback={<div className="min-h-screen bg-white" />}>
            <Routes>
           {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/auth" element={<Navigate to="/login" replace />} />
          
          <Route path="/" element={<ProtectedRoute><ChatInterface /></ProtectedRoute>} />
          <Route path="/landing" element={<Navigate to="/" replace />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          <Route path="/agents" element={<ProtectedRoute><ChatInterface /></ProtectedRoute>} />
          <Route path="/agents/:agent_id" element={<ProtectedRoute><ChatInterface /></ProtectedRoute>} />
          <Route path="/agents/settings" element={<ProtectedRoute><ChatInterface /></ProtectedRoute>} />
          <Route path="/agents/mcp-config" element={<ProtectedRoute><ChatInterface /></ProtectedRoute>} />
          <Route path="/agents/memory" element={<ProtectedRoute><ChatInterface /></ProtectedRoute>} />
          <Route path="/agents/playground" element={<ProtectedRoute><ChatInterface /></ProtectedRoute>} />
          <Route path="/chat/*" element={<LegacyChatRouteRedirect />} />
          <Route path="/settings" element={<LegacyWorkspaceRedirect view="settings" />} />
          <Route path="/mcp-config" element={<LegacyWorkspaceRedirect view="mcp-config" />} />
          <Route path="/memory" element={<LegacyWorkspaceRedirect view="memory" />} />
          <Route path="/experience" element={<ExperienceRedirect />} />
          <Route path="/playground" element={<LegacyWorkspaceRedirect view="playground" />} />

          <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
      <Toaster />
    </InstrumentationProvider>
  </StrictMode>
);
const root = existingRoot ?? createRoot(rootEl);
(globalThis as unknown as { __evaReactRoot?: ReturnType<typeof createRoot> }).__evaReactRoot = root;
root.render(app);
