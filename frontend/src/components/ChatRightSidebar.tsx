import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bot,
  Brain,
  ChevronDown,
  ChevronRight,
  Database,
  Expand,
  Plus,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";

import { useAuth } from "@/hooks/use-auth";
import {
  analyticsAPI,
  agentsAPI,
  mcpAPI,
  type AgentPolicyResponse,
  type AnalyticsSummary,
  type CatalogTool,
  type CatalogSubagent,
  type MCPServer,
  type MCPServerDetails,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import AgentPolicyPanel from "@/components/AgentPolicyPanel";

export type RightSidebarTab = "usage" | "armory" | "memory";
type ArmoryTab = "policy" | "tools" | "subagents" | "servers";
type PolicyChangeMode = "form" | "json";

interface ChatRightSidebarProps {
  agentId: string | null;
  activeTab: RightSidebarTab;
  onTabChange: (tab: RightSidebarTab) => void;
  onClose?: () => void;
  isExecuting?: boolean;
  onTuneSettingsChange?: (settings: {
    maxTokens: string;
    responseFormat: string;
    temperature: string;
    instructions: string;
    enabledTools?: string[];
  }) => void;
}

type UsageState = {
  sessions: number;
  messages: number;
  tokens: number;
  inputTokens: number;
  outputTokens: number;
  cachedTokens: number;
  reasoningTokens: number;
  errors: number;
  estCost: string;
  totalCostUsd: number;
  plan: string;
};

function formatStateLabel(state: string | undefined): string {
  if (!state) return "unknown";
  return state.replace(/_/g, " ");
}

function FormattedText({ children }: { children: string }) {
  return (
    <div className="prose prose-sm max-w-none break-words text-[11px] leading-5 text-gray-700 prose-headings:mb-1 prose-headings:mt-2 prose-headings:text-xs prose-p:my-1 prose-pre:my-2 prose-pre:overflow-x-auto prose-pre:whitespace-pre-wrap prose-pre:rounded-md prose-pre:bg-gray-950 prose-pre:p-2 prose-pre:text-[10px] prose-code:break-all prose-li:my-0">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function analyticsModelLabel(model: string, cost: number) {
  return UUID_PATTERN.test(model) && cost === 0 ? "Cache" : model;
}

type ArmoryDetail =
  | { kind: "tool"; item: CatalogTool }
  | { kind: "subagent"; item: CatalogSubagent }
  | { kind: "server"; item: MCPServer };

export default function ChatRightSidebar({
  agentId,
  activeTab,
  onTabChange,
  onClose,
  isExecuting = false,
  onTuneSettingsChange,
}: ChatRightSidebarProps) {
  const { user, isAuthenticated } = useAuth();

  const [armoryTab, setArmoryTab] = useState<ArmoryTab>("policy");
  const [loading, setLoading] = useState(false);
  const [usage, setUsage] = useState<UsageState | null>(null);
  const [analyticsDetail, setAnalyticsDetail] = useState<AnalyticsSummary | null>(null);

  const [policyData, setPolicyData] = useState<AgentPolicyResponse | null>(null);
  const [policySaving, setPolicySaving] = useState(false);

  const [tools, setTools] = useState<CatalogTool[]>([]);
  const [enabledTools, setEnabledTools] = useState<string[] | undefined>(undefined);
  const [toolSearch, setToolSearch] = useState("");

  const [servers, setServers] = useState<MCPServer[]>([]);
  const [serverDetails, setServerDetails] = useState<Record<string, MCPServerDetails>>({});
  const [subagents, setSubagents] = useState<CatalogSubagent[]>([]);

  const [memoryEntries, setMemoryEntries] = useState<Array<{ key: string; value: string; category?: string }>>([]);
  const [memoryChunks, setMemoryChunks] = useState<Array<Record<string, unknown>>>([]);
  const [memorySearch, setMemorySearch] = useState("");
  const [showMemoryPolicyEditor, setShowMemoryPolicyEditor] = useState(false);
  const [showArmoryPolicyEditor, setShowArmoryPolicyEditor] = useState(false);
  const [policyChangeMode, setPolicyChangeMode] = useState<PolicyChangeMode>("form");

  const [newResourceGroup, setNewResourceGroup] = useState("");
  const [newResourceType, setNewResourceType] = useState("tool");
  const [newResourceName, setNewResourceName] = useState("");
  const [newGroupType, setNewGroupType] = useState("");
  const [policyJsonInput, setPolicyJsonInput] = useState("{\n  \"resources\": {},\n  \"groups\": {}\n}");
  const [policyJsonError, setPolicyJsonError] = useState<string | null>(null);

  const [updatingServerId, setUpdatingServerId] = useState<string | null>(null);
  const [connectingServerId, setConnectingServerId] = useState<string | null>(null);
  const [armoryDetail, setArmoryDetail] = useState<ArmoryDetail | null>(null);

  const canLoad = Boolean(user && isAuthenticated);

  const refreshUsage = useCallback(async () => {
    const analytics = agentId
      ? await agentsAPI.getAnalytics(agentId)
      : await analyticsAPI.getSummary();
    setAnalyticsDetail(analytics);
    const tokens = analytics.llm.tokens.total || 0;
    const totalCost = analytics.llm.cost_usd.total || 0;
    const estimatedCost = `$${totalCost.toFixed(4)}`;

    setUsage({
      sessions: analytics.agent.runtime.runs || 0,
      messages: analytics.agent.messages.total || 0,
      tokens,
      inputTokens: analytics.llm.tokens.input || 0,
      outputTokens: analytics.llm.tokens.output || 0,
      cachedTokens: analytics.llm.tokens.cached_input || 0,
      reasoningTokens: analytics.llm.tokens.reasoning || 0,
      errors: analytics.agent.runtime.failed_runs || 0,
      estCost: estimatedCost,
      totalCostUsd: totalCost,
      plan: (user as { role?: string } | null)?.role || "standard",
    });
  }, [agentId, user]);

  const refreshPolicy = useCallback(async () => {
    if (!agentId) {
      setPolicyData(null);
      return;
    }
    setPolicyData(await agentsAPI.getPolicy(agentId));
  }, [agentId]);

  const refreshArmory = useCallback(async () => {
    if (!agentId) return;
    const [catalog, rawServers, subagentCatalog] = await Promise.all([
      agentsAPI.getArmoryTools(agentId).catch(() => ({ internal: [], mcp: [] })),
      agentsAPI.getArmoryMcp(agentId).catch(() => []),
      agentsAPI.getArmorySubagents(agentId).catch(() => ({ subagents: [] })),
    ]);
    setTools([...(catalog.internal || []), ...(catalog.mcp || [])]);
    const normalizedServers = (rawServers || []).map((server) => ({
      ...server,
      id: String(server.id),
      name: String(server.name || ""),
      enabled: server.enabled !== false,
      connected: Boolean(server.connected),
      is_connected: Boolean(server.connected),
    } as MCPServer));
    setServers(normalizedServers);
    const details = await Promise.all(
      normalizedServers
        .filter((server) => server.is_connected)
        .map(async (server) => {
          try {
            const result = await mcpAPI.getServerDetails(server.id);
            return [server.id, result.details] as const;
          } catch {
            return null;
          }
        })
    );
    setServerDetails(Object.fromEntries(details.filter((detail): detail is readonly [string, MCPServerDetails] => detail !== null)));
    setSubagents(subagentCatalog.subagents || []);
  }, [agentId]);

  const refreshMemory = useCallback(async () => {
    if (!agentId) {
      setMemoryEntries([]);
      setMemoryChunks([]);
      return;
    }
    const memory = await agentsAPI.getMemory(agentId);
    setMemoryEntries(memory.entries || []);
    setMemoryChunks(memory.extraction_requests || []);
  }, [agentId]);

  useEffect(() => {
    if (!canLoad) return;
    setLoading(true);
    Promise.all([refreshUsage(), refreshPolicy(), refreshArmory(), refreshMemory()])
      .finally(() => setLoading(false));
  }, [canLoad, refreshArmory, refreshMemory, refreshPolicy, refreshUsage]);

  useEffect(() => {
    if (!canLoad || !isExecuting) return;
    const update = () => void refreshUsage().catch(() => undefined);
    update();
    const timer = window.setInterval(update, 2000);
    return () => {
      window.clearInterval(timer);
      update();
    };
  }, [canLoad, isExecuting, refreshUsage]);

  useEffect(() => {
    onTuneSettingsChange?.({
      maxTokens: "",
      responseFormat: "text",
      temperature: "",
      instructions: "",
      enabledTools,
    });
  }, [enabledTools, onTuneSettingsChange]);

  const filteredTools = useMemo(
    () => tools.filter((t) => t.name.toLowerCase().includes(toolSearch.toLowerCase())),
    [toolSearch, tools]
  );

  const allToolNames = useMemo(() => tools.map((t) => t.name), [tools]);

  const filteredMemoryEntries = useMemo(() => {
    const query = memorySearch.trim().toLowerCase();
    if (!query) return memoryEntries;
    return memoryEntries.filter((entry) =>
      [entry.key, entry.value, entry.category].some((value) => value?.toLowerCase().includes(query))
    );
  }, [memoryEntries, memorySearch]);

  const toggleTool = (name: string) => {
    setEnabledTools((prev) => {
      if (!prev) {
        return allToolNames.filter((toolName) => toolName !== name);
      }
      return prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name];
    });
  };

  const isToolEnabled = (name: string) => !enabledTools || enabledTools.includes(name);

  const savePolicyChange = async (change: {
    armory?: Partial<AgentPolicyResponse["policy"]["armory"]>;
    memory?: Partial<AgentPolicyResponse["policy"]["memory"]>;
  }) => {
    if (!agentId || !policyData) return;
    setPolicySaving(true);
    try {
      const updated = await agentsAPI.updatePolicy(agentId, policyData.version, change as any);
      setPolicyData(updated);
    } finally {
      setPolicySaving(false);
    }
  };

  const addResource = async () => {
    if (!policyData) return;
    const group = newResourceGroup.trim();
    const type = newResourceType.trim();
    const name = newResourceName.trim();
    if (!group || !type || !name) return;

    const current = policyData.policy.armory.resources[group] || [];
    const exists = current.some((r) => r.name === name);
    if (exists) return;

    await savePolicyChange({
      armory: {
        groups: {
          ...policyData.policy.armory.groups,
          [group]: { enabled: true },
        },
        resources: {
          ...policyData.policy.armory.resources,
          [group]: [...current, { type, name, enabled: true }],
        },
      },
    });

    setNewResourceName("");
  };

  const addResourceType = async () => {
    if (!policyData) return;
    const group = newGroupType.trim();
    if (!group) return;
    await savePolicyChange({
      armory: {
        groups: {
          ...policyData.policy.armory.groups,
          [group]: { enabled: true },
        },
        resources: {
          ...policyData.policy.armory.resources,
          [group]: policyData.policy.armory.resources[group] || [],
        },
      },
    });
    setNewGroupType("");
  };

  const applyPolicyJsonPatch = async () => {
    setPolicyJsonError(null);
    try {
      const parsed = JSON.parse(policyJsonInput);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("JSON must be an object");
      }
      await savePolicyChange({ armory: parsed as Partial<AgentPolicyResponse["policy"]["armory"]> });
      toast.success("Policy patch applied");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Invalid JSON";
      setPolicyJsonError(message);
      toast.error(`Policy patch failed: ${message}`);
    }
  };

  const toggleServerEnabled = async (server: MCPServer) => {
    try {
      setUpdatingServerId(server.id);
      await mcpAPI.updateServer(server.id, { enabled: !server.enabled });
      await refreshArmory();
    } catch {
      toast.error("Failed to update server");
    } finally {
      setUpdatingServerId(null);
    }
  };

  const connectServer = async (server: MCPServer) => {
    try {
      setConnectingServerId(server.id);
      await mcpAPI.connectServer(server.id);
      await refreshArmory();
    } catch {
      toast.error(`Could not connect ${server.name}`);
    } finally {
      setConnectingServerId(null);
    }
  };

  const disconnectServer = async (server: MCPServer) => {
    try {
      setConnectingServerId(server.id);
      await mcpAPI.disconnectServer(server.id);
      await refreshArmory();
    } catch {
      toast.error(`Could not disconnect ${server.name}`);
    } finally {
      setConnectingServerId(null);
    }
  };

  const usageTokens = usage?.tokens ?? 0;
  const usageMessages = usage?.messages ?? 0;
  const usageSessions = usage?.sessions ?? 0;
  const usageErrors = usage?.errors ?? 0;
  const errorRate = usageMessages > 0 ? (usageErrors / usageMessages) * 100 : 0;
  const avgTokensPerMessage = usageMessages > 0 ? Math.round(usageTokens / usageMessages) : 0;
  const activeServers = servers.filter((server) => server.is_connected).length;
  const enabledPolicyResources = Object.values(policyData?.policy.armory.resources || {})
    .flat()
    .filter((resource) => resource.enabled).length;
  const policyResourceGroups = Object.entries(policyData?.policy.armory.resources || {})
    .filter(([, resources]) => resources.length > 0)
    .sort(([left], [right]) => left.localeCompare(right));

  const detailTitle = armoryDetail?.kind === "server"
    ? armoryDetail.item.name
    : armoryDetail?.kind === "subagent"
      ? armoryDetail.item.display_name || armoryDetail.item.name
      : armoryDetail?.item.name;

  const memoryStateTone = (state: string) => {
    const normalized = state.toLowerCase();
    if (normalized.includes("approved") || normalized.includes("done")) {
      return { border: "#86efac", bg: "#f0fdf4", text: "#166534" };
    }
    if (normalized.includes("reject") || normalized.includes("error")) {
      return { border: "#fca5a5", bg: "#fef2f2", text: "#991b1b" };
    }
    return { border: "#facc15", bg: "#fefce8", text: "#854d0e" };
  };

  return (
    <div className="h-full flex flex-col" style={{ background: "linear-gradient(180deg, #fffef8 0%, #f7f7f5 60%, #f3f3f2 100%)" }}>
      <div
        className="border-b p-3 flex items-center justify-between shadow-sm"
        style={{ borderColor: "#facc15", background: "linear-gradient(180deg, #fffde7 0%, #f3f4f6 100%)" }}
      >
        <div>
          <h2 className="text-sm font-semibold text-gray-900">Session Panel</h2>
          <p className="text-xs text-gray-600">Usage, armory, and memory</p>
        </div>
        {onClose && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 hover:bg-yellow-100 text-gray-700"
            onClick={onClose}
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={(v) => onTabChange(v as RightSidebarTab)} className="flex-1 flex flex-col min-h-0">
        <div className="border-b p-2" style={{ borderColor: "#e5e7eb", backgroundColor: "#fefce8" }}>
          <TabsList className="grid w-full grid-cols-3 gap-1 h-9 bg-[#f3f4f6] border border-[#d4d4d8] shadow-sm">
            <TabsTrigger
              value="usage"
              className="text-xs data-[state=active]:bg-[#facc15] data-[state=active]:text-[#111827] data-[state=active]:shadow-sm"
            >
              Usage
            </TabsTrigger>
            <TabsTrigger
              value="armory"
              className="text-xs data-[state=active]:bg-[#facc15] data-[state=active]:text-[#111827] data-[state=active]:shadow-sm"
            >
              Armory
            </TabsTrigger>
            <TabsTrigger
              value="memory"
              className="text-xs data-[state=active]:bg-[#facc15] data-[state=active]:text-[#111827] data-[state=active]:shadow-sm"
            >
              Memory
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="usage" className="mt-0 min-w-0 flex-1 overflow-hidden p-3">
          {loading && !usage ? (
            <div className="text-xs text-gray-600">Loading usage...</div>
          ) : (
            <ScrollArea className="h-full min-w-0">
              <div className="min-w-0 space-y-4 pb-6 pr-3">
                <div
                  className="min-w-0 rounded-xl border p-4 shadow-sm"
                  style={{ borderColor: "#facc15", background: "linear-gradient(135deg, #fffef0 0%, #f5f5f4 100%)" }}
                >
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-500">Usage overview</p>
                  <h3 className="mt-1 text-base font-bold capitalize text-gray-950">
                    {analyticsDetail?.scope.type ?? "agent"} scope
                  </h3>
                  <p className="mt-1 text-xs leading-relaxed text-gray-600">
                    Activity, cost, and reliability for the current analytics window.
                  </p>
                  <div className="mt-3 grid min-w-0 grid-cols-2 gap-2 text-xs">
                    <div className="min-w-0 rounded-lg border p-2.5" style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff" }}>
                      <p className="break-words text-[10px] font-medium text-gray-500">Total LLM cost</p>
                      <p className="mt-0.5 break-words text-base font-bold text-gray-900">${(usage?.totalCostUsd ?? 0).toFixed(4)}</p>
                    </div>
                    <div className="min-w-0 rounded-lg border p-2.5" style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff" }}>
                      <p className="break-words text-[10px] font-medium text-gray-500">Failed run rate</p>
                      <p className="mt-0.5 break-words text-base font-bold text-gray-900">{errorRate.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>

                <div className="min-w-0">
                  <h3 className="text-xs font-bold uppercase tracking-wide text-gray-900">Key metrics</h3>
                  <div className="mt-2 grid min-w-0 grid-cols-2 gap-2">
                    {[
                      { label: "Total tokens", value: usageTokens.toLocaleString() },
                      { label: "Messages", value: usageMessages.toLocaleString() },
                      { label: "Runs", value: usageSessions.toLocaleString() },
                      { label: "Failed runs", value: usageErrors.toLocaleString() },
                      { label: "Avg. tokens / message", value: avgTokensPerMessage.toLocaleString() },
                      { label: "Connected servers", value: activeServers.toLocaleString() },
                    ].map((item) => (
                      <div key={item.label} className="min-w-0 rounded-lg border bg-white p-2.5 shadow-sm" style={{ borderColor: "#d4d4d8" }}>
                        <p className="break-words text-[10px] font-medium leading-snug text-gray-500">{item.label}</p>
                        <p className="mt-1 break-words text-sm font-bold text-gray-900">{item.value}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="min-w-0 rounded-xl border bg-white p-3 shadow-sm" style={{ borderColor: "#e4e4e7" }}>
                  <h3 className="text-xs font-bold text-gray-900">Token breakdown</h3>
                  <div className="mt-2 divide-y divide-gray-100 text-xs">
                    {[
                      ["Input", usage?.inputTokens ?? 0],
                      ["Output", usage?.outputTokens ?? 0],
                      ["Cached input", usage?.cachedTokens ?? 0],
                      ["Reasoning", usage?.reasoningTokens ?? 0],
                    ].map(([label, value]) => (
                      <div key={String(label)} className="flex min-w-0 items-center justify-between gap-3 py-2 first:pt-0 last:pb-0">
                        <span className="min-w-0 break-words text-gray-600">{label}</span>
                        <strong className="shrink-0 text-gray-900">{Number(value).toLocaleString()}</strong>
                      </div>
                    ))}
                  </div>
                </div>

                {analyticsDetail && (
                  <>
                    <div className="min-w-0 rounded-xl border p-3 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f8fafc" }}>
                      <h3 className="mb-2 text-xs font-bold text-gray-900">LLM calls</h3>
                      <div className="grid min-w-0 grid-cols-2 gap-2 text-[11px]">
                        {[
                          ["Total", analyticsDetail.llm.calls.total],
                          ["Successful", analyticsDetail.llm.calls.successful],
                          ["Failed", analyticsDetail.llm.calls.failed],
                          ["Cached", analyticsDetail.llm.calls.cached],
                          ["Actual cost", `$${analyticsDetail.llm.cost_usd.actual.toFixed(4)}`],
                          ["Estimated cost", `$${analyticsDetail.llm.cost_usd.estimated.toFixed(4)}`],
                        ].map(([label, value]) => (
                          <div key={String(label)} className="min-w-0 rounded-md bg-white p-2">
                            <span className="block break-words text-gray-500">{label}</span>
                            <strong className="mt-0.5 block break-words text-gray-900">{value}</strong>
                          </div>
                        ))}
                      </div>
                      <div className="mt-2 space-y-1">
                        {(analyticsDetail.llm.models || []).slice(0, 3).map((m) => {
                          const modelLabel = analyticsModelLabel(m.model, m.cost_usd.total);
                          const isCacheBucket = modelLabel === "Cache";
                          return (
                          <div key={m.model} className="min-w-0 rounded border p-2" style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff" }}>
                            <strong className="block break-all text-[11px] text-gray-900">{modelLabel}</strong>
                            <span className="mt-1 block break-words text-[10px] leading-relaxed text-gray-600">
                              {m.tokens.total.toLocaleString()} tokens · ${m.cost_usd.total.toFixed(4)}
                            </span>
                            {isCacheBucket && <span className="mt-1 block text-[9px] text-gray-400">Cached response activity</span>}
                          </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="min-w-0 rounded-xl border p-3 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f8fafc" }}>
                      <h3 className="mb-2 text-xs font-bold text-gray-900">Planning & runtime</h3>
                      <div className="space-y-2 text-[11px]">
                        {[
                          ["Planner invocations", analyticsDetail.agent.planner.invocations.toLocaleString()],
                          ["Plans created", analyticsDetail.agent.planner.plans_created.toLocaleString()],
                          ["Failed steps", analyticsDetail.agent.planner.steps_failed.toLocaleString()],
                          ["Planning overhead", `${analyticsDetail.agent.planner.current_plan_overhead.total_tokens.toLocaleString()} tokens`],
                          ["Total runtime", `${analyticsDetail.agent.runtime.total_ms.toLocaleString()} ms`],
                          ["LLM runtime", `${analyticsDetail.agent.runtime.splits.llm_ms.toLocaleString()} ms`],
                        ].map(([label, value]) => (
                          <div key={String(label)} className="flex min-w-0 justify-between gap-3">
                            <span className="min-w-0 break-words text-gray-600">{label}</span>
                            <strong className="shrink-0 text-right text-gray-900">{value}</strong>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="min-w-0 rounded-xl border p-3 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f8fafc" }}>
                      <h3 className="mb-2 text-xs font-bold text-gray-900">Context, armory & memory</h3>
                      <div className="space-y-2 text-[11px]">
                        {[
                          ["Latest context", `${analyticsDetail.agent.context.latest.total_tokens.toLocaleString()} tokens`],
                          ["Average context", `${analyticsDetail.agent.context.aggregate.average_tokens.toLocaleString()} tokens`],
                          ["Configured tools", analyticsDetail.agent.armory.configured.tools.toLocaleString()],
                          ["Configured MCP servers", analyticsDetail.agent.armory.configured.mcp_servers.toLocaleString()],
                          ["Memory chunks extracted", analyticsDetail.agent.memory.chunks_extracted.toLocaleString()],
                          ["Memory extraction failures", analyticsDetail.agent.memory.extraction_failures.toLocaleString()],
                        ].map(([label, value]) => (
                          <div key={String(label)} className="flex min-w-0 justify-between gap-3">
                            <span className="min-w-0 break-words text-gray-600">{label}</span>
                            <strong className="shrink-0 text-right text-gray-900">{value}</strong>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#fefce8" }}>
                  <p className="text-xs font-semibold text-gray-900 mb-2">Live footprint</p>
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] text-gray-700">
                      <span>Policy-enabled resources</span>
                      <Badge variant="outline" className="text-[10px] border-yellow-300 bg-white">{enabledPolicyResources}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-gray-700">
                      <span>Tools loaded in armory</span>
                      <Badge variant="outline" className="text-[10px] border-yellow-300 bg-white">{tools.length}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-gray-700">
                      <span>Subagent entries</span>
                      <Badge variant="outline" className="text-[10px] border-yellow-300 bg-white">{subagents.length}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-gray-700">
                      <span>Memory entries</span>
                      <Badge variant="outline" className="text-[10px] border-yellow-300 bg-white">{memoryEntries.length}</Badge>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f4f4f5" }}>
                  <p className="text-xs font-semibold text-gray-900 mb-2">Reliability signal</p>
                  <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.max(5, Math.min(100, 100 - errorRate))}%`,
                        background: "linear-gradient(90deg, #facc15 0%, #a3a3a3 100%)",
                      }}
                    />
                  </div>
                  <p className="mt-1 text-[10px] text-gray-600">
                    Based on run errors vs message/run volume in this analytics window.
                  </p>
                </div>
              </div>
            </ScrollArea>
          )}
        </TabsContent>

        <TabsContent value="armory" className="mt-0 flex-1 overflow-hidden p-3">
          <div className="mb-3 rounded-xl border border-gray-200 bg-white p-1.5 shadow-sm">
            <div className="grid grid-cols-2 gap-1.5">
              {([
                ["policy", "Policy", ShieldCheck],
                ["tools", "Tools", Wrench],
                ["subagents", "Subagents", Bot],
                ["servers", "Servers", Server],
              ] as const).map(([tab, label, Icon]) => (
                <Button
                  key={tab}
                  size="sm"
                  variant="ghost"
                  aria-pressed={armoryTab === tab}
                  className={`h-8 justify-start gap-2 px-2.5 text-[11px] ${armoryTab === tab ? "bg-yellow-300 font-semibold text-gray-950 hover:bg-yellow-300" : "text-gray-600 hover:bg-gray-100"}`}
                  onClick={() => setArmoryTab(tab)}
                >
                  <Icon className="h-3.5 w-3.5" /> {label}
                </Button>
              ))}
            </div>
          </div>

          <ScrollArea className="h-[calc(100%-5rem)] pr-2">
            {armoryTab === "policy" && (
              <div className="space-y-3">
                <div>
                  <h3 className="text-sm font-semibold text-gray-950">Resource policy</h3>
                  <p className="mt-0.5 text-[11px] leading-4 text-gray-500">Control which configured capabilities this agent may use.</p>
                </div>
                {!policyData ? (
                  <p className="rounded-xl border border-dashed border-gray-300 bg-white p-5 text-center text-xs text-gray-600">Select a chat session to load policy resources.</p>
                ) : policyResourceGroups.length > 0 && (
                  <div className="space-y-2">
                    {policyResourceGroups.map(([group, resources]) => (
                      <div
                        key={group}
                        className="min-w-0 rounded-xl border border-gray-200 bg-white p-3 shadow-sm"
                      >
                        <div className="mb-3 flex items-start justify-between gap-2">
                          <div className="flex min-w-0 items-center gap-2">
                            <Checkbox
                              checked={Boolean(policyData.policy.armory.groups[group]?.enabled)}
                              disabled={policySaving}
                              onCheckedChange={(checked) => {
                                void savePolicyChange({
                                  armory: {
                                    groups: {
                                      ...policyData.policy.armory.groups,
                                      [group]: { enabled: !!checked },
                                    },
                                  },
                                });
                              }}
                            />
                            <div className="min-w-0">
                              <p className="break-words text-xs font-bold capitalize text-gray-950">{group.replace(/_/g, " ")}</p>
                              <p className="text-[10px] text-gray-500">{resources.filter((resource) => resource.enabled).length} enabled</p>
                            </div>
                          </div>
                          <Badge variant="outline" className="shrink-0 border-yellow-300 bg-yellow-50 text-[10px]">{resources.length}</Badge>
                        </div>
                        <div className="grid grid-cols-1 gap-1.5 min-[560px]:grid-cols-2">
                          {resources.map((resource) => (
                            <label
                              key={`${group}:${resource.name}`}
                              className="flex min-w-0 items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 p-2 text-xs text-gray-700"
                            >
                              <Checkbox
                                checked={resource.enabled}
                                disabled={policySaving || !policyData.policy.armory.groups[group]?.enabled}
                                onCheckedChange={(checked) => {
                                  const next = (policyData.policy.armory.resources[group] || []).map((item) =>
                                    item.name === resource.name ? { ...item, enabled: !!checked } : item
                                  );
                                  void savePolicyChange({
                                    armory: {
                                      resources: {
                                        ...policyData.policy.armory.resources,
                                        [group]: next,
                                      },
                                    },
                                  });
                                }}
                              />
                              <span className="min-w-0 flex-1 break-all font-medium">{resource.name}</span>
                              <Badge variant="outline" className="shrink-0 border-gray-300 bg-white font-mono text-[9px]">{resource.type}</Badge>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f4f4f5" }}>
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-xs font-semibold text-gray-900">Change policy</p>
                    <div className="grid grid-cols-2 gap-1 rounded-md border p-0.5" style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff" }}>
                      <Button
                        size="sm"
                        variant={policyChangeMode === "form" ? "default" : "ghost"}
                        className="h-6 px-2 text-[10px]"
                        onClick={() => setPolicyChangeMode("form")}
                      >
                        Form
                      </Button>
                      <Button
                        size="sm"
                        variant={policyChangeMode === "json" ? "default" : "ghost"}
                        className="h-6 px-2 text-[10px]"
                        onClick={() => setPolicyChangeMode("json")}
                      >
                        JSON
                      </Button>
                    </div>
                  </div>

                  {policyChangeMode === "form" ? (
                    <div className="grid gap-2">
                      <p className="text-[11px] text-gray-600">Add a single resource or create a new resource type.</p>
                      <Input placeholder="Resource type/group, e.g. tools" value={newResourceGroup} onChange={(e) => setNewResourceGroup(e.target.value)} />
                      <Input placeholder="Resource item type, e.g. tool" value={newResourceType} onChange={(e) => setNewResourceType(e.target.value)} />
                      <Input placeholder="Resource name" value={newResourceName} onChange={(e) => setNewResourceName(e.target.value)} />
                      <Button size="sm" onClick={() => void addResource()} disabled={!agentId || policySaving}>
                        <Plus className="h-3.5 w-3.5 mr-1" /> Add Resource
                      </Button>
                      <div className="flex gap-1.5 pt-1 border-t" style={{ borderColor: "#e5e7eb" }}>
                        <Input placeholder="New resource type/group" value={newGroupType} onChange={(e) => setNewGroupType(e.target.value)} />
                        <Button size="sm" onClick={() => void addResourceType()} disabled={!agentId || policySaving}>Create</Button>
                      </div>
                    </div>
                  ) : (
                    <div className="grid gap-2">
                      <p className="text-[11px] text-gray-600">Paste an armory policy section JSON object and apply it directly.</p>
                      <Textarea
                        value={policyJsonInput}
                        onChange={(e) => setPolicyJsonInput(e.target.value)}
                        className="min-h-[140px] font-mono text-[11px]"
                        placeholder='{"resources":{"tools":[{"type":"tool","name":"x","enabled":true}]}}'
                      />
                      {policyJsonError && <p className="text-[11px] text-red-600">{policyJsonError}</p>}
                      <Button size="sm" onClick={() => void applyPolicyJsonPatch()} disabled={!agentId || policySaving}>
                        Apply JSON Patch
                      </Button>
                    </div>
                  )}
                </div>

                <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f4f4f5" }}>
                  <button
                    type="button"
                    className="w-full flex items-center justify-between"
                    onClick={() => setShowArmoryPolicyEditor((open) => !open)}
                  >
                    <span className="text-xs font-semibold text-gray-900">Policy edit</span>
                    {showArmoryPolicyEditor ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                  </button>
                  {showArmoryPolicyEditor && (
                    <div className="mt-2 rounded border shadow-inner" style={{ borderColor: "#d4d4d8", backgroundColor: "#fffeff" }}>
                      <AgentPolicyPanel agentId={agentId} />
                    </div>
                  )}
                </div>
              </div>
            )}

            {armoryTab === "tools" && (
              <div className="space-y-2">
                <div>
                  <h3 className="text-sm font-semibold text-gray-950">Available tools</h3>
                  <p className="mt-0.5 text-[11px] leading-4 text-gray-500">Choose which capabilities this session can use.</p>
                </div>
                <div className="relative">
                  <Search className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-gray-400" />
                  <Input aria-label="Search tools" className="pl-8" placeholder="Search by tool name…" value={toolSearch} onChange={(e) => setToolSearch(e.target.value)} />
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-gray-600">{filteredTools.length} tools</p>
                  <div className="flex gap-1">
                    <Button size="sm" variant="outline" className="text-[10px] h-7" onClick={() => setEnabledTools(undefined)}>Enable all</Button>
                    <Button size="sm" variant="outline" className="text-[10px] h-7" onClick={() => setEnabledTools([])}>Disable all</Button>
                  </div>
                </div>
                {filteredTools.length === 0 && (
                  <div className="rounded-xl border border-dashed border-gray-300 bg-white p-5 text-center text-xs text-gray-500">
                    {tools.length ? "No tools match your search." : "No tools are available for this agent."}
                  </div>
                )}
                <div className="space-y-2">
                  {filteredTools.map((tool) => (
                    <div key={tool.name} className="flex min-w-0 flex-col rounded-xl border border-gray-200 bg-white p-3 text-xs shadow-sm">
                      <div className="flex items-start gap-2">
                        <Checkbox className="mt-0.5" checked={isToolEnabled(tool.name)} onCheckedChange={() => toggleTool(tool.name)} />
                        <div className="min-w-0 flex-1">
                          <p className="break-all font-bold text-gray-950">{tool.name}</p>
                          {tool.server_name && <Badge variant="outline" className="mt-1 border-blue-200 bg-blue-50 text-[9px] text-blue-700">MCP · {tool.server_name}</Badge>}
                          {tool.description && <p className="mt-1 line-clamp-3 break-words text-[11px] leading-4 text-gray-600">{tool.description}</p>}
                        </div>
                      </div>
                      <div className="mt-auto flex items-center justify-between gap-2 pt-3">
                        <Badge variant="outline" className="border-gray-300 bg-yellow-50 text-[9px]">{isToolEnabled(tool.name) ? "Enabled" : "Disabled"}</Badge>
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-[10px]" onClick={() => setArmoryDetail({ kind: "tool", item: tool })}>
                          <Expand className="mr-1 h-3 w-3" /> Expand
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {armoryTab === "subagents" && (
              <div className="space-y-2">
                <div>
                  <h3 className="text-sm font-semibold text-gray-950">Subagents</h3>
                  <p className="mt-0.5 text-[11px] leading-4 text-gray-500">{subagents.length} specialist {subagents.length === 1 ? "agent" : "agents"} available for delegated work.</p>
                </div>
                {subagents.length === 0 && <div className="rounded-xl border border-dashed border-gray-300 bg-white p-5 text-center text-xs text-gray-500">No subagents are configured.</div>}
                <div className="space-y-2">
                {subagents.map((agent) => (
                  <div
                    key={agent.name}
                    className="flex min-w-0 flex-col rounded-xl border border-gray-200 bg-white p-3 shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="break-words text-xs font-semibold text-gray-900">{agent.display_name || agent.name}</p>
                        {agent.description && <div className="mt-1 whitespace-pre-wrap break-words text-[11px] leading-4 text-gray-600">{agent.description}</div>}
                        <div className="mt-1 flex items-center gap-1.5">
                          {agent.source && <Badge variant="outline" className="text-[9px] border-gray-300 bg-gray-50">{agent.source}</Badge>}
                          {agent.status && <Badge variant="outline" className="text-[9px] border-gray-300 bg-yellow-50">{agent.status}</Badge>}
                        </div>
                      </div>
                      <Sparkles className="h-3.5 w-3.5 shrink-0 text-gray-500" />
                    </div>
                    <Button size="sm" variant="ghost" className="mt-2 h-7 self-end px-2 text-[10px]" onClick={() => setArmoryDetail({ kind: "subagent", item: agent })}>
                      <Expand className="mr-1 h-3 w-3" /> Expand
                    </Button>
                  </div>
                ))}
                </div>
              </div>
            )}

            {armoryTab === "servers" && (
              <div className="space-y-2">
                <div>
                  <h3 className="text-sm font-semibold text-gray-950">MCP servers</h3>
                  <p className="mt-0.5 text-[11px] leading-4 text-gray-500">{activeServers} connected of {servers.length} configured.</p>
                </div>
                {servers.length === 0 && <div className="rounded-xl border border-dashed border-gray-300 bg-white p-5 text-center text-xs text-gray-500">No MCP servers are configured.</div>}
                <div className="space-y-2">
                {servers.map((server) => (
                  <div
                    key={server.id}
                    className="min-w-0 overflow-hidden rounded-xl border border-gray-200 bg-white p-3 shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="break-words text-xs font-semibold text-gray-900">{server.name}</p>
                        <p className="mt-0.5 break-all font-mono text-[10px] leading-4 text-gray-500">{server.url || server.command || "No endpoint provided"}</p>
                      </div>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                      <Badge
                        variant="outline"
                        className="text-[10px]"
                        style={{
                          borderColor: server.is_connected ? "#86efac" : "#d4d4d8",
                          backgroundColor: server.is_connected ? "#f0fdf4" : "#f4f4f5",
                          color: server.is_connected ? "#166534" : "#52525b",
                        }}
                      >
                        {server.is_connected ? "Connected" : "Disconnected"}
                      </Badge>
                      <div className="flex items-center gap-1.5">
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-[10px]" onClick={() => setArmoryDetail({ kind: "server", item: server })}>
                          <Expand className="mr-1 h-3 w-3" /> Expand
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-[10px]"
                          disabled={updatingServerId === server.id}
                          onClick={() => void toggleServerEnabled(server)}
                        >
                          {server.enabled ? "Disable" : "Enable"}
                        </Button>
                        {server.is_connected ? (
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-[10px]"
                            disabled={connectingServerId === server.id}
                            onClick={() => void disconnectServer(server)}
                          >
                            {connectingServerId === server.id ? "..." : "Disconnect"}
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            className="h-7 text-[10px] bg-yellow-300 text-gray-900 hover:bg-yellow-200"
                            disabled={connectingServerId === server.id || !server.enabled}
                            onClick={() => void connectServer(server)}
                          >
                            {connectingServerId === server.id ? "..." : "Connect"}
                          </Button>
                        )}
                      </div>
                    </div>
                    {server.is_connected && (
                      <div className="mt-3 border-t border-gray-100 pt-3">
                        <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">Discovered MCP capabilities</p>
                        {(serverDetails[server.id]?.tools?.length || 0) > 0 ? (
                          <div className="mt-1.5 grid grid-cols-1 gap-1.5 min-[560px]:grid-cols-2">
                            {serverDetails[server.id].tools!.map((tool) => (
                              <div key={tool.name} className="min-w-0 rounded-lg border border-blue-100 bg-blue-50 p-2">
                                <p className="break-all text-[11px] font-semibold text-gray-900">{tool.name}</p>
                                {tool.description && <p className="mt-0.5 break-words text-[10px] leading-4 text-gray-600">{tool.description}</p>}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="mt-1 text-[11px] text-gray-500">No tools discovered.</p>
                        )}
                        {(serverDetails[server.id]?.resources?.length || 0) > 0 && (
                          <div className="mt-2">
                            <p className="text-[10px] font-semibold text-gray-600">Resources</p>
                            <div className="mt-1 grid grid-cols-1 gap-1.5 min-[560px]:grid-cols-2">
                              {serverDetails[server.id].resources!.map((resource) => (
                                <div key={resource.uri} className="min-w-0 rounded-lg border border-gray-200 bg-gray-50 p-2">
                                  <p className="break-words text-[11px] font-medium text-gray-900">{resource.name || resource.uri}</p>
                                  {resource.name && <p className="mt-0.5 break-all font-mono text-[9px] text-gray-500">{resource.uri}</p>}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                </div>
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="memory" className="mt-0 flex-1 overflow-hidden p-3">
          <ScrollArea className="h-full pr-2">
            <div className="space-y-3 pb-5">
              <div className="rounded-xl border border-yellow-300 bg-gradient-to-br from-yellow-50 to-white p-3.5 shadow-sm">
                <div className="flex items-start gap-2.5">
                  <div className="rounded-lg bg-yellow-300 p-2 text-gray-950"><Brain className="h-4 w-4" /></div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-gray-950">Session memory</h3>
                    <p className="mt-0.5 text-[11px] leading-4 text-gray-600">Review what was extracted from this conversation and what the agent currently remembers.</p>
                  </div>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <div className="rounded-lg border border-gray-200 bg-white p-2"><span className="block text-[10px] text-gray-500">Extraction requests</span><strong className="text-sm text-gray-950">{memoryChunks.length}</strong></div>
                  <div className="rounded-lg border border-gray-200 bg-white p-2"><span className="block text-[10px] text-gray-500">Stored entries</span><strong className="text-sm text-gray-950">{memoryEntries.length}</strong></div>
                </div>
              </div>

              <section className="rounded-xl border border-gray-200 bg-white p-3 shadow-sm">
                <div className="mb-2 flex items-center gap-2">
                  <Database className="h-3.5 w-3.5 text-gray-500" />
                  <h3 className="text-xs font-semibold text-gray-900">Extraction activity</h3>
                </div>
                {!agentId ? (
                  <p className="text-xs text-gray-600">Select a chat to view chunk extraction from this conversation.</p>
                ) : memoryChunks.length === 0 ? (
                  <p className="text-xs text-gray-600">No chunk extraction requests for this conversation yet.</p>
                ) : (
                  <div className="space-y-1.5">
                    {memoryChunks.map((chunk, idx) => (
                      <details
                        key={`chunk-${idx}`}
                        className="group rounded-lg border p-2.5 shadow-sm"
                        style={{
                          borderColor: memoryStateTone(String(chunk.state || "pending")).border,
                          backgroundColor: memoryStateTone(String(chunk.state || "pending")).bg,
                        }}
                      >
                        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 [&::-webkit-details-marker]:hidden">
                          <div className="min-w-0">
                            <p className="text-[11px] font-semibold text-gray-900">Extraction {idx + 1}</p>
                            <p className="truncate font-mono text-[9px] text-gray-500">{String(chunk.request_id || `chunk-${idx}`)}</p>
                          </div>
                          <Badge
                            variant="outline"
                            className="text-[10px]"
                            style={{
                              borderColor: memoryStateTone(String(chunk.state || "pending")).border,
                              color: memoryStateTone(String(chunk.state || "pending")).text,
                              backgroundColor: "#ffffff",
                            }}
                          >
                            {formatStateLabel(String(chunk.state || "pending"))}
                          </Badge>
                        </summary>
                        <div className="mt-2 border-t border-black/10 pt-2"><FormattedText>{String(chunk.reason || "No reason provided")}</FormattedText></div>
                      </details>
                    ))}
                  </div>
                )}
              </section>

              <section className="rounded-xl border border-gray-200 bg-white p-3 shadow-sm">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <div>
                    <h3 className="text-xs font-semibold text-gray-900">Current memory store</h3>
                    <p className="mt-0.5 text-[10px] text-gray-500">Select an entry to read its full contents.</p>
                  </div>
                  <Badge variant="outline" className="border-yellow-300 bg-yellow-50 text-[10px]">{filteredMemoryEntries.length}</Badge>
                </div>
                <div className="relative mb-2">
                  <Search className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-gray-400" />
                  <Input aria-label="Search memory" className="pl-8" placeholder="Search keys, content, or categories…" value={memorySearch} onChange={(event) => setMemorySearch(event.target.value)} />
                </div>
                <div className="space-y-1.5">
                  {memoryEntries.length === 0 ? (
                    <p className="text-xs text-gray-600">No memory entries yet.</p>
                  ) : filteredMemoryEntries.length === 0 ? (
                    <p className="rounded-lg border border-dashed border-gray-300 p-4 text-center text-xs text-gray-500">No memories match your search.</p>
                  ) : (
                    filteredMemoryEntries.slice(0, 30).map((entry) => (
                      <details
                        key={`${entry.category || "memory"}:${entry.key}`}
                        className="group rounded-lg border p-2.5 shadow-sm open:border-yellow-300 open:bg-yellow-50/40"
                        style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff", boxShadow: "inset 2px 0 0 #a1a1aa" }}
                      >
                        <summary className="flex cursor-pointer list-none items-center gap-2 [&::-webkit-details-marker]:hidden">
                          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-gray-400 transition-transform group-open:rotate-90" />
                          <p className="min-w-0 flex-1 break-words text-[11px] font-semibold text-gray-900">{entry.key}</p>
                          {entry.category && (
                            <Badge variant="outline" className="shrink-0 border-gray-300 bg-gray-50 text-[9px]">
                              {entry.category}
                            </Badge>
                          )}
                        </summary>
                        <div className="mt-2 border-t border-gray-200 pt-2"><FormattedText>{entry.value}</FormattedText></div>
                      </details>
                    ))
                  )}
                </div>
              </section>

              <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f4f4f5" }}>
                <button
                  type="button"
                  className="w-full flex items-center justify-between"
                  onClick={() => setShowMemoryPolicyEditor((open) => !open)}
                >
                  <span className="text-xs font-semibold text-gray-900">Policy edit</span>
                  {showMemoryPolicyEditor ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                </button>
                {showMemoryPolicyEditor && (
                  <div className="mt-2 rounded border shadow-inner" style={{ borderColor: "#d4d4d8", backgroundColor: "#fffeff" }}>
                    <AgentPolicyPanel agentId={agentId} />
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
      <Dialog open={Boolean(armoryDetail)} onOpenChange={(open) => !open && setArmoryDetail(null)}>
        <DialogContent className="max-h-[80vh] max-w-2xl overflow-hidden bg-white">
          <DialogHeader>
            <DialogTitle className="break-words pr-8">{detailTitle || "Armory details"}</DialogTitle>
            <DialogDescription>
              {armoryDetail?.kind === "server" ? "MCP server configuration and connection information."
                : armoryDetail?.kind === "subagent" ? "Subagent capabilities and availability."
                  : "Tool description, source, and parameters."}
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh] pr-3">
            {armoryDetail && (
              <pre className="whitespace-pre-wrap break-all rounded-xl border border-gray-200 bg-gray-50 p-4 font-mono text-xs leading-5 text-gray-800">
                {JSON.stringify(
                  armoryDetail.kind === "server"
                    ? {
                        ...armoryDetail.item,
                        env: armoryDetail.item.env ? Object.fromEntries(Object.keys(armoryDetail.item.env).map((key) => [key, "[REDACTED]"])) : undefined,
                        auth: armoryDetail.item.auth ? { ...armoryDetail.item.auth, password: undefined } : undefined,
                      }
                    : armoryDetail.item,
                  null,
                  2,
                )}
              </pre>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}
