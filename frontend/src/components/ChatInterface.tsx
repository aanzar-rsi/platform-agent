import EnhancedChatView from "./EnhancedChatView";
import ChatSidebar from "./ChatSidebar";
import ChatRightSidebar, { type RightSidebarTab } from "./ChatRightSidebar";
import { useState, useEffect, useCallback } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { useParams } from "react-router";
import { useLocation } from "react-router";
import type { ChatTuneSettings } from "./EnhancedChatView";
import { DEFAULT_MODEL } from "@/lib/availableModels";
import Settings from "@/pages/Settings";
import MCPConfig from "@/pages/MCPConfig";
import Memory from "@/pages/Memory";
import Playground from "@/pages/Playground";

const CHAT_VIEW_STORAGE_KEY = "eva_chat_view_mode";

export default function ChatInterface() {
  const { agent_id } = useParams();
  const { pathname } = useLocation();
  const workspaceView = pathname.startsWith("/agents/") && !agent_id
    ? pathname.slice("/agents/".length)
    : null;
  const ParamsSessionId = agent_id;
  const [activeSessionId, setActiveSessionId] = useState<string | null>(ParamsSessionId);

  // Sync activeSessionId with URL params
  useEffect(() => {
    setActiveSessionId(ParamsSessionId || null);
  }, [ParamsSessionId]);
  const [activeRightTab, setActiveRightTab] = useState<RightSidebarTab>("usage");
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true);
  const [executingSessionIds, setExecutingSessionIds] = useState<string[]>([]);
  const [tuneSettings, setTuneSettings] = useState<ChatTuneSettings>({
    maxTokens: "",
    responseFormat: "text",
    temperature: "",
    topK: "",
    topP: "",
    model: DEFAULT_MODEL,
    instructions: "",
    agentMode: "basic",
  });

  // Chat view mode — synced with EnhancedChatView's localStorage-backed state
  const [chatViewMode, setChatViewMode] = useState<"beginner" | "advanced">(() => {
    if (typeof window === "undefined") return "advanced";
    const v = localStorage.getItem(CHAT_VIEW_STORAGE_KEY);
    return v === "beginner" ? "beginner" : "advanced";
  });

  const handleViewModeChange = useCallback((mode: "beginner" | "advanced") => {
    setChatViewMode(mode);
    if (mode === "advanced") {
      setIsRightSidebarOpen(false);
    }
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden ">
      <nav aria-label="Breadcrumb" className="sr-only"><a href="/">Chat</a></nav>
      <div className="relative flex h-full w-full min-w-0 flex-1 overflow-hidden">
        {/* Left Sidebar - Chat Sessions */}
        <div className={`transition-all duration-300 ease-in-out shrink-0 border-r backdrop-blur-md ${isLeftSidebarOpen ? 'w-80' : 'w-0 overflow-hidden'}`} style={{ borderColor: 'var(--theme-border)', backgroundColor: 'var(--theme-sidebar-bg)' }}>
          <ChatSidebar
            activeSessionId={activeSessionId}
            executingSessionIds={executingSessionIds}
            onSessionSelect={setActiveSessionId}
            onCollapse={() => setIsLeftSidebarOpen(false)}
          />
        </div>

        {/* Collapsed Left Sidebar Tab */}
        {!isLeftSidebarOpen && (
          <button
            onClick={() => setIsLeftSidebarOpen(true)}
            title="Expand sidebar"
            className="absolute left-0 top-20 h-8 w-8 flex items-center justify-center rounded-r-lg border-r border-t border-b bg-white/95 backdrop-blur-sm shadow-sm hover:bg-white hover:shadow-md transition-all duration-200 z-50 group"
            style={{
              borderColor: 'rgba(163, 163, 163, 0.3)',
              color: 'rgba(113, 113, 122, 0.8)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--theme-panel-text)';
              e.currentTarget.style.borderColor = 'var(--theme-accent)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'rgba(113, 113, 122, 0.8)';
              e.currentTarget.style.borderColor = 'rgba(163, 163, 163, 0.3)';
            }}
          >
            <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-[2px]" />
          </button>
        )}

        {/* Main + Right Sidebar Resizable Area */}

        <ResizablePanelGroup direction="horizontal" className="min-w-0 flex-1">
          <ResizablePanel defaultSize={workspaceView || !isRightSidebarOpen ? 100 : 70} minSize={50} className="min-w-0 overflow-hidden">
            <div className="h-full min-w-0 overflow-hidden">
              {workspaceView === "settings" ? <Settings embedded />
                : workspaceView === "mcp-config" ? <MCPConfig embedded />
                : workspaceView === "memory" ? <Memory embedded />
                : workspaceView === "playground" ? <Playground embedded />
                : <EnhancedChatView
                 key={activeSessionId || "new-chat"}
                 sessionId={activeSessionId}
                tuneSettings={tuneSettings}
                onTuneSettingsChange={setTuneSettings}
                onViewModeChange={handleViewModeChange}
                onExecutionStateChange={(state) => {
                  if (!state.sessionId) {
                    return;
                  }
                  setExecutingSessionIds((prev) => {
                    const has = prev.includes(state.sessionId as string);
                    if (state.isExecuting) {
                      return has ? prev : [...prev, state.sessionId as string];
                    }
                    return has ? prev.filter((id) => id !== state.sessionId) : prev;
                  });
                }}
                />}
            </div>
          </ResizablePanel>
          {isRightSidebarOpen && !workspaceView && (
            <>
              <ResizableHandle withHandle style={{ backgroundColor: 'rgba(163, 163, 163, 0.3)' }} />
              <ResizablePanel defaultSize={30} minSize={26} maxSize={50} style={{ backgroundColor: '#fffeff' }}>
                <div className="h-full overflow-hidden" style={{ backgroundColor: '#fffeff' }}>
                  <div className="flex h-full flex-col">
                    <ChatRightSidebar
                      agentId={activeSessionId}
                      isExecuting={Boolean(activeSessionId && executingSessionIds.includes(activeSessionId))}
                      activeTab={activeRightTab}
                      onTabChange={setActiveRightTab}
                      onClose={() => setIsRightSidebarOpen(false)}
                      onTuneSettingsChange={setTuneSettings}
                    />
                  </div>
                </div>
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>

        {/* Collapsed Right Sidebar Tab */}
        {!isRightSidebarOpen && !workspaceView && (
          <button
            onClick={() => setIsRightSidebarOpen(true)}
            title="Expand sidebar"
            className="absolute right-0 top-20 h-8 w-8 flex items-center justify-center rounded-l-lg border-l border-t border-b bg-white/95 backdrop-blur-sm shadow-sm hover:bg-white hover:shadow-md transition-all duration-200 z-50 group"
            style={{
              borderColor: 'rgba(163, 163, 163, 0.3)',
              color: 'rgba(113, 113, 122, 0.8)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--theme-panel-text)';
              e.currentTarget.style.borderColor = 'var(--theme-accent)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'rgba(113, 113, 122, 0.8)';
              e.currentTarget.style.borderColor = 'rgba(163, 163, 163, 0.3)';
            }}
          >
            <ChevronLeft className="h-3.5 w-3.5 transition-transform group-hover:translate-x-[-2px]" />
          </button>
        )}
      </div>
    </div>
  );
}
