import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/use-auth";
import { motion, AnimatePresence } from "framer-motion";
import { 
  LogOut, 
  MessageSquarePlus, 
  MoreVertical, 
  Trash2, 
  ChevronLeft,
  ChevronDown,
  ChevronRight,
  MessageSquare,
  FolderKanban,
  FileCode,
  LayoutGrid,
  Share2,
  Circle,
  Settings,
  Server,
  Brain,
  Wrench,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  clearNewChatPolicyPreset,
  getNewChatPolicyPreset,
  setNewChatPolicyPreset,
} from "@/lib/chatPolicyPreset";
import type { AgentPolicyResponse } from "@/lib/api";
import { useNavigate } from "react-router";
import { mockSessions } from "@/lib/mockData";
import { agentsAPI } from "@/lib/api";
import { Chat } from "@/types/backend";
import { getInitials } from "@/lib/utils";
import { mapHistoryMessages } from "@/lib/chatMappers";
import { setCachedChat } from "@/lib/chatCache";
import CustomLoader from "@/components/CustomLoader";
// import { getInitials } from "@/lib/utils";

const sidebarDropdownItemClass =
  "cursor-pointer text-[var(--theme-sidebar-text)] data-[highlighted]:bg-[var(--theme-sidebar-hover)] focus:bg-[var(--theme-sidebar-hover)]";

interface ChatSidebarProps {
  activeSessionId: string | null;
  executingSessionIds?: string[];
  onSessionSelect: (chatId: string) => void;
  onCollapse?: () => void;
}

interface SidebarSection {
  id: string;
  title: string;
  icon: any;
  description?: string;
  items?: { id: string; label: string; icon: any; path?: string }[];
}

type PolicyPresetMode = "form" | "json";
type PolicyPresetForm = {
  confirmTools: boolean;
  memoryEnabled: boolean;
  confirmBeforeExtracting: boolean;
  allowAdminPromotion: boolean;
  read: string[];
  write: string[];
  promote: string[];
};

const emptyPolicyPresetForm: PolicyPresetForm = {
  confirmTools: false,
  memoryEnabled: true,
  confirmBeforeExtracting: false,
  allowAdminPromotion: false,
  read: [],
  write: [],
  promote: [],
};

const SidebarExecutionLoader = () => {
  return (
    <CustomLoader className="custom-loader--tiny" />
  );
};

export default function ChatSidebar({ activeSessionId, executingSessionIds = [], onSessionSelect, onCollapse }: ChatSidebarProps) {
  const { user, signOut, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const USE_BACKEND = true;
  
  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    projects: false,
    chats: true,
    workspace: true,
  });
  const [policyPresetOpen, setPolicyPresetOpen] = useState(false);
  const [policyPresetText, setPolicyPresetText] = useState(
    '{\n  "armory": {},\n  "memory": {}\n}'
  );
  const [policyPresetError, setPolicyPresetError] = useState<string | null>(null);
  const [policyPresetMode, setPolicyPresetMode] = useState<PolicyPresetMode>("form");
  const [policyPresetForm, setPolicyPresetForm] = useState<PolicyPresetForm>(emptyPolicyPresetForm);

  const truncateSessionName = (text: string | undefined): string => {
    // Titles are already capped at 40 chars (+ "..."); avoid a second shorter cut.
    return text || '';
  };

  const prefetchChat = useCallback((chatId: string) => {
    if (!USE_BACKEND || !chatId) return;
    void agentsAPI.get(user?.user_id, chatId).then((response) => {
      if (!response.success || !response.data) return;
      setCachedChat(chatId, {
        title: response.data.title || response.data.session_name || "Chat",
        messages: mapHistoryMessages(
          response.data.messages || [],
          response.data.execution_history || []
        ),
        rollbackCheckpointId: response.data.rollback_checkpoint_id || null,
      });
    });
  }, [USE_BACKEND, user?.user_id]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const sidebarSections: SidebarSection[] = [
    {
      id: 'workspace',
      title: 'Workspace',
      icon: LayoutGrid,
      items: [
        { id: 'settings', label: 'Settings', icon: Settings, path: '/agents/settings' },
        { id: 'mcp-config', label: 'MCP Config', icon: Server, path: '/agents/mcp-config' },
        { id: 'memory', label: 'Memory', icon: Brain, path: '/agents/memory' },
        { id: 'playground', label: 'Playground', icon: Wrench, path: '/agents/playground' },
      ],
    },
    {
      id: 'projects',
      title: 'Projects',
      icon: FolderKanban,
      description: 'Your saved projects and workspaces',
      items: []
    }
  ];

  
  // const loadChats = async () => {
  const loadChats = useCallback(async () => {
    if (!user || !('user_id' in user)) return;

    setIsLoading(true);
    try {
      const response = await agentsAPI.list({ user_id: user.user_id });
      // console.log("chart list----------->", response)
      // Backend returns 'sessions' array, but we'll check both for compatibility
      const chatsList = response.chats || response.sessions || [];

      if (response.success && chatsList.length >= 0) {
        setChats(chatsList);
      }
    } catch (error) {
      console.error('Failed to load chats:', error);
      setChats([]);
    } finally {
      setIsLoading(false);
    }
  }, [user, setChats, setIsLoading]);

  const handleNewChat = () => {
    onSessionSelect("");
    navigate('/agents');
  };

  const openPolicyPresetDialog = () => {
    const preset = getNewChatPolicyPreset();
    const armory = (preset?.armory || {}) as Record<string, unknown>;
    const memory = (preset?.memory || {}) as Record<string, unknown>;
    setPolicyPresetForm({
      confirmTools: Boolean(armory.confirm_tools),
      memoryEnabled: memory.enabled !== false,
      confirmBeforeExtracting: Boolean(memory.confirm_before_extracting),
      allowAdminPromotion: Boolean(memory.allow_admin_promotion),
      read: Array.isArray(memory.read) ? memory.read.map(String) : [],
      write: Array.isArray(memory.write) ? memory.write.map(String) : [],
      promote: Array.isArray(memory.promote) ? memory.promote.map(String) : [],
    });
    setPolicyPresetText(
      JSON.stringify(
        preset || {
          armory: {},
          memory: {},
        },
        null,
        2
      )
    );
    setPolicyPresetError(null);
    setPolicyPresetMode("form");
    setPolicyPresetOpen(true);
  };

  const applyPolicyPreset = () => {
    setPolicyPresetError(null);
    try {
      const parsed = (policyPresetMode === "json" ? JSON.parse(policyPresetText) : {
        armory: { confirm_tools: policyPresetForm.confirmTools },
        memory: {
          enabled: policyPresetForm.memoryEnabled,
          confirm_before_extracting: policyPresetForm.confirmBeforeExtracting,
          allow_admin_promotion: policyPresetForm.allowAdminPromotion,
          read: policyPresetForm.read,
          write: policyPresetForm.write,
          promote: policyPresetForm.promote,
        },
      }) as {
        armory?: Partial<AgentPolicyResponse["policy"]["armory"]>;
        memory?: Partial<AgentPolicyResponse["policy"]["memory"]>;
      };

      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Preset must be a JSON object");
      }
      if (!parsed.armory && !parsed.memory) {
        throw new Error("Preset needs at least one of: armory or memory");
      }

      setNewChatPolicyPreset(parsed);
      setPolicyPresetOpen(false);
      toast.success("New chat policy preset saved");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Invalid JSON";
      setPolicyPresetError(message);
      toast.error(`Could not save preset: ${message}`);
    }
  };

  const togglePresetScope = (field: "read" | "write" | "promote", scope: string, checked: boolean) => {
    setPolicyPresetForm((current) => ({
      ...current,
      [field]: checked
        ? Array.from(new Set([...current[field], scope]))
        : current[field].filter((item) => item !== scope),
    }));
  };

  const selectPolicyPresetMode = (mode: PolicyPresetMode) => {
    setPolicyPresetError(null);
    if (mode === "json") {
      setPolicyPresetText(JSON.stringify({
        armory: { confirm_tools: policyPresetForm.confirmTools },
        memory: {
          enabled: policyPresetForm.memoryEnabled,
          confirm_before_extracting: policyPresetForm.confirmBeforeExtracting,
          allow_admin_promotion: policyPresetForm.allowAdminPromotion,
          read: policyPresetForm.read,
          write: policyPresetForm.write,
          promote: policyPresetForm.promote,
        },
      }, null, 2));
    } else {
      try {
        const parsed = JSON.parse(policyPresetText) as Record<string, Record<string, unknown>>;
        const armory = parsed.armory || {};
        const memory = parsed.memory || {};
        setPolicyPresetForm({
          confirmTools: Boolean(armory.confirm_tools),
          memoryEnabled: memory.enabled !== false,
          confirmBeforeExtracting: Boolean(memory.confirm_before_extracting),
          allowAdminPromotion: Boolean(memory.allow_admin_promotion),
          read: Array.isArray(memory.read) ? memory.read.map(String) : [],
          write: Array.isArray(memory.write) ? memory.write.map(String) : [],
          promote: Array.isArray(memory.promote) ? memory.promote.map(String) : [],
        });
      } catch {
        setPolicyPresetError("Fix the JSON before switching to form mode");
        return;
      }
    }
    setPolicyPresetMode(mode);
  };

  const handleDeleteChat = async (chatId: string) => {
    if (!user?.user_id) return toast.error("User not logged in");

    try {
      if (USE_BACKEND) {
        await agentsAPI.edit({
          operation: "delete_chat",
          agent_id: chatId,
          user_id: user.user_id
        });

        toast.success(`Chat deleted - ${chatId}`);

        if (chats) {
          const remainingChats = chats.filter(chat => chat.agent_id !== chatId);
          setChats(remainingChats); // <-- important!

          if (activeSessionId === chatId) {
            if (remainingChats.length > 0) {
              onSessionSelect(remainingChats[0].agent_id);
            } else {
              onSessionSelect(""); // or create new chat
            }
          }
        }
        return;
      }

      // Mock mode
      toast.success("Chat deleted");
      if (activeSessionId === chatId && chats && chats.length > 0) {
        onSessionSelect(chats[0].agent_id);
      }
    } catch (error) {
      console.error("Failed to delete chat:", error);
      toast.error("Failed to delete chat");
    }
  };


  const handleDeleteAllChats = async () => {
    if (!user?.user_id) {
      toast.error("User not logged in");
      return;
    }

    try {
      if (USE_BACKEND) {
        const response = await agentsAPI.edit({
          operation: "delete_chat",
          delete_all: true,
          user_id: user.user_id,
        });


        toast.success("All chats deleted");
        setChats([]);
        onSessionSelect(""); // reset active chat
        return;
      }

      // Mock mode
      toast.success("All chats deleted");
      setChats([]);
      onSessionSelect("");
    } catch (error: any) {
      console.error(
        "Failed to delete all chats:",
        error.response?.data || error
      );
      toast.error("Failed to delete all chats");
    }
  };


  const handleSignOut = async () => {
    await signOut();
    navigate("/login");
  };

  const renderSectionHeader = (section: SidebarSection) => {
    const Icon = section.icon;
    const isExpanded = expandedSections[section.id];
    
    return (
      <button
        onClick={() => toggleSection(section.id)}
        className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all group"
        style={{ color: 'var(--theme-sidebar-text)', opacity: 0.8 }}
        onMouseEnter={(e) => {
          e.currentTarget.style.opacity = '1';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.opacity = '0.8';
        }}
      >
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" />
          <span className="text-xs font-semibold uppercase tracking-wider">{section.title}</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
      </button>
    );
  };

  // Load chats when component mounts or user changes
  useEffect(() => {
    if (USE_BACKEND && user && isAuthenticated) {
      loadChats();
    } else if (!USE_BACKEND) {
      // Mock mode - use mock sessions
      setChats(mockSessions.map(s => ({
         agent_id: s._id as string,
        user_id: s.userId as string,
        title: s.title,
        created_at: new Date(s._creationTime).toISOString(),
        lastMessageAt: s.lastMessageAt,
      })));
    }
  }, [user, isAuthenticated, USE_BACKEND, loadChats]);

  useEffect(() => {
    if (!USE_BACKEND || !user || !isAuthenticated) return;
    const onChatsChanged = () => {
      void loadChats();
    };
    window.addEventListener("eva:chats-changed", onChatsChanged);
    return () => window.removeEventListener("eva:chats-changed", onChatsChanged);
  }, [USE_BACKEND, user, isAuthenticated, loadChats]);


  const renderSectionItems = (section: SidebarSection) => {
    if (!expandedSections[section.id]) return null;
    
    return (
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="pl-2 space-y-1"
        >
          {section.description && (
            <div className="px-3 py-1.5 mb-1">
              <span className="text-sm leading-tight" style={{ color: 'var(--theme-sidebar-text)', opacity: 0.8 }}>
                {section.description}
              </span>
            </div>
          )}
          {!section.items || section.items.length === 0 ? (
            <div className="text-center py-4 text-red-500 text-xs">
              No {section.title.toLowerCase()} yet.
            </div>
          ) : (
            section.items.map((item) => {
              const ItemIcon = item.icon;
              const handleClick = () => {
                if (item.path) {
                  navigate(item.path);
                  return;
                }
                toast.info(`${item.label} coming soon!`);
              };
              return (
                <motion.button
                  key={item.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-all"
                  style={{ color: 'var(--theme-sidebar-text)' }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  onClick={handleClick}
                >
                  <ItemIcon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </motion.button>
              );
            })
          )}
        </motion.div>
      </AnimatePresence>
    );
  };

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: 'var(--theme-sidebar-bg)', color: 'var(--theme-sidebar-text)' }}>
      {/* Header with Logo + controls */}
      <div className="px-4 py-3 border-b shadow-md" style={{ borderColor: 'var(--theme-border)', backgroundColor: 'var(--theme-sidebar-bg)' }}>
        <div className="flex items-center justify-between mb-2">
           <a href="/" className="flex items-center gap-2 cursor-pointer">
             <img src="/brain_icon.svg" alt="" width={40} height={40} className="h-10 w-10 rounded-xl relative" />
            <div className="flex flex-col">
              <span className="text-lg font-semibold" style={{ color: 'var(--theme-sidebar-text)' }}>PlatformAgent</span>
              <span className="text-xs" style={{ color: 'var(--theme-sidebar-text)', opacity: 0.7 }}>V1</span>
            </div>
          </a>
          {onCollapse && (
            <Button
              onClick={onCollapse}
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0 shadow-xl"
              style={{ color: 'var(--theme-sidebar-text)', backgroundColor: 'rgba(0,0,0,0.1)' }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.1)'}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          )}
        </div>
        <div className="flex w-full overflow-hidden rounded-lg shadow-lg">
          <Button
            onClick={handleNewChat}
            className="h-12 flex-1 rounded-none border-0 font-medium transition-all"
            style={{ 
              backgroundColor: 'var(--theme-accent)', 
              color: '#010101',
              padding: '12px 16px',
              fontSize: '14px'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent-hover)'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent)'}
          >
            <span>New Chat</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-12 w-11 shrink-0 rounded-none border-0 border-l border-black/15"
            style={{
              color: '#010101',
              backgroundColor: 'var(--theme-accent)',
            }}
            onClick={openPolicyPresetDialog}
            title="New chat policy preset"
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent-hover)'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent)'}
          >
            <ChevronDown className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <ScrollArea className="flex-1 overflow-hidden chat_sidebar">
        <div className="py-4 space-y-4 px-2">
          {/* Dynamic Sections (Tasks, Code Space) */}
          {sidebarSections.map((section) => (
            <div key={section.id} className="space-y-1">
              {renderSectionHeader(section)}
              {renderSectionItems(section)}
            </div>
          ))}

          {/* Chat Section */}
          <div className="space-y-1">
            <button
              onClick={() => toggleSection('chats')}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all group"
              style={{ color: 'var(--theme-sidebar-text)' }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">RECENT CHATS</span>
              </div>
              {expandedSections.chats ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </button>

            {expandedSections.chats && (
              <AnimatePresence>
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-1"
                >
                  {isLoading && (
                    <div className="flex items-center justify-center py-4" style={{ color: 'var(--theme-sidebar-text)' }}>
                      <CustomLoader className="custom-loader--inline mr-2" /> Loading...
                    </div>
                  )}

                  {!isLoading &&
                    (
                      <div className="px-3 py-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs" style={{ color: 'var(--theme-sidebar-text)', opacity: 0.5 }}>{chats.length} chats</span>
                        </div>
                      </div>
                    )
                  }

                  {/* general Chat */}
                  {!isLoading && chats.map((chat) => (
                    <motion.div
                      key={`${chat.chat_id || chat.session_id || chat.created_at}-${chat.created_at}`}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="group"
                    >
                      <div
                        className={`flex items-start gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all min-w-0 group ${
                           activeSessionId === chat.agent_id 
                            ? "" 
                            : ""
                        }`}
                        style={{
                           backgroundColor: activeSessionId === chat.agent_id ? 'var(--theme-chat-selected-bg)' : 'transparent',
                          color: 'var(--theme-sidebar-text)',
                        }}
                        onMouseEnter={(e) => {
                           if (activeSessionId !== chat.agent_id) {
                            e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)';
                          }
                        }}
                        onMouseLeave={(e) => {
                           if (activeSessionId !== chat.agent_id) {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }
                        }}
                        onClick={() => {
                          prefetchChat(chat.agent_id);
                          navigate(`/agents/${chat.agent_id}`);
                           onSessionSelect(chat.agent_id)
                        }}
                      >
                         {activeSessionId === chat.agent_id && (
                          <div className="mt-1.5 shrink-0">
                            <Circle className="h-2 w-2 fill-current" style={{ color: 'var(--theme-active-indicator)' }} />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="text-sm truncate font-medium" style={{ color: 'var(--theme-sidebar-text)' }}>
                            {truncateSessionName(chat.session_name || chat.title) || `Chat ${new Date(chat.created_at).toLocaleDateString()}`}
                          </div>
                          <div className="text-xs mt-0.5" style={{ color: 'var(--theme-sidebar-text)', opacity: 0.6 }}>
                            {(() => {
                              const now = new Date();
                              const chatDate = new Date(chat.created_at || chat.lastMessageAt);
                              const diffMs = now.getTime() - chatDate.getTime();
                              const diffMins = Math.floor(diffMs / 60000);
                              const diffHours = Math.floor(diffMs / 3600000);
                              const diffDays = Math.floor(diffMs / 86400000);
                              
                              if (diffMins < 1) return 'Just now';
                              if (diffMins < 60) return `${diffMins}m ago`;
                              if (diffHours < 24) return `${diffHours}h ago`;
                              if (diffDays === 1) return 'Yesterday';
                              if (diffDays < 7) return `${diffDays} days ago`;
                              return chatDate.toLocaleDateString();
                            })()}
                          </div>
                        </div>
                        <div
                          className={`shrink-0 transition-opacity flex items-center gap-1 ${
                             executingSessionIds.includes(chat.agent_id) ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                          }`}
                        >
                           {executingSessionIds.includes(chat.agent_id) && <SidebarExecutionLoader />}
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                style={{ color: 'var(--theme-sidebar-text)' }}
                                onClick={(e) => e.stopPropagation()}
                              >
                                <MoreVertical className="h-3.5 w-3.5" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" style={{ backgroundColor: 'var(--theme-sidebar-bg)', borderColor: 'var(--theme-border)' }}>
                              <DropdownMenuItem
                                className={sidebarDropdownItemClass}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toast.info(`Share "${truncateSessionName(chat.session_name || chat.title)}" coming soon`);
                                }}
                              >
                                <Share2 className="h-4 w-4 mr-2" />
                                Share
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className={sidebarDropdownItemClass}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toast.info(`Rename "${truncateSessionName(chat.session_name || chat.title)}" coming soon`);
                                }}
                              >
                                <FileCode className="h-4 w-4 mr-2" />
                                Rename
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                   handleDeleteChat(chat.agent_id);
                                }}
                                className={`${sidebarDropdownItemClass} text-danger-500 data-[highlighted]:text-danger-400 focus:text-danger-400`}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  
                  {!isLoading && chats.length === 0 && (
                    <div className="text-center py-4 text-xs" style={{ color: 'var(--theme-sidebar-text)', opacity: 0.6 }}>
                      No chats yet. Create one!
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            )}
          </div>
        </div>
      </ScrollArea>

      {/* User Profile Footer */}
      <div className="border-t px-4 py-4" style={{ borderColor: 'rgba(255,255,255,0.1)', backgroundColor: 'var(--theme-sidebar-bg)' }}>
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-full flex items-center justify-center text-base font-bold" style={{ backgroundColor: 'var(--theme-accent)', color: '#010101' }}>
            {getInitials(user?.name)} 
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate" style={{ color: 'var(--theme-sidebar-text)' }}>{user?.name || "User"}</p>
            <p className="text-xs truncate" style={{ color: 'var(--theme-sidebar-text)', opacity: 0.7 }}>{user?.email || "user@example.com"}</p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0"
                style={{ color: 'var(--theme-sidebar-text)' }}
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" style={{ backgroundColor: 'var(--theme-sidebar-bg)', borderColor: 'var(--theme-border)' }}>
              <DropdownMenuItem
                onClick={handleDeleteAllChats}
                className={sidebarDropdownItemClass}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete All Chats
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={handleSignOut}
                className={`${sidebarDropdownItemClass} text-danger-500 data-[highlighted]:text-danger-400 focus:text-danger-400`}
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <Dialog open={policyPresetOpen} onOpenChange={setPolicyPresetOpen}>
        <DialogContent className="max-w-xl" style={{ backgroundColor: '#fffeff', borderColor: 'var(--theme-border)' }}>
          <DialogHeader>
            <DialogTitle>New Chat Policy Preset</DialogTitle>
            <DialogDescription>
              Optional policy applied automatically after a new chat is created. If cleared, new chats use your default policy.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-1 rounded-lg border border-gray-200 bg-gray-100 p-1">
              {(["form", "json"] as const).map((mode) => (
                <Button key={mode} size="sm" variant="ghost" className={`h-8 capitalize ${policyPresetMode === mode ? "bg-white shadow-sm" : ""}`} onClick={() => selectPolicyPresetMode(mode)}>
                  {mode}
                </Button>
              ))}
            </div>
            {policyPresetMode === "json" ? (
              <Textarea
                value={policyPresetText}
                onChange={(e) => setPolicyPresetText(e.target.value)}
                className="min-h-[220px] font-mono text-xs"
                placeholder='{"armory": {"confirm_tools": true}, "memory": {"enabled": true}}'
              />
            ) : (
              <div className="max-h-[55vh] space-y-4 overflow-y-auto pr-1 text-sm">
                <section className="space-y-2 rounded-lg border border-gray-200 p-3">
                  <h3 className="font-semibold">Armory</h3>
                  <label className="flex items-center gap-2"><Checkbox checked={policyPresetForm.confirmTools} onCheckedChange={(checked) => setPolicyPresetForm((form) => ({ ...form, confirmTools: !!checked }))} />Require confirmation before using tools</label>
                </section>
                <section className="space-y-3 rounded-lg border border-gray-200 p-3">
                  <h3 className="font-semibold">Memory</h3>
                  <label className="flex items-center gap-2"><Checkbox checked={policyPresetForm.memoryEnabled} onCheckedChange={(checked) => setPolicyPresetForm((form) => ({ ...form, memoryEnabled: !!checked }))} />Enable memory</label>
                  <label className="flex items-center gap-2"><Checkbox checked={policyPresetForm.confirmBeforeExtracting} onCheckedChange={(checked) => setPolicyPresetForm((form) => ({ ...form, confirmBeforeExtracting: !!checked }))} />Confirm before extracting memory</label>
                  <label className="flex items-center gap-2"><Checkbox checked={policyPresetForm.allowAdminPromotion} onCheckedChange={(checked) => setPolicyPresetForm((form) => ({ ...form, allowAdminPromotion: !!checked }))} />Allow admin promotion</label>
                  {(["read", "write", "promote"] as const).map((field) => (
                    <fieldset key={field} className="space-y-1.5">
                      <legend className="text-xs font-semibold capitalize">{field} scopes</legend>
                      <div className="grid grid-cols-3 gap-2">
                        {(field === "promote" ? ["TENANT", "AGENT"] : ["USER", "TENANT", "AGENT"]).map((scope) => (
                          <label key={`${field}:${scope}`} className="flex items-center gap-1.5 text-xs"><Checkbox checked={policyPresetForm[field].includes(scope)} onCheckedChange={(checked) => togglePresetScope(field, scope, !!checked)} />{scope}</label>
                        ))}
                      </div>
                    </fieldset>
                  ))}
                </section>
              </div>
            )}
            {policyPresetError && <p className="text-xs text-red-600">{policyPresetError}</p>}
            <div className="flex items-center justify-between gap-2 pt-1">
              <Button
                variant="outline"
                onClick={() => {
                  clearNewChatPolicyPreset();
                  setPolicyPresetOpen(false);
                  toast.success("Preset cleared. New chats will use default policy.");
                }}
              >
                Clear Preset
              </Button>
              <Button onClick={applyPolicyPreset}>Save Preset</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
