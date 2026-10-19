// Page that shows mcp tools, memory and servers in chat page

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { useState, useEffect, useCallback, useMemo, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Brain, Settings, Loader2, ChevronDown, ChevronRight, ChevronLeft, Box, Package, Check, Search, Server, Plus, Power, PowerOff, Eye, CheckSquare, X, Sparkles } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  TOOL_BUCKET_ALL_ID,
  TOOL_BUCKET_MIXED_ID,
  LS_TOOL_BUCKETS,
  LS_ACTIVE_TOOL_BUCKET,
  type ToolBucketDef,
} from "@/lib/toolBuckets";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router";
import { hardcodedMemoryItems } from "@/lib/hardcodedMemory";
import { useAuth } from "@/hooks/use-auth";
import {
  mcpAPI,
  memoryAPI,
  subagentsAPI,
  CatalogSubagent,
  MCPServer,
  MCPServerDetails,
} from "@/lib/api";
import { fetchToolsCatalog, type MCPTool } from "@/lib/mcp-api";
import { Memory } from "@/types/backend";

type ToolGroupItem = { name: string; description?: string; selectable: boolean; groupKey: string };
type ToolGroup = {
  title: string;
  groupKey: string;
  serverId?: string;
  connected?: boolean;
  items: ToolGroupItem[];
};

const TOOL_CARD_HEIGHT = "h-[65px]";
const TOOL_HOVER_DELAY_MS = 500;
const TOOL_HIDE_DELAY_MS = 400;

type ToolDetail = {
  name: string;
  description?: string;
  server_name?: string;
  parameters?: MCPTool["parameters"];
};

type TipLayout = {
  tip: { top: number; left: number; width: number };
  bridge: { top: number; left: number; width: number; height: number };
};

function formatToolParameters(tool: ToolDetail): string {
  const params = tool.parameters;
  if (!params?.length) return "None";
  return params
    .map((p) => {
      const req = p.required ? "*" : "";
      const desc = p.description ? ` — ${p.description}` : "";
      return `${req}${p.name} (${p.type || "any"})${desc}`;
    })
    .join("\n");
}

function computeTipLayout(rect: DOMRect, variant: "panel" | "dialog"): TipLayout {
  const tipW = variant === "dialog" ? Math.max(rect.width, 280) : 288;
  const tipH = 256;
  const margin = 8;

  if (variant === "dialog") {
    let top = rect.bottom;
    let left = rect.left;
    if (left + tipW > window.innerWidth - margin) {
      left = window.innerWidth - tipW - margin;
    }
    if (left < margin) left = margin;

    if (top + tipH > window.innerHeight - margin) {
      top = rect.top - tipH;
    }
    if (top < margin) top = margin;

    const bridgeTop = top > rect.bottom ? rect.top - 4 : rect.bottom - 4;
    const bridgeBottom = top > rect.bottom ? top + tipH : top;
    return {
      tip: { top, left, width: tipW },
      bridge: {
        top: Math.min(bridgeTop, bridgeBottom),
        left: Math.min(rect.left, left),
        width: Math.max(rect.width, tipW),
        height: Math.abs(bridgeBottom - Math.min(bridgeTop, bridgeBottom)) + 8,
      },
    };
  }

  let left = rect.left - tipW - 2;
  if (left < margin) left = rect.right + 2;
  if (left + tipW > window.innerWidth - margin) left = window.innerWidth - tipW - margin;

  let top = rect.top;
  if (top + tipH > window.innerHeight - margin) top = window.innerHeight - tipH - margin;
  if (top < margin) top = margin;

  const bridgeLeft = left < rect.left ? left + tipW - 4 : rect.right - 4;
  const bridgeRight = left < rect.left ? rect.left + 4 : left + 4;
  return {
    tip: { top, left, width: tipW },
    bridge: {
      top: Math.min(rect.top, top) - 2,
      left: Math.min(bridgeLeft, bridgeRight),
      width: Math.abs(bridgeRight - bridgeLeft),
      height: Math.max(rect.height, tipH) + 4,
    },
  };
}

function ToolHoverLayer({
  tool,
  layout,
  onMouseEnter,
  onMouseLeave,
}: {
  tool: ToolDetail;
  layout: TipLayout;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}) {
  return createPortal(
    <>
      <div
        className="fixed z-[9998]"
        style={{
          top: layout.bridge.top,
          left: layout.bridge.left,
          width: layout.bridge.width,
          height: layout.bridge.height,
        }}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        aria-hidden
      />
      <div
        className="fixed z-[9999] max-h-64 overflow-y-auto rounded-lg border bg-white p-3 shadow-lg"
        style={{
          top: layout.tip.top,
          left: layout.tip.left,
          width: layout.tip.width,
          borderColor: "var(--theme-border)",
        }}
        role="tooltip"
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      >
        <div className="break-words text-xs font-semibold text-gray-900">{tool.name}</div>
        {tool.server_name && (
          <div className="mt-0.5 text-[10px] text-gray-600">{tool.server_name}</div>
        )}
        <div className="mt-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
          Parameters
        </div>
        <pre className="mt-0.5 whitespace-pre-wrap text-[11px] leading-relaxed text-gray-800">
          {formatToolParameters(tool)}
        </pre>
        {tool.description && (
          <>
            <div className="mt-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
              Description
            </div>
            <p className="mt-0.5 whitespace-pre-wrap text-[11px] leading-relaxed text-gray-800">
              {tool.description}
            </p>
          </>
        )}
      </div>
    </>,
    document.body
  );
}

function useDelayedToolTip(variant: "panel" | "dialog", delayMs = TOOL_HOVER_DELAY_MS) {
  const anchorRef = useRef<HTMLDivElement>(null);
  const showTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hoverDepthRef = useRef(0);
  const [visible, setVisible] = useState(false);
  const [layout, setLayout] = useState<TipLayout | null>(null);

  const clearShowTimer = useCallback(() => {
    if (showTimerRef.current) {
      clearTimeout(showTimerRef.current);
      showTimerRef.current = null;
    }
  }, []);

  const clearHideTimer = useCallback(() => {
    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
  }, []);

  const updateLayout = useCallback(() => {
    const el = anchorRef.current;
    if (!el) return;
    setLayout(computeTipLayout(el.getBoundingClientRect(), variant));
  }, [variant]);

  const scheduleHide = useCallback(() => {
    clearHideTimer();
    hideTimerRef.current = setTimeout(() => {
      if (hoverDepthRef.current <= 0) setVisible(false);
    }, TOOL_HIDE_DELAY_MS);
  }, [clearHideTimer]);

  const onHoverEnter = useCallback(() => {
    hoverDepthRef.current += 1;
    clearHideTimer();
    if (hoverDepthRef.current === 1) {
      updateLayout();
      clearShowTimer();
      showTimerRef.current = setTimeout(() => {
        updateLayout();
        setVisible(true);
      }, delayMs);
    }
  }, [clearHideTimer, clearShowTimer, delayMs, updateLayout]);

  const onHoverLeave = useCallback(() => {
    hoverDepthRef.current = Math.max(0, hoverDepthRef.current - 1);
    clearShowTimer();
    if (hoverDepthRef.current === 0) scheduleHide();
  }, [clearShowTimer, scheduleHide]);

  useEffect(
    () => () => {
      clearShowTimer();
      clearHideTimer();
    },
    [clearHideTimer, clearShowTimer]
  );

  return {
    anchorRef,
    visible,
    layout,
    onCardEnter: onHoverEnter,
    onCardLeave: onHoverLeave,
    onTipEnter: onHoverEnter,
    onTipLeave: onHoverLeave,
  };
}

function ToolPickerCard({
  tool,
  checked,
  disabled = false,
  onToggle,
  variant = "panel",
}: {
  tool: ToolDetail;
  checked: boolean;
  disabled?: boolean;
  onToggle: () => void;
  variant?: "panel" | "dialog";
}) {
  const { anchorRef, visible, layout, onCardEnter, onCardLeave, onTipEnter, onTipLeave } =
    useDelayedToolTip(variant);
  const active = checked && !disabled;

  return (
    <>
      <div
        ref={anchorRef}
        className={`flex ${TOOL_CARD_HEIGHT} cursor-pointer items-start gap-2 overflow-hidden rounded border px-2 py-2 transition-colors ${
          disabled
            ? "cursor-not-allowed opacity-40"
            : active
              ? "opacity-100"
              : "border-gray-400 bg-gray-200 opacity-60"
        }`}
        style={active ? { backgroundColor: "#fffeff", borderColor: "var(--theme-border)" } : undefined}
        onMouseEnter={onCardEnter}
        onMouseLeave={onCardLeave}
        onClick={() => {
          if (disabled) return;
          onToggle();
        }}
      >
        <Checkbox checked={checked} className="pointer-events-none mt-0.5 h-4 w-4 shrink-0" />
        <div className="flex h-full min-w-0 flex-1 flex-col justify-between overflow-hidden pb-0.5">
          <div className="truncate text-xs font-medium leading-tight text-gray-900">{tool.name}</div>
          {tool.server_name && (
            <div className="truncate text-[10px] leading-tight text-gray-600">{tool.server_name}</div>
          )}
          {tool.description && (
            <div className="line-clamp-2 text-[11px] leading-snug text-gray-700">{tool.description}</div>
          )}
        </div>
      </div>
      {visible && layout && (
        <ToolHoverLayer
          tool={tool}
          layout={layout}
          onMouseEnter={onTipEnter}
          onMouseLeave={onTipLeave}
        />
      )}
    </>
  );
}

export type InfoPanelTab = "servers" | "mcp" | "memory" | "subagents";

interface InfoPanelProps {
  activeTab: InfoPanelTab;
  onTabChange: (tab: InfoPanelTab) => void;
  onClose?: () => void;
  onTuneSettingsChange?: (settings: {
    maxTokens: string;
    responseFormat: string;
    temperature: string;
    instructions: string;
    enabledTools?: string[];
  }) => void;
}

function parseMemoryValue(raw: string): unknown {
  const trimmed = raw?.trim?.() ?? "";
  if (trimmed === "" || trimmed === "null") return null;
  if (trimmed === "true") return true;
  if (trimmed === "false") return false;
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed);
  if (
    (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
    (trimmed.startsWith("[") && trimmed.endsWith("]"))
  ) {
    try {
      return JSON.parse(trimmed);
    } catch {
      return raw;
    }
  }
  return raw;
}

function entriesToPanelMemory(
  entries: Array<{ key: string; value: string; category?: string; updated_at?: string | null }>,
): Memory[] {
  return entries.map((e) => ({
    key: e.key,
    value: parseMemoryValue(e.value) as any,
    category: e.category || "general",
    lastUpdated: e.updated_at ? Date.parse(e.updated_at) || Date.now() : Date.now(),
  }));
}

function MemoryValueRenderer({ value, depth = 0 }: { value: any; depth?: number }) {
  if (depth > 5) return <span className="text-gray-900">[Too deep]</span>;

  if (value === null || value === undefined || value === 'null') {
    return <span className="text-gray-900 italic">(empty)</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-gray-900">[]</span>;
    return (
      <div className={`ml-2 ${depth > 0 ? 'mt-1' : ''}`}>
        {value.map((item, idx) => (
          <div key={idx} className="border-l-2 border-gray-900 pl-2 py-0.5">
            <MemoryValueRenderer value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value);
    if (entries.length === 0) return <span className="text-gray-900">&#123; &#125;</span>;
    return (
      <div className={`${depth > 0 ? 'mt-1' : ''}`}>
        {entries.map(([key, val]) => (
          <div key={key} className={`${depth > 0 ? 'ml-2 border-l-2 border-neutral-700 pl-2 py-0.5' : ''}`}>
            <span className="text-brand font-medium">{key}:</span>{' '}
            <MemoryValueRenderer value={val} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  return <span>{String(value)}</span>;
}

function ToolCard({ tool }: { tool: MCPTool }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card className="bg-neutral-900/50 border-neutral-800 hover:border-primary-600/50 transition-colors">
      <CardHeader
        className="p-3 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="h-3 w-3 text-neutral-400" />
          ) : (
            <ChevronRight className="h-3 w-3 text-neutral-400" />
          )}
          <CardTitle className="text-sm text-neutral-50">{tool.name}</CardTitle>
        </div>
      </CardHeader>
      {isExpanded && tool.description && (
        <CardContent className="pt-0 px-3 pb-3">
          <CardDescription className="text-xs text-neutral-400 whitespace-pre-wrap">
            {tool.description}
          </CardDescription>
        </CardContent>
      )}
    </Card>
  );
}

function SubagentCard({ subagent }: { subagent: CatalogSubagent }) {
  const [detailsOpen, setDetailsOpen] = useState(true);
  const hasDetails = Boolean(
    subagent.when_to_use || subagent.scope || (subagent.tools && subagent.tools.length > 0)
  );
  const isStudio = subagent.source === "agent_studio";

  return (
    <div
      className="rounded-xl border p-3 shadow-sm"
      style={{ backgroundColor: "#f8f8f6", borderColor: "var(--theme-border)" }}
    >
      <div className="flex items-start gap-2.5">
        <div
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
          style={{ backgroundColor: "var(--theme-accent)" }}
        >
          <Sparkles className="h-4 w-4" style={{ color: "#ffffff" }} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-bold text-gray-900">
            {subagent.display_name || subagent.name}
          </div>
          <div className="mt-0.5 font-mono text-[10px] text-gray-600">{subagent.name}</div>
          {subagent.description && (
            <p className="mt-2 text-xs leading-relaxed text-gray-700">{subagent.description}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-1">
            {isStudio && (
              <Badge
                className="text-[9px] px-1.5 py-0 text-gray-900"
                style={{ backgroundColor: "#fffeff", borderColor: "var(--theme-border)" }}
              >
                Your agent
              </Badge>
            )}
            {subagent.status && (
              <Badge
                className="text-[9px] px-1.5 py-0 text-gray-900"
                style={{ backgroundColor: "#fffeff", borderColor: "var(--theme-border)" }}
              >
                {subagent.status}
              </Badge>
            )}
            {subagent.availability && (
              <Badge
                className="text-[9px] px-1.5 py-0 text-gray-900"
                style={{ backgroundColor: "#fffeff", borderColor: "var(--theme-border)" }}
              >
                {subagent.availability}
              </Badge>
            )}
            {subagent.scope && (
              <Badge
                variant="outline"
                className="max-w-full truncate text-[9px] px-1.5 py-0 text-gray-700"
                style={{ backgroundColor: "#fffeff", borderColor: "var(--theme-border)" }}
                title={subagent.scope}
              >
                Scoped task
              </Badge>
            )}
          </div>
        </div>
      </div>

      {hasDetails && (
        <div className="mt-3 border-t pt-2" style={{ borderColor: "var(--theme-border)" }}>
          <button
            type="button"
            onClick={() => setDetailsOpen((open) => !open)}
            className="flex w-full items-center gap-1.5 text-left text-xs font-semibold text-gray-900 transition-colors hover:text-gray-700"
          >
            {detailsOpen ? (
              <ChevronDown className="h-3.5 w-3.5 shrink-0" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5 shrink-0" />
            )}
            Details
          </button>
          {detailsOpen && (
            <div className="mt-2 space-y-2.5 text-xs text-gray-700">
              {subagent.scope && (
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                    Scope
                  </div>
                  <p className="mt-0.5 leading-relaxed">{subagent.scope}</p>
                </div>
              )}
              {subagent.when_to_use && (
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                    When to use
                  </div>
                  <p className="mt-0.5 leading-relaxed">{subagent.when_to_use}</p>
                </div>
              )}
              {subagent.tools && subagent.tools.length > 0 && (
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                    Tools & capabilities
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {subagent.tools.map((tool) => (
                      <Badge
                        key={tool}
                        className="text-[9px] px-1.5 py-0 text-gray-900"
                        style={{ backgroundColor: "#fffeff", borderColor: "var(--theme-border)" }}
                      >
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ServerToolItem({ tool, enabled, onToggle }: { tool: MCPTool; enabled: boolean; onToggle: (name: string) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <Card className="bg-neutral-900/50 border-neutral-800">
      <CardHeader className="p-3">
        <div className="flex items-center gap-2">
          <button className="p-1 text-neutral-400 hover:text-neutral-200" onClick={() => setIsOpen(!isOpen)}>
            {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          </button>
          <div className="flex-1 min-w-0 cursor-pointer" onClick={() => onToggle(tool.name)}>
            <div className="flex items-center gap-2">
              <Checkbox checked={enabled} className="pointer-events-none h-3 w-3" />
              <span className="text-xs text-neutral-100 truncate">{tool.name}</span>
            </div>
          </div>
        </div>
      </CardHeader>
      {isOpen && tool.description && (
        <CardContent className="pt-0 px-3 pb-3">
          <CardDescription className="text-xs text-neutral-400 whitespace-pre-wrap">
            {tool.description}
          </CardDescription>
        </CardContent>
      )}
    </Card>
  );
}

export default function InfoPanel({ activeTab, onTabChange, onClose, onTuneSettingsChange }: InfoPanelProps) {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const USE_BACKEND = true;
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  const [tools, setTools] = useState<MCPTool[]>([]);
  const [internalTools, setInternalTools] = useState<MCPTool[]>([]);
  const [mcpTools, setMcpTools] = useState<MCPTool[]>([]);
  const [userMemory, setUserMemory] = useState<Memory[]>([]);
  const [subagents, setSubagents] = useState<CatalogSubagent[]>([]);
  const [subagentsLoading, setSubagentsLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [enabledTools, setEnabledTools] = useState<string[] | undefined>(undefined);
  const [serverToolsSearch, setServerToolsSearch] = useState("");
  const [bucketSearch, setBucketSearch] = useState("");
  const [serverToolsExpanded, setServerToolsExpanded] = useState(true);
  const [collapsedServerGroups, setCollapsedServerGroups] = useState<Set<string>>(new Set());
  const [collapsedToolSections, setCollapsedToolSections] = useState<Set<string>>(new Set());
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [isLoadingServers, setIsLoadingServers] = useState(false);
  const [connectingServerId, setConnectingServerId] = useState<string | null>(null);
  const [newServer, setNewServer] = useState<{ name: string; url: string }>({ name: "", url: "" });
  const [constraints, setConstraints] = useState({ maxTokens: "", responseFormat: "text", temperature: "" });
  const [instructions, setInstructions] = useState("");
  const [serverDetails, setServerDetails] = useState<Record<string, MCPServerDetails | null>>({});
  const [mcpStatus, setMcpStatus] = useState<{ connected: boolean; server_url?: string } | null>(null);
  const [showToolPicker, setShowToolPicker] = useState(false);
  const [toolPickerLoading, setToolPickerLoading] = useState(false);
  const [toolPickerSearch, setToolPickerSearch] = useState("");
  const [groupedTools, setGroupedTools] = useState<ToolGroup[]>([]);
  const [modalSelected, setModalSelected] = useState<Set<string>>(new Set());
  const [modalCollapsedGroups, setModalCollapsedGroups] = useState<Set<string>>(new Set());

  const toolCatalogByName = useMemo(() => {
    const map = new Map<string, MCPTool>();
    for (const t of [...internalTools, ...mcpTools, ...tools]) {
      map.set(t.name, t);
    }
    return map;
  }, [internalTools, mcpTools, tools]);

  const resolveToolDetail = useCallback(
    (item: Pick<ToolGroupItem, "name" | "description">): ToolDetail => {
      const found = toolCatalogByName.get(item.name);
      if (found) return found;
      return { name: item.name, description: item.description };
    },
    [toolCatalogByName]
  );

  const [toolBuckets, setToolBuckets] = useState<ToolBucketDef[]>(() => {
    try {
      const raw = localStorage.getItem(LS_TOOL_BUCKETS);
      if (raw) return JSON.parse(raw) as ToolBucketDef[];
    } catch { /* empty */ }
    return [];
  });
  const [activeToolBucketId, setActiveToolBucketId] = useState<string>(() => {
    try {
      return localStorage.getItem(LS_ACTIVE_TOOL_BUCKET) || TOOL_BUCKET_ALL_ID;
    } catch {
      return TOOL_BUCKET_ALL_ID;
    }
  });
  const [showCreateToolBucket, setShowCreateToolBucket] = useState(false);
  const [newBucketName, setNewBucketName] = useState("");
  const [newBucketPicked, setNewBucketPicked] = useState<Set<string>>(() => new Set());
  const [createBucketFilter, setCreateBucketFilter] = useState("");
  const [createBucketGroupedTools, setCreateBucketGroupedTools] = useState<ToolGroup[]>([]);
  const [createBucketCollapsedGroups, setCreateBucketCollapsedGroups] = useState<Set<string>>(() => new Set());
  const [mcpToolsDialogLoading, setMcpToolsDialogLoading] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(LS_ACTIVE_TOOL_BUCKET, activeToolBucketId);
    } catch { /* ignore */ }
  }, [activeToolBucketId]);

  useEffect(() => {
    try {
      localStorage.setItem(LS_TOOL_BUCKETS, JSON.stringify(toolBuckets));
    } catch { /* ignore */ }
  }, [toolBuckets]);

  const applyAllToolsBucket = useCallback(() => {
    setEnabledTools(undefined);
    setActiveToolBucketId(TOOL_BUCKET_ALL_ID);
  }, []);

  const applyNamedBucket = useCallback((b: ToolBucketDef) => {
    setEnabledTools(b.toolNames.length ? [...b.toolNames] : undefined);
    setActiveToolBucketId(b.id);
  }, []);

  const loadToolGroups = useCallback(async (): Promise<ToolGroup[]> => {
    const groups: ToolGroup[] = [];

    if (internalTools.length > 0) {
      groups.push({
        title: "Internal tools",
        groupKey: "internal",
        connected: true,
        items: internalTools.map((t) => ({
          name: t.name,
          description: t.description,
          selectable: true,
          groupKey: "internal",
        })),
      });
    }

    const serverList = servers.length > 0 ? servers : (await mcpAPI.listServers()).servers;
    const details = await Promise.all(
      serverList.map(async (s) => {
        try {
          const cached = serverDetails[s.id];
          if (cached?.tools) {
            return [s, cached.tools, cached.connected || false] as const;
          }
          const d = await mcpAPI.getServerDetails(s.id, true);
          return [s, d.details?.tools || [], d.details?.connected || false] as const;
        } catch {
          return [s, [], false] as const;
        }
      })
    );
    for (const [srv, toolsArr, connected] of details) {
      if (toolsArr.length > 0) {
        groups.push({
          title: srv.name,
          groupKey: srv.id,
          serverId: srv.id,
          connected,
          items: toolsArr.map((t: any) => ({
            name: t.name,
            description: t.description,
            selectable: true,
            groupKey: srv.id,
          })),
        });
      }
    }
    if (groups.filter((g) => g.groupKey !== "internal" && g.groupKey !== "mcp").every((g) => g.items.length === 0)) {
      if (mcpTools.length > 0) {
        groups.push({
          title: "MCP tools",
          groupKey: "mcp",
          connected: servers.some((s) => s.is_connected),
          items: mcpTools.map((t) => ({
            name: t.name,
            description: t.description,
            selectable: true,
            groupKey: "mcp",
          })),
        });
      }
    } else if (mcpTools.length > 0) {
      const seenMcp = new Set(
        groups.flatMap((g) => g.items.map((i) => i.name))
      );
      const orphanMcp = mcpTools.filter((t) => t.name && !seenMcp.has(t.name));
      if (orphanMcp.length > 0) {
        groups.push({
          title: "MCP tools",
          groupKey: "mcp",
          connected: servers.some((s) => s.is_connected),
          items: orphanMcp.map((t) => ({
            name: t.name,
            description: t.description,
            selectable: true,
            groupKey: "mcp",
          })),
        });
      }
    }
    const seen = new Set<string>();
    for (const g of groups) {
      g.items.forEach((i) => {
        if (i.name) seen.add(i.name);
      });
    }
    const orphanTools = tools.filter((t) => t.name && !seen.has(t.name));
    if (orphanTools.length > 0) {
      groups.push({
        title: "Other tools",
        groupKey: "other",
        items: orphanTools.map((t) => ({
          name: t.name,
          description: t.description,
          selectable: true,
          groupKey: "other",
        })),
      });
    }
    groups.sort((a, b) => {
      if (a.groupKey === "internal") return -1;
      if (b.groupKey === "internal") return 1;
      if (a.groupKey === "mcp") return 1;
      if (b.groupKey === "mcp") return -1;
      if (a.groupKey === "other") return 1;
      if (b.groupKey === "other") return -1;
      return a.title.localeCompare(b.title);
    });
    return groups;
  }, [servers, serverDetails, tools, internalTools, mcpTools]);

  const openCreateToolBucket = useCallback(async () => {
    setNewBucketName("");
    setNewBucketPicked(new Set());
    setCreateBucketFilter("");
    setCreateBucketCollapsedGroups(new Set());
    setShowCreateToolBucket(true);
    setMcpToolsDialogLoading(true);
    try {
      const groups = await loadToolGroups();
      setCreateBucketGroupedTools(groups);
    } catch {
      setCreateBucketGroupedTools([]);
    } finally {
      setMcpToolsDialogLoading(false);
    }
  }, [loadToolGroups]);

  const createToolBucketSubmit = useCallback(() => {
    const name = newBucketName.trim();
    if (!name) return;
    if (newBucketPicked.size === 0) return;
    const id = `b-${Date.now()}`;
    const created: ToolBucketDef = { id, name, toolNames: Array.from(newBucketPicked) };
    setToolBuckets((prev) => [...prev, created]);
    setEnabledTools([...created.toolNames]);
    setActiveToolBucketId(id);
    setShowCreateToolBucket(false);
    setNewBucketName("");
    setNewBucketPicked(new Set());
  }, [newBucketName, newBucketPicked]);

  const removeToolBucket = useCallback(
    (id: string) => {
      setToolBuckets((prev) => prev.filter((b) => b.id !== id));
      if (activeToolBucketId === id) {
        setEnabledTools(undefined);
        setActiveToolBucketId(TOOL_BUCKET_ALL_ID);
      }
    },
    [activeToolBucketId]
  );

  // Short label for MCP tab badge
  const mcpBucketBadge = useMemo(() => {
    if (activeToolBucketId === TOOL_BUCKET_ALL_ID) return "All tools";
    if (activeToolBucketId === TOOL_BUCKET_MIXED_ID) {
      if (enabledTools === undefined) return "All tools";
      return enabledTools.length ? `Custom ${enabledTools.length}` : "None";
    }
    return toolBuckets.find((b) => b.id === activeToolBucketId)?.name ?? "Bucket";
  }, [activeToolBucketId, enabledTools, toolBuckets]);

  // Handler to toggle tools between enabled/disabled
  const handleToolToggle = (toolName: string) => {
    setActiveToolBucketId(TOOL_BUCKET_MIXED_ID);
    setEnabledTools((prev) => {
      if (!prev) return [toolName];
      return prev.includes(toolName) ? prev.filter((name) => name !== toolName) : [...prev, toolName];
    });
  };

  const toggleToolSectionCollapse = (sectionId: string) => {
    setCollapsedToolSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) next.delete(sectionId);
      else next.add(sectionId);
      return next;
    });
  };

  const isToolEnabled = (toolName: string) => !enabledTools || enabledTools.includes(toolName);

  const selectAllToolsInList = (toolList: Array<{ name: string }>) => {
    setActiveToolBucketId(TOOL_BUCKET_MIXED_ID);
    setEnabledTools((prev) => {
      const next = new Set(prev || []);
      toolList.forEach((tool) => next.add(tool.name));
      return Array.from(next);
    });
  };

  const deselectAllToolsInList = (toolList: Array<{ name: string }>) => {
    setActiveToolBucketId(TOOL_BUCKET_MIXED_ID);
    setEnabledTools((prev) => {
      if (!prev) {
        const allNames = new Set([...internalTools, ...mcpTools].map((t) => t.name));
        toolList.forEach((tool) => allNames.delete(tool.name));
        return Array.from(allNames);
      }
      const toolNames = new Set(toolList.map((t) => t.name));
      return prev.filter((name) => !toolNames.has(name));
    });
  };

  const areAllToolsSelectedInList = (toolList: Array<{ name: string }>): boolean => {
    if (toolList.length === 0) return false;
    if (!enabledTools) return true;
    return toolList.every((tool) => enabledTools.includes(tool.name));
  };

  const renderToolListSection = (
    sectionId: string,
    title: string,
    subtitle: string,
    toolList: MCPTool[],
    icon: ReactNode
  ) => {
    const filtered = toolList.filter((tool) =>
      tool.name.toLowerCase().includes(bucketSearch.toLowerCase())
    );
    const isCollapsed = collapsedToolSections.has(sectionId);
    const allSelected = areAllToolsSelectedInList(filtered);

    return (
      <div key={sectionId} className="space-y-1">
        <div
          className="flex items-center justify-between rounded border p-1.5"
          style={{ backgroundColor: "#f5f5f5", borderColor: "var(--theme-border)" }}
        >
          <button
            type="button"
            onClick={() => toggleToolSectionCollapse(sectionId)}
            className="flex flex-1 items-center gap-1.5 text-left transition-colors"
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4 text-gray-900" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-900" />
            )}
            {icon}
            <div className="min-w-0">
              <span className="block text-xs font-semibold text-gray-900">{title}</span>
              <span className="block text-[10px] text-gray-600">{subtitle}</span>
            </div>
            <Badge
              className="ml-auto text-[9px] px-1.5 py-0 text-gray-900"
              style={{ backgroundColor: "#fffeff", borderColor: "var(--theme-border)" }}
            >
              {filtered.length} {filtered.length === 1 ? "tool" : "tools"}
            </Badge>
          </button>
          <Button
            variant="ghost"
            size="sm"
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              if (allSelected) deselectAllToolsInList(filtered);
              else selectAllToolsInList(filtered);
            }}
            className="h-5 px-1.5 text-[9px] text-gray-900 hover:text-gray-800"
            disabled={filtered.length === 0}
          >
            <CheckSquare className="h-2.5 w-2.5" />
            {allSelected ? "Deselect All" : "Select All"}
          </Button>
        </div>

        {!isCollapsed && (
          <div className="space-y-1">
            {filtered.length === 0 ? (
              <p className="px-1 py-2 text-center text-xs text-gray-600">
                {bucketSearch ? "No tools match your search" : "No tools available"}
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-1">
                {filtered.map((tool) => (
                  <ToolPickerCard
                    key={`${sectionId}-${tool.name}`}
                    tool={tool}
                    checked={isToolEnabled(tool.name)}
                    onToggle={() => handleToolToggle(tool.name)}
                    variant="panel"
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // Group tools by server
  const getToolsByServer = () => {
    const grouped: Array<{ serverId: string; serverName: string; tools: Array<{ name: string; description?: string }>; connected: boolean }> = [];
    
    // Get tools from serverDetails
    for (const [serverId, details] of Object.entries(serverDetails)) {
      if (details?.tools && details.tools.length > 0) {
        const server = servers.find(s => s.id === serverId);
        grouped.push({
          serverId,
          serverName: server?.name || details.server_name || 'Unknown Server',
          tools: details.tools.map((t: any) => ({
            name: t.name,
            description: t.description
          })),
          connected: details.connected || false
        });
      }
    }
    
    // Also include tools from the main tools list that might not be in serverDetails
    const serverToolNames = new Set(grouped.flatMap(g => g.tools.map(t => t.name)));
    const orphanTools = tools.filter(t => !serverToolNames.has(t.name));
    
    if (orphanTools.length > 0) {
      grouped.push({
        serverId: 'other',
        serverName: 'Other Tools',
        tools: orphanTools.map(t => ({ name: t.name, description: t.description })),
        connected: true
      });
    }
    
    return grouped;
  };

  // Toggle collapse for a server group
  const toggleServerGroupCollapse = (serverId: string) => {
    setCollapsedServerGroups(prev => {
      const next = new Set(prev);
      if (next.has(serverId)) {
        next.delete(serverId);
      } else {
        next.add(serverId);
      }
      return next;
    });
  };

  // Select all tools for a server
  const selectAllToolsForServer = (serverId: string, serverTools: Array<{ name: string }>) => {
    setActiveToolBucketId(TOOL_BUCKET_MIXED_ID);
    setEnabledTools((prev) => {
      const next = new Set(prev || []);
      serverTools.forEach((tool) => next.add(tool.name));
      return Array.from(next);
    });
  };

  // Deselect all tools for a server
  const deselectAllToolsForServer = (serverId: string, serverTools: Array<{ name: string }>) => {
    setActiveToolBucketId(TOOL_BUCKET_MIXED_ID);
    setEnabledTools((prev) => {
      if (!prev) return [];
      const toolNames = new Set(serverTools.map((t) => t.name));
      return prev.filter((name) => !toolNames.has(name));
    });
  };

  // Check if all tools for a server are selected
  const areAllToolsSelectedForServer = (serverTools: Array<{ name: string }>): boolean => {
    if (serverTools.length === 0) return false;
    if (!enabledTools) return true; // If undefined, all tools are enabled
    return serverTools.every(tool => enabledTools.includes(tool.name));
  };

  // Modal helper functions
  const toggleModalGroupCollapse = (groupKey: string) => {
    setModalCollapsedGroups(prev => {
      const next = new Set(prev);
      if (next.has(groupKey)) {
        next.delete(groupKey);
      } else {
        next.add(groupKey);
      }
      return next;
    });
  };

  const selectAllToolsForModalGroup = (groupItems: Array<{ name: string; selectable: boolean }>) => {
    setModalSelected(prev => {
      const next = new Set(prev);
      groupItems.filter(item => item.selectable).forEach(item => next.add(item.name));
      return next;
    });
  };

  const deselectAllToolsForModalGroup = (groupItems: Array<{ name: string; selectable: boolean }>) => {
    setModalSelected(prev => {
      const next = new Set(prev);
      const toolNames = new Set(groupItems.filter(item => item.selectable).map(item => item.name));
      toolNames.forEach(name => next.delete(name));
      return next;
    });
  };

  const areAllToolsSelectedForModalGroup = (groupItems: Array<{ name: string; selectable: boolean }>): boolean => {
    const selectableTools = groupItems.filter(item => item.selectable);
    if (selectableTools.length === 0) return false;
    return selectableTools.every(item => modalSelected.has(item.name));
  };

  const toggleCreateBucketGroupCollapse = (groupKey: string) => {
    setCreateBucketCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupKey)) next.delete(groupKey);
      else next.add(groupKey);
      return next;
    });
  };

  const selectAllToolsForCreateBucketGroup = (groupItems: Array<{ name: string; selectable: boolean }>) => {
    setNewBucketPicked((prev) => {
      const next = new Set(prev);
      groupItems.filter((item) => item.selectable).forEach((item) => next.add(item.name));
      return next;
    });
  };

  const deselectAllToolsForCreateBucketGroup = (groupItems: Array<{ name: string; selectable: boolean }>) => {
    setNewBucketPicked((prev) => {
      const next = new Set(prev);
      const toolNames = new Set(groupItems.filter((item) => item.selectable).map((item) => item.name));
      toolNames.forEach((name) => next.delete(name));
      return next;
    });
  };

  const areAllToolsSelectedForCreateBucketGroup = (groupItems: Array<{ name: string; selectable: boolean }>): boolean => {
    const selectableTools = groupItems.filter((item) => item.selectable);
    if (selectableTools.length === 0) return false;
    return selectableTools.every((item) => newBucketPicked.has(item.name));
  };

  // Treat all MCP tools as server tools for selection in Quick Access
  const serverTools = tools;

  // DON'T auto-initialize enabledTools - undefined means "use all tools" (both internal + external)
  // Only set enabledTools when user explicitly selects tools in the tool picker
  // This way, internal tools (cache_retrieve, llm_summary, etc.) are always available
  // useEffect(() => {
  //   if (tools.length > 0 && enabledTools === undefined) {
  //     setEnabledTools(tools.map(t => t.name));
  //   }
  // }, [tools, enabledTools]);

  // Notify parent when tune settings change
  useEffect(() => {
    const settings = {
      maxTokens: constraints.maxTokens,
      responseFormat: constraints.responseFormat,
      temperature: constraints.temperature,
      instructions,
      enabledTools
    };
    onTuneSettingsChange?.(settings);
  }, [constraints, instructions, enabledTools, onTuneSettingsChange]);

  const loadData = useCallback(async () => {
    if (!user || !('user_id' in user)) return;

    setLoading(true);
    try {
      const [memoryRes, catalog] = await Promise.all([
        memoryAPI.get({ user_id: user.user_id }).catch(() => null),
        fetchToolsCatalog(),
      ]);

      if (memoryRes?.entries?.length) {
        setUserMemory(entriesToPanelMemory(memoryRes.entries));
      } else {
        setUserMemory(hardcodedMemoryItems() as any);
      }

      setInternalTools(catalog.internal);
      setMcpTools(catalog.mcp);
      setTools([...catalog.internal, ...catalog.mcp]);
    } catch (error) {
      console.error('Failed to load panel data:', error);
      setUserMemory(hardcodedMemoryItems() as any);
      setTools([]);
      setInternalTools([]);
      setMcpTools([]);
    } finally {
      setLoading(false);
    }
  }, [user]);

  const loadServers = useCallback(async () => {
    try {
      setIsLoadingServers(true);
      const [response, status] = await Promise.all([
        mcpAPI.listServers(),
        mcpAPI.getStatus().catch(() => ({ connected: false })),
      ]);
      setServers(response.servers || []);
      setMcpStatus(status as any);

      const detailsEntries = await Promise.all(
        (response.servers || []).map(async (s: MCPServer) => {
          try {
            const d = await mcpAPI.getServerDetails(s.id, true);
            return [s.id, d.details] as [string, MCPServerDetails | null];
          } catch {
            return [s.id, null] as [string, MCPServerDetails | null];
          }
        })
      );
      const detailsMap: Record<string, MCPServerDetails | null> = {};
      for (const [id, d] of detailsEntries) {
        if (d) {
          detailsMap[id] = d;
        }
      }
      setServerDetails(detailsMap);
    } catch (error) {
      console.error("Failed to load servers:", error);
      setServers([]);
    } finally {
      setIsLoadingServers(false);
    }
  }, []);

  const refreshMcpServersAndTools = useCallback(async () => {
    await loadServers();
    await loadData();
  }, [loadServers, loadData]);

  const loadSubagents = useCallback(async () => {
    setSubagentsLoading(true);
    try {
      const catalog = await subagentsAPI.list();
      setSubagents(catalog.subagents || []);
    } catch (error) {
      console.error("Failed to load subagents:", error);
      setSubagents([]);
    } finally {
      setSubagentsLoading(false);
    }
  }, []);

  // Load data when component mounts or user changes
  useEffect(() => {
    if (USE_BACKEND && user && isAuthenticated) {
      void refreshMcpServersAndTools();
      void loadSubagents();
    } else {
      setUserMemory(hardcodedMemoryItems() as any);
    }
  }, [user, isAuthenticated, USE_BACKEND, refreshMcpServersAndTools, loadSubagents]);

  // Resync when switching to MCP, Servers, Memory, or Subagents tab (skip first run; mount effect already loaded)
  const previousTabRef = useRef<string | null>(null);
  useEffect(() => {
    if (!USE_BACKEND || !user || !isAuthenticated) return;
    const onMcpOrServers = activeTab === "mcp" || activeTab === "servers";
    const onSubagents = activeTab === "subagents";
    const onMemory = activeTab === "memory";
    const prev = previousTabRef.current;
    previousTabRef.current = activeTab;
    if (prev === null) return;
    if (onMcpOrServers) {
      void refreshMcpServersAndTools();
    } else if (onSubagents) {
      void loadSubagents();
    } else if (onMemory) {
      void loadData();
    }
  }, [activeTab, user, isAuthenticated, USE_BACKEND, refreshMcpServersAndTools, loadSubagents, loadData]);

  // Listen for MCP server updates (e.g. from chat / other views)
  useEffect(() => {
    const handleMCPUpdate = () => {
      if (USE_BACKEND && user && isAuthenticated) {
        void refreshMcpServersAndTools();
      }
    };
    window.addEventListener("mcp-servers-updated", handleMCPUpdate);
    return () => {
      window.removeEventListener("mcp-servers-updated", handleMCPUpdate);
    };
  }, [user, isAuthenticated, USE_BACKEND, refreshMcpServersAndTools]);

  const openToolPicker = async () => {
    setShowToolPicker(true);
    setToolPickerLoading(true);
    try {
      const groups = await loadToolGroups();
      setGroupedTools(groups);
      if (enabledTools === undefined) {
        const allSelectableTools = groups.flatMap((g) => g.items.filter((item) => item.selectable).map((item) => item.name));
        setModalSelected(new Set(allSelectableTools));
      } else {
        setModalSelected(new Set(enabledTools));
      }
    } finally {
      setToolPickerLoading(false);
    }
  };

  const handleToggleServerEnabled = async (server: MCPServer) => {
    try {
      await mcpAPI.updateServer(server.id, { enabled: !server.enabled });
      await refreshMcpServersAndTools();
    } catch (error) {
      console.error('Failed to update server:', error);
    }
  };

  const handleConnectServer = async (server: MCPServer) => {
    try {
      setConnectingServerId(server.id);
      await mcpAPI.connectServer(server.id);
    } catch (error) {
      console.error('Failed to connect server:', error);
    } finally {
      setConnectingServerId(null);
      await refreshMcpServersAndTools();
    }
  };

  const handleDisconnectServer = async (server?: MCPServer) => {
    try {
      await mcpAPI.disconnectServer(server?.id);
    } catch (error) {
      console.error('Failed to disconnect server:', error);
    } finally {
      await refreshMcpServersAndTools();
    }
  };

  const handleConnectAll = async () => {
    const enabledServers = servers.filter(s => s.enabled && s.is_connected !== true);
    if (enabledServers.length === 0) return;

    for (const server of enabledServers) {
      try {
        await mcpAPI.connectServer(server.id);
      } catch (error) {
        console.error(`Failed to connect server ${server.name}:`, error);
      }
    }
    await refreshMcpServersAndTools();
  };

  const handleAddServer = async () => {
    if (!newServer.name.trim() || !newServer.url.trim()) return;
    try {
      await mcpAPI.createServer({ name: newServer.name.trim(), url: newServer.url.trim(), enabled: true });
      setNewServer({ name: "", url: "" });
      await refreshMcpServersAndTools();
    } catch (error) {
      console.error('Failed to add server:', error);
    }
  };

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#fffeff', color: 'var(--theme-panel-text)' }}>
      <div className="border-b p-3 flex items-center justify-between relative min-h-15.25" style={{ borderColor: 'var(--theme-border)', backgroundColor: '#fffeff' }}>
        <div className="flex items-center gap-2">
          {onClose && (
            <button
              onClick={onClose}
              title="Collapse"
              className="h-6 w-6 shrink-0 rounded-md flex items-center justify-center transition-all duration-200 hover:bg-gray-100 active:scale-95"
              style={{ 
                color: 'rgba(113, 113, 122, 0.8)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--theme-panel-text)';
                e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.04)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'rgba(113, 113, 122, 0.8)';
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          )}
          <div className="flex flex-col">
            <h2 className="font-semibold text-sm" style={{ color: 'var(--theme-panel-text)' }}>Quick Access</h2>
            <p className="text-xs" style={{ color: 'var(--theme-panel-text)', opacity: 0.6 }}>Configure your session</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            style={{ color: 'var(--theme-panel-text)' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--theme-accent)';
              e.currentTarget.style.color = '#171717';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = 'var(--theme-panel-text)';
            }}
            onClick={() => navigate("/agents/settings")}
            title="Settings"
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => onTabChange(v as typeof activeTab)} className="flex-1 flex flex-col min-h-0" style={{ backgroundColor: '#fffeff' }}>
        <div className="border-b p-2 shrink-0" style={{ borderColor: 'rgba(163, 163, 163, 0.2)', backgroundColor: '#fffeff' }}>
          <TabsList className="grid gap-2 w-full grid-cols-4 h-9" style={{ backgroundColor: 'transparent' }}>
            <TabsTrigger 
              value="mcp" 
              className="text-xs relative flex items-center justify-center gap-1.5 h-full"
              style={{ 
                color: activeTab === 'mcp' ? '#fbe232' : 'rgba(113, 113, 122, 0.8)',
                backgroundColor: 'transparent',
                border: 'none',
                boxShadow: 'none'
              }}
              data-state={activeTab === 'mcp' ? 'active' : 'inactive'}
              title="Tools: internal and MCP tool toggles"
            >
              <Box className="h-3.5 w-3.5" style={{ color: activeTab === 'mcp' ? '#fbe232' : 'rgba(113, 113, 122, 0.8)' }} />
              <span className="whitespace-nowrap">Tools</span>
              <Badge
                variant="outline"
                className="max-w-[4.5rem] truncate border-yellow-200/80 bg-yellow-50 px-1 py-0 text-[8px] font-normal text-gray-700"
                title="Active tool selection (next message)"
              >
                {mcpBucketBadge}
              </Badge>
              {activeTab === 'mcp' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5" style={{ backgroundColor: '#fbe232' }} />
              )}
            </TabsTrigger>
            <TabsTrigger
              value="subagents"
              className="text-xs relative flex items-center justify-center gap-1.5 h-full"
              style={{
                color: activeTab === 'subagents' ? '#fbe232' : 'rgba(113, 113, 122, 0.8)',
                backgroundColor: 'transparent',
                border: 'none',
                boxShadow: 'none'
              }}
              data-state={activeTab === 'subagents' ? 'active' : 'inactive'}
              title="Subagents: specialist agents PlatformAgent can delegate a task to"
            >
              <Sparkles className="h-3.5 w-3.5" style={{ color: activeTab === 'subagents' ? '#fbe232' : 'rgba(113, 113, 122, 0.8)' }} />
              Subagents
              {subagents.length > 0 && (
                <Badge
                  variant="outline"
                  className="max-w-[4.5rem] truncate border-yellow-200/80 bg-yellow-50 px-1 py-0 text-[8px] font-normal text-gray-700"
                >
                  {subagents.length}
                </Badge>
              )}
              {activeTab === 'subagents' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5" style={{ backgroundColor: '#fbe232' }} />
              )}
            </TabsTrigger>
            <TabsTrigger 
              value="servers" 
              className="text-xs relative flex items-center justify-center gap-1.5 h-full"
              style={{ 
                color: activeTab === 'servers' ? '#fbe232' : 'rgba(113, 113, 122, 0.8)',
                backgroundColor: 'transparent',
                border: 'none',
                boxShadow: 'none'
              }}
              data-state={activeTab === 'servers' ? 'active' : 'inactive'}
            >
              <Server className="h-3.5 w-3.5" style={{ color: activeTab === 'servers' ? '#fbe232' : 'rgba(113, 113, 122, 0.8)' }} />
              Servers
              {activeTab === 'servers' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5" style={{ backgroundColor: '#fbe232' }} />
              )}
            </TabsTrigger>
            <TabsTrigger 
              value="memory" 
              className="text-xs relative flex items-center justify-center gap-1.5 h-full"
              style={{ 
                color: activeTab === 'memory' ? '#fbe232' : 'rgba(113, 113, 122, 0.8)',
                backgroundColor: 'transparent',
                border: 'none',
                boxShadow: 'none'
              }}
              data-state={activeTab === 'memory' ? 'active' : 'inactive'}
            >
              <Brain className="h-3.5 w-3.5" style={{ color: activeTab === 'memory' ? '#fbe232' : 'rgba(113, 113, 122, 0.8)' }} />
              Memory
              {activeTab === 'memory' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5" style={{ backgroundColor: '#fbe232' }} />
              )}
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="mcp" className="mt-0 flex-1 overflow-y-auto p-3 flex flex-col info-panel-content focus-visible:ring-0 focus-visible:ring-offset-0" style={{ backgroundColor: '#fffeff' }}>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-brand mr-2" /> Loading...
            </div>
          ) : (
            <div className="flex flex-col">
              <p className="text-xs mb-2 px-0.5" style={{ color: 'var(--theme-panel-text)', opacity: 0.7 }}>
                Choose which <strong>internal</strong> and <strong>MCP</strong> tools the agent can use on the next message. Use <strong>tool buckets</strong> for presets, or fine-tune with per-tool toggles below.
              </p>

              <div
                className="mb-3 min-h-[8.5rem] rounded-xl border p-3 shadow-sm"
                style={{ backgroundColor: "#f8f8f6", borderColor: "var(--theme-border)" }}
              >
                <div className="mb-1.5 text-xs font-bold" style={{ color: "var(--theme-panel-text)" }}>
                  Tool buckets
                </div>
                <p className="mb-2 text-[10px] leading-snug" style={{ color: "var(--theme-panel-text)", opacity: 0.75 }}>
                  Tap a bucket for the next message. <strong>All tools</strong> is the default (no filter). Custom buckets are stored in this browser.
                </p>
                <div className="grid max-h-[min(40vh,280px)] grid-cols-1 gap-2 overflow-y-auto pr-0.5 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={applyAllToolsBucket}
                    className={cn(
                      "relative rounded-lg border-2 p-2.5 text-left transition-all",
                      activeToolBucketId === TOOL_BUCKET_ALL_ID
                        ? "border-yellow-400 bg-[#fffeff] shadow-sm ring-1 ring-yellow-200/80"
                        : "border-gray-200/90 bg-white hover:border-gray-300"
                    )}
                    title="Use every tool the backend exposes (same as no filter)"
                  >
                    <div className="flex items-start justify-between gap-1">
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-gray-900">All tools</div>
                        <div className="mt-0.5 text-[10px] leading-tight text-gray-600">Default · full catalog</div>
                      </div>
                      <Box className="h-4 w-4 shrink-0 text-yellow-500" />
                    </div>
                  </button>
                  {toolBuckets.map((b) => {
                    const active = activeToolBucketId === b.id;
                    return (
                      <div
                        key={b.id}
                        className={cn(
                          "relative flex rounded-lg border-2 p-0.5 transition-all",
                          active
                            ? "border-yellow-400 bg-[#fffeff] shadow-sm ring-1 ring-yellow-200/80"
                            : "border-gray-200/90 bg-white hover:border-gray-300"
                        )}
                      >
                        <button
                          type="button"
                          onClick={() => applyNamedBucket(b)}
                          className="min-w-0 flex-1 cursor-pointer rounded-md p-2 text-left"
                          title={b.name}
                        >
                          <div className="text-xs font-bold text-gray-900 truncate pr-5">{b.name}</div>
                          <div className="mt-0.5 text-[10px] text-gray-600">{b.toolNames.length} tools</div>
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeToolBucket(b.id);
                          }}
                          className="absolute right-1 top-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-gray-500 hover:bg-red-50 hover:text-red-600"
                          title="Delete bucket"
                          aria-label={`Delete ${b.name}`}
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    );
                  })}
                  <button
                    type="button"
                    onClick={() => {
                      void openCreateToolBucket();
                    }}
                    className="flex min-h-[3.5rem] flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed border-gray-300 bg-white/60 p-2 text-center text-xs font-medium text-gray-700 transition-colors hover:border-yellow-400 hover:bg-yellow-50/50"
                  >
                    <Plus className="h-4 w-4 text-yellow-600" />
                    <span>New bucket</span>
                  </button>
                </div>
              </div>

              <Card className="rounded-xl border shrink-0 mb-2 shadow-sm" style={{ backgroundColor: '#f8f8f6', borderColor: 'var(--theme-border)' }}>
                <CardHeader className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--theme-accent)' }}>
                        <Box className="h-4 w-4" style={{ color: '#ffffff' }} />
                      </div>
                      <CardTitle className="text-sm font-bold" style={{ color: 'var(--theme-panel-text)' }}>Tools</CardTitle>
                    </div>
                    <Button
                      size="sm"
                      className="h-6 px-2 text-xs rounded-md"
                      style={{ backgroundColor: 'var(--theme-accent)', color: '#010101' }}
                      onClick={openToolPicker}
                      title="Open full tool picker"
                    >
                      All
                    </Button>
                  </div>
                  <CardDescription className="text-xs mt-2" style={{ color: 'var(--theme-panel-text)', opacity: 0.6 }}>
                    {enabledTools === undefined
                      ? `All tools enabled (${internalTools.length + mcpTools.length} total)`
                      : `${enabledTools.length} of ${internalTools.length + mcpTools.length} tools enabled`}
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-2 flex-1 flex flex-col min-h-0">
                  <div className="relative mb-1.5 shrink-0">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4" style={{ color: 'var(--theme-panel-text)' }} />
                    <Input
                      value={bucketSearch}
                      onChange={(e) => setBucketSearch(e.target.value)}
                      placeholder="Search tools..."
                      className="pl-9"
                      style={{ backgroundColor: '#fffeff', borderColor: 'var(--theme-border)', color: '#171717' }}
                    />
                  </div>
                  <ScrollArea className="flex-1">
                    <div className="space-y-3 pr-2">
                      {renderToolListSection(
                        "internal",
                        "Internal tools",
                        "Built-in agent capabilities",
                        internalTools,
                        <Package className="h-3 w-3 text-brand shrink-0" />
                      )}
                      {renderToolListSection(
                        "mcp",
                        "MCP tools",
                        mcpTools.length
                          ? "Tools from connected MCP servers"
                          : "Add servers in the Servers tab; tools appear when registered",
                        mcpTools,
                        <Server className="h-3 w-3 text-brand shrink-0" />
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="servers" className="mt-0 flex-1 overflow-y-auto p-2.5 info-panel-content focus-visible:ring-0 focus-visible:ring-offset-0" style={{ backgroundColor: '#fffeff' }}>
          {isLoadingServers ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-brand mr-2" /> Loading...
            </div>
          ) : (
            <ScrollArea className="h-full">
              <div className="space-y-2.5 pb-3 pr-2">
                {/* Add Server */}
                <Card className="max-w-full" style={{ backgroundColor: '#f8f8f6', borderColor: 'var(--theme-border)' }}>
                  <CardHeader className="p-2.5 pb-1.5">
                    <div className="flex items-center justify-between gap-1.5">
                      <div className="flex items-center gap-1.5 flex-1 min-w-0">
                        <Plus className="h-3.5 w-3.5 text-gray-900 shrink-0" />
                        <CardTitle className="text-xs text-gray-900 truncate">Add New Server</CardTitle>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 text-gray-900 hover:text-black hover:bg-brand shrink-0"
                        onClick={() => navigate("/agents/mcp-config")}
                        title="Open MCP Config"
                      >
                        <Settings className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="p-2.5 pt-0">
                    <div className="space-y-1.5">
                      <div className="w-full">
                        <label className="text-[11px] font-medium text-gray-900 mb-1 block">Server Name</label>
                        <Input
                          placeholder="My MCP Server"
                          value={newServer.name}
                          onChange={(e) => setNewServer({ ...newServer, name: e.target.value })}
                          className="h-7 bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500 w-full"
                        />
                      </div>
                      <div className="w-full">
                        <label className="text-[11px] font-medium text-gray-900 mb-1 block">Server URL</label>
                        <Input
                          placeholder="http://localhost:8000/mcp"
                          value={newServer.url}
                          onChange={(e) => setNewServer({ ...newServer, url: e.target.value })}
                          className="h-7 bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500 w-full"
                        />
                      </div>
                      <Button
                        className="w-full transition-all border-0 shadow-xl"
                        style={{ backgroundColor: 'var(--theme-accent)', color: '#171717' }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent-hover)'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent)'}
                        onClick={handleAddServer}
                        disabled={!newServer.name.trim() || !newServer.url.trim()}
                      >
                        <Plus className="h-3 w-3 mr-1" />
                        Add Server
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Connect All Button */}
                {servers.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full transition-all border-0 shadow-xl"
                    style={{ backgroundColor: 'var(--theme-accent)', color: '#171717' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent-hover)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--theme-accent)'}
                    onClick={handleConnectAll}
                    disabled={servers.filter(s => s.enabled && s.is_connected !== true).length === 0}
                  >
                    <Power className="h-3 w-3 mr-1" />
                    Connect All
                  </Button>
                )}

                {/* Server List */}
                <div className="space-y-2">
                  {servers.length === 0 ? (
                    <div className="text-center py-8">
                      <Server className="h-8 w-8 text-brand mx-auto mb-2" />
                      <p className="text-xs text-gray-900">No servers configured</p>
                      <p className="text-[10px] text-gray-900 mt-1">Add a server to get started</p>
                    </div>
                  ) : (
                    servers.map((server) => {
                      const isConnected = server.is_connected === true;
                      const isConnecting = connectingServerId === server.id;
                      const d = serverDetails[server.id];
                      const serverToolsList = d?.tools && d.tools.length > 0 ? d.tools : [] as any[];

                      return (
                        <Card key={server.id} className="transition-colors max-w-full" style={{ backgroundColor: '#f8f8f6', borderColor: 'var(--theme-border)' }}>
                          <CardHeader className="p-2.5 pb-1.5">
                            <div className="flex items-start gap-2">
                              {/* Enable Checkbox */}
                              <div className="pt-0.5 shrink-0">
                                <Checkbox
                                  checked={server.enabled}
                                  onCheckedChange={() => handleToggleServerEnabled(server)}
                                  className="h-5 w-5"
                                />
                              </div>

                              {/* Server Info */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1.5 mb-0.5">
                                  <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${isConnected
                                    ? 'bg-green-500 animate-pulse'
                                    : server.connection_status === 'error'
                                      ? 'bg-red-500'
                                      : 'bg-neutral-600'
                                    }`} />
                                  <span className="text-xs font-medium text-gray-900 truncate">{server.name}</span>
                                </div>
                                 <div className="text-[10px] text-gray-900 truncate font-mono">{server.url || `${server.command} ${(server.args || []).join(' ')}`}</div>
                              </div>

                              {/* Actions */}
                              <div className="flex items-center gap-1 shrink-0">
                                {isConnected ? (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-6 w-6 border-gray-900 text-gray-900 hover:bg-brand hover:border-brand text-[10px]"
                                    onClick={() => handleDisconnectServer(server)}
                                    title="Disconnect"
                                  >
                                    <PowerOff className="h-3 w-3" />
                                  </Button>
                                ) : (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={!server.enabled || isConnecting}
                                    className={`h-6 w-6 border-gray-900 hover:bg-brand hover:border-brand text-[10px] ${!server.enabled
                                      ? 'text-gray-900 cursor-not-allowed'
                                      : 'text-gray-900'
                                      }`}
                                    onClick={() => handleConnectServer(server)}
                                    title={!server.enabled ? "Enable server first" : "Connect"}
                                  >
                                    {isConnecting ? (
                                      <Loader2 className="h-3 w-3 animate-spin" />
                                    ) : (
                                      <Power className="h-3 w-3" />
                                    )}
                                  </Button>
                                )}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 border border-gray-900 text-gray-900 hover:bg-brand hover:border-brand text-[10px]"
                                  onClick={() => navigate(`/agents/mcp-config?view=${server.id}`)}
                                  title="View details"
                                >
                                  <Eye className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                          </CardHeader>


                          {/* Details */}
                          <CardContent className="p-2.5 pt-0">
                            <div className="space-y-1.5 text-[10px]">
                              {/* Tools */}
                              <div>
                                <span className="text-gray-900 font-medium">Tools:</span>
                                <div className="flex flex-wrap gap-1 mt-0.5">
                                  {serverToolsList.length === 0 ? (
                                    <span className="text-red-500">No tools available</span>
                                  ) : (
                                    <>
                                      {serverToolsList.slice(0, 3).map((t: any) => (
                                        <Badge
                                          key={t.name}
                                          className="text-gray-900 text-[9px] px-1.5 py-0"
                                          style={{ backgroundColor: '#f5f5f5', borderColor: 'var(--theme-border)' }}
                                        >
                                          {t.name}
                                        </Badge>
                                      ))}
                                      {serverToolsList.length > 3 && (
                                        <Badge className="text-gray-900 text-[9px] px-1.5 py-0" style={{ backgroundColor: '#f5f5f5', borderColor: 'var(--theme-border)' }}>
                                          +{serverToolsList.length - 3}
                                        </Badge>
                                      )}
                                    </>
                                  )}
                                </div>
                              </div>

                              {/* Server Config */}
                              <div className="flex flex-wrap items-center gap-2 text-gray-900 pt-1 border-t border-neutral-800">
                                <div className="flex items-center gap-1">
                                  <span className="font-medium">Status:</span>
                                  <span className={`font-medium ${isConnected
                                    ? 'text-green-700'
                                    : server.enabled
                                      ? 'text-green-700'
                                      : 'text-red-700'
                                    }`}>
                                    {isConnected ? 'Connected' : server.enabled ? 'Enabled' : 'Disabled'}
                                  </span>
                                </div>
                                <span>•</span>
                                <span>Timeout: {server.timeout}ms</span>
                                <span>•</span>
                                <span>Retries: {server.retry_attempts}×</span>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })
                  )}
                </div>
              </div>
            </ScrollArea>
          )}
        </TabsContent>

        <TabsContent value="memory" className="mt-0 flex-1 overflow-y-auto p-3 info-panel-content focus-visible:ring-0 focus-visible:ring-offset-0" style={{ backgroundColor: '#fffeff' }}>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-brand mr-2" /> Loading...
            </div>
          ) : userMemory && userMemory.length > 0 ? (
            <ScrollArea className="h-full">
              <div className="space-y-2 pb-3">
                {userMemory.map((memory, idx) => {
                  // Get category color
                  const categoryColors: Record<string, string> = {
                    'user_data': 'bg-neutral-900/20 text-neutral-900 border-neutral-900',
                    'user_preferences': 'bg-neutral-900/20 text-neutral-900 border-neutral-900',
                    'knowledge_base': 'bg-green-900/20 text-green-900 border-green-900',
                    'interaction_history': 'bg-yellow-900/20 text-yellow-900 border-yellow-900',
                    'goals_and_intentions': 'bg-neutral-900/20 text-neutral-900 border-neutral-900',
                  };

                  const colorClass = categoryColors[memory.category] || 'bg-brand/20 text-gray-900 border-brand';

                  return (
                    <div key={`${memory.category}-${memory.key}-${idx}`} className="text-gray-900 border rounded-lg p-2 transition-colors" style={{ backgroundColor: '#f8f8f6', borderColor: 'var(--theme-border)' }}>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <span className="font-medium text-xs text-gray-900 wrap-break-word flex-1">{memory.key}</span>
                        <Badge className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${colorClass}`}>
                          {memory.category}
                        </Badge>
                      </div>
                      <div className="text-xs text-gray-900 wrap-break-word font-mono">
                        <MemoryValueRenderer value={memory.value} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          ) : (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <Brain className="h-12 w-12 text-brand mx-auto mb-2" />
                <p className="text-xs text-gray-900">
                  No memories yet
                </p>
                <p className="text-[10px] text-gray-900 mt-1">
                  PlatformAgent will learn about you as you chat
                </p>
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="subagents" className="mt-0 flex-1 overflow-y-auto p-3 info-panel-content focus-visible:ring-0 focus-visible:ring-offset-0" style={{ backgroundColor: '#fffeff' }}>
          {subagentsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-brand mr-2" /> Loading...
            </div>
          ) : subagents.length > 0 ? (
            <div className="flex flex-col">
              <p className="text-xs mb-2 px-0.5" style={{ color: 'var(--theme-panel-text)', opacity: 0.7 }}>
                Specialist agents PlatformAgent can <strong>delegate</strong> to mid-conversation.
              </p>
              <div
                className="mb-3 rounded-xl border p-3 shadow-sm"
                style={{ backgroundColor: "#f8f8f6", borderColor: "var(--theme-border)" }}
              >
                <div className="mb-1.5 text-xs font-bold" style={{ color: "var(--theme-panel-text)" }}>
                  Registered subagents
                </div>
                <p className="text-[10px] leading-snug" style={{ color: "var(--theme-panel-text)", opacity: 0.75 }}>
                  {subagents.length} callable specialist{subagents.length === 1 ? "" : "s"}. The planner picks one when your request matches its scope.
                </p>
              </div>
              <ScrollArea className="h-full">
                <div className="space-y-2.5 pb-3 pr-1">
                  {subagents.map((subagent) => (
                    <SubagentCard key={subagent.name} subagent={subagent} />
                  ))}
                </div>
              </ScrollArea>
            </div>
          ) : (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                 <img src="/brain_icon.svg" alt="PlatformAgent" width={48} height={48} className="h-12 w-12 mx-auto mb-2" />
                <p className="text-xs text-gray-900">
                  No subagents available
                </p>
                <p className="text-[10px] text-gray-900 mt-1">
                  Specialist agents PlatformAgent can delegate a task to will show up here
                </p>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
      {/* Tools Picker Modal */}
      <Dialog open={showToolPicker} onOpenChange={setShowToolPicker}>
        <DialogContent className="max-w-2xl shadow-2xl" style={{ backgroundColor: '#fffeff', borderColor: 'rgba(163, 163, 163, 0.3)' }}>
          <DialogHeader className="pt-5">
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle style={{ color: '#010101' }}>Tools Bucket</DialogTitle>
                <DialogDescription style={{ color: 'rgba(9, 26, 53, 0.7)' }}>
                  {(() => {
                    const allSelectable = groupedTools.flatMap(g => 
                      g.items.filter(item => item.selectable)
                    );
                    return modalSelected.size === allSelectable.length 
                      ? "All tools enabled (internal + external)"
                      : "Currently enabled tools for agent execution";
                  })()}
                </DialogDescription>
              </div>
              <Badge style={{ backgroundColor: '#fbe232', borderColor: '#fbe232', color: '#010101' }}>
                {(() => {
                  const allSelectable = groupedTools.flatMap(g => 
                    g.items.filter(item => item.selectable)
                  );
                  return modalSelected.size === allSelectable.length 
                    ? "All" 
                    : `${modalSelected.size} selected`;
                })()}
              </Badge>
            </div>
          </DialogHeader>
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4" style={{ color: 'rgba(9, 26, 53, 0.5)' }} />
              <Input
                placeholder="Search tools..."
                value={toolPickerSearch}
                onChange={(e) => setToolPickerSearch(e.target.value)}
                className="pl-9"
                style={{ backgroundColor: '#fffeff', borderColor: 'rgba(163, 163, 163, 0.3)', color: '#010101' }}
              />
            </div>
            <div className="max-h-105 overflow-auto">
              {toolPickerLoading ? (
                <div className="flex items-center justify-center py-8" style={{ color: '#fbe232' }}>
                  <Loader2 className="h-6 w-6 animate-spin mr-2" style={{ color: '#fbe232' }} /> Loading...
                </div>
              ) : (
                <div className="space-y-2">
                  {groupedTools.map((group) => {
                    const filtered = group.items.filter(i => i.name.toLowerCase().includes(toolPickerSearch.toLowerCase()));
                    if (filtered.length === 0) return null;
                    
                    const isCollapsed = modalCollapsedGroups.has(group.groupKey);
                    const allSelected = areAllToolsSelectedForModalGroup(filtered);
                    const selectableTools = filtered.filter(item => item.selectable);
                    const isServerGroup = group.serverId !== undefined;

                    return (
                      <div key={group.groupKey} className="space-y-2">
                        {/* Group Header */}
                        <div className="flex items-center justify-between p-1.5 rounded border" style={{ backgroundColor: '#f8f8f6', borderColor: 'rgba(163, 163, 163, 0.3)' }}>
                          <button
                            onClick={() => toggleModalGroupCollapse(group.groupKey)}
                            className="flex items-center gap-1.5 flex-1 text-left transition-colors"
                            style={{ color: '#010101' }}
                          >
                            {isCollapsed ? (
                              <ChevronRight className="h-4 w-4" style={{ color: '#010101' }} />
                            ) : (
                              <ChevronDown className="h-4 w-4" style={{ color: '#010101' }} />
                            )}
                            {isServerGroup ? (
                              <Server className="h-3 w-3" style={{ color: '#fbe232' }} />
                            ) : (
                              <Package className="h-3 w-3" style={{ color: '#010101' }} />
                            )}
                            <span className="text-xs font-semibold" style={{ color: '#010101' }}>{group.title}</span>
                            <Badge className="text-[9px] px-1.5 py-0" style={{ backgroundColor: '#fffeff', borderColor: 'rgba(163, 163, 163, 0.3)', color: '#010101' }}>
                              {filtered.length} {filtered.length === 1 ? 'tool' : 'tools'}
                            </Badge>
                            {isServerGroup && group.connected !== undefined && (
                              <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                                group.connected ? 'bg-green-500' : 'bg-gray-400'
                              }`} />
                            )}
                          </button>
                          {selectableTools.length > 0 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (allSelected) {
                                  deselectAllToolsForModalGroup(filtered);
                                } else {
                                  selectAllToolsForModalGroup(filtered);
                                }
                              }}
                              className="h-5 px-1.5 text-[9px]"
                              style={{ color: '#010101' }}
                              disabled={selectableTools.length === 0}
                            >
                              <CheckSquare className="h-2.5 w-2.5 mr-1" />
                              {allSelected ? 'Deselect All' : 'Select All'}
                            </Button>
                          )}
                        </div>

                        {/* Group Tools List */}
                        {!isCollapsed && (
                          <div className="grid grid-cols-2 gap-2">
                            {filtered.map((item) => {
                              const isSelected = modalSelected.has(item.name);
                              return (
                                <ToolPickerCard
                                  key={`${group.groupKey}-${item.name}`}
                                  tool={resolveToolDetail(item)}
                                  checked={isSelected}
                                  disabled={!item.selectable}
                                  variant="dialog"
                                  onToggle={() => {
                                    if (!item.selectable) return;
                                    setModalSelected((prev) => {
                                      const next = new Set(prev);
                                      if (next.has(item.name)) next.delete(item.name);
                                      else next.add(item.name);
                                      return next;
                                    });
                                  }}
                                />
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {groupedTools.filter(g => {
                    const filtered = g.items.filter(i => i.name.toLowerCase().includes(toolPickerSearch.toLowerCase()));
                    return filtered.length > 0;
                  }).length == 0 && (
                    <div className="text-center py-8">
                      <p className="text-sm" style={{ color: '#dc2626' }}>
                        {toolPickerSearch ? 'No tools match your search' : 'No tools available'}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" className="text-sm shadow-xl" style={{ color: '#010101', borderColor: 'rgba(163, 163, 163, 0.3)', backgroundColor: 'transparent' }} onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f8f8f6'; }} onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }} onClick={() => setShowToolPicker(false)}>Cancel</Button>
              <Button className="shadow-xl" style={{ backgroundColor: '#fbe232', color: '#010101' }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#fbe232'} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#fbe232'} onClick={() => {
                // Get all selectable tools
                const allSelectableTools = groupedTools.flatMap(g => 
                  g.items.filter(item => item.selectable).map(item => item.name)
                );
                
                // If all tools are selected, set to undefined (meaning "use all tools")
                // Otherwise, set to the specific selected tools array
                if (modalSelected.size === allSelectableTools.length && modalSelected.size > 0) {
                  setEnabledTools(undefined);
                  setActiveToolBucketId(TOOL_BUCKET_ALL_ID);
                } else if (modalSelected.size === 0) {
                  setEnabledTools([]);
                  setActiveToolBucketId(TOOL_BUCKET_MIXED_ID);
                } else {
                  const selectedArray = Array.from(modalSelected);
                  setEnabledTools(selectedArray);
                  setActiveToolBucketId(TOOL_BUCKET_MIXED_ID);
                }
                setShowToolPicker(false);
              }}>Apply</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={showCreateToolBucket} onOpenChange={setShowCreateToolBucket}>
        <DialogContent
          className="z-[300] max-h-[90vh] max-w-2xl overflow-y-auto shadow-2xl"
          style={{ backgroundColor: "#fffeff", borderColor: "rgba(163, 163, 163, 0.3)" }}
        >
          <DialogHeader className="pt-2">
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle style={{ color: "#010101" }}>New tool bucket</DialogTitle>
                <DialogDescription style={{ color: "rgba(9, 26, 53, 0.7)" }}>
                  Name the bucket and choose tools (same list as Tools Bucket). Saved in this browser only.
                </DialogDescription>
              </div>
              <Badge style={{ backgroundColor: "#fbe232", borderColor: "#fbe232", color: "#010101" }}>
                {(() => {
                  const allSelectable = createBucketGroupedTools.flatMap((g) => g.items.filter((i) => i.selectable));
                  if (allSelectable.length === 0) return "0 selected";
                  return newBucketPicked.size === allSelectable.length
                    ? "All"
                    : `${newBucketPicked.size} selected`;
                })()}
              </Badge>
            </div>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs font-semibold" style={{ color: "#010101" }}>
                Name
              </label>
              <Input
                value={newBucketName}
                onChange={(e) => setNewBucketName(e.target.value)}
                placeholder="e.g. Research only"
                className="pl-3"
                style={{ backgroundColor: "#fffeff", borderColor: "rgba(163, 163, 163, 0.3)", color: "#010101" }}
              />
            </div>
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform"
                style={{ color: "rgba(9, 26, 53, 0.5)" }}
              />
              <Input
                placeholder="Search tools..."
                value={createBucketFilter}
                onChange={(e) => setCreateBucketFilter(e.target.value)}
                className="pl-9"
                style={{ backgroundColor: "#fffeff", borderColor: "rgba(163, 163, 163, 0.3)", color: "#010101" }}
              />
            </div>
            <div className="max-h-105 overflow-auto">
              {mcpToolsDialogLoading ? (
                <div className="flex items-center justify-center py-8" style={{ color: "#fbe232" }}>
                  <Loader2 className="mr-2 h-6 w-6 animate-spin" style={{ color: "#fbe232" }} /> Loading...
                </div>
              ) : (
                <div className="space-y-2">
                  {createBucketGroupedTools.map((group) => {
                    const filtered = group.items.filter((i) =>
                      i.name.toLowerCase().includes(createBucketFilter.toLowerCase())
                    );
                    if (filtered.length === 0) return null;

                    const isCollapsed = createBucketCollapsedGroups.has(group.groupKey);
                    const allSelected = areAllToolsSelectedForCreateBucketGroup(filtered);
                    const selectableTools = filtered.filter((item) => item.selectable);
                    const isServerGroup = group.serverId !== undefined;

                    return (
                      <div key={group.groupKey} className="space-y-2">
                        <div
                          className="flex items-center justify-between rounded border p-1.5"
                          style={{ backgroundColor: "#f8f8f6", borderColor: "rgba(163, 163, 163, 0.3)" }}
                        >
                          <button
                            type="button"
                            onClick={() => toggleCreateBucketGroupCollapse(group.groupKey)}
                            className="flex flex-1 items-center gap-1.5 text-left transition-colors"
                            style={{ color: "#010101" }}
                          >
                            {isCollapsed ? (
                              <ChevronRight className="h-4 w-4" style={{ color: "#010101" }} />
                            ) : (
                              <ChevronDown className="h-4 w-4" style={{ color: "#010101" }} />
                            )}
                            {isServerGroup ? (
                              <Server className="h-3 w-3" style={{ color: "#fbe232" }} />
                            ) : (
                              <Package className="h-3 w-3" style={{ color: "#010101" }} />
                            )}
                            <span className="text-xs font-semibold" style={{ color: "#010101" }}>
                              {group.title}
                            </span>
                            <Badge
                              className="px-1.5 py-0 text-[9px]"
                              style={{
                                backgroundColor: "#fffeff",
                                borderColor: "rgba(163, 163, 163, 0.3)",
                                color: "#010101",
                              }}
                            >
                              {filtered.length} {filtered.length === 1 ? "tool" : "tools"}
                            </Badge>
                            {isServerGroup && group.connected !== undefined && (
                              <div
                                className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                                  group.connected ? "bg-green-500" : "bg-gray-400"
                                }`}
                              />
                            )}
                          </button>
                          {selectableTools.length > 0 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (allSelected) {
                                  deselectAllToolsForCreateBucketGroup(filtered);
                                } else {
                                  selectAllToolsForCreateBucketGroup(filtered);
                                }
                              }}
                              className="h-5 px-1.5 text-[9px]"
                              style={{ color: "#010101" }}
                              disabled={selectableTools.length === 0}
                            >
                              <CheckSquare className="mr-1 h-2.5 w-2.5" />
                              {allSelected ? "Deselect All" : "Select All"}
                            </Button>
                          )}
                        </div>

                        {!isCollapsed && (
                          <div className="grid grid-cols-2 gap-2">
                            {filtered.map((item) => {
                              const isSelected = newBucketPicked.has(item.name);
                              return (
                                <ToolPickerCard
                                  key={`${group.groupKey}-${item.name}`}
                                  tool={resolveToolDetail(item)}
                                  checked={isSelected}
                                  disabled={!item.selectable}
                                  variant="dialog"
                                  onToggle={() => {
                                    if (!item.selectable) return;
                                    setNewBucketPicked((prev) => {
                                      const next = new Set(prev);
                                      if (next.has(item.name)) next.delete(item.name);
                                      else next.add(item.name);
                                      return next;
                                    });
                                  }}
                                />
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {createBucketGroupedTools.filter((g) => {
                    const filtered = g.items.filter((i) => i.name.toLowerCase().includes(createBucketFilter.toLowerCase()));
                    return filtered.length > 0;
                  }).length === 0 && !mcpToolsDialogLoading && (
                    <div className="py-8 text-center">
                      <p className="text-sm" style={{ color: "#dc2626" }}>
                        {createBucketFilter
                          ? "No tools match your search"
                          : "No tools found. Connect an MCP server in the Servers tab, then open this again."}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                className="text-sm shadow-xl"
                style={{ color: "#010101", borderColor: "rgba(163, 163, 163, 0.3)", backgroundColor: "transparent" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#f8f8f6";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
                onClick={() => setShowCreateToolBucket(false)}
              >
                Cancel
              </Button>
              <Button
                className="shadow-xl"
                style={{ backgroundColor: "#fbe232", color: "#010101" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#fbe232";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "#fbe232";
                }}
                onClick={createToolBucketSubmit}
              >
                Create bucket
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
