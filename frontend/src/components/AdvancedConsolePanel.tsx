import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  ChevronDown,
  Database,
  Eye,
  Layers,
  Loader2,
  Zap,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

// ============================================================================
// TYPES
// ============================================================================

export interface ExecutionMemoryEntry {
  id: string;
  timestamp: number;
  memory_key: string;
  step_id: string;
  status: string;
  output_preview: string;
  output_length: number;
}

export interface ContextMemoryEntry {
  id: string;
  timestamp: number;
  write_mode: "push" | "replace" | "clean";
  key: string | null;
  data_preview: string;
  snapshot_preview: string;
  total_keys: string[];
}

export interface LLMCallEntry {
  id: string;
  timestamp: number;
  label: string | null;
  model: string;
  llm_type: string;
  status: "running" | "completed" | "failed";
  temperature?: number;
  response_format?: string;
  prompt_preview?: string;
  prompt_length?: number;
  system_prompt_preview?: string;
  system_prompt_length?: number;
  has_image?: boolean;
  execution_time?: number;
  success?: boolean;
  error?: string | null;
  response_preview?: string;
  response_length?: number;
}

export interface StepCriticEntry {
  id: string;
  timestamp: number;
  step_id: string;
  step_name: string;
  status: "evaluating" | "success" | "failed";
  execution_success?: boolean;
  evaluation_reason?: string;
  memory_ref?: string | null;
  extracted_memory_keys?: string[];
}

export interface PlanCriticEntry {
  id: string;
  timestamp: number;
  status: "reviewing" | "done";
  steps_count?: number;
  steps?: Array<{ id: string; name: string }>;
  steps_reviewed?: Array<{ id: string; name: string }>;
  feedback_summary?: string;
  has_feedback?: boolean;
}

export interface AdvancedEventData {
  executionMemory: ExecutionMemoryEntry[];
  contextMemory: ContextMemoryEntry[];
  llmCalls: LLMCallEntry[];
  stepCritics: StepCriticEntry[];
  planCritics: PlanCriticEntry[];
}

// ============================================================================
// HELPER: label -> human-readable name
// ============================================================================

const LLM_LABEL_NAMES: Record<string, string> = {
  algorithm_generator: "Algorithm Generator",
  initial_steps_generator: "Steps Generator",
  next_steps_generator: "Next Steps",
  recovery_generator: "Recovery",
  plan_critic: "Plan Critic",
  sequencer: "Sequencer",
  evaluator: "Evaluator",
  summariser: "Summariser",
  context_memory_extractor: "Memory Extractor",
};

function humanLabel(label: string | null): string {
  if (!label) return "LLM Call";
  if (label.startsWith("step_critic_")) return `Step Critic ${label.replace("step_critic_", "")}`;
  return LLM_LABEL_NAMES[label] || label;
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

function EmptyState({ icon: Icon, text }: { icon: React.ElementType; text: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 opacity-40">
      <Icon className="h-6 w-6 mb-1.5" />
      <span className="text-[10px]">{text}</span>
    </div>
  );
}

function TruncatedText({ text, maxLen = 300 }: { text: string; maxLen?: number }) {
  const [expanded, setExpanded] = useState(false);
  if (!text) return null;
  const needsTruncation = text.length > maxLen;
  const displayed = expanded || !needsTruncation ? text : text.slice(0, maxLen) + "…";
  return (
    <div>
      <pre
        className="whitespace-pre-wrap break-words text-[10px] leading-relaxed font-mono"
        style={{ color: "var(--theme-main-text)", opacity: 0.85 }}
      >
        {displayed}
      </pre>
      {needsTruncation && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] mt-1 transition-colors"
          style={{ color: "var(--theme-accent)" }}
        >
          {expanded ? "Show less" : `Show full (${text.length} chars)`}
        </button>
      )}
    </div>
  );
}

// ── Execution Memory Tab ────────────────────────────────────────────────────

function ExecutionMemoryTab({ entries }: { entries: ExecutionMemoryEntry[] }) {
  if (entries.length === 0) return <EmptyState icon={Database} text="No execution memory writes yet" />;

  return (
    <div className="space-y-1.5 p-1.5">
      {entries.map((entry) => (
        <Collapsible key={entry.id}>
          <CollapsibleTrigger asChild>
            <button
              className="group w-full text-left rounded-lg border px-2.5 py-1.5 transition-colors"
              style={{
                backgroundColor: "var(--theme-card-bg)",
                borderColor: entry.status === "success"
                  ? "rgba(34, 197, 94, 0.3)"
                  : "rgba(239, 68, 68, 0.3)",
              }}
            >
              <div className="flex items-center gap-1.5">
                <Database className="h-3 w-3 shrink-0" style={{ color: "var(--theme-accent)" }} />
                <code className="text-[10px] font-mono flex-1 truncate" style={{ color: "var(--theme-main-text)" }}>
                  {entry.memory_key}
                </code>
                <Badge
                  className={`text-[8px] h-3.5 border-0 ${
                    entry.status === "success"
                      ? "bg-green-600/20 text-green-700"
                      : "bg-red-600/20 text-red-700"
                  }`}
                >
                  {entry.status}
                </Badge>
                <span className="text-[8px] opacity-50 tabular-nums">{entry.output_length}c</span>
                <ChevronDown className="h-2.5 w-2.5 shrink-0 opacity-40 transition-transform group-data-[state=open]:rotate-180" />
              </div>
              <div className="text-[9px] opacity-50 mt-0.5">Step: {entry.step_id}</div>
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div
              className="mx-0.5 mt-0.5 rounded-lg p-2 border"
              style={{ backgroundColor: "var(--theme-panel-bg)", borderColor: "var(--theme-border)" }}
            >
              <TruncatedText text={entry.output_preview} maxLen={500} />
            </div>
          </CollapsibleContent>
        </Collapsible>
      ))}
    </div>
  );
}

// ── Context Memory Tab ──────────────────────────────────────────────────────

function ContextMemoryTab({ entries }: { entries: ContextMemoryEntry[] }) {
  if (entries.length === 0) return <EmptyState icon={Layers} text="No context memory updates yet" />;

  const latestSnapshot = entries[entries.length - 1];
  const activeKeys = latestSnapshot?.total_keys || [];

  return (
    <div className="space-y-2 p-1.5">
      {/* Current state summary */}
      <div
        className="rounded-lg border px-2.5 py-2"
        style={{ backgroundColor: "var(--theme-card-bg)", borderColor: "var(--theme-border)" }}
      >
        <div className="flex items-center gap-1.5 mb-1.5">
          <Layers className="h-3 w-3" style={{ color: "var(--theme-accent)" }} />
          <span className="text-[10px] font-semibold" style={{ color: "var(--theme-main-text)" }}>
            Current Context Memory
          </span>
          <Badge
            className="text-[8px] h-3.5 border-0"
            style={{ backgroundColor: "rgba(251, 226, 50, 0.15)", color: "var(--theme-accent)" }}
          >
            {activeKeys.length} key{activeKeys.length !== 1 ? "s" : ""}
          </Badge>
        </div>
        {activeKeys.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-1.5">
            {activeKeys.map((k) => (
              <span
                key={k}
                className="text-[9px] px-1 py-0.5 rounded font-mono border"
                style={{
                  backgroundColor: "var(--theme-panel-bg)",
                  borderColor: "var(--theme-border)",
                  color: "var(--theme-main-text)",
                }}
              >
                {k}
              </span>
            ))}
          </div>
        )}
        {latestSnapshot?.snapshot_preview && (
          <div
            className="rounded p-1.5 border"
            style={{ backgroundColor: "var(--theme-panel-bg)", borderColor: "var(--theme-border)" }}
          >
            <TruncatedText text={latestSnapshot.snapshot_preview} maxLen={2000} />
          </div>
        )}
      </div>

      {/* Event log */}
      <div>
        <div className="text-[9px] font-medium opacity-50 px-1 mb-1" style={{ color: "var(--theme-main-text)" }}>
          Update History
        </div>
        <div className="space-y-1">
          {entries.map((entry) => (
            <Collapsible key={entry.id}>
              <CollapsibleTrigger asChild>
                <button
                  className="group w-full text-left rounded-lg border px-2.5 py-1 transition-colors"
                  style={{ backgroundColor: "var(--theme-card-bg)", borderColor: "var(--theme-border)" }}
                >
                  <div className="flex items-center gap-1.5">
                    <Badge
                      className={`text-[8px] h-3.5 border-0 shrink-0 ${
                        entry.write_mode === "push"
                          ? "bg-green-600/20 text-green-700"
                          : entry.write_mode === "replace"
                          ? "bg-yellow-600/20 text-yellow-700"
                          : "bg-red-600/20 text-red-700"
                      }`}
                    >
                      {entry.write_mode}
                    </Badge>
                    {entry.key && (
                      <code className="text-[9px] font-mono truncate" style={{ color: "var(--theme-main-text)" }}>
                        {entry.key}
                      </code>
                    )}
                    <ChevronDown className="h-2.5 w-2.5 shrink-0 opacity-30 ml-auto transition-transform group-data-[state=open]:rotate-180" />
                  </div>
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div
                  className="mx-0.5 mt-0.5 rounded-lg p-1.5 border"
                  style={{ backgroundColor: "var(--theme-panel-bg)", borderColor: "var(--theme-border)" }}
                >
                  <TruncatedText text={entry.data_preview} maxLen={1000} />
                </div>
              </CollapsibleContent>
            </Collapsible>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── LLM Calls Tab ───────────────────────────────────────────────────────────

function LLMCallsTab({ entries }: { entries: LLMCallEntry[] }) {
  if (entries.length === 0) return <EmptyState icon={Zap} text="No LLM calls yet" />;

  return (
    <div className="space-y-1.5 p-1.5">
      {entries.map((entry) => (
        <Collapsible key={entry.id}>
          <CollapsibleTrigger asChild>
            <button
              className="group w-full text-left rounded-lg border px-2.5 py-1.5 transition-colors"
              style={{
                backgroundColor: "var(--theme-card-bg)",
                borderColor:
                  entry.status === "running"
                    ? "rgba(59, 130, 246, 0.4)"
                    : entry.status === "completed"
                    ? "rgba(34, 197, 94, 0.25)"
                    : "rgba(239, 68, 68, 0.3)",
              }}
            >
              <div className="flex items-center gap-1.5">
                {entry.status === "running" ? (
                  <Loader2 className="h-3 w-3 shrink-0 text-neutral-500 animate-spin" />
                ) : entry.status === "completed" ? (
                  <Zap className="h-3 w-3 shrink-0 text-green-600" />
                ) : (
                  <AlertCircle className="h-3 w-3 shrink-0 text-red-500" />
                )}
                <span className="text-[10px] font-medium flex-1 truncate" style={{ color: "var(--theme-main-text)" }}>
                  {humanLabel(entry.label)}
                </span>
                {entry.execution_time !== undefined && (
                  <span className="text-[9px] tabular-nums opacity-60">{entry.execution_time.toFixed(2)}s</span>
                )}
                <Badge className="text-[8px] h-3.5 border-0 bg-gray-200 text-gray-600 shrink-0">
                  {(entry.model || "").split("/").pop()?.split(":")[0] || entry.model}
                </Badge>
                <ChevronDown className="h-2.5 w-2.5 shrink-0 opacity-40 transition-transform group-data-[state=open]:rotate-180" />
              </div>
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div
              className="mx-0.5 mt-0.5 rounded-lg p-2 space-y-2 border"
              style={{ backgroundColor: "var(--theme-panel-bg)", borderColor: "var(--theme-border)" }}
            >
              {/* Metadata row */}
              <div className="flex flex-wrap gap-1.5 text-[9px]">
                {entry.temperature !== undefined && (
                  <span className="px-1 py-0.5 rounded border" style={{ borderColor: "var(--theme-border)", color: "var(--theme-main-text)" }}>
                    temp: {entry.temperature}
                  </span>
                )}
                {entry.prompt_length !== undefined && (
                  <span className="px-1 py-0.5 rounded border" style={{ borderColor: "var(--theme-border)", color: "var(--theme-main-text)" }}>
                    prompt: {entry.prompt_length}c
                  </span>
                )}
                {entry.response_length !== undefined && (
                  <span className="px-1 py-0.5 rounded border" style={{ borderColor: "var(--theme-border)", color: "var(--theme-main-text)" }}>
                    response: {entry.response_length}c
                  </span>
                )}
                {entry.has_image && (
                  <span className="px-1 py-0.5 rounded bg-neutral-100 text-neutral-700">has image</span>
                )}
              </div>

              {entry.system_prompt_preview && (
                <div>
                  <div className="text-[9px] font-medium mb-0.5" style={{ color: "var(--theme-accent)" }}>System Prompt</div>
                  <div className="rounded p-1.5 border" style={{ backgroundColor: "var(--theme-card-bg)", borderColor: "var(--theme-border)" }}>
                    <TruncatedText text={entry.system_prompt_preview} maxLen={400} />
                  </div>
                </div>
              )}

              {entry.prompt_preview && (
                <div>
                  <div className="text-[9px] font-medium text-neutral-600 mb-0.5">Prompt</div>
                  <div className="rounded p-1.5 border" style={{ backgroundColor: "var(--theme-card-bg)", borderColor: "var(--theme-border)" }}>
                    <TruncatedText text={entry.prompt_preview} maxLen={400} />
                  </div>
                </div>
              )}

              {entry.response_preview && (
                <div>
                  <div className="text-[9px] font-medium text-green-600 mb-0.5">Response</div>
                  <div className="rounded p-1.5 border" style={{ backgroundColor: "var(--theme-card-bg)", borderColor: "var(--theme-border)" }}>
                    <TruncatedText text={entry.response_preview} maxLen={400} />
                  </div>
                </div>
              )}

              {entry.error && (
                <div>
                  <div className="text-[9px] font-medium text-red-500 mb-0.5">Error</div>
                  <pre className="text-[9px] text-red-600 whitespace-pre-wrap break-words">{entry.error}</pre>
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ))}
    </div>
  );
}

// ── Plan Critics Section ────────────────────────────────────────────────────

function PlanCriticCard({ entry }: { entry: PlanCriticEntry }) {
  const isDone = entry.status === "done";
  const stepsLabel = entry.steps_reviewed ?? entry.steps;
  return (
    <Collapsible>
      <CollapsibleTrigger asChild>
        <button
          className="group w-full text-left rounded-lg border px-2.5 py-1.5 transition-colors"
          style={{
            backgroundColor: "var(--theme-card-bg)",
            borderColor: isDone
              ? entry.has_feedback ? "rgba(217, 119, 6, 0.35)" : "rgba(34, 197, 94, 0.3)"
              : "rgba(168, 85, 247, 0.3)",
          }}
        >
          <div className="flex items-center gap-1.5">
            {!isDone ? (
              <Loader2 className="h-3 w-3 shrink-0 text-neutral-500 animate-spin" />
            ) : entry.has_feedback ? (
              <AlertCircle className="h-3 w-3 shrink-0 text-yellow-500" />
            ) : (
              <CheckCircle className="h-3 w-3 shrink-0 text-green-600" />
            )}
            <span className="text-[10px] font-semibold flex-1" style={{ color: "var(--theme-main-text)" }}>
              Plan Critic
            </span>
            {entry.steps_count !== undefined && (
              <span className="text-[8px] opacity-50">{entry.steps_count} steps</span>
            )}
            <Badge
              className={`text-[8px] h-3.5 border-0 ${
                !isDone
                  ? "bg-neutral-100 text-neutral-700"
                  : entry.has_feedback
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-green-100 text-green-700"
              }`}
            >
              {isDone ? (entry.has_feedback ? "has feedback" : "passed") : "reviewing"}
            </Badge>
            <ChevronDown className="h-2.5 w-2.5 shrink-0 opacity-40 transition-transform group-data-[state=open]:rotate-180" />
          </div>
          {stepsLabel && stepsLabel.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {stepsLabel.map((s) => (
                <span
                  key={s.id}
                  className="text-[8px] px-1 py-0.5 rounded font-mono border"
                  style={{ backgroundColor: "var(--theme-panel-bg)", borderColor: "var(--theme-border)", color: "var(--theme-main-text)" }}
                >
                  {s.id}: {s.name}
                </span>
              ))}
            </div>
          )}
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        {entry.feedback_summary && (
          <div
            className="mx-0.5 mt-0.5 rounded-lg p-1.5 border"
            style={{ backgroundColor: "var(--theme-panel-bg)", borderColor: "var(--theme-border)" }}
          >
            <div className="text-[9px] font-medium text-yellow-600 mb-0.5">Feedback</div>
            <TruncatedText text={entry.feedback_summary} maxLen={600} />
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}

// ── Step Critics Section ────────────────────────────────────────────────────

function StepCriticCard({ entry }: { entry: StepCriticEntry }) {
  return (
    <div
      className="rounded-lg border px-2.5 py-1.5"
      style={{
        backgroundColor: "var(--theme-card-bg)",
        borderColor:
          entry.status === "evaluating"
            ? "rgba(168, 85, 247, 0.3)"
            : entry.status === "success"
            ? "rgba(34, 197, 94, 0.3)"
            : "rgba(239, 68, 68, 0.3)",
      }}
    >
      <div className="flex items-center gap-1.5">
        {entry.status === "evaluating" ? (
          <Loader2 className="h-3 w-3 shrink-0 text-neutral-500 animate-spin" />
        ) : entry.status === "success" ? (
          <CheckCircle className="h-3 w-3 shrink-0 text-green-600" />
        ) : (
          <AlertCircle className="h-3 w-3 shrink-0 text-red-500" />
        )}
        <span className="text-[10px] font-medium flex-1 truncate" style={{ color: "var(--theme-main-text)" }}>
          {entry.step_name}
        </span>
        <code className="text-[8px] font-mono opacity-50">{entry.step_id}</code>
        <Badge
          className={`text-[8px] h-3.5 border-0 ${
            entry.status === "evaluating"
              ? "bg-neutral-100 text-neutral-700"
              : entry.status === "success"
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {entry.status}
        </Badge>
      </div>
      {entry.evaluation_reason && (
        <div className="text-[9px] mt-1 opacity-75 break-words leading-relaxed" style={{ color: "var(--theme-main-text)" }}>
          {entry.evaluation_reason}
        </div>
      )}
      {entry.extracted_memory_keys && entry.extracted_memory_keys.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {entry.extracted_memory_keys.map((k) => (
            <span
              key={k}
              className="text-[8px] px-1 py-0.5 rounded font-mono border"
              style={{ backgroundColor: "var(--theme-panel-bg)", borderColor: "var(--theme-border)", color: "var(--theme-accent)" }}
            >
              {k}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Combined Critics Tab ────────────────────────────────────────────────────

function CriticsTab({ stepCritics, planCritics }: { stepCritics: StepCriticEntry[]; planCritics: PlanCriticEntry[] }) {
  if (stepCritics.length === 0 && planCritics.length === 0) {
    return <EmptyState icon={Eye} text="No evaluations yet" />;
  }

  return (
    <div className="space-y-2 p-1.5">
      {planCritics.length > 0 && (
        <div>
          <div className="text-[9px] font-semibold tracking-wider uppercase mb-1 px-0.5" style={{ color: "var(--theme-accent)", opacity: 0.7 }}>
            Plan Critics
          </div>
          <div className="space-y-1.5">
            {planCritics.map((entry) => (
              <PlanCriticCard key={entry.id} entry={entry} />
            ))}
          </div>
        </div>
      )}

      {stepCritics.length > 0 && (
        <div>
          <div className="text-[9px] font-semibold tracking-wider uppercase mb-1 px-0.5" style={{ color: "var(--theme-main-text)", opacity: 0.5 }}>
            Step Critics
          </div>
          <div className="space-y-1.5">
            {stepCritics.map((entry) => (
              <StepCriticCard key={entry.id} entry={entry} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT — inline console for embedding in message area
// ============================================================================

type TabId = "memory" | "llm" | "critics";

interface AdvancedConsolePanelProps {
  data: AdvancedEventData;
  isLive?: boolean;
  /**
   * When true (default), stretch to the parent flex column (`h-full`). Parent should be
   * `self-stretch min-h-0` beside a taller content column — not `100dvh`.
   * When false, use fixed max heights for a compact panel.
   */
  fillColumn?: boolean;
}

export default function AdvancedConsolePanel({
  data,
  isLive,
  fillColumn = true,
}: AdvancedConsolePanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("memory");

  const tabs: { id: TabId; label: string; icon: React.ElementType; count: number }[] = useMemo(
    () => [
      { id: "memory", label: "Memory", icon: Database, count: data.executionMemory.length + data.contextMemory.length },
      { id: "llm", label: "LLM Calls", icon: Zap, count: data.llmCalls.length },
      { id: "critics", label: "Critics", icon: Eye, count: data.stepCritics.length + (data.planCritics?.length || 0) },
    ],
    [data]
  );

  const hasData = data.executionMemory.length > 0 || data.contextMemory.length > 0 ||
    data.llmCalls.length > 0 || data.stepCritics.length > 0 || (data.planCritics?.length || 0) > 0;

  if (!hasData && !isLive) return null;

  return (
    <div
      className={cn(
        "flex min-h-0 flex-col overflow-hidden rounded-xl border",
        fillColumn ? "h-full min-h-0 w-full" : "max-h-[500px]"
      )}
      style={{
        backgroundColor: "var(--theme-ai-bubble-bg)",
        borderColor: "var(--theme-border)",
      }}
    >
      {/* Tab bar */}
      <div
        className="shrink-0 flex border-b"
        style={{ borderColor: "var(--theme-border)", backgroundColor: "var(--theme-panel-bg)" }}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex-1 flex items-center justify-center gap-1 py-1.5 text-[10px] font-medium transition-all relative"
              style={{
                color: isActive ? "var(--theme-accent)" : "var(--theme-main-text)",
                opacity: isActive ? 1 : 0.5,
              }}
            >
              <tab.icon className="h-3 w-3" />
              <span>{tab.label}</span>
              {tab.count > 0 && (
                <span
                  className="text-[8px] px-1 py-0 rounded-full tabular-nums"
                  style={{
                    backgroundColor: isActive ? "var(--theme-card-bg)" : "transparent",
                    color: isActive ? "var(--theme-accent)" : "var(--theme-main-text)",
                    border: `1px solid ${isActive ? "var(--theme-accent)" : "var(--theme-border)"}`,
                  }}
                >
                  {tab.count}
                </span>
              )}
              {isActive && (
                <motion.div
                  layoutId="advConsoleTab"
                  className="absolute bottom-0 left-0 right-0 h-[2px]"
                  style={{ backgroundColor: "var(--theme-accent)" }}
                />
              )}
            </button>
          );
        })}
        {isLive && (
          <div className="flex items-center px-2">
            <span className="flex items-center gap-1 text-[9px] text-green-600">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              LIVE
            </span>
          </div>
        )}
      </div>

      {/* Tab content — flex-1 fills remaining height when fillColumn */}
      <ScrollArea
        className={cn(fillColumn ? "min-h-0 flex-1" : "max-h-[450px]")}
      >
        <div style={{ color: "var(--theme-main-text)" }}>
          {activeTab === "memory" && (
            <div>
              <div className="px-1.5 pt-1.5">
                <div className="text-[9px] font-semibold tracking-wider uppercase mb-0.5 px-0.5" style={{ color: "var(--theme-accent)", opacity: 0.7 }}>
                  Context Memory
                </div>
              </div>
              <ContextMemoryTab entries={data.contextMemory} />
              <div className="px-1.5 pt-2">
                <div className="text-[9px] font-semibold tracking-wider uppercase mb-0.5 px-0.5" style={{ color: "var(--theme-accent)", opacity: 0.7 }}>
                  Execution Memory
                </div>
              </div>
              <ExecutionMemoryTab entries={data.executionMemory} />
            </div>
          )}
          {activeTab === "llm" && <LLMCallsTab entries={data.llmCalls} />}
          {activeTab === "critics" && <CriticsTab stepCritics={data.stepCritics} planCritics={data.planCritics || []} />}
        </div>
      </ScrollArea>
    </div>
  );
}
