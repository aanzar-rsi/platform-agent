import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { motion, AnimatePresence } from "framer-motion";
import {
  Loader2,
  Network,
  Brain,
  RefreshCw,
  Search,
  X,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Wrench,
  MessageSquare,
  Sparkles,
  Filter,
  ChevronLeft,
  ChevronRight,
  Save,
  Trash2,
  User,
  Layers,
} from "lucide-react";
import HeaderNavbar from "@/components/HeaderNavbar";
import Breadcrumb from "@/components/Breadcrumb";
import ExperienceGraph from "@/components/ExperienceGraph";
import MemoryGraph from "@/components/MemoryGraph";
import KnowledgeBase from "@/components/KnowledgeBase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/hooks/use-auth";
import {
  experienceAPI,
  memoryAPI,
  type ExperienceChunk,
  type ExperienceResponse,
  type MemoryEntry,
} from "@/lib/api";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const OUTCOMES = ["success", "failure", "unexpected", "unknown"] as const;
const BROWSE_PAGE_SIZE = 6;
const TOOL_PAGE_SIZE = 5;
const MEM_PAGE_SIZE = 6;

const OUTCOME_META: Record<
  string,
  { label: string; color: string; Icon: typeof CheckCircle2 }
> = {
  success: { label: "Success", color: "#3d9b7a", Icon: CheckCircle2 },
  failure: { label: "Failure", color: "#c45c4a", Icon: XCircle },
  unexpected: { label: "Unexpected", color: "#fbe232", Icon: AlertTriangle },
  unknown: { label: "Unknown", color: "#737373", Icon: AlertTriangle },
};

const CATEGORY_META: Record<string, { label: string; color: string }> = {
  user_data: { label: "User data", color: "#e8cc12" },
  user_preferences: { label: "Preferences", color: "#a3a3a3" },
  knowledge_base: { label: "Knowledge", color: "#3d9b7a" },
  interaction_history: { label: "History", color: "#fbe232" },
  goals_and_intentions: { label: "Goals", color: "#756200" },
  system_metadata: { label: "System", color: "#737373" },
  behavioral_patterns: { label: "Behavior", color: "#404040" },
  user_instructions: { label: "Instructions", color: "#9b8200" },
  general: { label: "General", color: "#fbe232" },
};

function formatDate(iso?: string | null) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function prettyCategory(cat: string) {
  return (CATEGORY_META[cat]?.label || cat).replace(/_/g, " ");
}

function formatDisplayValue(raw: string): string {
  if (!raw || raw === "null") return "(empty)";
  try {
    const parsed = JSON.parse(raw);
    return typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
  } catch {
    return raw;
  }
}

function PaginationBar({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
}) {
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between gap-2 pt-2 border-t border-[#171717]/06 mt-auto shrink-0">
      <button
        type="button"
        disabled={page <= 0}
        onClick={() => onChange(page - 1)}
        className="inline-flex items-center gap-1 text-xs text-[#171717]/60 disabled:opacity-30 hover:text-[#171717] px-2 py-1.5 rounded-md hover:bg-[#171717]/05"
      >
        <ChevronLeft className="h-3.5 w-3.5" />
        Prev
      </button>
      <span className="text-[11px] tabular-nums text-[#171717]/45">
        {page + 1} / {totalPages}
      </span>
      <button
        type="button"
        disabled={page >= totalPages - 1}
        onClick={() => onChange(page + 1)}
        className="inline-flex items-center gap-1 text-xs text-[#171717]/60 disabled:opacity-30 hover:text-[#171717] px-2 py-1.5 rounded-md hover:bg-[#171717]/05"
      >
        Next
        <ChevronRight className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

function StatCard({
  label,
  value,
  Icon,
  accent,
}: {
  label: string;
  value: string | number;
  Icon: typeof Sparkles;
  accent: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl bg-white/80 border border-[#171717]/08 px-4 py-3 shadow-sm"
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] uppercase tracking-wider text-[#171717]/45 font-medium">
          {label}
        </span>
        <Icon className="h-3.5 w-3.5" style={{ color: accent }} />
      </div>
      <div className="text-2xl font-bold text-[#171717] tabular-nums">{value}</div>
    </motion.div>
  );
}

/* ─── User Memory Tab ─── */

function UserMemoryTab({ userId }: { userId: string }) {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [browsePage, setBrowsePage] = useState(0);
  const [editValue, setEditValue] = useState("");
  const [editing, setEditing] = useState(false);

  const allCategories = useMemo(() => {
    const s = new Set<string>();
    for (const e of entries) s.add(e.category || "general");
    return Array.from(s).sort();
  }, [entries]);

  const [categoryFilter, setCategoryFilter] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (allCategories.length && categoryFilter.size === 0) {
      setCategoryFilter(new Set(allCategories));
    }
  }, [allCategories, categoryFilter.size]);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await memoryAPI.get({ user_id: userId });
      setEntries(res.entries || []);
    } catch (err: any) {
      toast.error(`Failed to load memory: ${err.message || "unknown"}`);
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setBrowsePage(0);
  }, [search, categoryFilter, entries]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return entries.filter((e) => {
      if (!categoryFilter.has(e.category || "general")) return false;
      if (!q) return true;
      return `${e.key} ${e.value} ${e.category}`.toLowerCase().includes(q);
    });
  }, [entries, search, categoryFilter]);

  const browseTotalPages = Math.max(1, Math.ceil(filtered.length / MEM_PAGE_SIZE));
  const browseSlice = filtered.slice(
    browsePage * MEM_PAGE_SIZE,
    browsePage * MEM_PAGE_SIZE + MEM_PAGE_SIZE,
  );

  const selected = useMemo(() => {
    if (!selectedId) return null;
    if (selectedId.startsWith("cat:")) {
      const cat = selectedId.slice(4);
      return {
        kind: "category" as const,
        category: cat,
        related: entries.filter((e) => (e.category || "general") === cat),
      };
    }
    if (selectedId.startsWith("mem:")) {
      const rest = selectedId.slice(4);
      const idx = rest.indexOf(":");
      if (idx < 0) return null;
      const cat = rest.slice(0, idx);
      const key = rest.slice(idx + 1);
      const entry = entries.find(
        (e) => e.key === key && (e.category || "general") === cat,
      );
      return entry ? { kind: "entry" as const, entry } : null;
    }
    return null;
  }, [selectedId, entries]);

  useEffect(() => {
    if (selected?.kind === "entry") {
      setEditValue(selected.entry.value === "null" ? "" : selected.entry.value);
      setEditing(false);
    }
  }, [selected]);

  const categoryCounts = useMemo(() => {
    const m: Record<string, number> = {};
    for (const e of entries) {
      const c = e.category || "general";
      m[c] = (m[c] || 0) + 1;
    }
    return m;
  }, [entries]);

  const toggleCategory = (c: string) => {
    setCategoryFilter((prev) => {
      const next = new Set(prev);
      if (next.has(c)) {
        if (next.size > 1) next.delete(c);
      } else next.add(c);
      return next;
    });
  };

  const handleSaveEntry = async () => {
    if (selected?.kind !== "entry") return;
    const next = entries.map((e) =>
      e.key === selected.entry.key && e.category === selected.entry.category
        ? {
            ...e,
            value: editValue.trim() === "" ? "null" : editValue,
            updated_at: new Date().toISOString(),
          }
        : e,
    );
    try {
      setSaving(true);
      await memoryAPI.update({ user_id: userId, memory: {}, entries: next });
      setEntries(next);
      setEditing(false);
      toast.success("Memory updated");
    } catch (err: any) {
      toast.error(`Save failed: ${err.message || "unknown"}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteEntry = async () => {
    if (selected?.kind !== "entry") return;
    if (!confirm(`Delete "${selected.entry.key}"?`)) return;
    const next = entries.filter(
      (e) =>
        !(e.key === selected.entry.key && e.category === selected.entry.category),
    );
    try {
      setSaving(true);
      await memoryAPI.update({ user_id: userId, memory: {}, entries: next });
      setEntries(next);
      setSelectedId(null);
      toast.success("Entry deleted");
    } catch (err: any) {
      toast.error(`Delete failed: ${err.message || "unknown"}`);
    } finally {
      setSaving(false);
    }
  };

  const activeFilter =
    categoryFilter.size > 0 ? categoryFilter : new Set(allCategories);

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="Entries" value={entries.length} Icon={Sparkles} accent="#fbe232" />
        <StatCard
          label="Categories"
          value={allCategories.length}
          Icon={Layers}
          accent="#e8cc12"
        />
        <StatCard
          label="Preferences"
          value={categoryCounts.user_preferences || 0}
          Icon={User}
          accent="#a3a3a3"
        />
        <StatCard
          label="User data"
          value={categoryCounts.user_data || 0}
          Icon={Brain}
          accent="#3d9b7a"
        />
      </div>

      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#171717]/35" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search keys, values, categories…"
            className="pl-9 bg-white border-[#171717]/15 focus-visible:ring-[#fbe232]/40"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="h-4 w-4 text-[#171717]/35" />
          {allCategories.map((c) => {
            const meta = CATEGORY_META[c] || CATEGORY_META.general;
            const active = activeFilter.has(c);
            return (
              <button
                key={c}
                type="button"
                onClick={() => toggleCategory(c)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium border transition-all",
                  active ? "bg-white shadow-sm" : "bg-transparent opacity-40",
                )}
                style={{
                  borderColor: active ? meta.color + "55" : "#17171722",
                  color: active ? meta.color : "#17171766",
                }}
              >
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ background: meta.color }}
                />
                {meta.label}
                <span className="opacity-60 tabular-nums">
                  {categoryCounts[c] || 0}
                </span>
              </button>
            );
          })}
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            disabled={loading}
            className="border-[#171717]/20 text-[#171717] ml-auto"
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-4 items-start">
        <div className="h-[min(72vh,720px)]">
          {loading && entries.length === 0 ? (
            <div className="h-full rounded-2xl bg-[#101010] flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-[#fbe232]" />
            </div>
          ) : entries.length === 0 ? (
            <div className="h-full rounded-2xl bg-[#101010] flex flex-col items-center justify-center text-center px-6">
              <Brain className="h-10 w-10 text-[#fbe232]/50 mb-3" />
              <h3 className="text-lg font-semibold text-white mb-1">No memory yet</h3>
              <p className="text-sm text-white/50 max-w-sm">
                Long-term facts about you will appear here as PlatformAgent learns.
              </p>
            </div>
          ) : (
            <MemoryGraph
              entries={entries}
              selectedId={selectedId}
              onSelect={setSelectedId}
              search={search}
              categoryFilter={activeFilter}
            />
          )}
        </div>

        <div className="h-[min(72vh,720px)] rounded-2xl bg-white border border-[#171717]/08 shadow-lg overflow-hidden flex flex-col">
          <div className="shrink-0 px-4 py-3 border-b border-[#171717]/06 bg-[#f8f8f6]/80 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[#171717]">
              {selected ? "Selection" : "Browse"}
            </h2>
            {selectedId && (
              <button
                type="button"
                onClick={() => setSelectedId(null)}
                className="p-1 rounded-md hover:bg-[#171717]/05 text-[#171717]/40"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto p-4 flex flex-col">
            <AnimatePresence mode="wait">
              {!selected ? (
                <motion.div
                  key="browse"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col flex-1 min-h-0"
                >
                  <p className="text-xs text-[#171717]/45 mb-3 shrink-0">
                    Click a hub or entry on the graph, or browse below.
                  </p>
                  <div className="space-y-3 flex-1">
                    {browseSlice.map((e) => {
                      const meta = CATEGORY_META[e.category] || CATEGORY_META.general;
                      return (
                        <button
                          key={`${e.category}-${e.key}`}
                          type="button"
                          onClick={() =>
                            setSelectedId(`mem:${e.category || "general"}:${e.key}`)
                          }
                          className="w-full text-left rounded-xl border border-[#171717]/08 hover:border-[#fbe232]/40 hover:shadow-md bg-[#f8f8f6] px-3 py-2.5 transition-all"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className="text-[10px] font-semibold uppercase tracking-wide"
                              style={{ color: meta.color }}
                            >
                              {prettyCategory(e.category || "general")}
                            </span>
                            <span className="text-[10px] text-[#171717]/35 font-mono truncate">
                              {e.key}
                            </span>
                          </div>
                          <p className="text-xs text-[#171717]/80 line-clamp-2 font-mono">
                            {formatDisplayValue(e.value)}
                          </p>
                        </button>
                      );
                    })}
                    {browseSlice.length === 0 && (
                      <p className="text-xs text-[#171717]/45 text-center py-8">
                        No entries match this filter.
                      </p>
                    )}
                  </div>
                  <PaginationBar
                    page={Math.min(browsePage, browseTotalPages - 1)}
                    totalPages={browseTotalPages}
                    onChange={setBrowsePage}
                  />
                </motion.div>
              ) : selected.kind === "category" ? (
                <motion.div
                  key={`cat-${selected.category}`}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  className="flex flex-col flex-1 min-h-0 space-y-3"
                >
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.18em] text-[#fbe232] mb-1">
                      Category hub
                    </div>
                    <h3 className="text-lg font-bold text-[#171717] capitalize">
                      {prettyCategory(selected.category)}
                    </h3>
                    <p className="text-sm text-[#171717]/55 mt-1">
                      {selected.related.length} entries
                    </p>
                  </div>
                  <div className="space-y-2 flex-1 overflow-y-auto">
                    {selected.related.map((e) => (
                      <button
                        key={e.key}
                        type="button"
                        onClick={() =>
                          setSelectedId(`mem:${e.category || "general"}:${e.key}`)
                        }
                        className="w-full text-left rounded-lg border border-[#171717]/08 px-3 py-2 hover:border-[#fbe232]/35"
                      >
                        <span className="text-[11px] font-mono font-semibold text-[#171717]">
                          {e.key}
                        </span>
                        <p className="text-xs text-[#171717]/65 line-clamp-2 mt-0.5 font-mono">
                          {formatDisplayValue(e.value)}
                        </p>
                      </button>
                    ))}
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key={`${selected.entry.category}-${selected.entry.key}`}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  className="space-y-4"
                >
                  <div>
                    <button
                      type="button"
                      className="text-[10px] uppercase tracking-[0.16em] text-[#fbe232] hover:underline"
                      onClick={() =>
                        setSelectedId(`cat:${selected.entry.category || "general"}`)
                      }
                    >
                      {prettyCategory(selected.entry.category || "general")}
                    </button>
                    <h3 className="text-lg font-bold text-[#171717] font-mono mt-1">
                      {selected.entry.key}
                    </h3>
                  </div>

                  {editing ? (
                    <Textarea
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      rows={8}
                      className="font-mono text-xs bg-[#f8f8f6] border-[#171717]/15"
                    />
                  ) : (
                    <pre className="text-xs text-[#171717]/80 whitespace-pre-wrap break-words bg-[#f8f8f6] rounded-lg px-3 py-2 border border-[#171717]/05 font-mono max-h-64 overflow-y-auto">
                      {formatDisplayValue(selected.entry.value)}
                    </pre>
                  )}

                  <div className="flex flex-wrap gap-2">
                    {editing ? (
                      <>
                        <Button
                          size="sm"
                          onClick={handleSaveEntry}
                          disabled={saving}
                          className="bg-[#fbe232] hover:bg-[#fbe232]/90 text-white"
                        >
                          <Save className="h-3.5 w-3.5 mr-1.5" />
                          Save
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setEditing(false)}
                          className="border-[#171717]/20"
                        >
                          Cancel
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setEditing(true)}
                          className="border-[#171717]/20"
                        >
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleDeleteEntry}
                          className="border-red-200 text-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                          Delete
                        </Button>
                      </>
                    )}
                  </div>

                  <dl className="grid grid-cols-1 gap-2 text-xs pt-2 border-t border-[#171717]/06">
                    <div>
                      <dt className="text-[#171717]/40">Updated</dt>
                      <dd className="text-[#171717]/80 mt-0.5">
                        {formatDate(selected.entry.updated_at)}
                      </dd>
                    </div>
                  </dl>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Experiences Tab ─── */

function ExperiencesTab() {
  const [data, setData] = useState<ExperienceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [browsePage, setBrowsePage] = useState(0);
  const [toolPage, setToolPage] = useState(0);
  const [outcomeFilter, setOutcomeFilter] = useState<Set<string>>(
    () => new Set(OUTCOMES),
  );

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await experienceAPI.list("user");
      setData(res);
    } catch (err: any) {
      toast.error(`Failed to load experiences: ${err.message || "unknown"}`);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setBrowsePage(0);
  }, [search, outcomeFilter, data]);

  useEffect(() => {
    setToolPage(0);
  }, [selectedId]);

  const chunkMap = useMemo(() => {
    const m = new Map<string, ExperienceChunk>();
    for (const c of data?.chunks || []) m.set(c.id, c);
    return m;
  }, [data]);

  const browseChunks = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (data?.chunks || [])
      .slice()
      .reverse()
      .filter((c) => {
        const outcome = c.metadata?.outcome || "unknown";
        if (!outcomeFilter.has(outcome)) return false;
        if (!q) return true;
        const hay = [
          c.advice,
          c.metadata?.observed_tool,
          c.metadata?.user_query,
          c.metadata?.learning,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      });
  }, [data, search, outcomeFilter]);

  const browseTotalPages = Math.max(1, Math.ceil(browseChunks.length / BROWSE_PAGE_SIZE));
  const browseSlice = browseChunks.slice(
    browsePage * BROWSE_PAGE_SIZE,
    browsePage * BROWSE_PAGE_SIZE + BROWSE_PAGE_SIZE,
  );

  const selected = useMemo(() => {
    if (!selectedId || !data) return null;
    if (selectedId.startsWith("tool:")) {
      const tool = selectedId.slice(5);
      return {
        kind: "tool" as const,
        tool,
        related: data.chunks.filter((c) => c.metadata?.observed_tool === tool),
      };
    }
    const chunk = chunkMap.get(selectedId);
    return chunk ? { kind: "experience" as const, chunk } : null;
  }, [selectedId, data, chunkMap]);

  const toolRelatedPages =
    selected?.kind === "tool"
      ? Math.max(1, Math.ceil(selected.related.length / TOOL_PAGE_SIZE))
      : 1;
  const toolRelatedSlice =
    selected?.kind === "tool"
      ? selected.related.slice(
          toolPage * TOOL_PAGE_SIZE,
          toolPage * TOOL_PAGE_SIZE + TOOL_PAGE_SIZE,
        )
      : [];

  const stats = data?.graph.stats;

  const toggleOutcome = (o: string) => {
    setOutcomeFilter((prev) => {
      const next = new Set(prev);
      if (next.has(o)) {
        if (next.size > 1) next.delete(o);
      } else next.add(o);
      return next;
    });
  };

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard
          label="Experiences"
          value={stats?.total ?? "—"}
          Icon={Sparkles}
          accent="#fbe232"
        />
        <StatCard
          label="Tools"
          value={stats?.tools ?? "—"}
          Icon={Wrench}
          accent="#404040"
        />
        <StatCard
          label="Source chats"
          value={stats?.chats ?? "—"}
          Icon={MessageSquare}
          accent="#3d9b7a"
        />
        <StatCard
          label="Success rate"
          value={
            stats
              ? `${Math.round(
                  ((stats.outcomes.success || 0) / Math.max(stats.total, 1)) * 100,
                )}%`
              : "—"
          }
          Icon={CheckCircle2}
          accent="#3d9b7a"
        />
      </div>

      <div className="flex flex-col md:flex-row gap-3 mb-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#171717]/35" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search advice, tools, queries…"
            className="pl-9 bg-white border-[#171717]/15 focus-visible:ring-[#fbe232]/40"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="h-4 w-4 text-[#171717]/35" />
          {OUTCOMES.map((o) => {
            const meta = OUTCOME_META[o];
            const active = outcomeFilter.has(o);
            const count = stats?.outcomes?.[o] || 0;
            return (
              <button
                key={o}
                type="button"
                onClick={() => toggleOutcome(o)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium border transition-all",
                  active ? "bg-white shadow-sm" : "bg-transparent opacity-40",
                )}
                style={{
                  borderColor: active ? meta.color + "55" : "#17171722",
                  color: active ? meta.color : "#17171766",
                }}
              >
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ background: meta.color }}
                />
                {meta.label}
                <span className="opacity-60 tabular-nums">{count}</span>
              </button>
            );
          })}
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            disabled={loading}
            className="border-[#171717]/20 text-[#171717] ml-auto"
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-4 items-start">
        <div className="h-[min(72vh,720px)]">
          {loading && !data ? (
            <div className="h-full rounded-2xl bg-[#101010] flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-[#fbe232]" />
            </div>
          ) : !data || data.chunks.length === 0 ? (
            <div className="h-full rounded-2xl bg-[#101010] flex flex-col items-center justify-center text-center px-6">
              <Network className="h-10 w-10 text-[#fbe232]/50 mb-3" />
              <h3 className="text-lg font-semibold text-white mb-1">
                No experiences yet
              </h3>
              <p className="text-sm text-white/50 max-w-sm">
                PlatformAgent learns tool patterns from idle chats. They will appear here as a
                knowledge graph.
              </p>
            </div>
          ) : (
            <ExperienceGraph
              nodes={data.graph.nodes}
              links={data.graph.links}
              chunks={data.chunks}
              selectedId={selectedId}
              onSelect={setSelectedId}
              outcomeFilter={outcomeFilter}
              search={search}
            />
          )}
        </div>

        <div className="h-[min(72vh,720px)] rounded-2xl bg-white border border-[#171717]/08 shadow-lg overflow-hidden flex flex-col">
          <div className="shrink-0 px-4 py-3 border-b border-[#171717]/06 bg-[#f8f8f6]/80 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[#171717]">
              {selected ? "Selection" : "Browse"}
            </h2>
            {selectedId && (
              <button
                type="button"
                onClick={() => setSelectedId(null)}
                className="p-1 rounded-md hover:bg-[#171717]/05 text-[#171717]/40"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto p-4 flex flex-col">
            <AnimatePresence mode="wait">
              {!selected ? (
                <motion.div
                  key="browse"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col flex-1 min-h-0"
                >
                  <p className="text-xs text-[#171717]/45 mb-3 shrink-0">
                    Click a node on the graph, or pick a recent lesson below.
                  </p>
                  <div className="space-y-3 flex-1">
                    {browseSlice.map((c) => {
                      const outcome = c.metadata?.outcome || "unknown";
                      const meta = OUTCOME_META[outcome] || OUTCOME_META.unknown;
                      return (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => setSelectedId(c.id)}
                          className="w-full text-left rounded-xl border border-[#171717]/08 hover:border-[#fbe232]/40 hover:shadow-md bg-[#f8f8f6] px-3 py-2.5 transition-all"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className="text-[10px] font-semibold uppercase tracking-wide"
                              style={{ color: meta.color }}
                            >
                              {outcome}
                            </span>
                            <span className="text-[10px] text-[#171717]/35 font-mono truncate">
                              {c.metadata?.observed_tool}
                            </span>
                          </div>
                          <p className="text-xs text-[#171717]/80 line-clamp-2">
                            {c.advice}
                          </p>
                        </button>
                      );
                    })}
                    {browseSlice.length === 0 && (
                      <p className="text-xs text-[#171717]/45 text-center py-8">
                        No experiences match this filter.
                      </p>
                    )}
                  </div>
                  <PaginationBar
                    page={Math.min(browsePage, browseTotalPages - 1)}
                    totalPages={browseTotalPages}
                    onChange={setBrowsePage}
                  />
                </motion.div>
              ) : selected.kind === "tool" ? (
                <motion.div
                  key={`tool-${selected.tool}`}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  className="flex flex-col flex-1 min-h-0"
                >
                  <div className="shrink-0 mb-4">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-[#fbe232] mb-1">
                      Tool hub
                    </div>
                    <h3 className="text-lg font-bold text-[#171717] font-mono">
                      {selected.tool}
                    </h3>
                    <p className="text-sm text-[#171717]/55 mt-1">
                      {selected.related.length} linked experiences
                    </p>
                  </div>
                  <div className="space-y-2 flex-1">
                    {toolRelatedSlice.map((c) => {
                      const outcome = c.metadata?.outcome || "unknown";
                      const meta = OUTCOME_META[outcome] || OUTCOME_META.unknown;
                      return (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => setSelectedId(c.id)}
                          className="w-full text-left rounded-lg border border-[#171717]/08 px-3 py-2 hover:border-[#fbe232]/35"
                        >
                          <span
                            className="text-[10px] font-semibold"
                            style={{ color: meta.color }}
                          >
                            {outcome}
                          </span>
                          <p className="text-xs text-[#171717]/75 line-clamp-2 mt-0.5">
                            {c.advice}
                          </p>
                        </button>
                      );
                    })}
                  </div>
                  <PaginationBar
                    page={Math.min(toolPage, toolRelatedPages - 1)}
                    totalPages={toolRelatedPages}
                    onChange={setToolPage}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key={selected.chunk.id}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  className="space-y-4"
                >
                  {(() => {
                    const c = selected.chunk;
                    const outcome = c.metadata?.outcome || "unknown";
                    const meta = OUTCOME_META[outcome] || OUTCOME_META.unknown;
                    const Icon = meta.Icon;
                    return (
                      <>
                        <div className="flex items-start gap-3">
                          <div
                            className="mt-0.5 p-2 rounded-lg"
                            style={{ background: meta.color + "18" }}
                          >
                            <Icon className="h-4 w-4" style={{ color: meta.color }} />
                          </div>
                          <div>
                            <div
                              className="text-[10px] font-semibold uppercase tracking-[0.16em]"
                              style={{ color: meta.color }}
                            >
                              {outcome}
                            </div>
                            <button
                              type="button"
                              className="text-sm font-mono font-semibold text-[#171717] hover:text-[#fbe232]"
                              onClick={() =>
                                setSelectedId(
                                  `tool:${c.metadata?.observed_tool || "unknown"}`,
                                )
                              }
                            >
                              {c.metadata?.observed_tool || "unknown"}
                            </button>
                          </div>
                        </div>
                        <section>
                          <h4 className="text-[10px] uppercase tracking-wider text-[#171717]/40 mb-1.5">
                            Advice
                          </h4>
                          <p className="text-sm text-[#171717] leading-relaxed">
                            {c.advice}
                          </p>
                        </section>
                        {c.metadata?.learning && (
                          <section>
                            <h4 className="text-[10px] uppercase tracking-wider text-[#171717]/40 mb-1.5">
                              Learning
                            </h4>
                            <p className="text-sm text-[#171717]/75 leading-relaxed">
                              {c.metadata.learning}
                            </p>
                          </section>
                        )}
                        {c.metadata?.user_query && (
                          <section>
                            <h4 className="text-[10px] uppercase tracking-wider text-[#171717]/40 mb-1.5">
                              Trigger query
                            </h4>
                            <p className="text-xs text-[#171717]/65 leading-relaxed bg-[#f8f8f6] rounded-lg px-3 py-2 border border-[#171717]/05">
                              {c.metadata.user_query}
                            </p>
                          </section>
                        )}
                        <dl className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-[#171717]/06">
                          <div>
                            <dt className="text-[#171717]/40">Prior tool</dt>
                            <dd className="font-mono text-[#171717]/80 mt-0.5">
                              {c.metadata?.prior_tool || "—"}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-[#171717]/40">Learned</dt>
                            <dd className="text-[#171717]/80 mt-0.5">
                              {formatDate(c.metadata?.created_at)}
                            </dd>
                          </div>
                        </dl>
                      </>
                    );
                  })()}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {stats?.tool_breakdown && stats.tool_breakdown.length > 0 && !selected && (
            <div className="shrink-0 border-t border-[#171717]/06 px-4 py-3 bg-[#f8f8f6]">
              <div className="text-[10px] uppercase tracking-wider text-[#171717]/40 mb-2">
                Top tools
              </div>
              <div className="flex flex-wrap gap-1.5">
                {stats.tool_breakdown.slice(0, 6).map(({ tool, count }) => (
                  <button
                    key={tool}
                    type="button"
                    onClick={() => setSelectedId(`tool:${tool}`)}
                    className="text-[11px] font-mono px-2 py-1 rounded-md bg-white border border-[#171717]/08 hover:border-[#fbe232]/40 text-[#171717]/70"
                  >
                    {tool}
                    <span className="ml-1 text-[#fbe232]">{count}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Page shell ─── */

export default function Memory({ embedded = false }: { embedded?: boolean }) {
  const { isLoading, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") === "experiences" ? "experiences"
    : searchParams.get("tab") === "knowledge" ? "knowledge" : "memory";

  useEffect(() => {
    if (!isLoading && !isAuthenticated) navigate("/login");
  }, [isLoading, isAuthenticated, navigate]);

  // Lock document scroll while mounted — stops scrolling into a stale chat shell under #root
  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const prevHtml = html.style.overflow;
    const prevBody = body.style.overflow;
    html.style.overflow = "hidden";
    body.style.overflow = "hidden";
    window.scrollTo(0, 0);
    return () => {
      html.style.overflow = prevHtml;
      body.style.overflow = prevBody;
    };
  }, []);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [tab]);

  if (isLoading || (!isAuthenticated && !isLoading)) {
    return (
      <div className="h-dvh flex items-center justify-center bg-[#f8f8f6]">
        <Loader2 className="h-8 w-8 animate-spin text-[#171717]" />
      </div>
    );
  }

  return (
    <div className={`${embedded ? "h-full" : "h-dvh"} bg-[#f8f8f6] overflow-hidden flex flex-col`}>
      {!embedded && <HeaderNavbar variant="app" isAuthenticated={isAuthenticated} />}
      {!embedded && <Breadcrumb
        items={[
          { label: "Chat", path: "/" },
          { label: "Memory", path: "/memory" },
        ]}
      />}

      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className={`container max-w-[94%] mx-auto px-6 pb-12 ${embedded ? "pt-8" : "pt-28"}`}>
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 mb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Brain className="h-5 w-5 text-[#756200]" />
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#fbe232]">
                  Cognition store
                </span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-[#171717] tracking-tight">
                Memory
              </h1>
              <p className="mt-2 text-[#171717]/60 max-w-xl text-sm md:text-base">
                What PlatformAgent knows about you, and the tool lessons it has learned —
                explored as knowledge graphs.
              </p>
            </div>
          </div>

          <Tabs
            value={tab}
            onValueChange={(v) => {
              setSearchParams(v === "memory" ? {} : { tab: v });
            }}
            className="w-full"
          >
            <TabsList className="bg-white/80 border border-[#171717]/08 p-1 h-auto mb-6 shadow-sm">
              <TabsTrigger
                value="memory"
                className="gap-2 data-[state=active]:bg-[#171717] data-[state=active]:text-white px-4 py-2"
              >
                <User className="h-4 w-4" />
                User memory
              </TabsTrigger>
              <TabsTrigger
                value="experiences"
                className="gap-2 data-[state=active]:bg-[#171717] data-[state=active]:text-white px-4 py-2"
              >
                <Network className="h-4 w-4" />
                Experiences
              </TabsTrigger>
              <TabsTrigger value="knowledge" className="gap-2 data-[state=active]:bg-[#171717] data-[state=active]:text-white px-4 py-2">
                <Layers className="h-4 w-4" />
                Knowledge base{user?.role === "admin" ? " · admin" : ""}
              </TabsTrigger>
            </TabsList>

            <TabsContent
              value="memory"
              className="mt-0 focus-visible:ring-0 focus-visible:outline-none"
              tabIndex={-1}
            >
              {user?.user_id ? (
                <UserMemoryTab userId={user.user_id} />
              ) : (
                <div className="py-20 text-center text-[#171717]/50">Not authenticated</div>
              )}
            </TabsContent>

            <TabsContent
              value="experiences"
              className="mt-0 focus-visible:ring-0 focus-visible:outline-none"
              tabIndex={-1}
            >
              <ExperiencesTab />
            </TabsContent>
            <TabsContent value="knowledge" className="mt-0 focus-visible:ring-0 focus-visible:outline-none" tabIndex={-1}>
              <KnowledgeBase admin={user?.role === "admin"} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
