/* Plan / algorithm / batch UI - module-level so expand/collapse state survives parent re-renders. */

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle,
  ChevronDown,
  Clock,
  FileText,
  GitBranch,
  Loader2,
  RotateCw,
  Sparkles,
  Target,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Message } from "@/types/backend";

export type StepStatus = 'pending' | 'running' | 'waiting' | 'success' | 'failed' | 'regenerated' | 'skipped';
export type CriticStatus = 'evaluating' | 'passed' | 'failed';
export type BatchType = 'initial' | 'replan' | 'recovery' | 'continuation';

/** One sequencer wave from `batch_prepared.execution_plan` (serial stack vs parallel row). */
export interface ExecutionPlanWave {
  mode: 'serial' | 'parallel';
  steps: Array<{ id: string | number; name?: string; tool?: string }>;
}

export interface BatchMeta {
  batchNum: number;
  type: BatchType;
  rationale?: string;
  criticState?: {
    status: 'reviewing' | 'done';
    stepsCount?: number;
    feedback?: string;
    hasFeedback?: boolean;
  };
  evaluationResult?: {
    targetReached: boolean;
    reasoning?: string;
    achievedSoFar?: string[];
    missingRequirements?: string[];
    recommendedAction?: string;
    iteration?: number;
  };
  dispatchMode?: 'serial' | 'parallel';
  /** Full ordered execution layout for this batch (from `batch_prepared`). */
  executionPlan?: ExecutionPlanWave[];
  /** Set when `batch_prepared` arrived; until then tiles stay full-width serial even if `executionPlan` is pre-filled. */
  executionPlanReady?: boolean;
}

export interface DecisionInfo {
  approach: 'planning' | 'direct';
  reason?: string;
}

/** Map persisted / backend status strings to UI step status (matches auto_memory._map_exec_status_to_ui). */
export function normalizePersistedStepStatus(raw: unknown): StepStatus {
  const s = String(raw ?? "").trim().toLowerCase();
  if (
    ["success", "succeeded", "succeed", "ok", "completed", "complete", "done", "finished", "pass", "passed"].includes(s)
  ) {
    return "success";
  }
  if (["failed", "failure", "error", "errored", "cancelled", "canceled", "aborted", "timeout", "timed_out", "timed out"].includes(s)) {
    return "failed";
  }
  if (["running", "started", "executing", "in_progress", "inprogress", "in-progress"].includes(s)) {
    return "running";
  }
  if (["skipped", "skip"].includes(s)) {
    return "skipped";
  }
  if (["waiting", "wait", "pending_input"].includes(s)) {
    return "waiting";
  }
  if (s === "regenerated") {
    return "regenerated";
  }
  if (["pending", "idle", "queued", "not_started", "not started"].includes(s)) {
    return "pending";
  }
  if (
    raw === "success" ||
    raw === "failed" ||
    raw === "running" ||
    raw === "waiting" ||
    raw === "skipped" ||
    raw === "regenerated" ||
    raw === "pending"
  ) {
    return raw as StepStatus;
  }
  return "pending";
}

export interface StepTile {
  key: string;
  name: string;
  status: StepStatus;
  absoluteIndex: number;
  batchNum: number;
  stepId?: string;
  description?: string;
  tool?: string;
  inputs?: any;
  reasoning?: string;
  result?: string;
  error?: string;
  executionTime?: number;
  evaluationPassed?: boolean;
  evaluationReason?: string;
  evaluationMode?: string;
  subroutineId?: string;
  requiresUserInput?: boolean;
  userInputReason?: string;
  dependencies?: (number | string)[];
  isRegenerated?: boolean;
  criticStatus?: CriticStatus;
}


/** Parsed JSON critic output for batch display (triggers + expandable body). */
type CriticFeedbackSummary = {
  qualityPassed: boolean | undefined;
  issues: string[];
  planAdjustments: string[];
  feedbackText: string | undefined;
  assessment: string | undefined;
  needsReplan: boolean | undefined;
} | null;

function stripOuterMarkdownJsonFence(s: string): string {
  let t = s.trim();
  const open = t.match(/^```(?:json)?\s*\n?/i);
  if (open) {
    t = t.slice(open[0].length);
    const close = t.lastIndexOf('```');
    if (close !== -1) t = t.slice(0, close);
    t = t.trim();
  }
  return t;
}

function tryParseJsonObjectLoose(s: string): unknown | null {
  const start = s.indexOf('{');
  if (start === -1) return null;
  let depth = 0;
  for (let i = start; i < s.length; i++) {
    const c = s[i];
    if (c === '{') depth++;
    else if (c === '}') {
      depth--;
      if (depth === 0) {
        try {
          return JSON.parse(s.slice(start, i + 1));
        } catch {
          return null;
        }
      }
    }
  }
  return null;
}

/** Lenient string value for broken/streamed JSON (reads until closing quote or end). */
function extractJsonStringValueLenient(text: string, key: string): string | undefined {
  const re = new RegExp(`"${key}"\\s*:\\s*"`, 'm');
  const m = text.match(re);
  if (!m || m.index === undefined) return undefined;
  let i = m.index + m[0].length;
  let out = '';
  while (i < text.length) {
    const c = text[i];
    if (c === '\\' && i + 1 < text.length) {
      const n = text[i + 1];
      if (n === 'n') out += '\n';
      else if (n === 'r') out += '\r';
      else if (n === 't') out += '\t';
      else out += n;
      i += 2;
      continue;
    }
    if (c === '"') break;
    out += c;
    i++;
  }
  const t = out.trim();
  return t.length > 0 ? t : undefined;
}

function extractPartialCriticFromText(text: string): CriticFeedbackSummary {
  const qp = text.match(/"quality_passed"\s*:\s*(true|false)\b/i);
  const qualityPassed = qp ? qp[1].toLowerCase() === 'true' : undefined;
  const assessment =
    extractJsonStringValueLenient(text, 'assessment') ||
    extractJsonStringValueLenient(text, 'summary');
  if (qualityPassed === undefined && !assessment) return null;
  return {
    qualityPassed,
    issues: [],
    planAdjustments: [],
    feedbackText: undefined,
    assessment,
    needsReplan: undefined,
  };
}

function summaryFromParsedObject(parsed: Record<string, unknown>): CriticFeedbackSummary {
  const p = parsed;
  const se = (p.step_evaluation ?? p.stepEvaluation ?? p) as Record<string, unknown>;
  const issues: string[] = Array.isArray(se?.issues_detected)
    ? (se.issues_detected as string[])
    : Array.isArray(p?.issues_detected) ? (p.issues_detected as string[]) : [];
  const planAdjustments: string[] = Array.isArray(se?.plan_adjustments_needed)
    ? (se.plan_adjustments_needed as string[])
    : Array.isArray(p?.plan_adjustments_needed) ? (p.plan_adjustments_needed as string[]) : [];
  const qualityPassed = typeof se?.quality_passed === 'boolean'
    ? se.quality_passed
    : typeof p?.quality_passed === 'boolean' ? (p.quality_passed as boolean) : undefined;
  const feedbackText = typeof p.feedback === 'string'
    ? p.feedback
    : typeof p.feedback_for_planner === 'string' ? (p.feedback_for_planner as string) : undefined;
  const assessment = typeof se?.assessment === 'string'
    ? se.assessment
    : typeof p?.assessment === 'string' ? (p.assessment as string) : undefined;
  const needsReplan = typeof p.needs_replan === 'boolean' ? p.needs_replan : undefined;
  return { qualityPassed, issues, planAdjustments, feedbackText, assessment, needsReplan };
}

function useCriticFeedbackModel(feedback: string) {
  const parsed = useMemo(() => {
    if (!feedback) return null;
    const stripped = stripOuterMarkdownJsonFence(feedback);
    try {
      return JSON.parse(stripped) as unknown;
    } catch {
      const loose = tryParseJsonObjectLoose(stripped);
      if (loose && typeof loose === 'object') return loose;
      return null;
    }
  }, [feedback]);

  const summary: CriticFeedbackSummary = useMemo(() => {
    if (!feedback) return null;
    const stripped = stripOuterMarkdownJsonFence(feedback);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return summaryFromParsedObject(parsed as Record<string, unknown>);
    }
    const partial = extractPartialCriticFromText(stripped);
    return partial;
  }, [feedback, parsed]);

  const issueCount = summary?.issues.length ?? 0;
  const adjustmentCount = summary?.planAdjustments.length ?? 0;
  return { summary, issueCount, adjustmentCount, feedback };
}

function CriticFeedbackBody({
  feedback,
  summary,
}: {
  feedback: string;
  summary: CriticFeedbackSummary;
}) {
  return (
    <div
      className="px-3 py-2 text-[11px] space-y-2 border-t"
      style={{ color: 'var(--theme-main-text)', borderColor: 'rgba(255,255,255,0.08)' }}
    >
      {summary ? (
        <>
          {summary.qualityPassed !== undefined && (
            <div className="font-medium" style={{ opacity: 0.9 }}>
              Quality check:{' '}
              <span className={summary.qualityPassed ? 'text-green-300' : 'text-yellow-200'}>
                {summary.qualityPassed ? 'passed' : 'needs attention'}
              </span>
            </div>
          )}
          {summary.assessment && (
            <div
              className="leading-relaxed break-words [overflow-wrap:anywhere]"
              style={{ opacity: 0.92 }}
            >
              {summary.assessment}
            </div>
          )}
          {summary.feedbackText && (
            <div className="italic break-words [overflow-wrap:anywhere]" style={{ opacity: 0.8 }}>{summary.feedbackText}</div>
          )}
          {summary.issues.length > 0 && (
            <div>
              <div className="font-medium mb-0.5 text-yellow-300/90">Issues detected</div>
              <ul className="list-disc list-inside space-y-0.5" style={{ opacity: 0.8 }}>
                {summary.issues.map((i, k) => <li key={k}>{i}</li>)}
              </ul>
            </div>
          )}
          {summary.planAdjustments.length > 0 && (
            <div>
              <div className="font-medium mb-0.5 text-neutral-300/90">Plan adjustments</div>
              <ul className="list-disc list-inside space-y-0.5" style={{ opacity: 0.8 }}>
                {summary.planAdjustments.map((a, k) => <li key={k}>{a}</li>)}
              </ul>
            </div>
          )}
          {summary.needsReplan !== undefined && (
            <div className="text-[10px]" style={{ opacity: 0.6 }}>
              Replan recommended: <span className="font-medium">{summary.needsReplan ? 'yes' : 'no'}</span>
            </div>
          )}
        </>
      ) : feedback.trim() ? (
        <pre
          className="whitespace-pre-wrap break-words [overflow-wrap:anywhere] text-[10px] leading-snug p-2 rounded max-w-full"
          style={{ backgroundColor: 'rgba(0,0,0,0.25)', color: 'var(--theme-main-text)', opacity: 0.75 }}
        >
          {feedback}
        </pre>
      ) : null}
    </div>
  );
}

type PlanTileGroup = { mode: 'serial' | 'parallel'; tiles: StepTile[] };

function normStepId(id: unknown): string {
  return String(id ?? '').trim();
}

/** One tile per logical step per batch — plan snapshots / persisted batches sometimes repeat rows after recovery. */
export function dedupeStepTiles(tiles: StepTile[]): StepTile[] {
  const m = new Map<string, StepTile>();
  for (const t of tiles) {
    const id =
      t.stepId && normStepId(t.stepId)
        ? `b${t.batchNum}:id:${normStepId(t.stepId)}`
        : `b${t.batchNum}:idx:${t.absoluteIndex}`;
    m.set(id, t);
  }
  return [...m.values()].sort((a, b) =>
    a.batchNum !== b.batchNum ? a.batchNum - b.batchNum : a.absoluteIndex - b.absoluteIndex
  );
}

/**
 * Do not infer parallel layout client-side. Parallel vs serial must come from the sequencer
 * (`batch_prepared` / `executionPlan`); otherwise steps stack serially until that arrives.
 */
export function inferExecutionPlanFromTiles(_tiles: StepTile[]): ExecutionPlanWave[] | undefined {
  return undefined;
}

function _depSignature(deps: unknown): string {
  if (!Array.isArray(deps) || deps.length === 0) return '[]';
  return JSON.stringify([...deps].map(d => String(d)).sort());
}

/**
 * When `planning_data.batches[].executionPlan` was never saved (older clients / merge gaps),
 * reconstruct a single parallel wave from persisted step rows + dispatchMode heuristics.
 */
export function inferExecutionPlanFromPersistedBatch(
  tiles: StepTile[],
  dispatchMode?: string | null,
): ExecutionPlanWave[] | undefined {
  if (dispatchMode === 'serial') return undefined;
  if (tiles.length < 2) return undefined;
  const ordered = [...tiles].sort((a, b) => a.absoluteIndex - b.absoluteIndex);
  const waveSteps = ordered.map(t => ({
    id: (t.stepId ?? String(t.absoluteIndex)) as string | number,
    name: t.name,
    tool: t.tool,
  }));
  if (dispatchMode === 'parallel') {
    return [{ mode: 'parallel', steps: waveSteps }];
  }
  const sigs = ordered.map(t => _depSignature(t.dependencies));
  if (!sigs.every(s => s === sigs[0])) return undefined;
  const shared = sigs[0];
  if (shared !== '[]') {
    return [{ mode: 'parallel', steps: waveSteps }];
  }
  if (ordered.length === 2) {
    return [{ mode: 'parallel', steps: waveSteps }];
  }
  return undefined;
}

function buildPlanTileGroups(tiles: StepTile[], executionPlan?: ExecutionPlanWave[]): PlanTileGroup[] {
  const plan = executionPlan?.length ? executionPlan : inferExecutionPlanFromTiles(tiles);
  if (!plan?.length) {
    return tiles.map(t => ({ mode: 'serial' as const, tiles: [t] }));
  }
  const byId = new Map<string, StepTile>();
  const byName = new Map<string, StepTile[]>();
  for (const t of tiles) {
    if (t.stepId) byId.set(normStepId(t.stepId), t);
    const nm = String(t.name ?? '').trim();
    if (nm) {
      const list = byName.get(nm) ?? [];
      list.push(t);
      byName.set(nm, list);
    }
  }
  const usedKeys = new Set<string>();
  const groups: PlanTileGroup[] = [];
  for (const wave of plan) {
    const mode = wave.mode === 'parallel' ? 'parallel' : 'serial';
    const waveTiles: StepTile[] = [];
    for (const s of wave.steps || []) {
      let tile = byId.get(normStepId(s.id));
      if (!tile && s.name) {
        const cand = byName.get(String(s.name).trim());
        if (cand?.length === 1) tile = cand[0];
      }
      // Skip if already placed (duplicate step ids in a wave or repeated across waves).
      if (tile && !usedKeys.has(tile.key)) {
        waveTiles.push(tile);
        usedKeys.add(tile.key);
      }
    }
    if (waveTiles.length > 0) groups.push({ mode, tiles: waveTiles });
  }
  const orphans = tiles.filter(t => !usedKeys.has(t.key)).sort((a, b) => a.absoluteIndex - b.absoluteIndex);
  for (const t of orphans) {
    groups.push({ mode: 'serial', tiles: [t] });
  }
  return groups;
}

function OverallEvaluationPanel({
  evaluationResult: ev,
}: {
  evaluationResult: NonNullable<BatchMeta['evaluationResult']>;
}) {
  const ok = ev.targetReached;
  const panel = ok
    ? {
        border: 'rgba(79, 70, 229, 0.42)',
        bg: 'rgba(79, 70, 229, 0.07)',
        headerBg: 'rgba(79, 70, 229, 0.13)',
      }
    : {
        border: 'rgba(217, 119, 6, 0.45)',
        bg: 'rgba(217, 119, 6, 0.08)',
        headerBg: 'rgba(217, 119, 6, 0.14)',
      };

  return (
    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}>
      <Collapsible
        defaultOpen={false}
        className="mb-3 rounded-xl border-2 text-[11px] overflow-hidden shadow-sm"
        style={{ backgroundColor: panel.bg, borderColor: panel.border }}
      >
        <CollapsibleTrigger asChild>
          <button
            type="button"
            className="group flex w-full items-center justify-between gap-2 px-3 py-2 text-left font-semibold text-xs transition-opacity hover:opacity-95"
            style={{ backgroundColor: panel.headerBg, color: 'var(--theme-main-text)' }}
          >
            <span className="flex min-w-0 flex-wrap items-center gap-2">
              {ok ? (
                <CheckCircle className="h-3.5 w-3.5 shrink-0 text-neutral-600 dark:text-neutral-400" />
              ) : (
                <AlertCircle className="h-3.5 w-3.5 shrink-0 text-yellow-600 dark:text-yellow-400" />
              )}
              <span>Agent evaluation</span>
              {ev.iteration !== undefined && ev.iteration !== null && (
                <span className="text-[10px] font-normal opacity-60">iter {ev.iteration}</span>
              )}
            </span>
            <ChevronDown className="h-3.5 w-3.5 shrink-0 opacity-70 transition-transform group-data-[state=open]:rotate-180" />
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div
            className="space-y-2 border-t px-3 py-2"
            style={{ borderColor: panel.border, color: 'var(--theme-main-text)' }}
          >
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="font-medium">
                {ok ? 'Goal reached' : `Not yet — ${ev.recommendedAction ?? 'replanning'}`}
              </span>
            </div>
            {ev.reasoning && (
              <div className="break-words text-[11px] italic leading-relaxed opacity-90 [overflow-wrap:anywhere]">
                {ev.reasoning}
              </div>
            )}
            {ev.achievedSoFar && ev.achievedSoFar.length > 0 && (
              <div>
                <div className="mb-0.5 text-[10px] font-medium text-neutral-700/90 dark:text-neutral-300/90">
                  Achieved
                </div>
                <ul className="list-inside list-disc space-y-0.5 break-words text-[10px] opacity-85">
                  {ev.achievedSoFar.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
            {!ok && ev.missingRequirements && ev.missingRequirements.length > 0 && (
              <div>
                <div className="mb-0.5 text-[10px] font-medium text-yellow-800/90 dark:text-yellow-200/90">
                  Missing
                </div>
                <ul className="list-inside list-disc space-y-0.5 break-words text-[10px] opacity-85">
                  {ev.missingRequirements.map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </motion.div>
  );
}

function StepTileRow({
  tile,
  expandedSteps,
  toggleExpand,
  fillHeight,
  parallelStepCount,
}: {
  tile: StepTile;
  expandedSteps: Set<string>;
  toggleExpand: (key: string) => void;
  /** Stretch to match sibling tiles in a parallel row */
  fillHeight?: boolean;
  /** Steps in this parallel wave; footer stacks below title only when more than two */
  parallelStepCount?: number;
}) {
  const isExpanded = expandedSteps.has(tile.key);
  const stackFooter = Boolean(fillHeight && parallelStepCount && parallelStepCount > 2);
  const base = 'rounded-md border overflow-hidden min-w-0 max-w-full';
  const color =
    tile.status === 'running'
      ? 'bg-neutral-900/15 border-neutral-700/40'
      : tile.status === 'waiting'
        ? 'bg-yellow-900/20 border-yellow-700/50'
        : tile.status === 'success'
          ? 'bg-green-900/15 border-green-700/40'
          : tile.status === 'failed'
            ? 'bg-red-900/15 border-red-700/40'
            : tile.status === 'regenerated'
              ? 'bg-yellow-900/25 border-yellow-700/60'
              : tile.status === 'skipped'
                ? 'bg-neutral-900/40 border-neutral-600/60'
                : 'bg-neutral-200/80 border-neutral-300/60';
  const Icon =
    tile.status === 'running'
      ? Loader2
      : tile.status === 'waiting'
        ? Clock
        : tile.status === 'success'
          ? CheckCircle
          : tile.status === 'failed'
            ? AlertCircle
            : tile.status === 'regenerated'
              ? Target
              : FileText;

  const iconColor =
    tile.status === 'running'
      ? 'text-neutral-400 animate-spin'
      : tile.status === 'waiting'
        ? 'text-yellow-400'
        : tile.status === 'success'
          ? 'text-green-400'
          : tile.status === 'failed'
            ? 'text-red-400'
            : tile.status === 'regenerated'
              ? 'text-yellow-400'
              : 'text-neutral-400';
  const iconCls = `h-3 w-3 shrink-0 mt-0.5 ${iconColor}`;

  const stepNumCls = `w-5 h-5 rounded-full text-[10px] font-medium flex items-center justify-center shrink-0 ${tile.status === 'running'
    ? 'bg-neutral-700/40 text-neutral-100 border border-neutral-400/70 shadow-[0_0_0_1px_rgba(82,82,82,0.5)]'
    : tile.status === 'waiting'
      ? 'bg-yellow-700/40 text-yellow-100 border border-yellow-400/70'
      : tile.status === 'success'
        ? 'bg-green-700/50 text-gray-900'
        : tile.status === 'failed'
          ? 'bg-red-700/50 text-red-200'
          : tile.status === 'regenerated'
            ? 'bg-yellow-700/50 text-yellow-200'
            : tile.status === 'skipped'
              ? 'bg-neutral-700/70 text-neutral-200'
              : 'bg-neutral-700/50 text-neutral-300'
  } ${tile.status === 'running' ? 'animate-pulse' : ''}`;

  const titleCls = `flex-1 min-w-0 text-left break-words [overflow-wrap:anywhere] ${tile.status === 'skipped' ? 'line-through opacity-70' : ''
  }`;

  const badgeRow = (
    <div className="flex items-center gap-1 shrink-0">
      <Badge
        variant={tile.status === 'failed' ? 'destructive' : 'secondary'}
        className={`text-[10px] h-4 px-1.5 shrink-0 border-0 font-medium ${tile.status === 'running'
          ? 'bg-neutral-600 text-white'
          : tile.status === 'waiting'
            ? 'bg-yellow-500 text-neutral-900'
            : tile.status === 'success'
              ? 'bg-green-600 text-white'
              : tile.status === 'failed'
                ? 'bg-red-600 text-white'
                : tile.status === 'regenerated'
                  ? 'bg-yellow-600 text-neutral-900'
                  : tile.status === 'skipped'
                    ? 'bg-neutral-500 text-white'
                    : 'bg-neutral-700 text-white'
        }`}
      >
        {tile.status === 'pending' && 'Pending'}
        {tile.status === 'running' && 'Running'}
        {tile.status === 'waiting' && 'Waiting'}
        {tile.status === 'success' && 'Success'}
        {tile.status === 'failed' && 'Failed'}
        {tile.status === 'regenerated' && 'Regenerated'}
        {tile.status === 'skipped' && 'Skipped'}
      </Badge>
      <ChevronDown
        className={`h-3 w-3 transition-transform shrink-0 ${isExpanded ? 'rotate-180' : ''}`}
        style={{ color: 'var(--theme-main-text)', opacity: 0.5 }}
      />
    </div>
  );

  const executionTimeEl =
    tile.executionTime !== undefined && tile.executionTime > 0 ? (
      <span className="text-[10px] tabular-nums shrink-0" style={{ color: 'var(--theme-main-text)', opacity: 0.6 }}>
        {tile.executionTime.toFixed(1)}s
      </span>
    ) : null;

  const criticEl =
    tile.criticStatus === 'evaluating' ? (
      <span className="flex items-center gap-0.5 text-[10px] text-neutral-400 shrink-0">
        <Loader2 className="h-2.5 w-2.5 animate-spin" />
        <span>Critic</span>
      </span>
    ) : null;

  const btnTint =
    tile.status === 'running'
      ? 'bg-neutral-900/20 hover:bg-neutral-900/30'
      : tile.status === 'waiting'
        ? 'bg-yellow-900/20 hover:bg-yellow-900/30'
        : tile.status === 'success'
          ? 'bg-green-900/20 hover:bg-green-900/30'
          : tile.status === 'failed'
            ? 'bg-red-900/20 hover:bg-red-900/30'
            : tile.status === 'regenerated'
              ? 'bg-yellow-900/20 hover:bg-yellow-900/30'
              : 'bg-neutral-200/40 hover:bg-neutral-200/60';

  const serialLikeHeader = (
    <>
      <div className={stepNumCls}>{tile.absoluteIndex + 1}</div>
      <div className="flex items-start gap-1.5 flex-1 min-w-0">
        <Icon className={iconCls} />
        <div className={`${titleCls} text-xs`} style={{ color: 'var(--theme-main-text)' }}>
          {tile.name}
        </div>
      </div>
      <div className="flex items-center gap-1.5 shrink-0 py-0.5">
        {executionTimeEl}
        {criticEl}
        {badgeRow}
      </div>
    </>
  );

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -8 }}
      className={`${base} ${color} w-full min-w-0 ${fillHeight && stackFooter ? 'h-full min-h-0 flex flex-col' : ''}`}
    >
      <button
        onClick={() => toggleExpand(tile.key)}
        className={
          fillHeight && stackFooter
            ? `w-full min-w-0 max-w-full flex-1 min-h-0 px-2 py-2 flex flex-col gap-2 items-stretch transition-colors text-left ${btnTint}`
            : `w-full min-w-0 max-w-full px-2 py-1.5 flex items-start gap-2 transition-colors text-left text-xs ${btnTint}`
        }
      >
        {fillHeight && stackFooter ? (
          <>
            <div className="flex items-start gap-2 w-full min-w-0 shrink-0">
              <div className={stepNumCls}>{tile.absoluteIndex + 1}</div>
              <Icon className={iconCls} />
              <div
                className={`${titleCls} text-xs leading-snug pt-0.5`}
                style={{ color: 'var(--theme-main-text)' }}
              >
                {tile.name}
              </div>
            </div>
            <div
              className="mt-auto flex flex-wrap items-center gap-x-2 gap-y-1 w-full min-w-0 pt-1.5 border-t shrink-0"
              style={{ borderColor: 'var(--theme-border)' }}
            >
              {executionTimeEl}
              {criticEl}
              <div className="ml-auto shrink-0">{badgeRow}</div>
            </div>
          </>
        ) : (
          serialLikeHeader
        )}
      </button>

      {isExpanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className={`px-3 py-3 space-y-3 text-sm min-w-0 max-w-full ${fillHeight ? 'shrink-0' : ''}`}
          style={{
            borderTop: '1px solid var(--theme-border)',
            color: 'var(--theme-main-text)',
          }}
        >
          {tile.stepId && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-medium" style={{ color: 'var(--theme-main-text)', opacity: 0.6 }}>Step ID:</span>
              <code className="text-xs px-1.5 py-0.5 rounded break-all" style={{ backgroundColor: 'var(--theme-card-bg)', color: 'var(--theme-main-text)' }}>{tile.stepId}</code>
            </div>
          )}

          {tile.description && (
            <div className="min-w-0">
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--theme-main-text)' }}>Description</div>
              <div className="break-words [overflow-wrap:anywhere]" style={{ color: 'var(--theme-main-text)' }}>{tile.description}</div>
            </div>
          )}

          {tile.tool && (
            <div className="min-w-0">
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--theme-main-text)' }}>Tool</div>
              <code className="text-xs px-2 py-1 rounded break-all" style={{ backgroundColor: 'var(--theme-card-bg)', color: 'var(--theme-main-text)' }}>{tile.tool}</code>
              {tile.inputs && Object.keys(tile.inputs).length > 0 && (
                <div className="mt-2 min-w-0">
                  <div className="text-xs font-medium mb-1" style={{ color: 'var(--theme-main-text)' }}>Inputs</div>
                  <pre className="text-xs p-2 rounded overflow-x-auto whitespace-pre-wrap break-words [overflow-wrap:anywhere] max-w-full" style={{ backgroundColor: 'var(--theme-card-bg)', color: 'var(--theme-main-text)' }}>
                    {JSON.stringify(tile.inputs, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          {tile.reasoning && (
            <div className="min-w-0">
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--theme-main-text)' }}>Reasoning</div>
              <div className="break-words [overflow-wrap:anywhere] italic" style={{ color: 'var(--theme-main-text)' }}>{tile.reasoning}</div>
            </div>
          )}

          {tile.result && (
            <div className="min-w-0">
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--theme-main-text)' }}>Result</div>
              <div className="p-2 rounded border break-words [overflow-wrap:anywhere]" style={{ borderColor: 'var(--theme-border)', backgroundColor: 'rgba(34,197,94,0.08)', color: 'var(--theme-main-text)' }}>
                {tile.result}
              </div>
            </div>
          )}

          {tile.error && (
            <div className="min-w-0">
              <div className="text-xs font-medium text-red-500 mb-1">Error</div>
              <div className="font-mono text-xs p-2 rounded border break-words [overflow-wrap:anywhere]" style={{ color: 'var(--theme-main-text)', borderColor: 'rgba(239,68,68,0.4)', backgroundColor: 'rgba(239,68,68,0.08)' }}>
                {tile.error}
              </div>
            </div>
          )}

          {tile.evaluationPassed !== undefined && (
            <div className="min-w-0">
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--theme-main-text)' }}>Evaluation</div>
              <div className="flex items-start gap-2">
                {tile.evaluationPassed ? (
                  <CheckCircle className="h-4 w-4 text-green-600 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                )}
                <div className="flex-1 min-w-0">
                  <div className={tile.evaluationPassed ? 'text-green-800' : 'text-red-600'}>
                    {tile.evaluationPassed ? 'Passed' : 'Failed'}
                    {tile.evaluationMode && ` (${tile.evaluationMode})`}
                  </div>
                  {tile.evaluationReason && (
                    <div className="text-xs mt-1 break-words [overflow-wrap:anywhere]" style={{ color: 'var(--theme-main-text)' }}>{tile.evaluationReason}</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {tile.dependencies && tile.dependencies.length > 0 && (
            <div>
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--theme-main-text)' }}>Dependencies</div>
              <div className="flex flex-wrap gap-1">
                {tile.dependencies.map(dep => (
                  <Badge key={dep} variant="outline" className="text-xs">
                    Step {dep + 1}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {tile.requiresUserInput && (
            <div className="min-w-0">
              <div className="text-xs font-medium text-neutral-400 mb-1">Requires User Input</div>
              <div className="break-words [overflow-wrap:anywhere]" style={{ color: 'var(--theme-main-text)' }}>{tile.userInputReason || 'User input needed'}</div>
            </div>
          )}

          {tile.isRegenerated && (
            <div className="flex items-center gap-2 text-yellow-600 text-xs">
              <Target className="h-3 w-3 shrink-0" />
              <span>This step was regenerated during replanning</span>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}

export function PlanTiles({
  tiles,
  executionPlan,
  className,
}: {
  tiles: StepTile[];
  executionPlan?: ExecutionPlanWave[];
  className?: string;
}) {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(() => new Set());

  const groups = useMemo(
    () => buildPlanTileGroups(tiles, executionPlan),
    [tiles, executionPlan]
  );

  return (
    <div className={`w-full min-w-0 max-w-full space-y-2 ${className || ''}`}>
      <AnimatePresence initial={false}>
        {groups.map((group, gi) => {
          const isParallel = group.mode === 'parallel' && group.tiles.length > 1;
          const compactParallel = isParallel && group.tiles.length <= 2;
          const groupKeys = group.tiles.map(t => t.key);
          const toggleExpand = (key: string) => {
            setExpandedSteps(prev => {
              const next = new Set(prev);
              if (isParallel) {
                const anyExpanded = groupKeys.some(k => next.has(k));
                if (anyExpanded) {
                  groupKeys.forEach(k => next.delete(k));
                } else {
                  groupKeys.forEach(k => next.add(k));
                }
              } else {
                if (next.has(key)) next.delete(key);
                else next.add(key);
              }
              return next;
            });
          };
          return (
            <div
              key={`grp-${gi}-${group.tiles.map(t => t.key).join('|')}`}
              className={`flex w-full min-w-0 max-w-full flex-col gap-1 items-stretch ${isParallel ? 'overflow-x-hidden' : ''}`}
            >
              <div
                className={
                  isParallel
                    ? 'grid w-full min-w-0 max-w-full gap-2 items-stretch'
                    : 'flex w-full min-w-0 max-w-full flex-col gap-1 items-stretch'
                }
                style={
                  isParallel
                    ? {
                        width: '100%',
                        gridTemplateColumns: `repeat(${group.tiles.length}, minmax(0, 1fr))`,
                      }
                    : undefined
                }
              >
                {group.tiles.map(tile => (
                  <div
                    key={tile.key}
                    className={
                      isParallel
                        ? compactParallel
                          ? 'min-w-0 w-full flex flex-col [min-width:0]'
                          : 'min-w-0 w-full min-h-0 h-full flex flex-col'
                        : 'min-w-0 w-full max-w-full flex flex-col [min-width:0]'
                    }
                  >
                    <StepTileRow
                      tile={tile}
                      expandedSteps={expandedSteps}
                      toggleExpand={toggleExpand}
                      fillHeight={isParallel}
                      parallelStepCount={isParallel ? group.tiles.length : undefined}
                    />
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

  // ─── BatchSection ─────────────────────────────────────────────────
  // Renders a single batch (header + critic feedback + step tiles + evaluation).
  // Used by both the live execution panel and the archived planning_data display.
function BatchSection({
    meta,
    tiles,
    isActive,
    defaultCollapsed = false,
    beginnerView = false,
  }: {
    meta: BatchMeta;
    tiles: StepTile[];
    isActive?: boolean;
    defaultCollapsed?: boolean;
    /** Hide planner rationale & critic panels for a simpler view */
    beginnerView?: boolean;
  }) {
    const [collapsed, setCollapsed] = useState(defaultCollapsed);
    const [detailPanel, setDetailPanel] = useState<'reasoning' | 'critic' | null>(null);

    const criticFeedbackStr =
      !beginnerView && !collapsed && meta.criticState?.status === 'done' && meta.criticState.hasFeedback && meta.criticState.feedback
        ? meta.criticState.feedback
        : '';
    const hasRationale = Boolean(!beginnerView && !collapsed && meta.rationale);
    const showReasoningCriticRow = hasRationale || Boolean(criticFeedbackStr);
    const criticModel = useCriticFeedbackModel(criticFeedbackStr);

    useEffect(() => {
      if (collapsed) setDetailPanel(null);
    }, [collapsed]);

    const batchLabel =
      meta.type === 'initial' ? 'Initial Plan'
      : meta.type === 'replan' ? `Replan ${meta.batchNum - 1}`
      : meta.type === 'recovery' ? 'Recovery'
      : `Continuation ${meta.batchNum - 1}`;

    // Commanding color scheme per batch type
    const theme = meta.type === 'initial'
      ? { bg: 'rgba(251,226,50,0.12)', border: 'rgba(251,226,50,0.45)', headBg: 'rgba(251,226,50,0.22)', badgeBg: '#fbe232', badgeText: '#010101' }
      : meta.type === 'recovery'
        ? { bg: 'rgba(38,38,38,0.12)', border: 'rgba(38,38,38,0.45)', headBg: 'rgba(38,38,38,0.22)', badgeBg: '#262626', badgeText: '#fff' }
        : meta.type === 'replan'
          ? { bg: 'rgba(155,130,0,0.12)', border: 'rgba(155,130,0,0.45)', headBg: 'rgba(155,130,0,0.22)', badgeBg: '#756200', badgeText: '#fff' }
          : { bg: 'rgba(82,82,82,0.12)', border: 'rgba(82,82,82,0.45)', headBg: 'rgba(82,82,82,0.22)', badgeBg: '#525252', badgeText: '#fff' };

    const TypeIcon = meta.type === 'recovery' ? AlertCircle
      : meta.type === 'replan' ? RotateCw
        : meta.type === 'continuation' ? ArrowRight
          : Sparkles;

    // Don't render empty batch cards while the plan is still being assembled.
    // Show only once steps exist, or critic data arrived (run evaluation is a separate panel).
    if (tiles.length === 0 && !meta.criticState) return null;

    const layoutExecutionPlan =
      meta.executionPlanReady === true && meta.executionPlan?.length
        ? meta.executionPlan
        : undefined;

    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-3 w-full min-w-0 max-w-full rounded-xl overflow-hidden border-2 shadow-sm"
        style={{ borderColor: theme.border, backgroundColor: theme.bg }}
      >
        {/* Commanding Batch Header */}
        <button
          type="button"
          className="flex w-full min-w-0 max-w-full items-start gap-2 overflow-hidden px-3 py-2 text-left transition-colors"
          style={{ backgroundColor: theme.headBg }}
          onClick={() => setCollapsed(c => !c)}
        >
          <div className="flex min-w-0 max-w-full flex-1 items-center gap-2">
            <span
              className="px-2 py-0.5 rounded-md text-xs font-bold tracking-wide shadow-sm shrink-0"
              style={{ backgroundColor: theme.badgeBg, color: theme.badgeText }}
            >
              BATCH {meta.batchNum}
            </span>
            <TypeIcon className="h-3.5 w-3.5 shrink-0" style={{ color: theme.badgeBg }} />
            <div className="min-w-0 max-w-full flex-1">
              <span className="text-sm font-semibold leading-tight" style={{ color: 'var(--theme-main-text)' }}>
                {batchLabel}
              </span>
            </div>
            {tiles.length > 0 && (
              <span className="text-[10px] shrink-0" style={{ color: 'var(--theme-main-text)', opacity: 0.6 }}>
                {tiles.length} step{tiles.length !== 1 ? 's' : ''}
              </span>
            )}
            {isActive && (
              <span className="flex items-center gap-1 text-[10px] shrink-0" style={{ color: 'var(--theme-accent)' }}>
                <div className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                Active
              </span>
            )}
          </div>
          <ChevronDown
            className={`h-4 w-4 mt-0.5 shrink-0 transition-transform ${collapsed ? '' : 'rotate-180'}`}
            style={{ color: 'var(--theme-main-text)', opacity: 0.5 }}
          />
        </button>

        {/* Reasoning + Critic: side-by-side toggles; only one open at a time */}
        {showReasoningCriticRow && (
          <div className="border-t" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
            <div
              className={`flex min-w-0 ${hasRationale && criticFeedbackStr ? 'divide-x divide-white/10' : ''}`}
            >
              {hasRationale && (
                <button
                  type="button"
                  className="group flex min-w-0 flex-1 items-center justify-between gap-1.5 px-2 py-1.5 text-left text-[10px] font-medium transition-colors hover:bg-black/10"
                  style={{ color: 'var(--theme-main-text)' }}
                  onClick={() => setDetailPanel(p => (p === 'reasoning' ? null : 'reasoning'))}
                >
                  <span className="opacity-80">Reasoning</span>
                  <ChevronDown
                    className={`h-3 w-3 shrink-0 opacity-50 transition-transform duration-200 ${detailPanel === 'reasoning' ? 'rotate-180' : ''}`}
                  />
                </button>
              )}
              {criticFeedbackStr && (
                <button
                  type="button"
                  className="group flex min-w-0 flex-1 items-center justify-between gap-1 px-2 py-1.5 text-left text-[10px] font-medium transition-colors hover:bg-black/10"
                  style={{ color: 'var(--theme-main-text)', opacity: 0.8 }}
                  onClick={() => setDetailPanel(p => (p === 'critic' ? null : 'critic'))}
                >
                  <div className="flex min-w-0 flex-1 items-center gap-1.5 flex-wrap pr-0.5">
                    <FileText className="h-3 w-3 shrink-0" />
                    <span className="font-medium">Critic feedback</span>
                    {criticModel.summary?.qualityPassed !== undefined && (
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          criticModel.summary.qualityPassed
                            ? 'bg-green-600/30 text-green-300'
                            : 'bg-yellow-600/30 text-yellow-200'
                        }`}
                      >
                        {criticModel.summary.qualityPassed ? 'passed' : 'issues'}
                      </span>
                    )}
                    {criticModel.issueCount > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-yellow-700/30 text-yellow-200 text-[10px]">
                        {criticModel.issueCount} issue{criticModel.issueCount !== 1 ? 's' : ''}
                      </span>
                    )}
                    {criticModel.adjustmentCount > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-neutral-700/30 text-neutral-200 text-[10px]">
                        {criticModel.adjustmentCount} adjustment{criticModel.adjustmentCount !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                  <ChevronDown
                    className={`h-3 w-3 shrink-0 transition-transform ${detailPanel === 'critic' ? 'rotate-180' : ''}`}
                    style={{ opacity: 0.5 }}
                  />
                </button>
              )}
            </div>
            {detailPanel === 'reasoning' && meta.rationale && (
              <div
                className="px-3 pb-2.5 text-left text-[10px] italic leading-relaxed break-words [overflow-wrap:anywhere] border-t"
                style={{ color: 'var(--theme-main-text)', opacity: 0.75, borderColor: 'rgba(255,255,255,0.08)' }}
              >
                {meta.rationale}
              </div>
            )}
            {detailPanel === 'critic' && criticFeedbackStr && (
              <CriticFeedbackBody feedback={criticModel.feedback} summary={criticModel.summary} />
            )}
          </div>
        )}

        {!collapsed && (
          <div className="w-full min-w-0 max-w-full px-2 pt-2 pb-4">
            <PlanTiles tiles={tiles} executionPlan={layoutExecutionPlan} />
          </div>
        )}
      </motion.div>
    );
  }

  // ─── AlgorithmCollapsible ─────────────────────────────────────────
  // decision (planning vs direct) + `algorithm_generator` high-level steps from `plan_start`.
  // Batch plan rationales stay in each BatchSection header.
  // Default collapsed.
function AlgorithmCollapsible({
    decision,
    algorithm,
  }: {
    decision?: DecisionInfo | null;
    algorithm?: string[];
  }) {
    const [open, setOpen] = useState(false);
    const steps = Array.isArray(algorithm) ? algorithm.map(s => String(s).trim()).filter(Boolean) : [];
    if (!decision && steps.length === 0) return null;

    return (
      <div
        className="mb-3 min-w-0 max-w-full rounded-lg border overflow-hidden"
        style={{ borderColor: 'rgba(139,92,246,0.4)', backgroundColor: 'rgba(139,92,246,0.08)' }}
      >
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          className="w-full min-w-0 flex items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-black/10"
        >
          <GitBranch className="h-3.5 w-3.5 text-neutral-400 shrink-0" />
          <div className="min-w-0 flex-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
            <span className="text-xs font-semibold shrink-0" style={{ color: 'var(--theme-main-text)' }}>
              Agent algorithm
            </span>
            {decision && (
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium shrink-0 ${
                decision.approach === 'planning'
                  ? 'bg-neutral-600/40 text-neutral-100'
                  : 'bg-teal-600/40 text-teal-100'
              }`}>
                {decision.approach === 'planning' ? 'Planning' : 'Direct'}
              </span>
            )}
            {steps.length > 0 && (
              <span className="text-[10px] shrink-0" style={{ color: 'var(--theme-main-text)', opacity: 0.6 }}>
                {steps.length} high-level step{steps.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <ChevronDown
            className={`h-3.5 w-3.5 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
            style={{ color: 'var(--theme-main-text)', opacity: 0.5 }}
          />
        </button>
        {open && (
          <div className="px-3 pb-3 pt-1 space-y-3 text-[11px] min-w-0" style={{ color: 'var(--theme-main-text)' }}>
            {decision && (
              <div>
                <div
                  className="px-1.5 py-0.5 rounded text-[10px] font-medium inline-block mb-1"
                  style={{
                    backgroundColor: decision.approach === 'planning' ? 'rgba(147,51,234,0.35)' : 'rgba(13,148,136,0.35)',
                  }}
                >
                  Route decision
                </div>
                <div className="break-words" style={{ opacity: 0.9 }}>
                  <span className="font-medium">
                    {decision.approach === 'planning' ? 'Use planning' : 'Direct answer'}
                  </span>
                  {decision.reason && (
                    <span style={{ opacity: 0.8 }}> — {decision.reason}</span>
                  )}
                </div>
              </div>
            )}
            {steps.length > 0 && (
              <div className="min-w-0">
                <div className="px-1.5 py-0.5 rounded text-[10px] font-medium inline-block mb-1" style={{ backgroundColor: 'rgba(82,82,82,0.35)' }}>
                  Generated algorithm
                </div>
                <ol className="list-decimal list-outside pl-4 space-y-1 break-words" style={{ opacity: 0.88 }}>
                  {steps.map((line, i) => (
                    <li key={i} className="pl-0.5">{line}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ─── BatchedPlanDisplay ───────────────────────────────────────────
  // Unified batched plan view: algorithm + batches with tiles.
  // Works for both the live execution panel and archived assistant messages.
export function BatchedPlanDisplay({
    batchMetas: metas,
    stepTiles: tiles,
    decision,
    algorithm,
    currentBatchNum,
    evaluationResult,
    viewMode = "advanced",
  }: {
    batchMetas: BatchMeta[];
    stepTiles: StepTile[];
    decision?: DecisionInfo | null;
    /** High-level steps from `algorithm_generator` (`plan_start`). */
    algorithm?: string[];
    currentBatchNum?: number;
    /** Final run evaluation (single panel below all batches). */
    evaluationResult?: BatchMeta['evaluationResult'] | null;
    viewMode?: "beginner" | "advanced";
  }) {
    const beginner = viewMode === "beginner";
    return (
      <div className="w-full min-w-0 max-w-full overflow-x-hidden">
        {!beginner && <AlgorithmCollapsible decision={decision ?? null} algorithm={algorithm} />}
        {metas.map(meta => (
          <BatchSection
            key={meta.batchNum}
            meta={meta}
            tiles={tiles.filter(t => t.batchNum === meta.batchNum)}
            isActive={currentBatchNum !== undefined && currentBatchNum === meta.batchNum}
            beginnerView={beginner}
          />
        ))}
        {!beginner && evaluationResult ? <OverallEvaluationPanel evaluationResult={evaluationResult} /> : null}
      </div>
    );
  }

  // ─── ArchivedPlanDisplay ──────────────────────────────────────────
  // Reconstructs the batched plan view from a persisted `planning_data` metadata
  // blob on an assistant message. Works whether or not `batches` were persisted
  // (falls back to grouping by step.batchNum).
export function ArchivedPlanDisplay({
    planningData,
    viewMode = "advanced",
  }: {
    planningData: NonNullable<NonNullable<Message['metadata']>['planning_data']>;
    viewMode?: "beginner" | "advanced";
  }) {
    const { tiles, metas, decision, algorithm, overallEvaluation } = useMemo(() => {
      const pd = planningData as Record<string, unknown>;
      const topEval = (pd.evaluation ?? null) as BatchMeta['evaluationResult'] | null | undefined;
      const batchesRaw = (Array.isArray(pd.batches) ? pd.batches : []) as Array<Record<string, unknown>>;
      const goalReached = Boolean(topEval?.targetReached);
      const execTime =
        typeof planningData.execution_time === 'number' ? planningData.execution_time : 0;

      const hasNested = batchesRaw.some(
        b => Array.isArray(b.steps) && (b.steps as unknown[]).length > 0
      );

      const rowToTile = (s: Record<string, unknown>, i: number): StepTile => {
        const absoluteIndex = typeof s.index === 'number' ? (s.index as number) : i;
        const batchNum = typeof s.batchNum === 'number' && (s.batchNum as number) > 0 ? (s.batchNum as number) : 1;
        let status = normalizePersistedStepStatus(s.status);
        const errRaw = s.error;
        const hasErr = errRaw != null && String(errRaw).trim() !== '' && String(errRaw).toLowerCase() !== 'null';
        if (status === 'pending' && goalReached && execTime > 0 && !hasErr) {
          status = 'success';
        }
        return {
          key: `archived-${batchNum}-${absoluteIndex}-${String(s.name ?? '')}`,
          name: String(s.name ?? 'Step'),
          status,
          absoluteIndex,
          batchNum,
          stepId: s.stepId as string | undefined,
          description: s.description as string | undefined,
          tool: s.tool as string | undefined,
          inputs: s.inputs,
          reasoning: s.reasoning as string | undefined,
          result: s.result as string | undefined,
          error: s.error as string | undefined,
          executionTime: s.executionTime as number | undefined,
          evaluationPassed: s.evaluationPassed as boolean | undefined,
          evaluationReason: s.evaluationReason as string | undefined,
          evaluationMode: s.evaluationMode as string | undefined,
          subroutineId: s.subroutineId as string | undefined,
          requiresUserInput: s.requiresUserInput as boolean | undefined,
          userInputReason: s.userInputReason as string | undefined,
          dependencies: s.dependencies as (number | string)[] | undefined,
          isRegenerated: s.isRegenerated as boolean | undefined,
          criticStatus: s.criticStatus as CriticStatus | undefined,
        } as StepTile;
      };

      let rebuiltTiles: StepTile[] = [];
      if (hasNested) {
        let g = 0;
        for (const b of batchesRaw) {
          const bnum = (typeof b.batchNum === 'number' && b.batchNum > 0 ? b.batchNum : 1) as number;
          for (const raw of (b.steps as Record<string, unknown>[]) || []) {
            const s = { ...raw, batchNum: (raw.batchNum as number) ?? bnum } as Record<string, unknown>;
            rebuiltTiles.push(rowToTile(s, g++));
          }
        }
      } else {
        const planSteps = (planningData.plan_steps_state ?? []) as Record<string, unknown>[];
        rebuiltTiles = planSteps.map((s, i) => rowToTile(s, i));
      }

      rebuiltTiles = dedupeStepTiles(rebuiltTiles);

      let rebuiltMetas: BatchMeta[] = [];
      if (batchesRaw.length > 0) {
        rebuiltMetas = batchesRaw.map((b) => {
          const epRaw =
            (b.executionPlan as BatchMeta['executionPlan'] | undefined) ??
            (b.execution_plan as BatchMeta['executionPlan'] | undefined);
          const rawReady =
            (b.executionPlanReady as boolean | undefined) ??
            (b.execution_plan_ready as boolean | undefined);
          let ep = Array.isArray(epRaw) && epRaw.length > 0 ? epRaw : undefined;
          let executionPlanReady =
            rawReady === false
              ? false
              : ep
                ? true
                : undefined;
          const batchNum = b.batchNum as number;
          const dispatchMode = b.dispatchMode as BatchMeta['dispatchMode'];
          if (!ep && executionPlanReady !== false) {
            const batchTiles = rebuiltTiles.filter(t => t.batchNum === batchNum);
            const inferred = inferExecutionPlanFromPersistedBatch(batchTiles, dispatchMode ?? null);
            if (inferred?.length) {
              ep = inferred;
              executionPlanReady = true;
            }
          }
          return {
            batchNum,
            type: b.type as BatchType,
            rationale: b.rationale as string | undefined,
            criticState: b.criticState as BatchMeta['criticState'],
            dispatchMode,
            executionPlan: ep,
            executionPlanReady,
          };
        });
      } else {
        const uniqueBatchNums = Array.from(new Set(rebuiltTiles.map(t => t.batchNum))).sort((a, b) => a - b);
        rebuiltMetas = uniqueBatchNums.map(n => ({
          batchNum: n,
          type: (n === 1 ? 'initial' : 'continuation') as BatchType,
        }));
        if (rebuiltMetas.length === 0) {
          rebuiltMetas = [{ batchNum: 1, type: 'initial' }];
        }
        rebuiltMetas = rebuiltMetas.map(meta => {
          if (meta.executionPlanReady === false) return meta;
          if (meta.executionPlan?.length) return meta;
          const batchTiles = rebuiltTiles.filter(t => t.batchNum === meta.batchNum);
          const inferred = inferExecutionPlanFromPersistedBatch(batchTiles, meta.dispatchMode ?? null);
          if (!inferred?.length) return meta;
          return { ...meta, executionPlan: inferred, executionPlanReady: true };
        });
      }

      const mergedOverall: BatchMeta['evaluationResult'] | null =
        topEval ??
        (batchesRaw.length > 0
          ? ((batchesRaw[batchesRaw.length - 1] as { evaluationResult?: BatchMeta['evaluationResult'] })
              .evaluationResult ?? null)
          : null);

      const dec: DecisionInfo | null =
        planningData.decision ??
        (pd.reasoning != null && String(pd.reasoning).length > 0
          ? {
              approach: planningData.used_planning === false ? 'direct' : 'planning',
              reason: String(pd.reasoning),
            }
          : null);

      const rawAlgo = planningData.algorithm;
      const archivedAlgo =
        Array.isArray(rawAlgo) && rawAlgo.length > 0
          ? rawAlgo.map(s => (typeof s === 'string' ? s.trim() : String(s).trim())).filter(Boolean)
          : undefined;

      return {
        tiles: rebuiltTiles,
        metas: rebuiltMetas,
        decision: dec,
        algorithm: archivedAlgo,
        overallEvaluation: mergedOverall,
      };
    }, [planningData]);

    // Fallback for very old messages that only have plan_steps (strings), no plan_steps_state
    if (tiles.length === 0 && Array.isArray(planningData.plan_steps) && planningData.plan_steps.length > 0) {
      const legacyName = (row: unknown, idx: number) =>
        typeof row === "string" ? row : (row as { name?: string })?.name ?? `Step ${idx + 1}`;
      const ranToCompletion =
        typeof planningData.execution_time === "number" &&
        planningData.execution_time > 0 &&
        planningData.used_planning !== false;
      const legacyTiles: StepTile[] = planningData.plan_steps.map((row: unknown, idx: number) => ({
        key: `archived-legacy-${idx}-${legacyName(row, idx)}`,
        name: legacyName(row, idx),
        status: ranToCompletion ? "success" : "pending",
        absoluteIndex: idx,
        batchNum: 1,
      }));
      const rawAlgo = planningData.algorithm;
      const archivedAlgo =
        Array.isArray(rawAlgo) && rawAlgo.length > 0
          ? rawAlgo.map(s => (typeof s === 'string' ? s.trim() : String(s).trim())).filter(Boolean)
          : undefined;
      const ev = (planningData.evaluation ?? null) as BatchMeta['evaluationResult'] | null;
      return (
        <BatchedPlanDisplay
          batchMetas={[{ batchNum: 1, type: 'initial' }]}
          stepTiles={legacyTiles}
          decision={null}
          algorithm={archivedAlgo}
          evaluationResult={ev}
          viewMode={viewMode}
        />
      );
    }

    if (tiles.length === 0 && metas.length === 0) return null;

    return (
      <BatchedPlanDisplay
        batchMetas={metas}
        stepTiles={tiles}
        decision={decision}
        algorithm={algorithm}
        evaluationResult={overallEvaluation}
        viewMode={viewMode}
      />
    );
  }
