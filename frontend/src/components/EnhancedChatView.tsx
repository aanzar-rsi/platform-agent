import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState, type ReactNode, Fragment } from "react";
import { useNavigate } from "react-router";
import { AnimatePresence, motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";
import {
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Copy,
  FileText,
  FolderOpen,
  GitBranch,
  IdCard,
  ListChecks,
  Loader2,
  Lock,
  MessageSquare,
  Mic,
  Paperclip,
  Pause,
  Pencil,
  RefreshCw,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Square,
  Tag,
  User,
  Wrench,
  X,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import LiquidEther from "@/components/LiquidEther";
import InterruptPrompt from "@/components/InterruptPrompt";
import CheckpointTree from "@/components/CheckpointTree";
import { CheckpointActionPanel } from "@/components/CheckpointActionPanel";
import AgentSettingsPanel from "@/components/AgentSettingsPanel";
import CustomLoader from "@/components/CustomLoader";
import { DEFAULT_MODEL } from "@/lib/availableModels";
import { agentsAPI, filesAPI, preferencesAPI } from "@/lib/api";
import { AgentWebSocketClient, createWebSocketClient } from "@/lib/websocket";
import {
  AgentCardPayload,
  AgentTestCasePayload,
  AgentTestResultPayload,
  Message,
  PendingInterrupt,
  SubagentCallEvent,
  SubagentProgressEvent,
  ToolCallEvent,
} from "@/types/backend";
import { useAuth } from "@/hooks/use-auth";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  assistantAnswerContent,
  mapHistoryMessages,
  mapStepsToCheckpoints,
  excludeInFlightAssistantTurn,
  freezeAssistantTurn,
} from "@/lib/chatMappers";
import { getCachedChat, setCachedChat } from "@/lib/chatCache";
import { titleFromFirstMessage } from "@/lib/chatTitle";
import {
  appendReasoningStep,
  appendChildProgress,
  appendChildStarted,
  appendSubagentProgress,
  appendSubagentStarted,
  appendToolStarted,
  formatReadablePayload,
  stepsFromLegacyMetadata,
  updateChildFinished,
  updateSubagentFinished,
  updateToolFinished,
} from "@/lib/agentSteps";
import { markdownLinkComponent, stabilizeMarkdownLinks } from "@/lib/markdown";
import { cn } from "@/lib/utils";
import type { AgentStep, CheckpointTreeNode } from "@/types/backend";
import {
  type ChatAttachment,
  formatMessageWithAttachments,
  newAttachment,
  parseMessageWithAttachments,
  resolveDirectoryPath,
  resolveFilePath,
} from "@/lib/chatAttachments";
import {
  markSmokeBuildCompleted,
  matchSmokeScript,
  playSmokeScript,
  type SmokeScriptId,
} from "@/lib/smokescreen";
import { getNewChatPolicyPreset, clearNewChatPolicyPreset } from "@/lib/chatPolicyPreset";

const USE_BACKEND = true;
const CHAT_VIEW_STORAGE_KEY = "eva_chat_view_mode";
const MARKDOWN_BUBBLE_CLASS =
  "chat-md prose prose-sm prose-neutral min-w-0 max-w-none overflow-hidden break-words text-sm";
const INPUT_LINE_HEIGHT_PX = 22;
const INPUT_MAX_LINES = 10;
const INPUT_MIN_HEIGHT_PX = INPUT_LINE_HEIGHT_PX + 12;
const INPUT_MAX_HEIGHT_PX = INPUT_LINE_HEIGHT_PX * INPUT_MAX_LINES + 12;
const ATTACH_MENU_ITEM_CLASS =
  "cursor-pointer rounded-xl text-[#171717] data-[highlighted]:bg-[#f8f8f6] focus:bg-[#f8f8f6]";

function formatSubagentDisplayName(agentName: string): string {
  return agentName
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function subagentStatusLabel(subagent: SubagentCallEvent): string {
  if (subagent.status === "running") return "Running";
  if (subagent.status === "error" || subagent.success === false) return "Failed";
  return "Done";
}

function normalizeProgressEvent(
  event: { step: string; message: string; status: string; ts?: string; kind?: string; detail?: unknown }
): SubagentProgressEvent {
  return {
    ...event,
    kind: (event.kind as SubagentProgressEvent["kind"]) || "status",
  };
}

function formatNodeStatus(node: string): string {
  const label = node.replace(/_node$/, "").replace(/_/g, " ").trim();
  if (!label) return "Thinking…";
  if (label.toLowerCase() === "agent") return "Thinking…";
  return `${label.charAt(0).toUpperCase()}${label.slice(1)}…`;
}

/** Ordered pipeline phases for AgentStudio — drives the header's live stepper. */
const AGENT_STUDIO_PHASES: { key: string; label: string }[] = [
  { key: "validate_request", label: "Validate" },
  { key: "expand_requirement", label: "Scope" },
  { key: "create_agent_card", label: "Card" },
  { key: "design_agent", label: "Design" },
  { key: "generate_code", label: "Code" },
  { key: "static_validate", label: "Check" },
  { key: "generate_tests", label: "Tests" },
  { key: "run_tests", label: "Run" },
  { key: "evaluate_tests", label: "Grade" },
  { key: "finalize", label: "Finalize" },
];

function useElapsedLabel(startedAt: number | undefined, endedAt: number | undefined, running: boolean): string {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!running) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [running]);
  if (!startedAt) return "";
  const end = running ? now : endedAt || now;
  const seconds = Math.max(0, Math.round((end - startedAt) / 1000));
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}

function PhaseStepper({ visited, current }: { visited: Set<string>; current?: string }) {
  return (
    <div className="flex items-center gap-1 shrink-0" aria-hidden>
      {AGENT_STUDIO_PHASES.map((phase) => {
        const isActive = phase.key === current;
        const isSeen = visited.has(phase.key);
        return (
          <span
            key={phase.key}
            title={phase.label}
            className={`h-1.5 rounded-full transition-all duration-300 ease-out ${
              isActive ? "w-4 animate-pulse" : "w-1.5"
            }`}
            style={{
              backgroundColor: isActive || isSeen ? "var(--theme-accent)" : "var(--theme-border)",
              opacity: isActive ? 1 : isSeen ? 0.55 : 0.35,
            }}
          />
        );
      })}
    </div>
  );
}

function PermissionBadge({ label, granted }: { label: string; granted?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide ${
        granted ? "text-emerald-700" : "text-gray-400"
      }`}
      style={{
        backgroundColor: granted ? "rgba(16,185,129,0.1)" : "var(--theme-card-bg)",
        border: `1px solid ${granted ? "rgba(16,185,129,0.3)" : "var(--theme-border)"}`,
      }}
    >
      <Lock className="h-2.5 w-2.5" />
      {label}
    </span>
  );
}

function AgentCardView({ card }: { card: AgentCardPayload }) {
  const permissions = card.permissions || {};
  const tools = card.tools_used || [];
  return (
    <motion.div
      initial={{ opacity: 0, y: 6, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="my-1.5 overflow-hidden rounded-lg border"
      style={{ borderColor: "var(--theme-accent)", backgroundColor: "#fffeff" }}
    >
      <div
        className="flex items-center gap-2 border-b px-2.5 py-1.5"
        style={{ backgroundColor: "rgba(64,64,64,0.08)", borderColor: "var(--theme-border)" }}
      >
        <IdCard className="h-3.5 w-3.5 shrink-0" style={{ color: "var(--theme-accent)" }} />
        <span className="truncate text-[11px] font-semibold text-gray-900">{card.name || "Untitled agent"}</span>
        {card.status && (
          <span
            className="ml-auto shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide"
            style={{
              backgroundColor:
                card.status === "passed"
                  ? "rgba(16,185,129,0.12)"
                  : card.status === "pending"
                    ? "var(--theme-card-bg)"
                    : "rgba(239,68,68,0.1)",
              color: card.status === "passed" ? "#047857" : card.status === "pending" ? "#6b7280" : "#b91c1c",
            }}
          >
            {card.status}
          </span>
        )}
      </div>
      <div className="space-y-2 px-2.5 py-2 text-[10.5px] leading-relaxed">
        {card.description && <p className="whitespace-pre-wrap text-gray-700">{card.description}</p>}

        <div className="flex flex-wrap items-center gap-2 text-gray-500">
          {card.function_name && (
            <span className="inline-flex items-center gap-1 font-mono">
              <span className="opacity-60">fn:</span>
              <code
                className="rounded px-1 py-0.5"
                style={{ backgroundColor: "var(--theme-card-bg)", border: "1px solid var(--theme-border)" }}
              >
                {card.function_name}()
              </code>
            </span>
          )}
          {card.model?.uses_llm !== undefined && (
            <span className="inline-flex items-center gap-1">
              <Sparkles className="h-2.5 w-2.5" />
              {card.model.uses_llm ? "uses LLM" : "no LLM"}
            </span>
          )}
          {typeof card.constraints?.timeout_seconds === "number" && (
            <span className="inline-flex items-center gap-1">
              <Clock className="h-2.5 w-2.5" />
              {card.constraints.timeout_seconds}s timeout
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <PermissionBadge label="read" granted={permissions.read} />
          <PermissionBadge label="write" granted={permissions.write} />
          <PermissionBadge label="execute" granted={permissions.execute} />
        </div>

        {tools.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <Wrench className="h-2.5 w-2.5 shrink-0 opacity-50" />
            {tools.map((tool) => (
              <span
                key={tool}
                className="rounded px-1.5 py-0.5 text-[9px] font-medium text-gray-700"
                style={{ backgroundColor: "var(--theme-card-bg)", border: "1px solid var(--theme-border)" }}
              >
                {tool}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function shortenValue(value: unknown, maxLen = 60): string {
  if (value === undefined) return "—";
  const text = typeof value === "string" ? value : JSON.stringify(value);
  if (text == null) return "—";
  return text.length > maxLen ? `${text.slice(0, maxLen)}…` : text;
}

function TestCasesCard({ cases }: { cases: AgentTestCasePayload[] }) {
  if (!cases.length) return null;
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="my-1.5 overflow-hidden rounded-lg border"
      style={{ borderColor: "var(--theme-border)", backgroundColor: "#fffeff" }}
    >
      <div
        className="flex items-center gap-2 border-b px-2.5 py-1.5"
        style={{ backgroundColor: "rgba(64,64,64,0.08)", borderColor: "var(--theme-border)" }}
      >
        <ListChecks className="h-3.5 w-3.5 shrink-0" style={{ color: "var(--theme-accent)" }} />
        <span className="text-[11px] font-semibold text-gray-900">Test plan · {cases.length} case(s)</span>
      </div>
      <div className="divide-y" style={{ borderColor: "var(--theme-border)" }}>
        {cases.map((c, idx) => (
          <div key={`${c.name}-${idx}`} className="flex items-start gap-2 px-2.5 py-1.5 text-[10.5px]">
            <Tag className="mt-0.5 h-2.5 w-2.5 shrink-0 opacity-40" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="font-medium text-gray-800">{c.name}</span>
                <span
                  className="rounded px-1 py-0.5 text-[9px] font-medium uppercase tracking-wide text-gray-500"
                  style={{ backgroundColor: "var(--theme-card-bg)" }}
                >
                  {c.kind}
                </span>
                <span className="text-[9px] italic text-gray-400">expect: {c.expectation_type}</span>
              </div>
              {c.input_kwargs && Object.keys(c.input_kwargs).length > 0 && (
                <div className="mt-0.5 truncate font-mono text-[9.5px] text-gray-500">
                  {shortenValue(c.input_kwargs, 90)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function TestResultsCard({ results, graded }: { results: AgentTestResultPayload[]; graded: boolean }) {
  if (!results.length) return null;
  const passedCount = results.filter((r) => r.passed).length;
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="my-1.5 overflow-hidden rounded-lg border"
      style={{
        borderColor: graded && passedCount < results.length ? "rgba(239,68,68,0.4)" : "var(--theme-border)",
        backgroundColor: "#fffeff",
      }}
    >
      <div
        className="flex items-center gap-2 border-b px-2.5 py-1.5"
        style={{ backgroundColor: "rgba(64,64,64,0.08)", borderColor: "var(--theme-border)" }}
      >
        <ShieldCheck className="h-3.5 w-3.5 shrink-0" style={{ color: "var(--theme-accent)" }} />
        <span className="text-[11px] font-semibold text-gray-900">
          {graded ? "Graded results" : "Sandbox run"} · {results.length} case(s)
        </span>
        {graded && (
          <span
            className="ml-auto shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium"
            style={{
              backgroundColor: passedCount === results.length ? "rgba(16,185,129,0.12)" : "rgba(239,68,68,0.1)",
              color: passedCount === results.length ? "#047857" : "#b91c1c",
            }}
          >
            {passedCount}/{results.length} passed
          </span>
        )}
      </div>
      <div className="divide-y" style={{ borderColor: "var(--theme-border)" }}>
        {results.map((r, idx) => {
          const errored = Boolean(r.raw_error || r.error);
          const failed = graded ? r.passed === false : errored;
          return (
            <div key={`${r.name}-${idx}`} className="flex items-start gap-2 px-2.5 py-1.5 text-[10.5px]">
              {graded ? (
                failed ? (
                  <XCircle className="mt-0.5 h-3 w-3 shrink-0 text-red-500" />
                ) : (
                  <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-emerald-500" />
                )
              ) : errored ? (
                <XCircle className="mt-0.5 h-3 w-3 shrink-0 text-yellow-500" />
              ) : (
                <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-gray-400" />
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className={`font-medium ${failed ? "text-red-700" : "text-gray-800"}`}>{r.name}</span>
                  {typeof r.duration_ms === "number" && (
                    <span className="inline-flex items-center gap-0.5 text-[9px] text-gray-400">
                      <Clock className="h-2.5 w-2.5" />
                      {r.duration_ms.toFixed(0)}ms
                    </span>
                  )}
                </div>
                <div className="mt-0.5 truncate font-mono text-[9.5px] text-gray-500">
                  {errored ? `error: ${shortenValue(r.raw_error || r.error, 90)}` : `→ ${shortenValue(r.actual, 90)}`}
                </div>
                {r.reason && <div className="mt-0.5 text-[9.5px] italic text-gray-500">{r.reason}</div>}
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}

function SubagentProgressLine({ entry }: { entry: SubagentProgressEvent }) {
  const kind = entry.kind || "status";

  if (kind === "card") {
    const card = (entry.detail as { agent_card?: AgentCardPayload } | null)?.agent_card;
    if (!card) return null;
    return <AgentCardView card={card} />;
  }

  if (kind === "test_plan") {
    const cases = (entry.detail as { test_cases?: AgentTestCasePayload[] } | null)?.test_cases;
    if (!cases?.length) return null;
    return <TestCasesCard cases={cases} />;
  }

  if (kind === "test_results") {
    const detail = entry.detail as { test_results?: AgentTestResultPayload[]; graded?: boolean } | null;
    if (!detail?.test_results?.length) return null;
    return <TestResultsCard results={detail.test_results} graded={Boolean(detail.graded)} />;
  }

  if (kind === "reasoning") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="mb-2 flex items-start gap-2 rounded-r-md border-l-2 py-1.5 pl-2.5 pr-1"
        style={{ borderColor: "var(--theme-accent)", backgroundColor: "rgba(64,64,64,0.05)" }}
      >
        <BrainCircuit className="mt-0.5 h-3 w-3 shrink-0 opacity-50" style={{ color: "var(--theme-accent)" }} />
        <p className="min-w-0 flex-1 whitespace-pre-wrap italic leading-relaxed text-gray-600">
          {entry.message || " "}
          {!entry.reasoningDone && (
            <span
              className="ml-0.5 inline-block h-3 w-1.5 animate-pulse align-middle"
              style={{ backgroundColor: "var(--theme-accent)" }}
              aria-hidden
            />
          )}
        </p>
      </motion.div>
    );
  }

  const colorClass =
    entry.status === "error"
      ? "text-red-700"
      : entry.status === "warning"
        ? "text-yellow-700"
        : entry.status === "in_progress"
          ? "text-[#404040]"
          : "text-gray-800";

  const detail =
    entry.detail && typeof entry.detail === "object" ? (entry.detail as Record<string, unknown>) : null;
  const codePreview = typeof detail?.code_preview === "string" ? detail.code_preview : null;

  return (
    <motion.div
      initial={{ opacity: 0, x: -4 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className="py-0.5"
    >
      <div className="flex items-start gap-2">
        <span className="shrink-0 text-gray-400">{kind === "log" ? "$" : ">"}</span>
        <span className="min-w-0 flex-1">
          <span className="font-medium text-gray-500">[{entry.step}]</span>{" "}
          <span className={colorClass}>{entry.message}</span>
        </span>
      </div>
      {codePreview && (
        <pre
          className="ml-5 mt-1 overflow-x-auto rounded border px-2 py-1.5 text-[10px] leading-relaxed text-gray-700"
          style={{ borderColor: "var(--theme-border)", backgroundColor: "var(--theme-card-bg)" }}
        >
          {codePreview}
        </pre>
      )}
    </motion.div>
  );
}

function SubagentConsole({ subagent }: { subagent: SubagentCallEvent }) {
  const displayName = formatSubagentDisplayName(subagent.agent_name);
  const status = subagentStatusLabel(subagent);
  const isRunning = subagent.status === "running";
  const isError = subagent.status === "error" || subagent.success === false;
  const elapsed = useElapsedLabel(subagent.startedAt, subagent.endedAt, isRunning);

  const visitedPhases = useMemo(
    () => new Set(subagent.progress.map((p) => p.step)),
    [subagent.progress]
  );
  const currentPhase = isRunning ? subagent.progress[subagent.progress.length - 1]?.step : undefined;

  const scrollRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);
  useEffect(() => {
    const el = scrollRef.current;
    if (el && isNearBottomRef.current) el.scrollTop = el.scrollHeight;
    // `subagent.progress` gets a new array reference on every update — including
    // in-place reasoning-delta growth that doesn't change `.length` — so this
    // fires on every streamed chunk, not just when a new line is appended.
  }, [subagent.progress, subagent.result]);

  return (
    <div
      className="overflow-hidden rounded-xl border-2 shadow-sm transition-shadow"
      style={{
        borderColor: isRunning ? "var(--theme-accent)" : "var(--theme-border)",
        backgroundColor: "#fffeff",
        boxShadow: isRunning ? "0 0 0 3px rgba(64,64,64,0.08)" : undefined,
      }}
    >
      <div
        className="flex items-center gap-2 border-b px-3 py-2"
        style={{ backgroundColor: "#f8f8f6", borderColor: "var(--theme-border)" }}
      >
        <span className="relative flex h-2 w-2 shrink-0" aria-hidden>
          {isRunning && (
            <span
              className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60"
              style={{ backgroundColor: "#fbe232" }}
            />
          )}
          <span
            className={`relative inline-flex h-2 w-2 rounded-full ${
              isRunning ? "bg-yellow-400" : isError ? "bg-red-500" : "bg-green-500"
            }`}
          />
        </span>
        <Sparkles className="h-3.5 w-3.5 shrink-0" style={{ color: "var(--theme-accent)" }} />
        <span className="truncate text-xs font-semibold text-gray-900">{displayName}</span>

        <PhaseStepper visited={visitedPhases} current={currentPhase} />

        {elapsed && (
          <span className="shrink-0 font-mono text-[10px] tabular-nums text-gray-500">{elapsed}</span>
        )}
        <span
          className="ml-1 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-gray-600"
          style={{ backgroundColor: "#fffeff", border: "1px solid var(--theme-border)" }}
        >
          {status}
        </span>
      </div>

      <div
        ref={scrollRef}
        onScroll={(e) => {
          const el = e.currentTarget;
          isNearBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
        }}
        className="min-h-44 max-h-96 overflow-auto px-3 py-3 font-mono text-[11px] leading-relaxed text-gray-800"
        style={{ backgroundColor: "#fffeff" }}
      >
        {subagent.task?.trim() && (
          <div
            className="mb-3 rounded-md border px-2.5 py-2 text-[10px] leading-relaxed"
            style={{ backgroundColor: "#f8f8f6", borderColor: "var(--theme-border)" }}
          >
            <span className="font-semibold uppercase tracking-wide text-gray-500">Task</span>
            <p className="mt-1 whitespace-pre-wrap text-gray-700">{subagent.task.trim()}</p>
          </div>
        )}

        {subagent.progress.length > 0 ? (
          <div
            className="rounded-md border px-2.5 py-2"
            style={{ backgroundColor: "#f8f8f6", borderColor: "var(--theme-border)" }}
          >
            <AnimatePresence initial={false}>
              {subagent.progress.map((entry, entryIndex) => (
                <SubagentProgressLine key={entryIndex} entry={entry} />
              ))}
            </AnimatePresence>
          </div>
        ) : subagent.result ? null : (
          <div
            className="flex min-h-24 items-center gap-2 rounded-md border px-2.5 py-3 italic text-gray-600"
            style={{ backgroundColor: "#f8f8f6", borderColor: "var(--theme-border)" }}
          >
            <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" style={{ color: "var(--theme-accent)" }} />
            <span>Waiting for sub-agent output…</span>
            <span
              className="inline-block h-4 w-2 animate-pulse"
              style={{ backgroundColor: "var(--theme-accent)" }}
              aria-hidden
            />
          </div>
        )}

        {subagent.result && (
          <div
            className={
              subagent.progress.length > 0 ? "mt-3 border-t pt-3" : "mt-0"
            }
            style={{ borderColor: "var(--theme-border)" }}
          >
            <div className="mb-1.5 flex items-center justify-between gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">
                Result
              </span>
            </div>
            <pre
              className="whitespace-pre-wrap rounded-md border px-2.5 py-2 text-gray-800"
              style={{ backgroundColor: "#f8f8f6", borderColor: "var(--theme-border)" }}
            >
              {formatReadablePayload(subagent.result)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

function AttachmentChipList({
  attachments,
  onRemove,
}: {
  attachments: Array<{ id?: string; name: string; path: string; kind?: "file" | "directory" }>;
  onRemove?: (id: string) => void;
}) {
  if (!attachments.length) return null;
  return (
    <div className="mb-2 flex flex-wrap gap-2">
      {attachments.map((item) => (
        <div
          key={item.id || item.path}
          className="inline-flex max-w-[240px] items-center gap-1.5 rounded-full border bg-white/90 px-2.5 py-1.5 text-xs shadow-sm"
          style={{ borderColor: "var(--theme-border)" }}
          title={item.path}
        >
          {item.kind === "directory" ? (
            <FolderOpen className="h-3.5 w-3.5 shrink-0 opacity-70" />
          ) : (
            <FileText className="h-3.5 w-3.5 shrink-0 opacity-70" />
          )}
          <span className="truncate font-medium leading-none text-gray-900">{item.name}</span>
          {onRemove && item.id && (
            <button
              type="button"
              className="inline-flex shrink-0 items-center justify-center rounded-full p-0.5 text-gray-500 hover:bg-gray-100 hover:text-gray-800"
              onClick={() => onRemove(item.id!)}
              aria-label={`Remove ${item.name}`}
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

function UserMessageBody({ content }: { content: string }) {
  const { displayText, attachments } = parseMessageWithAttachments(content);
  const chips = attachments.map((path) => ({
    path,
    name: path.split(/[/\\]/).filter(Boolean).pop() || path,
  }));
  return (
    <>
      <AttachmentChipList attachments={chips} />
      {displayText ? <p className="text-sm whitespace-pre-wrap text-left">{displayText}</p> : null}
    </>
  );
}

export interface ChatTuneSettings {
  maxTokens: string;
  responseFormat: string;
  temperature: string;
  topK?: string;
  topP?: string;
  model?: string;
  instructions: string;
  enabledTools?: string[];
  consoleMode?: "basic" | "advanced";
  agentMode?: "basic" | "intermediate" | "advanced";
  [key: string]: unknown;
}

interface ChatViewProps {
  sessionId: string | null;
  onTuneSettingsChange?: (settings: ChatTuneSettings) => void;
  tuneSettings?: ChatTuneSettings;
  onViewModeChange?: (mode: "beginner" | "advanced") => void;
  onExecutionStateChange?: (state: { sessionId: string | null; isExecuting: boolean }) => void;
}

/** Imperative API exposed to parent components for rewind/fork actions. */
export interface EnhancedChatViewHandle {
  rewindToCheckpoint: (checkpointId: string) => Promise<void>;
  forkFromCheckpoint: (checkpointId: string, note: string) => Promise<void>;
}

/** Branch graph panel toggled from the bubble action row. */
function BubbleBranchTree({
  sessionId,
  refreshKey,
  onRewind,
  onFork,
}: {
  sessionId: string | null;
  refreshKey: number;
  onRewind: (checkpointId: string) => Promise<void>;
  onFork: (checkpointId: string, note: string) => Promise<void>;
}) {
  if (!sessionId) return null;

  return (
    <div className="mt-3 border-t pt-3" style={{ borderColor: "var(--theme-border)" }}>
      <CheckpointTree
        embedded
        chatId={sessionId}
        refreshSignal={refreshKey}
        onRewind={onRewind}
        onFork={onFork}
      />
    </div>
  );
}

/** Clickable step row — selection state is managed by the parent conversation renderer. */
function StepBranchTarget({
  checkpointId,
  disabled,
  selected,
  onSelect,
  children,
  className,
}: {
  checkpointId: string | null | undefined;
  disabled?: boolean;
  selected?: boolean;
  onSelect: () => void;
  children: ReactNode;
  className?: string;
}) {
  if (!checkpointId) {
    return <div className={className}>{children}</div>;
  }

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onSelect}
      className={cn(
        "w-full rounded-md text-left transition-colors",
        "hover:bg-black/[0.04] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--theme-accent)]",
        selected && "bg-black/[0.04] ring-1 ring-[var(--theme-accent)]/40",
        disabled && "pointer-events-none opacity-60",
        className
      )}
    >
      {children}
    </button>
  );
}

function CacheHitBadge() {
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
      style={{
        color: "#0f766e",
        backgroundColor: "rgba(20,184,166,0.14)",
        border: "1px solid rgba(20,184,166,0.35)",
      }}
    >
      cache
    </span>
  );
}

const EnhancedChatView = forwardRef<EnhancedChatViewHandle, ChatViewProps>(function EnhancedChatView({
  sessionId,
  tuneSettings,
  onTuneSettingsChange,
  onViewModeChange,
  onExecutionStateChange,
}: ChatViewProps, ref) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const userId = user?.user_id || user?.uid;

  const [agentSettingsOpen, setAgentSettingsOpen] = useState(false);
  const [chatTitle, setChatTitle] = useState("New chat");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [streamingOutput, setStreamingOutput] = useState("");
  const [streamingReasoning, setStreamingReasoning] = useState("");
  const [liveCacheHit, setLiveCacheHit] = useState(false);
  const [liveTools, setLiveTools] = useState<ToolCallEvent[]>([]);
  const [liveSteps, setLiveSteps] = useState<AgentStep[]>([]);
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [activeInFlightQuery, setActiveInFlightQuery] = useState<string | null>(null);
  const [pendingAttachments, setPendingAttachments] = useState<ChatAttachment[]>([]);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [pendingInterrupt, setPendingInterrupt] = useState<PendingInterrupt | null>(null);
  const [interruptBusy, setInterruptBusy] = useState(false);
  const [branchRefreshKey, setBranchRefreshKey] = useState(0);
  const [branchesOpenFor, setBranchesOpenFor] = useState<string | null>(null);
  const [checkpointTree, setCheckpointTree] = useState<CheckpointTreeNode[]>([]);
  const [selectedStepBranch, setSelectedStepBranch] = useState<{
    scopeId: string;
    stepIndex: number;
  } | null>(null);
  const [stepForkNote, setStepForkNote] = useState("");
  const [stepBranchBusy, setStepBranchBusy] = useState(false);
  const bumpBranchRefresh = useCallback(() => setBranchRefreshKey((k) => k + 1), []);

  useEffect(() => {
    setBranchesOpenFor(null);
    setSelectedStepBranch(null);
    setStepForkNote("");
  }, [sessionId]);

  const loadCheckpointTree = useCallback(async () => {
    if (!sessionId) {
      setCheckpointTree([]);
      return;
    }
    try {
      setCheckpointTree(await agentsAPI.listCheckpointTree(sessionId));
    } catch {
      setCheckpointTree([]);
    }
  }, [sessionId]);

  useEffect(() => {
    void loadCheckpointTree();
  }, [loadCheckpointTree, branchRefreshKey]);

  useEffect(() => {
    if (!sessionId || !isLoading) return;
    const timer = window.setTimeout(() => {
      void loadCheckpointTree();
    }, 600);
    return () => window.clearTimeout(timer);
  }, [isLoading, liveSteps.length, loadCheckpointTree, sessionId]);

  const wsClientRef = useRef<AgentWebSocketClient | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dirInputRef = useRef<HTMLInputElement | null>(null);
  const runActiveRef = useRef(false);
  const streamingOutputRef = useRef("");
  const streamingReasoningRef = useRef("");
  const liveCacheHitRef = useRef(false);
  const liveToolsRef = useRef<ToolCallEvent[]>([]);
  const liveStepsRef = useRef<AgentStep[]>([]);
  const lastUserQueryRef = useRef<string>("");
  /** Drop WS backlog from a finished run after reconnect (run_active=false). */
  const ignoreStaleRunEventsRef = useRef(true);
  const loadGenerationRef = useRef(0);
  const runFinalizedRef = useRef(false);
  const activeExecutionIdRef = useRef<string | null>(null);
  const smokeAbortRef = useRef<AbortController | null>(null);
  const smokeActiveRef = useRef(false);
  const chatTitleRef = useRef(chatTitle);
  chatTitleRef.current = chatTitle;

  const welcomeMessages = useMemo(
    () => [
      "What can I help you with today?",
      "Ask me anything — I'm ready when you are.",
      "Let's get started. What's on your mind?",
    ],
    []
  );
  const [currentWelcomeMessage] = useState(
    () => welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)]
  );
  const suggestedQuestions = useMemo(
    () => [
      "What can you help me with?",
      "Summarize my recent work",
      "Help me draft an email",
      "Explain a complex topic simply",
    ],
    []
  );

  const setExecuting = useCallback(
    (executing: boolean) => {
      runActiveRef.current = executing;
      setIsLoading(executing);
      onExecutionStateChange?.({ sessionId, isExecuting: executing });
    },
    [onExecutionStateChange, sessionId]
  );

  const scrollToBottom = useCallback(() => {
    if (!shouldAutoScroll) return;
    requestAnimationFrame(() => {
      const el = scrollRef.current;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }, [shouldAutoScroll]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingOutput, liveSteps, activeInFlightQuery, scrollToBottom]);

  // Sync console_mode preference into parent view mode (no in-chat toggle).
  useEffect(() => {
    if (!USE_BACKEND) return;
    preferencesAPI
      .get()
      .then((res) => {
        const mode = res.preferences?.console_mode === "advanced" ? "advanced" : "basic";
        const viewMode = mode === "advanced" ? "advanced" : "beginner";
        localStorage.setItem(CHAT_VIEW_STORAGE_KEY, viewMode);
        onViewModeChange?.(viewMode);
        const prefs = res.preferences as Record<string, unknown> | undefined;
        const agent = (prefs?.agent_config || prefs?.agent || {}) as Record<string, unknown>;
        const modelFromPrefs =
          (agent.model as { default?: string } | undefined)?.default ||
          (agent.model as string | undefined) ||
          DEFAULT_MODEL;
        onTuneSettingsChange?.({
          ...(tuneSettings || {
            maxTokens: "",
            responseFormat: "text",
            temperature: "",
            topK: "",
            topP: "",
            model: DEFAULT_MODEL,
            instructions: "",
            agentMode: "basic",
          }),
          consoleMode: mode,
          model: tuneSettings?.model || modelFromPrefs,
          temperature: tuneSettings?.temperature || String(agent.temperature ?? ""),
          topP: tuneSettings?.topP || String(agent.top_p ?? ""),
          topK: tuneSettings?.topK || String(agent.top_k ?? ""),
        });
      })
      .catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetLiveState = useCallback(() => {
    setStreamingOutput("");
    setStreamingReasoning("");
    setLiveTools([]);
    setLiveSteps([]);
    setCurrentNode(null);
    setPendingInterrupt(null);
    setLiveCacheHit(false);
    streamingOutputRef.current = "";
    streamingReasoningRef.current = "";
    liveCacheHitRef.current = false;
    liveToolsRef.current = [];
    liveStepsRef.current = [];
  }, []);

  const clearInput = useCallback(() => {
    setInput("");
    if (inputRef.current) {
      inputRef.current.textContent = "";
      inputRef.current.style.height = `${INPUT_MIN_HEIGHT_PX}px`;
      inputRef.current.style.overflowY = "hidden";
    }
  }, []);

  const syncInputHeight = useCallback(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    const next = Math.min(Math.max(el.scrollHeight, INPUT_MIN_HEIGHT_PX), INPUT_MAX_HEIGHT_PX);
    el.style.height = `${next}px`;
    el.style.overflowY = el.scrollHeight > INPUT_MAX_HEIGHT_PX ? "auto" : "hidden";
  }, []);

  const addAttachmentsFromPaths = useCallback((paths: string[], kind: "file" | "directory") => {
    setPendingAttachments((prev) => {
      const next = [...prev];
      for (const path of paths) {
        const trimmed = path.trim();
        if (!trimmed || next.some((a) => a.path === trimmed)) continue;
        next.push(newAttachment(trimmed, kind));
      }
      return next;
    });
  }, []);

  const addAttachmentsFromFiles = useCallback((files: FileList | File[], kind: "file" | "directory") => {
    if (kind === "directory") {
      const dirPath = resolveDirectoryPath(files);
      if (!dirPath) {
        toast.error("Could not resolve folder path");
        return;
      }
      addAttachmentsFromPaths([dirPath], "directory");
      return;
    }

    const paths = Array.from(files).map((file) => resolveFilePath(file));
    addAttachmentsFromPaths(paths, "file");
  }, [addAttachmentsFromPaths]);

  const pickAttachments = useCallback(
    async (kind: "file" | "directory") => {
      if (USE_BACKEND) {
        try {
          const { paths } = await filesAPI.pick(kind === "directory" ? "directory" : "files", true);
          if (!paths.length) return;
          addAttachmentsFromPaths(paths, kind);
        } catch (e: unknown) {
          const message = e instanceof Error ? e.message : "Could not open file picker";
          toast.error(message);
        }
        return;
      }

      if (kind === "directory") dirInputRef.current?.click();
      else fileInputRef.current?.click();
    },
    [addAttachmentsFromPaths]
  );

  const removePendingAttachment = useCallback((id: string) => {
    setPendingAttachments((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const refetchChat = useCallback(async (chatId: string, expectedGeneration?: number) => {
    const response = await agentsAPI.get(userId, chatId);
    if (expectedGeneration !== undefined && loadGenerationRef.current !== expectedGeneration) {
      return;
    }
    if (response.success && response.data) {
      const title = response.data.title || response.data.session_name || "Chat";
      const messages = mapHistoryMessages(
        response.data.messages || [],
        response.data.execution_history || []
      );
      const rollbackCheckpointId = response.data.rollback_checkpoint_id || null;
      setChatTitle((prev) => {
        if (prev !== title) {
          queueMicrotask(() => window.dispatchEvent(new CustomEvent("eva:chats-changed")));
        }
        return title;
      });
      setMessages(messages);
      setCachedChat(chatId, { title, messages, rollbackCheckpointId });
    }
  }, [userId]);

  const finalizeRun = useCallback(
    async (payload?: {
      execution_id?: string;
      stopped?: boolean;
      answer?: string | null;
      checkpoint_id?: string;
      /** Skip backend history refetch (used by frontend smokescreen demos). */
      skipRefetch?: boolean;
    }) => {
      if (runFinalizedRef.current) return;
      runFinalizedRef.current = true;
      bumpBranchRefresh();

      const streamedAnswer = streamingOutputRef.current.trim();
      const answerFallback =
        (typeof payload?.answer === "string" && payload.answer.trim()
          ? payload.answer.trim()
          : null) ||
        (streamedAnswer || null);
      const reasoningFallback = streamingReasoningRef.current || undefined;
      const toolsFallback = liveToolsRef.current.length ? [...liveToolsRef.current] : undefined;
      const stepsFallback = liveStepsRef.current.length ? [...liveStepsRef.current] : undefined;
      const wasStopped = Boolean(payload?.stopped);
      const liveMetadata = {
        ...(reasoningFallback ? { reasoning: reasoningFallback } : {}),
        ...(toolsFallback ? { tools: toolsFallback } : {}),
        ...(stepsFallback ? { steps: stepsFallback } : {}),
        ...(liveCacheHitRef.current ? { cache_hit: true } : {}),
        ...(wasStopped ? { stopped: true } : {}),
        ...(payload?.execution_id ? { execution_id: payload.execution_id } : {}),
      };
      const hasLiveSnapshot = Boolean(
        answerFallback || stepsFallback?.length || toolsFallback?.length || reasoningFallback
      );

      ignoreStaleRunEventsRef.current = true;
      resetLiveState();
      setActiveInFlightQuery(null);
      setCurrentNode(null);
      setExecuting(false);
      clearInput();

      const chatId = sessionId;
      if (!chatId) return;

      const applyLiveFreeze = () => {
        if (!hasLiveSnapshot) return;
        setMessages((prev) => {
          const next = freezeAssistantTurn(prev, {
            content: answerFallback || "",
            checkpoint_id: payload?.checkpoint_id || null,
            metadata: Object.keys(liveMetadata).length ? liveMetadata : undefined,
          });
          if (payload?.skipRefetch) {
            setCachedChat(chatId, {
              title: chatTitleRef.current,
              messages: next,
              rollbackCheckpointId: null,
            });
          }
          return next;
        });
      };

      // Always keep a live freeze available — history refetch can lag behind
      // checkpoint/cache refresh and would otherwise blank the turn.
      if (hasLiveSnapshot) {
        applyLiveFreeze();
      }

      if (payload?.skipRefetch) return;

      try {
        await refetchChat(chatId);
        await loadCheckpointTree();
        if (hasLiveSnapshot) {
          // If history is still missing this turn, re-apply the freeze.
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            const hasStructuredAssistant =
              last?.role === "assistant" &&
              Boolean(last.metadata?.steps?.length || last.metadata?.reasoning || last.metadata?.tools?.length);
            if (hasStructuredAssistant && !wasStopped) return prev;
            return freezeAssistantTurn(prev, {
              content: answerFallback || "",
              checkpoint_id: payload?.checkpoint_id || null,
              metadata: Object.keys(liveMetadata).length ? liveMetadata : undefined,
            });
          });
        }
      } catch {
        if (hasLiveSnapshot) applyLiveFreeze();
      }
    },
    [bumpBranchRefresh, clearInput, loadCheckpointTree, refetchChat, resetLiveState, sessionId, setExecuting]
  );

  const runSmokescreen = useCallback(
    async (scriptId: SmokeScriptId, chatId: string) => {
      smokeAbortRef.current?.abort();
      const abort = new AbortController();
      smokeAbortRef.current = abort;
      smokeActiveRef.current = true;
      ignoreStaleRunEventsRef.current = false;
      activeExecutionIdRef.current = null;
      runFinalizedRef.current = false;

      const sink = {
        onNode: (node: string | null) => {
          if (abort.signal.aborted) return;
          setCurrentNode(node);
        },
        onReasoning: (text: string) => {
          if (abort.signal.aborted) return;
          streamingReasoningRef.current += text;
          setStreamingReasoning(streamingReasoningRef.current);
          appendReasoningStep(liveStepsRef.current, text);
          setLiveSteps([...liveStepsRef.current]);
        },
        onOutput: (text: string) => {
          if (abort.signal.aborted) return;
          streamingOutputRef.current += text;
          setStreamingOutput(streamingOutputRef.current);
        },
        onSubagentStarted: (payload: { agent_name: string; task?: string; tool_args?: unknown }) => {
          if (abort.signal.aborted || !payload.agent_name) return;
          const subagent: SubagentCallEvent = {
            id: `subagent_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            agent_name: payload.agent_name,
            task: payload.task,
            tool_args: payload.tool_args,
            status: "running",
            progress: [],
            startedAt: Date.now(),
          };
          appendSubagentStarted(liveStepsRef.current, subagent);
          setLiveSteps([...liveStepsRef.current]);
        },
        onSubagentStep: (payload: { agent_name: string; event: SubagentProgressEvent }) => {
          if (abort.signal.aborted || !payload.agent_name || !payload.event) return;
          appendSubagentProgress(liveStepsRef.current, payload.agent_name, payload.event);
          setLiveSteps([...liveStepsRef.current]);
        },
        onSubagentFinished: (payload: {
          agent_name: string;
          task?: string;
          result?: string;
          success?: boolean;
        }) => {
          if (abort.signal.aborted || !payload.agent_name) return;
          updateSubagentFinished(liveStepsRef.current, payload.agent_name, {
            task: payload.task,
            result: payload.result,
            success: payload.success,
            status: payload.success === false ? "error" : "done",
            endedAt: Date.now(),
          });
          setLiveSteps([...liveStepsRef.current]);
        },
        onChildStarted: (payload: { agent_name: string; child_agent_id?: string; task?: string }) => {
          if (abort.signal.aborted) return;
          const child = {
            id: payload.child_agent_id || `child_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            child_agent_id: payload.child_agent_id,
            agent_name: payload.agent_name || "child_agent",
            task: payload.task,
            status: "running" as const,
            progress: [],
            startedAt: Date.now(),
          };
          appendChildStarted(liveStepsRef.current, child);
          setLiveSteps([...liveStepsRef.current]);
        },
        onChildStep: (payload: { child_agent_id?: string; event: SubagentProgressEvent }) => {
          if (abort.signal.aborted || !payload.child_agent_id || !payload.event) return;
          appendChildProgress(liveStepsRef.current, payload.child_agent_id, payload.event);
          setLiveSteps([...liveStepsRef.current]);
        },
        onChildFinished: (payload: {
          child_agent_id?: string;
          task?: string;
          result?: string;
          success?: boolean;
        }) => {
          if (abort.signal.aborted) return;
          updateChildFinished(liveStepsRef.current, payload.child_agent_id, {
            ...(payload.task !== undefined ? { task: payload.task } : {}),
            result: payload.result,
            success: payload.success,
            status: payload.success === false ? "error" : "done",
            endedAt: Date.now(),
          });
          setLiveSteps([...liveStepsRef.current]);
        },
        onToolStarted: (payload: { tool_name: string; task?: string; tool_args?: unknown }) => {
          if (abort.signal.aborted) return;
          const tool: ToolCallEvent = {
            id: `tool_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            tool_name: payload.tool_name,
            tool_args: payload.tool_args,
            task: payload.task,
            status: "running",
          };
          liveToolsRef.current = [...liveToolsRef.current, tool];
          setLiveTools(liveToolsRef.current);
          appendToolStarted(liveStepsRef.current, tool);
          setLiveSteps([...liveStepsRef.current]);
        },
        onToolFinished: (payload: {
          tool_name: string;
          task?: string;
          tool_args?: unknown;
          result?: string;
          success?: boolean;
        }) => {
          if (abort.signal.aborted) return;
          liveToolsRef.current = liveToolsRef.current.map((t) =>
            t.tool_name === payload.tool_name && t.status === "running"
              ? {
                  ...t,
                  tool_args: payload.tool_args ?? t.tool_args,
                  task: payload.task ?? t.task,
                  result: payload.result,
                  success: payload.success,
                  status: payload.success === false ? "error" : "done",
                }
              : t
          );
          setLiveTools([...liveToolsRef.current]);
          updateToolFinished(liveStepsRef.current, payload.tool_name, {
            tool_args: payload.tool_args,
            task: payload.task,
            result: payload.result,
            success: payload.success,
            status: payload.success === false ? "error" : "done",
          });
          setLiveSteps([...liveStepsRef.current]);
        },
      };

      try {
        const { stopped } = await playSmokeScript(scriptId, sink, abort.signal);
        if (scriptId === "build" && !stopped) {
          markSmokeBuildCompleted(chatId);
        }
        await finalizeRun({
          stopped,
          skipRefetch: true,
          execution_id: `smoke_${scriptId}`,
          checkpoint_id: `smoke_cp_${scriptId}`,
        });
      } catch {
        await finalizeRun({ stopped: true, skipRefetch: true, execution_id: `smoke_${scriptId}` });
      } finally {
        if (smokeAbortRef.current === abort) smokeAbortRef.current = null;
        smokeActiveRef.current = false;
      }
    },
    [finalizeRun]
  );

  const disconnectWebSocket = useCallback(() => {
    wsClientRef.current?.disconnect();
    wsClientRef.current = null;
    setWsConnected(false);
  }, []);

  const connectWebSocket = useCallback(
    (chatId: string) => {
      disconnectWebSocket();
      ignoreStaleRunEventsRef.current = true;
      const client = createWebSocketClient(chatId, userId, {
        onOpen: () => setWsConnected(true),
        onClose: () => setWsConnected(false),
        onSessionReady: (payload) => {
          setWsConnected(true);
          if (payload.run_active) {
            ignoreStaleRunEventsRef.current = false;
            setExecuting(true);
          } else {
            ignoreStaleRunEventsRef.current = true;
            activeExecutionIdRef.current = null;
            resetLiveState();
            setActiveInFlightQuery(null);
            setExecuting(false);
          }
        },
        onRunStarted: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          activeExecutionIdRef.current = payload.execution_id || null;
          runFinalizedRef.current = false;
          setExecuting(true);
          if ((payload as { resumed?: boolean }).resumed) {
            setPendingInterrupt(null);
            setInterruptBusy(false);
            // Continuing a paused/interrupted run — keep the live transcript
            // (steps/streaming output) built up so far instead of wiping it.
            return;
          }
          setPendingInterrupt(null);
          setActiveInFlightQuery(payload.query);
          lastUserQueryRef.current = payload.query;
          resetLiveState();
        },
        onNodeStarted: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          setCurrentNode(payload.node);
        },
        onNodeFinished: () => {
          if (ignoreStaleRunEventsRef.current) return;
          setCurrentNode(null);
          // Finalize only on run.completed / run.error — node.finished(finish)
          // arrives earlier and racing refetchChat can wipe the live turn.
        },
        onLlmToken: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          const text = payload.text || "";
          if (payload.child_agent_id && payload.channel === "reasoning") {
            appendChildProgress(liveStepsRef.current, payload.child_agent_id, {
              step: "reasoning",
              status: "in_progress",
              kind: "reasoning",
              message: text,
              reasoningDone: false,
            });
            setLiveSteps([...liveStepsRef.current]);
            return;
          }
          if (payload.channel === "reasoning") {
            streamingReasoningRef.current += text;
            setStreamingReasoning(streamingReasoningRef.current);
            appendReasoningStep(liveStepsRef.current, text);
            setLiveSteps([...liveStepsRef.current]);
          } else {
            streamingOutputRef.current += text;
            setStreamingOutput(streamingOutputRef.current);
          }
        },
        onLlmCacheHit: () => {
          if (ignoreStaleRunEventsRef.current) return;
          liveCacheHitRef.current = true;
          setLiveCacheHit(true);
        },
        onToolStarted: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          const tool: ToolCallEvent = {
            id: `tool_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            tool_name: payload.tool_name,
            tool_args: payload.tool_args,
            task: payload.task,
            status: "running",
          };
          liveToolsRef.current = [...liveToolsRef.current, tool];
          setLiveTools(liveToolsRef.current);
          appendToolStarted(liveStepsRef.current, tool);
          setLiveSteps([...liveStepsRef.current]);
        },
        onToolFinished: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          liveToolsRef.current = liveToolsRef.current.map((t) =>
            t.tool_name === payload.tool_name && t.status === "running"
              ? {
                  ...t,
                  tool_args: payload.tool_args ?? t.tool_args,
                  task: payload.task ?? t.task,
                  result: payload.result,
                  success: payload.success,
                  status: payload.success === false ? "error" : "done",
                }
              : t
          );
          setLiveTools([...liveToolsRef.current]);
          updateToolFinished(liveStepsRef.current, payload.tool_name, {
            tool_args: payload.tool_args,
            task: payload.task,
            result: payload.result as string | undefined,
            success: payload.success,
            status: payload.success === false ? "error" : "done",
          });
          setLiveSteps([...liveStepsRef.current]);
        },
        onSubagentStarted: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          if (!payload.agent_name) return;
          const subagent: SubagentCallEvent = {
            id: `subagent_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            agent_name: payload.agent_name,
            task: payload.task,
            tool_args: payload.tool_args,
            status: "running",
            progress: [],
            startedAt: Date.now(),
          };
          appendSubagentStarted(liveStepsRef.current, subagent);
          setLiveSteps([...liveStepsRef.current]);
        },
        onSubagentStep: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          if (!payload.agent_name || !payload.event) return;
          appendSubagentProgress(liveStepsRef.current, payload.agent_name, normalizeProgressEvent(payload.event));
          setLiveSteps([...liveStepsRef.current]);
        },
        onSubagentFinished: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          if (!payload.agent_name) return;
          updateSubagentFinished(liveStepsRef.current, payload.agent_name, {
            task: payload.task,
            result: payload.result,
            success: payload.success,
            status: payload.success === false ? "error" : "done",
            endedAt: Date.now(),
          });
          setLiveSteps([...liveStepsRef.current]);
        },
        onChildStarted: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          const child = {
            id: payload.child_agent_id || `child_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
            child_agent_id: payload.child_agent_id,
            agent_name: payload.agent_name || "child_agent",
            task: payload.task,
            status: "running" as const,
            progress: [],
            startedAt: Date.now(),
          };
          appendChildStarted(liveStepsRef.current, child);
          setLiveSteps([...liveStepsRef.current]);
        },
        onChildStep: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          if (!payload.child_agent_id || !payload.event) return;
          appendChildProgress(liveStepsRef.current, payload.child_agent_id, normalizeProgressEvent(payload.event));
          setLiveSteps([...liveStepsRef.current]);
        },
        onChildFinished: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          updateChildFinished(liveStepsRef.current, payload.child_agent_id, {
            ...(payload.task !== undefined ? { task: payload.task } : {}),
            result: payload.result,
            success: payload.success,
            status: payload.success === false ? "error" : "done",
            endedAt: Date.now(),
          });
          setLiveSteps([...liveStepsRef.current]);
        },
        onCheckpointCreated: (payload) => {
          bumpBranchRefresh();
          if (payload.rollback) {
            resetLiveState();
            setActiveInFlightQuery(null);
            setExecuting(false);
          }
        },
        onRunInterrupted: (payload) => {
          if (ignoreStaleRunEventsRef.current) return;
          if (
            payload.execution_id &&
            activeExecutionIdRef.current &&
            payload.execution_id !== activeExecutionIdRef.current
          ) {
            return;
          }
          activeExecutionIdRef.current = null;
          setExecuting(false);
          setInterruptBusy(false);
          const innerPayload = (payload.payload || {}) as PendingInterrupt["payload"];
          setPendingInterrupt({
            execution_id: payload.execution_id,
            interrupt_id: payload.interrupt_id ?? null,
            kind: (payload.kind || innerPayload.kind || "paused") as string,
            checkpoint_id: payload.checkpoint_id ?? null,
            payload: innerPayload,
          });
        },
        onRunCompleted: async (payload) => {
          if (
            payload.execution_id &&
            activeExecutionIdRef.current &&
            payload.execution_id !== activeExecutionIdRef.current
          ) {
            return;
          }
          activeExecutionIdRef.current = null;
          if (payload.superseded) {
            // Tail-end of a run we deliberately interrupted to fork away from —
            // ignore it and wait for the fork's own run.started.
            return;
          }
          await finalizeRun(payload);
        },
        onRunError: (payload) => {
          if (
            payload.execution_id &&
            activeExecutionIdRef.current &&
            payload.execution_id !== activeExecutionIdRef.current
          ) {
            return;
          }
          activeExecutionIdRef.current = null;
          toast.error(payload.message || "Run failed");
          setInterruptBusy(false);
          void finalizeRun({ stopped: true, execution_id: payload.execution_id });
        },
        onError: (payload) => {
          toast.error(payload.message || "Error");
          setInterruptBusy(false);
          if (runActiveRef.current) {
            // e.g. a fork's stop-and-switch timed out — don't leave the UI
            // stuck showing "Thinking…" forever.
            void finalizeRun({ stopped: true });
          }
        },
      });

      wsClientRef.current = client;
      client.connect();
    },
    [disconnectWebSocket, finalizeRun, resetLiveState, setExecuting, userId]
  );

  // Session bootstrap — HTTP load is independent of WebSocket connect
  useEffect(() => {
    const generation = ++loadGenerationRef.current;
    let cancelled = false;

    const boot = async () => {
      resetLiveState();
      setActiveInFlightQuery(null);
      setExecuting(false);

      if (!sessionId || !USE_BACKEND) {
        disconnectWebSocket();
        setMessages([]);
        setIsChatLoading(false);
        return;
      }

      const cached = getCachedChat(sessionId);
      if (cached) {
        setChatTitle(cached.title);
        setMessages(cached.messages);
        setIsChatLoading(false);
      } else {
        setMessages([]);
        setIsChatLoading(true);
      }

      // WebSocket connects in parallel; never blocks chat history render
      connectWebSocket(sessionId);

      try {
        await refetchChat(sessionId, generation);
      } catch (err: any) {
        if (!cancelled && loadGenerationRef.current === generation) {
          console.error(err);
          toast.error("Failed to load chat");
          if (!cached) setMessages([]);
        }
      } finally {
        if (!cancelled && loadGenerationRef.current === generation) {
          setIsChatLoading(false);
        }
      }
    };

    boot();
    return () => {
      cancelled = true;
      smokeAbortRef.current?.abort();
      smokeAbortRef.current = null;
      smokeActiveRef.current = false;
      disconnectWebSocket();
    };
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Pending message after new-chat navigation
  useEffect(() => {
    if (!sessionId || isLoading || isChatLoading) return;
    const raw = sessionStorage.getItem("pendingMessage");
    if (!raw) return;
    try {
      const pending = JSON.parse(raw);
      if (pending.agentId !== sessionId) return;
      if (Date.now() - (pending.timestamp || 0) > 60_000) {
        sessionStorage.removeItem("pendingMessage");
        return;
      }

      const smokeId = matchSmokeScript(pending.message, {
        chatId: sessionId,
        hasAttachments: false,
      });

      // Normal runs wait for WS; smokescreen can start immediately.
      if (!smokeId && !wsConnected) return;

      sessionStorage.removeItem("pendingMessage");
      lastUserQueryRef.current = pending.message;
      setActiveInFlightQuery(pending.message);
      setMessages((prev) => [
        ...prev,
        {
          message_id: `user_${Date.now()}`,
          role: "user",
          content: pending.message,
          timestamp: Date.now(),
        },
      ]);
      setExecuting(true);
      ignoreStaleRunEventsRef.current = false;
      activeExecutionIdRef.current = null;
      runFinalizedRef.current = false;

      if (smokeId) {
        void runSmokescreen(smokeId, sessionId);
        return;
      }

      wsClientRef.current?.startRun(pending.message);
    } catch {
      sessionStorage.removeItem("pendingMessage");
    }
  }, [sessionId, wsConnected, isLoading, isChatLoading, setExecuting, runSmokescreen]);

  const sendQuery = useCallback(
    async (text: string, attachments: ChatAttachment[] = pendingAttachments) => {
      if (isLoading) return;
      const displayText = text.trim();
      const paths = attachments.map((a) => a.path);
      if (!displayText && !paths.length) return;
      const fullQuery = formatMessageWithAttachments(displayText, paths);

      if (!sessionId) {
        if (!userId) {
          toast.error("Please sign in");
          return;
        }
        try {
          const created = await agentsAPI.create({
            chat_name: titleFromFirstMessage(displayText || paths[0] || "New chat"),
          });
          if (!created.agent_id) throw new Error("No agent_id");

          const preset = getNewChatPolicyPreset();
          if (preset?.armory || preset?.memory) {
            try {
              const currentPolicy = await agentsAPI.getPolicy(created.agent_id);
              await agentsAPI.updatePolicy(created.agent_id, currentPolicy.version, {
                ...(preset.armory ? { armory: preset.armory as any } : {}),
                ...(preset.memory ? { memory: preset.memory as any } : {}),
              });
            } catch {
              clearNewChatPolicyPreset();
              toast.error("New-chat policy preset was invalid and has been cleared.");
            }
          }

          sessionStorage.setItem(
            "pendingMessage",
            JSON.stringify({ agentId: created.agent_id, message: fullQuery, timestamp: Date.now() })
          );
          navigate(`/agents/${created.agent_id}`);
        } catch (e: any) {
          toast.error(e?.message || "Failed to create chat");
        }
        return;
      }

      const smokeId = matchSmokeScript(fullQuery, {
        chatId: sessionId,
        hasAttachments: paths.length > 0,
      });

      if (!smokeId && !wsClientRef.current?.connected) {
        toast.error("Not connected — reconnecting…");
        connectWebSocket(sessionId);
        return;
      }

      const isFirstUserMessage = !messages.some((m) => m.role === "user");
      if (isFirstUserMessage) {
        const nextTitle = titleFromFirstMessage(displayText || paths[0] || "New chat");
        setChatTitle(nextTitle);
        void agentsAPI.update(sessionId, { title: nextTitle }).then(() => {
          window.dispatchEvent(new CustomEvent("eva:chats-changed"));
        });
      }

      lastUserQueryRef.current = fullQuery;
      setActiveInFlightQuery(fullQuery);
      setMessages((prev) => [
        ...prev,
        {
          message_id: `user_${Date.now()}`,
          role: "user",
          content: fullQuery,
          timestamp: Date.now(),
        },
      ]);
      setInput("");
      clearInput();
      setPendingAttachments([]);
      resetLiveState();
      setExecuting(true);
      ignoreStaleRunEventsRef.current = false;
      activeExecutionIdRef.current = null;
      runFinalizedRef.current = false;

      if (smokeId) {
        void runSmokescreen(smokeId, sessionId);
        return;
      }

      const ok = wsClientRef.current.startRun(fullQuery);
      if (!ok) {
        toast.error("Failed to start run");
        setExecuting(false);
        setActiveInFlightQuery(null);
      }
    },
    [
      clearInput,
      connectWebSocket,
      isLoading,
      messages,
      navigate,
      pendingAttachments,
      resetLiveState,
      runSmokescreen,
      sessionId,
      setExecuting,
      userId,
    ]
  );

  const handleStop = useCallback(() => {
    if (smokeActiveRef.current) {
      smokeAbortRef.current?.abort();
      return;
    }
    wsClientRef.current?.stopRun();
  }, []);

  const handlePause = useCallback(() => {
    if (smokeActiveRef.current) return;
    wsClientRef.current?.pauseRun();
  }, []);

  const handleInterruptResume = useCallback(
    (value: unknown) => {
      if (!pendingInterrupt) return;
      const response =
        typeof value === "string"
          ? value
          : value && typeof value === "object"
            ? String(
                (value as { note?: unknown; answer?: unknown; reason?: unknown }).note ??
                  (value as { answer?: unknown }).answer ??
                  (value as { reason?: unknown }).reason ??
                  ((value as { approved?: unknown }).approved === true
                    ? "Approved"
                    : (value as { approved?: unknown }).approved === false
                      ? "Declined"
                      : "")
              )
            : String(value ?? "");
      if (response.trim()) {
        liveStepsRef.current.push({
          type: "reasoning",
          content: `User response: ${response.trim()}`,
        });
        setLiveSteps([...liveStepsRef.current]);
      }
      setPendingInterrupt(null);
      setInterruptBusy(true);
      setExecuting(true);
      ignoreStaleRunEventsRef.current = false;
      activeExecutionIdRef.current = pendingInterrupt.execution_id || activeExecutionIdRef.current;
      runFinalizedRef.current = false;
      const ok = wsClientRef.current?.resumeRun(value);
      if (!ok) {
        toast.error("Failed to resume — reconnecting…");
        setExecuting(false);
        setInterruptBusy(false);
        if (sessionId) connectWebSocket(sessionId);
      }
    },
    [connectWebSocket, pendingInterrupt, sessionId, setExecuting]
  );

  const handleSend = useCallback(() => {
    const text = inputRef.current?.innerText?.trim() || input.trim();
    void sendQuery(text, pendingAttachments);
  }, [input, pendingAttachments, sendQuery]);

  const findRollbackCheckpointForUserIndex = useCallback(
    async (userIndex: number): Promise<string | null> => {
      // Prefer previous assistant's checkpoint (tip after prior turn)
      for (let i = userIndex - 1; i >= 0; i--) {
        if (messages[i]?.role === "assistant" && messages[i].checkpoint_id) {
          return messages[i].checkpoint_id as string;
        }
      }
      if (!sessionId) return null;
      try {
        const cps = await agentsAPI.listCheckpoints(sessionId);
        if (!cps.length) return null;
        // Earliest checkpoint as best-effort empty-ish state
        return cps[cps.length - 1]?.parent_checkpoint_id || cps[cps.length - 1]?.checkpoint_id || null;
      } catch {
        return null;
      }
    },
    [messages, sessionId]
  );

  const handleEditResend = useCallback(
    async (message: Message, index: number) => {
      if (!sessionId || isLoading) return;
      const checkpointId = await findRollbackCheckpointForUserIndex(index);
      // Optimistic truncate
      setMessages((prev) => prev.slice(0, index));
      const { displayText, attachments } = parseMessageWithAttachments(message.content);
      setInput(displayText);
      if (inputRef.current) inputRef.current.textContent = displayText;
      setPendingAttachments(attachments.map((path) => newAttachment(path, "file")));
      requestAnimationFrame(() => syncInputHeight());

      if (checkpointId) {
        try {
          await agentsAPI.rollback(sessionId, checkpointId);
          toast.success("Rewound — edit and send to continue from here");
        } catch (e: any) {
          toast.error(e?.message || "Rollback failed");
        }
      } else {
        toast.info("No checkpoint found — sending will continue from current tip");
      }
    },
    [findRollbackCheckpointForUserIndex, isLoading, sessionId, syncInputHeight]
  );

  const handleRegenerate = useCallback(
    async (assistantIndex: number) => {
      if (!sessionId || isLoading) return;
      const assistant = messages[assistantIndex];
      if (!assistant || assistant.role !== "assistant") return;

      // Find preceding user message
      let userIndex = -1;
      for (let i = assistantIndex - 1; i >= 0; i--) {
        if (messages[i].role === "user") {
          userIndex = i;
          break;
        }
      }
      if (userIndex < 0) {
        toast.error("No user message to regenerate from");
        return;
      }
      const query = messages[userIndex].content;

      let checkpointId: string | null = null;
      // Prefer parent of this assistant tip
      if (assistant.checkpoint_id) {
        try {
          const cps = await agentsAPI.listCheckpoints(sessionId);
          const tip = cps.find((c) => c.checkpoint_id === assistant.checkpoint_id);
          checkpointId = tip?.parent_checkpoint_id || null;
        } catch {
          /* ignore */
        }
      }
      if (!checkpointId) {
        checkpointId = await findRollbackCheckpointForUserIndex(userIndex);
      }

      // Optimistic truncate through user message (keep user, drop assistant+)
      setMessages((prev) => prev.slice(0, userIndex + 1));
      resetLiveState();

      if (checkpointId) {
        try {
          await agentsAPI.rollback(sessionId, checkpointId);
        } catch (e: any) {
          toast.error(e?.message || "Rollback failed");
          return;
        }
      }

      lastUserQueryRef.current = query;
      setActiveInFlightQuery(query);
      setExecuting(true);
      ignoreStaleRunEventsRef.current = false;
      activeExecutionIdRef.current = null;
      const ok = wsClientRef.current?.startRun(query);
      if (!ok) {
        toast.error("Failed to start regeneration");
        setExecuting(false);
        setActiveInFlightQuery(null);
      }
    },
    [findRollbackCheckpointForUserIndex, isLoading, messages, resetLiveState, sessionId, setExecuting]
  );

  /** Rewind — move the chat's active tip to a past checkpoint (from the branch
   * tree UI) without starting a new run; reloads the transcript up to that point. */
  const rewindToCheckpoint = useCallback(
    async (checkpointId: string) => {
      if (!sessionId) return;
      if (isLoading) {
        toast.error("Stop or wait for the current run before rewinding");
        return;
      }
      try {
        await agentsAPI.rollback(sessionId, checkpointId);
        resetLiveState();
        setSelectedStepBranch(null);
        setStepForkNote("");
        await refetchChat(sessionId);
        await loadCheckpointTree();
        bumpBranchRefresh();
        toast.success("Rewound to that checkpoint");
      } catch (e: any) {
        toast.error(e?.message || "Rewind failed");
      }
    },
    [bumpBranchRefresh, isLoading, loadCheckpointTree, refetchChat, resetLiveState, sessionId]
  );

  /** Fork — start a brand-new branch from a past checkpoint with a fresh
   * instruction/thought, leaving the original branch's checkpoints untouched.
   * If a run is currently active, it's preempted: the backend lets any
   * in-flight tool call finish, then stops that run and starts the fork —
   * we switch the live view over to the fork immediately, and silently drop
   * the superseded run's trailing `run.completed` when it arrives. */
  const forkFromCheckpoint = useCallback(
    async (checkpointId: string, note: string) => {
      if (!sessionId) return;
      if (!wsClientRef.current?.connected) {
        toast.error("Not connected — reconnecting…");
        connectWebSocket(sessionId);
        return;
      }
      const wasRunning = isLoading;
      const query = note.trim() || "Continue from this point.";
      lastUserQueryRef.current = query;
      setActiveInFlightQuery(query);
      setMessages((prev) => {
        const trimmed = [...prev];
        while (trimmed.length > 0 && trimmed[trimmed.length - 1]?.role === "assistant") {
          trimmed.pop();
        }
        return [
          ...trimmed,
          {
            message_id: `user_${Date.now()}`,
            role: "user",
            content: query,
            timestamp: Date.now(),
          },
        ];
      });
      resetLiveState();
      setExecuting(true);
      ignoreStaleRunEventsRef.current = false;
      activeExecutionIdRef.current = null;
      runFinalizedRef.current = false;
      const ok = wsClientRef.current.startRun(query, checkpointId);
      if (!ok) {
        toast.error("Failed to start new branch");
        setExecuting(false);
        setActiveInFlightQuery(null);
      } else {
        toast.success(
          wasRunning
            ? "Stopping the current run and switching to this branch…"
            : "Exploring a new branch from that checkpoint"
        );
      }
    },
    [connectWebSocket, isLoading, resetLiveState, sessionId, setExecuting]
  );

  useImperativeHandle(
    ref,
    () => ({
      rewindToCheckpoint,
      forkFromCheckpoint,
    }),
    [rewindToCheckpoint, forkFromCheckpoint]
  );

  const copyText = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied");
    } catch {
      toast.error("Copy failed");
    }
  };

  const showEmpty = messages.length === 0 && !activeInFlightQuery && !isLoading && !isChatLoading;

  /** Avoid duplicate AI bubbles when resuming an in-flight run (history + live panel). */
  const displayMessages = useMemo(
    () => excludeInFlightAssistantTurn(messages, isLoading),
    [messages, isLoading]
  );

  const showLiveAssistantPanel = Boolean(isLoading || activeInFlightQuery || pendingInterrupt);

  useEffect(() => {
    if (!isLoading) return;
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (lastUser && !activeInFlightQuery) {
      setActiveInFlightQuery(lastUser.content);
    }
  }, [activeInFlightQuery, isLoading, messages]);

  const toolStatusDotClass = (tool: ToolCallEvent) => {
    if (tool.status === "running") return "bg-yellow-400 animate-pulse";
    if (tool.status === "error" || tool.success === false) return "bg-red-500";
    return "bg-green-500";
  };

  const subagentStatusDotClass = (subagent: SubagentCallEvent) => {
    if (subagent.status === "running") return "bg-yellow-400 animate-pulse";
    if (subagent.status === "error" || subagent.success === false) return "bg-red-500";
    return "bg-green-500";
  };

  const toggleStepBranch = useCallback(
    (scopeId: string, stepIndex: number, checkpointId?: string) => {
      if (!checkpointId) return;
      setSelectedStepBranch((cur) => {
        const isSame = cur?.scopeId === scopeId && cur.stepIndex === stepIndex;
        if (!isSame) setStepForkNote("");
        return isSame ? null : { scopeId, stepIndex };
      });
    },
    []
  );

  const isStepBranchSelected = useCallback(
    (scopeId: string, stepIndex: number) =>
      selectedStepBranch?.scopeId === scopeId && selectedStepBranch.stepIndex === stepIndex,
    [selectedStepBranch]
  );

  const clearStepBranch = useCallback(() => {
    setSelectedStepBranch(null);
    setStepForkNote("");
  }, []);

  /** Inline rewind/fork widget rendered between the selected step and the next one. */
  const renderStepBranchPanel = (
    scopeId: string,
    stepIndex: number,
    checkpointId: string | undefined,
    checkpointNode: CheckpointTreeNode | undefined,
    detailOverride: string
  ) => {
    if (!checkpointId || !isStepBranchSelected(scopeId, stepIndex)) return null;

    const panelNode: CheckpointTreeNode = checkpointNode ?? {
      checkpoint_id: checkpointId,
      parent_checkpoint_id: null,
      timestamp: null,
      current_task: null,
      message_snippet: null,
      node: "unknown",
    };

    const handleRewind = async () => {
      if (isLoading) {
        toast.error("Stop or wait for the current run before rewinding");
        return;
      }
      setStepBranchBusy(true);
      try {
        await rewindToCheckpoint(checkpointId);
        clearStepBranch();
      } finally {
        setStepBranchBusy(false);
      }
    };

    const handleFork = async () => {
      setStepBranchBusy(true);
      try {
        await forkFromCheckpoint(checkpointId, stepForkNote);
        clearStepBranch();
      } finally {
        setStepBranchBusy(false);
      }
    };

    return (
      <div className="py-1">
        <CheckpointActionPanel
          node={panelNode}
          detailOverride={detailOverride}
          forkNote={stepForkNote}
          onForkNoteChange={setStepForkNote}
          busy={stepBranchBusy}
          onRewind={handleRewind}
          onFork={handleFork}
        />
      </div>
    );
  };

  /** Inline thinking + tool collapsibles (no outer Agent activity panel). */
  const renderAgentConversation = (
    stepsInput?: AgentStep[],
    metadata?: Message["metadata"],
    options?: { showBranchActions?: boolean; scopeId?: string }
  ) => {
    const steps = stepsInput?.length
      ? stepsInput
      : stepsFromLegacyMetadata(metadata as { reasoning?: string; tools?: ToolCallEvent[]; steps?: AgentStep[] });
    if (!steps.length) return null;

    const scopeId = options?.scopeId ?? "conversation";
    const showBranchActions = options?.showBranchActions !== false;
    const cpMap = showBranchActions ? mapStepsToCheckpoints(steps, checkpointTree) : new Map<number, string>();

    return (
      <div className="mb-3 w-full space-y-3">
        {steps.map((step, index) => {
          const stepSummary =
            step.type === "reasoning"
              ? step.content
              : step.type === "tool"
                ? step.tool?.task?.trim() || step.tool?.tool_name
                : step.type === "subagent"
                  ? step.subagent?.task?.trim() || step.subagent?.agent_name
                  : step.child?.task?.trim() || step.child?.agent_name;
          const stepCheckpointId = cpMap.get(index);
          const stepCheckpointNode = stepCheckpointId
            ? checkpointTree.find((n) => n.checkpoint_id === stepCheckpointId)
            : undefined;
          const stepSelected = isStepBranchSelected(scopeId, index);
          const branchPanel = showBranchActions
            ? renderStepBranchPanel(
                scopeId,
                index,
                stepCheckpointId,
                stepCheckpointNode,
                stepSummary || ""
              )
            : null;

          if (step.type === "reasoning") {
            return (
              <Fragment key={`reasoning-${index}`}>
                <StepBranchTarget
                  checkpointId={showBranchActions ? stepCheckpointId : undefined}
                  selected={stepSelected}
                  onSelect={() => toggleStepBranch(scopeId, index, stepCheckpointId)}
                >
                  <div className="text-xs whitespace-pre-wrap opacity-60 leading-relaxed italic px-1 py-0.5">
                    {step.content}
                  </div>
                </StepBranchTarget>
                {branchPanel}
              </Fragment>
            );
          }

          if (step.type === "subagent") {
            const { subagent } = step;
            if (!subagent) return null;
            const taskLabel = subagent.task?.trim() || `Sub-agent: ${subagent.agent_name}`;
            const showAgentName = Boolean(
              subagent.task?.trim() && subagent.task.trim() !== subagent.agent_name
            );
            return (
              <Fragment key={`${subagent.id || "subagent"}-${index}`}>
                <Collapsible
                  defaultOpen={subagent.status === "running"}
                  className="group/subagent w-full"
                >
                  <div className="flex items-start w-full">
                    <StepBranchTarget
                      checkpointId={showBranchActions ? stepCheckpointId : undefined}
                      selected={stepSelected}
                      onSelect={() => toggleStepBranch(scopeId, index, stepCheckpointId)}
                      className="flex-1 min-w-0"
                    >
                      <div className="flex items-center gap-2 py-1.5 text-xs">
                        <span
                          className={`h-2 w-2 shrink-0 rounded-full ${subagentStatusDotClass(subagent)}`}
                          aria-hidden
                        />
                        <Sparkles
                          className="h-3.5 w-3.5 shrink-0 opacity-60"
                          style={{ color: "var(--theme-accent)" }}
                        />
                        <span className="font-medium truncate flex-1 text-left">{taskLabel}</span>
                        {showAgentName && (
                          <span className="text-[10px] opacity-45 shrink-0">{subagent.agent_name}</span>
                        )}
                      </div>
                    </StepBranchTarget>
                    <CollapsibleTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 shrink-0 opacity-50 hover:opacity-100"
                        title="Show sub-agent details"
                      >
                        <ChevronRight className="h-3 w-3 group-data-[state=open]/subagent:hidden" />
                        <ChevronDown className="h-3 w-3 hidden group-data-[state=open]/subagent:inline" />
                      </Button>
                    </CollapsibleTrigger>
                  </div>
                  <CollapsibleContent>
                    <div className="pb-2 pt-1">
                      <SubagentConsole subagent={subagent} />
                    </div>
                  </CollapsibleContent>
                </Collapsible>
                {branchPanel}
              </Fragment>
            );
          }

          if (step.type === "child_agent") {
            const subagent = step.child;
            if (!subagent) return null;
            const taskLabel = subagent.task?.trim() || `Child: ${subagent.child_agent_id || subagent.agent_name}`;
            return (
              <Fragment key={`${subagent.id || "child"}-${index}`}>
                <Collapsible defaultOpen className="group/subagent w-full">
                  <div className="flex items-start w-full">
                    <StepBranchTarget
                      checkpointId={showBranchActions ? stepCheckpointId : undefined}
                      selected={stepSelected}
                      onSelect={() => toggleStepBranch(scopeId, index, stepCheckpointId)}
                      className="flex-1 min-w-0"
                    >
                      <div className="flex items-center gap-2 py-1.5 text-xs">
                        <span className={`h-2 w-2 shrink-0 rounded-full ${subagentStatusDotClass(subagent)}`} aria-hidden />
                        <Sparkles className="h-3.5 w-3.5 shrink-0 opacity-60" style={{ color: "var(--theme-accent)" }} />
                        <span className="font-medium truncate flex-1 text-left">{taskLabel}</span>
                        <span className="text-[10px] opacity-45 shrink-0">{subagent.child_agent_id || subagent.agent_name}</span>
                      </div>
                    </StepBranchTarget>
                    <CollapsibleTrigger asChild>
                      <Button type="button" variant="ghost" size="icon" className="h-7 w-7 shrink-0 opacity-50 hover:opacity-100" title="Show child details">
                        <ChevronRight className="h-3 w-3 group-data-[state=open]/subagent:hidden" />
                        <ChevronDown className="h-3 w-3 hidden group-data-[state=open]/subagent:inline" />
                      </Button>
                    </CollapsibleTrigger>
                  </div>
                  <CollapsibleContent>
                    <div className="pb-2 pt-1">
                      <SubagentConsole subagent={subagent} />
                    </div>
                  </CollapsibleContent>
                </Collapsible>
                {branchPanel}
              </Fragment>
            );
          }

          const { tool } = step;
          if (!tool) return null;
          const taskLabel = tool.task?.trim() || tool.tool_name;
          const showToolName = Boolean(tool.task?.trim() && tool.task.trim() !== tool.tool_name);
          return (
            <Fragment key={`${tool.id || "tool"}-${index}`}>
              <Collapsible defaultOpen={false} className="group/tool w-full">
                <div className="flex items-start w-full">
                  <StepBranchTarget
                    checkpointId={showBranchActions ? stepCheckpointId : undefined}
                    selected={stepSelected}
                    onSelect={() => toggleStepBranch(scopeId, index, stepCheckpointId)}
                    className="flex-1 min-w-0"
                  >
                    <div className="flex items-center gap-2 py-1.5 text-xs">
                      <span
                        className={`h-2 w-2 shrink-0 rounded-full ${toolStatusDotClass(tool)}`}
                        aria-hidden
                      />
                      <Wrench className="h-3.5 w-3.5 shrink-0 opacity-60" style={{ color: "var(--theme-accent)" }} />
                      <span className="font-medium truncate flex-1 text-left">{taskLabel}</span>
                      {showToolName && (
                        <span className="text-[10px] opacity-45 shrink-0">{tool.tool_name}</span>
                      )}
                    </div>
                  </StepBranchTarget>
                  <CollapsibleTrigger asChild>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 shrink-0 opacity-50 hover:opacity-100"
                      title="Show tool details"
                    >
                      <ChevronRight className="h-3 w-3 group-data-[state=open]/tool:hidden" />
                      <ChevronDown className="h-3 w-3 hidden group-data-[state=open]/tool:inline" />
                    </Button>
                  </CollapsibleTrigger>
                </div>
                <CollapsibleContent>
                  <div className="pl-6 pb-2 pt-1">
                    <div
                      className="rounded-md border px-3 py-2.5 space-y-3"
                      style={{
                        borderColor: "var(--theme-border)",
                        backgroundColor: "rgba(0,0,0,0.03)",
                      }}
                    >
                      {tool.tool_args != null && (
                        <div>
                          <div className="text-[10px] uppercase tracking-wide opacity-45 mb-1.5">
                            Parameters
                          </div>
                          <pre
                            className="font-mono text-[11px] leading-relaxed max-h-40 overflow-auto whitespace-pre-wrap opacity-90 rounded px-2 py-1.5"
                            style={{ backgroundColor: "var(--theme-card-bg)" }}
                          >
                            {formatReadablePayload(tool.tool_args)}
                          </pre>
                        </div>
                      )}
                      {tool.result && (
                        <div
                          className={tool.tool_args != null ? "pt-3 border-t" : ""}
                          style={tool.tool_args != null ? { borderColor: "var(--theme-border)" } : undefined}
                        >
                          <div className="text-[10px] uppercase tracking-wide opacity-45 mb-1.5">
                            Result
                          </div>
                          <pre
                            className="font-mono text-[11px] leading-relaxed max-h-56 overflow-auto whitespace-pre-wrap opacity-90 rounded px-2 py-1.5"
                            style={{ backgroundColor: "var(--theme-card-bg)" }}
                          >
                            {formatReadablePayload(tool.result)}
                          </pre>
                        </div>
                      )}
                      {!tool.tool_args && !tool.result && (
                        <p className="text-[11px] opacity-50 italic">No parameters or result recorded.</p>
                      )}
                    </div>
                  </div>
                </CollapsibleContent>
              </Collapsible>
              {branchPanel}
            </Fragment>
          );
        })}
      </div>
    );
  };

  return (
    <div
      className="relative flex h-full min-h-0 min-w-0 flex-col"
      style={{ backgroundColor: "var(--theme-main-bg)", color: "var(--theme-main-text)" }}
    >
      <div className="absolute inset-0 z-0">
        <LiquidEther
          colors={["#010101", "#fbe232", "#ffffff"]}
          mouseForce={6}
          cursorSize={60}
          resolution={0.4}
          autoDemo
          autoSpeed={0.2}
          autoIntensity={0.3}
          className="w-full h-full"
        />
      </div>

      <div className="relative z-10 flex h-full min-h-0 flex-col">
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-3 border-b backdrop-blur-sm"
          style={{ borderColor: "var(--theme-border)", backgroundColor: "rgba(255,254,255,0.85)" }}
        >
          <div className="min-w-0">
            <h1 className="text-sm font-semibold truncate">{chatTitle}</h1>
            <p className="text-[11px] opacity-60">
              {wsConnected ? "Connected" : sessionId ? "Connecting…" : "New chat"}
            </p>
          </div>
        </div>

        {/* Messages */}
        <div
          ref={scrollRef}
          className="flex-1 min-h-0 overflow-y-auto px-6 py-4"
          onScroll={(e) => {
            const el = e.currentTarget;
            const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
            setShouldAutoScroll(nearBottom);
          }}
        >
          {isChatLoading ? (
            <div
              data-testid="chat-loading"
              className="flex items-center justify-center min-h-[400px] w-full"
            >
              <Loader2
                className="h-8 w-8 animate-spin opacity-60"
                style={{ color: "var(--theme-accent)" }}
              />
            </div>
          ) : showEmpty ? (
            <div className="relative overflow-hidden w-full min-h-[600px] flex items-center justify-center p-8">
              <div className="relative z-10 w-full max-w-4xl p-8 text-center">
                 <img src="/brain_icon.svg" alt="PlatformAgent" width={80} height={80} className="h-20 w-20 mx-auto mb-4" />
                <h2 className="text-3xl md:text-4xl font-bold mb-4">{currentWelcomeMessage}</h2>
                <p className="text-lg mb-8 opacity-80">
                  {sessionId
                    ? "Continue the conversation by asking a question below"
                    : "Start typing below to create a new conversation"}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {suggestedQuestions.map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => void sendQuery(q)}
                      className="p-4 rounded-lg text-left transition-all hover:scale-105 hover:shadow-lg border backdrop-blur-sm"
                      style={{
                        backgroundColor: "var(--theme-card-bg)",
                        borderColor: "var(--theme-border)",
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <MessageSquare className="h-5 w-5 flex-shrink-0" style={{ color: "var(--theme-accent)" }} />
                        <span className="text-sm font-medium">{q}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6 w-full">
              {displayMessages.map((message, index) => {
                const isUser = message.role === "user";
                const answerContent = !isUser ? assistantAnswerContent(message) : "";
                const messageKey = message.message_id || `msg-${index}`;
                const branchesOpen = branchesOpenFor === messageKey;
                return (
                  <div
                    key={`${message.message_id || "msg"}-${index}`}
                    className={`flex w-full min-w-0 ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`flex gap-3 min-w-0 w-full max-w-[85%] ${isUser ? "flex-row-reverse" : ""}`}
                    >
                      <div
                        className="h-8 w-8 rounded-full flex items-center justify-center shrink-0"
                        style={{ backgroundColor: isUser ? "#010101" : "var(--theme-accent)" }}
                      >
                        {isUser ? (
                          <User className="h-4 w-4 text-white" />
                        ) : (
                           <img src="/brain_icon.svg" alt="" width={24} height={24} className="h-6 w-6" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div
                          className="rounded-2xl px-4 py-3 shadow-sm w-full"
                          style={{
                            backgroundColor: isUser
                              ? "var(--theme-user-bubble-bg)"
                              : "var(--theme-ai-bubble-bg)",
                            color: isUser
                              ? "var(--theme-user-bubble-text)"
                              : "var(--theme-ai-bubble-text)",
                            border: `1px solid ${isUser ? "var(--theme-user-bubble-bg)" : "var(--theme-border)"}`,
                          }}
                        >
                          {!isUser &&
                            renderAgentConversation(
                              message.metadata?.steps as AgentStep[] | undefined,
                              message.metadata,
                              { scopeId: messageKey }
                            )}
                          {!isUser && Boolean(message.metadata?.cache_hit) && (
                            <div className="mb-2">
                              <CacheHitBadge />
                            </div>
                          )}
                          {isUser ? (
                            <UserMessageBody content={message.content} />
                          ) : answerContent ? (
                            <div className={MARKDOWN_BUBBLE_CLASS}>
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={markdownLinkComponent}
                              >
                                {stabilizeMarkdownLinks(answerContent)}
                              </ReactMarkdown>
                            </div>
                          ) : null}
                          {!isUser && branchesOpen && (
                            <BubbleBranchTree
                              sessionId={sessionId}
                              refreshKey={branchRefreshKey}
                              onRewind={rewindToCheckpoint}
                              onFork={forkFromCheckpoint}
                            />
                          )}
                        </div>
                        <div className={`flex items-center gap-2 mt-2 px-2 ${isUser ? "justify-end" : "justify-start"}`}>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 rounded-md hover:bg-neutral-200"
                          onClick={() => copyText(message.content)}
                          title="Copy"
                        >
                          <Copy className="h-3.5 w-3.5" />
                        </Button>
                        {isUser ? (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 rounded-md hover:bg-neutral-200"
                            onClick={() => void handleEditResend(message, index)}
                            title="Edit & rewind"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                        ) : (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              className={`h-6 w-6 rounded-md hover:bg-neutral-200 ${branchesOpen ? "bg-neutral-200/80" : ""}`}
                              onClick={() =>
                                setBranchesOpenFor((cur) => (cur === messageKey ? null : messageKey))
                              }
                              title="Conversation branches"
                            >
                              <GitBranch className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6 rounded-md hover:bg-neutral-200"
                              onClick={() => void handleRegenerate(index)}
                              title="Regenerate"
                            >
                              <RefreshCw className="h-3.5 w-3.5" />
                            </Button>
                          </>
                        )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Live run UI */}
              {showLiveAssistantPanel && (
                <div className="space-y-4 w-full">
                  {activeInFlightQuery &&
                    displayMessages[displayMessages.length - 1]?.content !== activeInFlightQuery && (
                      <div className="flex w-full justify-end">
                        <div className="flex gap-3 flex-row-reverse max-w-[85%] min-w-0">
                          <div
                            className="h-8 w-8 rounded-full flex items-center justify-center shrink-0"
                            style={{ backgroundColor: "#010101" }}
                          >
                            <User className="h-4 w-4 text-white" />
                          </div>
                          <div
                            className="rounded-2xl px-4 py-3 shadow-sm"
                            style={{
                              backgroundColor: "var(--theme-user-bubble-bg)",
                              color: "var(--theme-user-bubble-text)",
                            }}
                          >
                            <UserMessageBody content={activeInFlightQuery} />
                          </div>
                        </div>
                      </div>
                    )}

                  <div className="flex w-full min-w-0 justify-start">
                    <div className="flex gap-3 min-w-0 w-full max-w-[85%]">
                      <div
                        className="h-8 w-8 rounded-full flex items-center justify-center shrink-0"
                        style={{ backgroundColor: "var(--theme-accent)" }}
                      >
                         <img src="/brain_icon.svg" alt="" width={24} height={24} className="h-6 w-6" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div
                          className="rounded-2xl px-4 py-3 shadow-sm w-full"
                          style={{
                            backgroundColor: "var(--theme-ai-bubble-bg)",
                            color: "var(--theme-ai-bubble-text)",
                            border: "1px solid var(--theme-border)",
                          }}
                        >
                      {renderAgentConversation(liveSteps, undefined, { scopeId: "live" })}
                      {liveCacheHit && (
                        <div className="mb-2">
                          <CacheHitBadge />
                        </div>
                      )}
                      {streamingOutput ? (
                        <div className={MARKDOWN_BUBBLE_CLASS}>
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={markdownLinkComponent}
                          >
                            {stabilizeMarkdownLinks(streamingOutput)}
                          </ReactMarkdown>
                          {isLoading && (
                            <span className="inline-block w-2 h-4 ml-1 bg-brand animate-pulse" />
                          )}
                        </div>
                      ) : (
                        !liveSteps.length &&
                        !pendingInterrupt && (
                          <div className="flex items-center gap-3 text-sm opacity-70">
                            <CustomLoader className="custom-loader--inline" />
                            {currentNode ? formatNodeStatus(currentNode) : "Thinking…"}
                          </div>
                        )
                      )}
                      {pendingInterrupt && (
                        <InterruptPrompt
                          embedded
                          interrupt={pendingInterrupt}
                          onSubmit={handleInterruptResume}
                          busy={interruptBusy}
                        />
                      )}
                        </div>
                      </div>
                    </div>
                  </div>
              </div>
              )}
            </div>
          )}
        </div>

        {/* Input */}
        <div
          className="border-t px-6 py-3 shadow-top-soft"
          style={{ borderColor: "rgba(163,163,163,0.4)", backgroundColor: "#fffeff" }}
        >
          {agentSettingsOpen && (
            <AgentSettingsPanel
              settings={
                tuneSettings || {
                  maxTokens: "",
                  responseFormat: "text",
                  temperature: "",
                  topK: "",
                  topP: "",
                  model: DEFAULT_MODEL,
                  instructions: "",
                  agentMode: "basic",
                }
              }
              onSettingsChange={(next) => onTuneSettingsChange?.(next)}
            />
          )}
          <AttachmentChipList attachments={pendingAttachments} onRemove={removePendingAttachment} />
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => {
              const files = e.target.files;
              if (files?.length) addAttachmentsFromFiles(files, "file");
              e.target.value = "";
            }}
          />
          <input
            ref={dirInputRef}
            type="file"
            multiple
            className="hidden"
            {...({ webkitdirectory: "", directory: "" } as React.InputHTMLAttributes<HTMLInputElement>)}
            onChange={(e) => {
              const files = e.target.files;
              if (files?.length) addAttachmentsFromFiles(files, "directory");
              e.target.value = "";
            }}
          />
          <div
            className="flex items-end gap-2 rounded-3xl border px-3 py-2.5 shadow-sm"
            style={{ borderColor: "var(--theme-border)", backgroundColor: "#f8f8f6" }}
          >
            <div className="flex shrink-0 items-center self-end pb-0.5">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9 rounded-2xl text-gray-500 hover:text-gray-800 hover:bg-white/70"
                    title="Attach"
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  side="top"
                  align="start"
                  sideOffset={8}
                  className="w-44 rounded-2xl border bg-[#fffeff] p-1.5 text-[#171717] shadow-lg"
                  style={{ borderColor: "var(--theme-border)" }}
                >
                  <DropdownMenuItem
                    className={ATTACH_MENU_ITEM_CLASS}
                    onClick={() => void pickAttachments("file")}
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    Attach files
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className={ATTACH_MENU_ITEM_CLASS}
                    onClick={() => void pickAttachments("directory")}
                  >
                    <FolderOpen className="mr-2 h-4 w-4" />
                    Attach folder
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-2xl text-gray-500 hover:text-gray-800 hover:bg-white/70"
                title="Voice input"
                onClick={() => toast.info("Voice not available in v1")}
              >
                <Mic className="h-4 w-4" />
              </Button>
            </div>

            <div
              ref={inputRef}
              contentEditable
              data-placeholder="Message PlatformAgent..."
              className="min-w-0 flex-1 overflow-y-auto whitespace-pre-wrap break-words px-2 py-1.5 text-sm leading-[22px] text-[#010101] outline-none"
              style={{
                minHeight: INPUT_MIN_HEIGHT_PX,
                maxHeight: INPUT_MAX_HEIGHT_PX,
              }}
              onInput={(e) => {
                setInput((e.target as HTMLDivElement).innerText);
                syncInputHeight();
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              suppressContentEditableWarning
            />

            <div className="flex shrink-0 items-center gap-0.5 self-end pb-0.5">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className={cn(
                  "h-9 w-9 rounded-2xl text-gray-500 hover:text-gray-800 hover:bg-white/70",
                  agentSettingsOpen && "bg-white/80 text-[#010101]"
                )}
                title="Agent settings"
                onClick={() => setAgentSettingsOpen((v) => !v)}
              >
                <Settings2 className="h-4 w-4" />
              </Button>
              {isLoading ? (
                <>
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    className="h-9 w-9 rounded-2xl text-yellow-700 hover:bg-yellow-100"
                    onClick={handlePause}
                    title="Pause (resumable)"
                  >
                    <Pause className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    type="button"
                    size="icon"
                    className="h-9 w-9 rounded-2xl bg-red-600 text-white hover:bg-red-700"
                    onClick={handleStop}
                    title="Stop"
                  >
                    <Square className="h-3.5 w-3.5 fill-current" />
                  </Button>
                </>
              ) : (
                <Button
                  type="button"
                  size="icon"
                  className="h-9 w-9 rounded-2xl text-white hover:opacity-90"
                  style={{ backgroundColor: "#010101" }}
                  onClick={handleSend}
                  title="Send"
                  disabled={!(input.trim() || pendingAttachments.length)}
                >
                  <Send className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
          <p className="mt-2 text-center text-[11px] opacity-50">
            PlatformAgent can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
});

export default EnhancedChatView;
