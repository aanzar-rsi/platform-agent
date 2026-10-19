import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Brain,
  ChevronDown,
  ChevronRight,
  Plus,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/hooks/use-auth";
import {
  analyticsAPI,
  agentsAPI,
  mcpAPI,
  type AgentPolicyResponse,
  type AnalyticsSummary,
  type CatalogSubagent,
  type MCPServer,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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

export default function ChatRightSidebar({
  agentId,
  activeTab,
  onTabChange,
  onClose,
  onTuneSettingsChange,
}: ChatRightSidebarProps) {
  const { user, isAuthenticated } = useAuth();

  const [armoryTab, setArmoryTab] = useState<ArmoryTab>("policy");
  const [loading, setLoading] = useState(false);
  const [usage, setUsage] = useState<UsageState | null>(null);
  const [analyticsDetail, setAnalyticsDetail] = useState<AnalyticsSummary | null>(null);

  const [policyData, setPolicyData] = useState<AgentPolicyResponse | null>(null);
  const [policySaving, setPolicySaving] = useState(false);

  const [tools, setTools] = useState<Array<{ name: string; description?: string }>>([]);
  const [enabledTools, setEnabledTools] = useState<string[] | undefined>(undefined);
  const [toolSearch, setToolSearch] = useState("");

  const [servers, setServers] = useState<MCPServer[]>([]);
  const [subagents, setSubagents] = useState<CatalogSubagent[]>([]);

  const [memoryEntries, setMemoryEntries] = useState<Array<{ key: string; value: string; category?: string }>>([]);
  const [memoryChunks, setMemoryChunks] = useState<Array<Record<string, unknown>>>([]);
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
    setServers((rawServers || []).map((server) => ({
      ...server,
      id: String(server.id),
      name: String(server.name || ""),
      enabled: server.enabled !== false,
      connected: Boolean(server.connected),
      is_connected: Boolean(server.connected),
    } as MCPServer)));
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

        <TabsContent value="usage" className="mt-0 flex-1 overflow-hidden p-3">
          {loading && !usage ? (
            <div className="text-xs text-gray-600">Loading usage...</div>
          ) : (
            <ScrollArea className="h-full pr-1">
              <div className="space-y-3">
                <div
                  className="rounded-xl border px-3 py-2.5 shadow-md"
                  style={{ borderColor: "#facc15", background: "linear-gradient(135deg, #fffef0 0%, #f5f5f4 100%)" }}
                >
                  <p className="text-[10px] uppercase tracking-wide text-gray-500">scope.type</p>
                  <p className="text-sm font-semibold text-gray-900 capitalize">{analyticsDetail?.scope.type ?? "agent"}</p>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded-md border px-2 py-1.5" style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff" }}>
                      <p className="text-gray-500 text-[10px] uppercase">llm.cost_usd.total</p>
                      <p className="text-gray-900 font-semibold">${(usage?.totalCostUsd ?? 0).toFixed(4)}</p>
                    </div>
                    <div className="rounded-md border px-2 py-1.5" style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff" }}>
                      <p className="text-gray-500 text-[10px] uppercase">agent.runtime.failed_rate</p>
                      <p className="text-gray-900 font-semibold">{errorRate.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: "llm.tokens.total", value: usageTokens.toLocaleString() },
                    { label: "llm.tokens.input", value: (usage?.inputTokens ?? 0).toLocaleString() },
                    { label: "llm.tokens.output", value: (usage?.outputTokens ?? 0).toLocaleString() },
                    { label: "llm.tokens.cached_input", value: (usage?.cachedTokens ?? 0).toLocaleString() },
                    { label: "llm.tokens.reasoning", value: (usage?.reasoningTokens ?? 0).toLocaleString() },
                    { label: "agent.messages.total", value: usageMessages.toLocaleString() },
                    { label: "agent.runtime.runs", value: usageSessions.toLocaleString() },
                    { label: "agent.runtime.failed_runs", value: usageErrors.toLocaleString() },
                    { label: "agent.messages.avg_tokens", value: avgTokensPerMessage.toLocaleString() },
                    { label: "agent.armory.connected_servers", value: activeServers.toLocaleString() },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="rounded-lg border p-2 shadow-sm"
                      style={{ borderColor: "#d4d4d8", backgroundColor: "#fafaf9" }}
                    >
                      <p className="text-[10px] uppercase text-gray-500">{item.label}</p>
                      <p className="text-sm font-semibold text-gray-900">{item.value}</p>
                    </div>
                  ))}
                </div>

                {analyticsDetail && (
                  <>
                    <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f8fafc" }}>
                      <p className="text-xs font-semibold text-gray-900 mb-2">llm</p>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div>llm.calls.total: <span className="font-semibold">{analyticsDetail.llm.calls.total}</span></div>
                        <div>llm.calls.successful: <span className="font-semibold">{analyticsDetail.llm.calls.successful}</span></div>
                        <div>llm.calls.failed: <span className="font-semibold">{analyticsDetail.llm.calls.failed}</span></div>
                        <div>llm.calls.cached: <span className="font-semibold">{analyticsDetail.llm.calls.cached}</span></div>
                        <div>llm.cost_usd.actual: <span className="font-semibold">${analyticsDetail.llm.cost_usd.actual.toFixed(4)}</span></div>
                        <div>llm.cost_usd.estimated: <span className="font-semibold">${analyticsDetail.llm.cost_usd.estimated.toFixed(4)}</span></div>
                      </div>
                      <div className="mt-2 space-y-1">
                        {(analyticsDetail.llm.models || []).slice(0, 3).map((m) => (
                          <div key={m.model} className="flex items-center justify-between rounded border px-2 py-1" style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff" }}>
                            <span className="truncate mr-2 text-[11px]">{m.model}</span>
                            <span className="text-[10px] text-gray-600">llm.models[].tokens.total={m.tokens.total.toLocaleString()} • llm.models[].cost_usd.total=${m.cost_usd.total.toFixed(4)}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f8fafc" }}>
                      <p className="text-xs font-semibold text-gray-900 mb-2">agent.planner and agent.runtime</p>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div>agent.planner.invocations: <span className="font-semibold">{analyticsDetail.agent.planner.invocations}</span></div>
                        <div>agent.planner.plans_created: <span className="font-semibold">{analyticsDetail.agent.planner.plans_created}</span></div>
                        <div>agent.planner.steps_failed: <span className="font-semibold">{analyticsDetail.agent.planner.steps_failed}</span></div>
                        <div>agent.planner.current_plan_overhead.total_tokens: <span className="font-semibold">{analyticsDetail.agent.planner.current_plan_overhead.total_tokens}</span></div>
                        <div>agent.runtime.total_ms: <span className="font-semibold">{analyticsDetail.agent.runtime.total_ms.toLocaleString()}</span></div>
                        <div>agent.runtime.splits.llm_ms: <span className="font-semibold">{analyticsDetail.agent.runtime.splits.llm_ms.toLocaleString()}</span></div>
                      </div>
                    </div>

                    <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f8fafc" }}>
                      <p className="text-xs font-semibold text-gray-900 mb-2">agent.context, agent.armory, agent.memory</p>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div>agent.context.latest.total_tokens: <span className="font-semibold">{analyticsDetail.agent.context.latest.total_tokens.toLocaleString()}</span></div>
                        <div>agent.context.aggregate.average_tokens: <span className="font-semibold">{analyticsDetail.agent.context.aggregate.average_tokens.toLocaleString()}</span></div>
                        <div>agent.armory.configured.tools: <span className="font-semibold">{analyticsDetail.agent.armory.configured.tools}</span></div>
                        <div>agent.armory.configured.mcp_servers: <span className="font-semibold">{analyticsDetail.agent.armory.configured.mcp_servers}</span></div>
                        <div>agent.memory.chunks_extracted: <span className="font-semibold">{analyticsDetail.agent.memory.chunks_extracted}</span></div>
                        <div>agent.memory.extraction_failures: <span className="font-semibold">{analyticsDetail.agent.memory.extraction_failures}</span></div>
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
          <div className="mb-2 grid grid-cols-4 gap-1">
            <Button size="sm" variant={armoryTab === "policy" ? "default" : "outline"} className="text-[10px] px-2 shadow-sm data-[state=active]:bg-yellow-300" onClick={() => setArmoryTab("policy")}>Policy</Button>
            <Button size="sm" variant={armoryTab === "tools" ? "default" : "outline"} className="text-[10px] px-2 shadow-sm data-[state=active]:bg-yellow-300" onClick={() => setArmoryTab("tools")}>Tools</Button>
            <Button size="sm" variant={armoryTab === "subagents" ? "default" : "outline"} className="text-[10px] px-2 shadow-sm data-[state=active]:bg-yellow-300" onClick={() => setArmoryTab("subagents")}>Subagents</Button>
            <Button size="sm" variant={armoryTab === "servers" ? "default" : "outline"} className="text-[10px] px-2 shadow-sm data-[state=active]:bg-yellow-300" onClick={() => setArmoryTab("servers")}>Servers</Button>
          </div>

          <ScrollArea className="h-[calc(100%-2.25rem)] pr-1">
            {armoryTab === "policy" && (
              <div className="space-y-3">
                <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#fefce8" }}>
                  <p className="text-xs font-semibold text-gray-900 mb-2">Policy-configured resource types</p>
                  {!policyData ? (
                    <p className="text-xs text-gray-600">Select a chat session to load policy resources.</p>
                  ) : (
                    Object.keys(policyData.policy.armory.resources || {}).sort().map((group) => (
                      <div
                        key={group}
                        className="mb-2 rounded-lg border p-2 shadow-sm"
                        style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff", boxShadow: "inset 3px 0 0 #facc15" }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
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
                            <p className="text-xs font-semibold text-gray-900 uppercase tracking-wide">{group}</p>
                          </div>
                          <Badge variant="outline" className="text-[10px] border-yellow-300 bg-yellow-50">{policyData.policy.armory.resources[group]?.length || 0}</Badge>
                        </div>
                        <div className="space-y-1.5 pl-6">
                          {(policyData.policy.armory.resources[group] || []).map((resource) => (
                            <label
                              key={`${group}:${resource.name}`}
                              className="flex items-center gap-2 rounded-md border px-2 py-1.5 text-xs text-gray-700"
                              style={{ borderColor: "#e4e4e7", backgroundColor: "#fafafa" }}
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
                              <Badge variant="outline" className="font-mono text-[9px] border-gray-300 bg-white">{resource.type}</Badge>
                              <span className="font-medium">{resource.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>

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
                <Input placeholder="Search tools" value={toolSearch} onChange={(e) => setToolSearch(e.target.value)} />
                <div className="flex items-center justify-between">
                  <p className="text-xs text-gray-600">{filteredTools.length} tools</p>
                  <div className="flex gap-1">
                    <Button size="sm" variant="outline" className="text-[10px] h-7" onClick={() => setEnabledTools(undefined)}>Enable all</Button>
                    <Button size="sm" variant="outline" className="text-[10px] h-7" onClick={() => setEnabledTools([])}>Disable all</Button>
                  </div>
                </div>
                {filteredTools.map((tool) => (
                  <label
                    key={tool.name}
                    className="flex items-center gap-2 rounded-lg border p-2.5 text-xs shadow-sm"
                    style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff", boxShadow: "inset 2px 0 0 #facc15" }}
                  >
                    <Checkbox checked={isToolEnabled(tool.name)} onCheckedChange={() => toggleTool(tool.name)} />
                    <div className="min-w-0">
                      <p className="text-gray-900 font-semibold truncate">{tool.name}</p>
                      {tool.description && <p className="text-gray-600 text-[11px] line-clamp-2">{tool.description}</p>}
                    </div>
                    <Badge variant="outline" className="ml-auto text-[9px] border-gray-300 bg-yellow-50">
                      {isToolEnabled(tool.name) ? "enabled" : "disabled"}
                    </Badge>
                  </label>
                ))}
              </div>
            )}

            {armoryTab === "subagents" && (
              <div className="space-y-2">
                <p className="text-xs text-gray-600">{subagents.length} configured subagents</p>
                {subagents.map((agent) => (
                  <div
                    key={agent.name}
                    className="rounded-lg border p-2.5 shadow-sm"
                    style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff", boxShadow: "inset 2px 0 0 #facc15" }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <p className="text-xs font-semibold text-gray-900">{agent.display_name || agent.name}</p>
                        {agent.description && <p className="text-[11px] text-gray-600 line-clamp-2">{agent.description}</p>}
                        <div className="mt-1 flex items-center gap-1.5">
                          {agent.source && <Badge variant="outline" className="text-[9px] border-gray-300 bg-gray-50">{agent.source}</Badge>}
                          {agent.status && <Badge variant="outline" className="text-[9px] border-gray-300 bg-yellow-50">{agent.status}</Badge>}
                        </div>
                      </div>
                      <Sparkles className="h-3.5 w-3.5 text-gray-500" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {armoryTab === "servers" && (
              <div className="space-y-2">
                <p className="text-xs text-gray-600">{servers.length} configured servers</p>
                {servers.map((server) => (
                  <div
                    key={server.id}
                    className="rounded-lg border p-2.5 shadow-sm"
                    style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff", boxShadow: "inset 2px 0 0 #facc15" }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-gray-900 truncate">{server.name}</p>
                        <p className="text-[11px] text-gray-600 truncate">{server.url || server.command}</p>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between gap-2">
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
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="memory" className="mt-0 flex-1 overflow-hidden p-3">
          <ScrollArea className="h-full pr-1">
            <div className="space-y-3">
              <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#fefce8" }}>
                <div className="flex items-center gap-2 mb-1">
                  <Brain className="h-3.5 w-3.5 text-gray-600" />
                  <p className="text-xs font-semibold text-gray-900">Conversation memory chunks</p>
                </div>
                {!agentId ? (
                  <p className="text-xs text-gray-600">Select a chat to view chunk extraction from this conversation.</p>
                ) : memoryChunks.length === 0 ? (
                  <p className="text-xs text-gray-600">No chunk extraction requests for this conversation yet.</p>
                ) : (
                  <div className="space-y-1.5">
                    {memoryChunks.map((chunk, idx) => (
                      <div
                        key={`chunk-${idx}`}
                        className="rounded-lg border p-2.5 shadow-sm"
                        style={{
                          borderColor: memoryStateTone(String(chunk.state || "pending")).border,
                          backgroundColor: memoryStateTone(String(chunk.state || "pending")).bg,
                        }}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-[11px] text-gray-900 font-medium">{String(chunk.request_id || `chunk-${idx}`)}</p>
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
                        </div>
                        <p className="text-[10px] text-gray-600 mt-1 line-clamp-2">{String(chunk.reason || "No reason provided")}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="rounded-xl border p-2.5 shadow-sm" style={{ borderColor: "#e4e4e7", backgroundColor: "#f4f4f5" }}>
                <div className="flex items-center justify-between gap-2 mb-1">
                  <p className="text-xs font-semibold text-gray-900">Current memory store</p>
                  <Badge variant="outline" className="text-[10px] border-yellow-300 bg-yellow-50">{memoryEntries.length}</Badge>
                </div>
                <div className="space-y-1.5 max-h-40 overflow-auto">
                  {memoryEntries.length === 0 ? (
                    <p className="text-xs text-gray-600">No memory entries yet.</p>
                  ) : (
                    memoryEntries.slice(0, 30).map((entry) => (
                      <div
                        key={`${entry.category || "memory"}:${entry.key}`}
                        className="rounded-lg border p-2 shadow-sm"
                        style={{ borderColor: "#d4d4d8", backgroundColor: "#ffffff", boxShadow: "inset 2px 0 0 #a1a1aa" }}
                      >
                        <div className="flex items-center justify-between gap-2 mb-0.5">
                          <p className="text-[11px] font-semibold text-gray-900 truncate">{entry.key}</p>
                          {entry.category && (
                            <Badge variant="outline" className="text-[9px] border-gray-300 bg-gray-50">
                              {entry.category}
                            </Badge>
                          )}
                        </div>
                        <p className="text-[10px] text-gray-600 line-clamp-2">{entry.value}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

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
    </div>
  );
}
