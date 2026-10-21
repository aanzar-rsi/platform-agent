import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  GitBranch,
  Loader2,
  MessageSquare,
  Pause,
  RefreshCw,
  Wrench,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { agentsAPI } from "@/lib/api";
import {
  CheckpointActionPanel,
  checkpointNodeStyle,
} from "@/components/CheckpointActionPanel";
import type { CheckpointTreeNode } from "@/types/backend";
const ROW_H_MIN = 36;
const COL_W = 34;
const PAD_X = 26;
const PAD_TOP = 22;
const LABEL_OFFSET = 14;
const LABEL_W_DEFAULT = 220;
const LABEL_W_EMBEDDED = 420;
const NODE_R = 7;
const LINE_H = 14;

function nodeStyle(node?: string | null) {
  return checkpointNodeStyle(node);
}
function nodeLabel(n: CheckpointTreeNode): string {
  return (n.current_task || n.message_snippet || nodeStyle(n.node).label).trim();
}

/** Rough word-wrap line count for label width (full text, no truncation). */
function labelLineCount(text: string, labelWidth: number): number {
  if (!text) return 1;
  const charsPerLine = Math.max(16, Math.floor((labelWidth - 18) / 5.4));
  const words = text.split(/\s+/);
  let lines = 1;
  let col = 0;
  for (const word of words) {
    const chunk = word.length + (col > 0 ? 1 : 0);
    if (col > 0 && col + chunk > charsPerLine) {
      lines += 1;
      col = word.length;
    } else {
      col += chunk;
    }
  }
  return lines;
}

type LaidOutNode = CheckpointTreeNode & {
  row: number;
  lane: number;
  children: string[];
  labelText: string;
  labelHeight: number;
  rowHeight: number;
  y: number;
};

function layout(nodes: CheckpointTreeNode[], labelWidth: number): { laid: LaidOutNode[]; laneCount: number; height: number } {
  const byId = new Map(nodes.map((n) => [n.checkpoint_id, n]));
  const childrenOf = new Map<string, string[]>();
  const roots: CheckpointTreeNode[] = [];
  for (const n of nodes) {
    if (n.parent_checkpoint_id && byId.has(n.parent_checkpoint_id)) {
      const list = childrenOf.get(n.parent_checkpoint_id) || [];
      list.push(n.checkpoint_id);
      childrenOf.set(n.parent_checkpoint_id, list);
    } else {
      roots.push(n);
    }
  }
  const byTime = (a: CheckpointTreeNode, b: CheckpointTreeNode) =>
    (a.timestamp ? Date.parse(a.timestamp) || 0 : 0) - (b.timestamp ? Date.parse(b.timestamp) || 0 : 0);
  roots.sort(byTime);
  for (const list of childrenOf.values()) {
    list.sort((a, b) => byTime(byId.get(a)!, byId.get(b)!));
  }

  const laid: LaidOutNode[] = [];
  let laneCounter = 0;
  let rowCounter = 0;

  const visit = (id: string, lane: number) => {
    const src = byId.get(id);
    if (!src) return;
    const labelText = nodeLabel(src);
    const lines = labelLineCount(labelText, labelWidth);
    const labelHeight = lines * LINE_H + 4;
    const rowHeight = Math.max(ROW_H_MIN, labelHeight + 14);
    const entry: LaidOutNode = {
      ...src,
      row: rowCounter++,
      lane,
      children: childrenOf.get(id) || [],
      labelText,
      labelHeight,
      rowHeight,
      y: 0,
    };
    laid.push(entry);
    const kids = childrenOf.get(id) || [];
    kids.forEach((childId, i) => {
      visit(childId, i === 0 ? lane : ++laneCounter);
    });
  };

  roots.forEach((root) => {
    visit(root.checkpoint_id, laneCounter);
    laneCounter += 1;
  });

  let yCursor = PAD_TOP;
  for (const entry of laid) {
    entry.y = yCursor + entry.rowHeight / 2;
    yCursor += entry.rowHeight;
  }

  return { laid, laneCount: Math.max(laneCounter, 1), height: yCursor + PAD_TOP };
}

interface CheckpointTreeProps {
  chatId: string | null;
  /** Bump to force a refetch (e.g. when the tab becomes active). */
  refreshSignal?: number;
  onRewind: (checkpointId: string) => Promise<void>;
  onFork: (checkpointId: string, note: string) => Promise<void>;
  /** Compact layout for embedding inside an assistant message bubble. */
  embedded?: boolean;
}

export default function CheckpointTree({
  chatId,
  refreshSignal,
  onRewind,
  onFork,
  embedded,
}: CheckpointTreeProps) {
  const [nodes, setNodes] = useState<CheckpointTreeNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [forkNote, setForkNote] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const labelWidth = embedded ? LABEL_W_EMBEDDED : LABEL_W_DEFAULT;

  const load = useCallback(async () => {
    if (!chatId) {
      setNodes([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const tree = await agentsAPI.listCheckpointTree(chatId);
      setNodes(tree);
    } catch (e: any) {
      setError(e?.message || "Failed to load branch tree");
    } finally {
      setLoading(false);
    }
  }, [chatId]);

  useEffect(() => {
    void load();
  }, [load, refreshSignal]);

  const { laid, laneCount, height } = useMemo(() => layout(nodes, labelWidth), [nodes, labelWidth]);
  const laidById = useMemo(() => new Map(laid.map((n) => [n.checkpoint_id, n])), [laid]);
  const selected = selectedId ? laidById.get(selectedId) : null;

  const width = Math.max(
    PAD_X * 2 + laneCount * COL_W + 40,
    PAD_X + (laneCount - 1) * COL_W + NODE_R + LABEL_OFFSET + labelWidth + PAD_X
  );

  const posOf = (n: LaidOutNode) => ({ x: PAD_X + n.lane * COL_W, y: n.y });

  const handleRewind = async (checkpointId: string) => {
    setBusyId(checkpointId);
    try {
      await onRewind(checkpointId);
      setSelectedId(null);
      await load();
    } finally {
      setBusyId(null);
    }
  };

  const handleFork = async (checkpointId: string) => {
    setBusyId(checkpointId);
    try {
      await onFork(checkpointId, forkNote);
      setSelectedId(null);
      setForkNote("");
    } finally {
      setBusyId(null);
    }
  };

  const selectedDetail = selected
    ? (() => {
        const task = selected.current_task?.trim();
        const snippet = selected.message_snippet?.trim();
        if (task && snippet && task !== snippet) return `${task}\n\n${snippet}`;
        return task || snippet || selected.labelText;
      })()
    : null;

  if (!chatId) {    return embedded ? null : (
      <p className="p-4 text-sm opacity-60">Start a chat to see its branch history.</p>
    );
  }

  return (
    <div className={embedded ? "flex flex-col gap-2" : "flex h-full min-h-0 flex-col gap-2"}>
      {!embedded && (
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-1.5 text-xs font-medium opacity-70">
            <GitBranch className="h-3.5 w-3.5" />
            {laid.length} checkpoint{laid.length === 1 ? "" : "s"}
            {laneCount > 1 ? ` · ${laneCount} branches` : ""}
          </div>
          <Button size="sm" variant="ghost" className="h-6 px-2 text-xs" onClick={() => void load()} disabled={loading}>
            {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
          </Button>
        </div>
      )}

      {error && <p className="px-1 text-xs text-red-600">{error}</p>}

      <div
        ref={containerRef}
        className={
          embedded
            ? "relative max-h-80 min-h-[7rem] overflow-auto rounded-lg border"
            : "relative flex-1 min-h-0 overflow-auto rounded-xl border"
        }
        style={{ borderColor: "var(--theme-border)" }}
      >
        {loading && laid.length === 0 ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-5 w-5 animate-spin opacity-50" />
          </div>
        ) : laid.length === 0 ? (
          <p className="p-4 text-sm opacity-60">No checkpoints yet — send a message to get started.</p>
        ) : (
          <svg width={width} height={height} className="block" style={{ minWidth: width }}>
            {laid.map((n) => {
              if (!n.parent_checkpoint_id) return null;
              const parent = laidById.get(n.parent_checkpoint_id);
              if (!parent) return null;
              const a = posOf(parent);
              const b = posOf(n);
              const path =
                a.x === b.x
                  ? `M ${a.x} ${a.y} L ${b.x} ${b.y}`
                  : `M ${a.x} ${a.y} C ${a.x} ${(a.y + b.y) / 2}, ${b.x} ${(a.y + b.y) / 2}, ${b.x} ${b.y}`;
              return (
                <path
                  key={`edge-${n.checkpoint_id}`}
                  d={path}
                  fill="none"
                  stroke="rgba(163,163,163,0.5)"
                  strokeWidth={1.6}
                />
              );
            })}

            {laid.map((n) => {
              const { x, y } = posOf(n);
              const style = nodeStyle(n.node);
              const Icon = style.icon;
              const isSelected = n.checkpoint_id === selectedId;
              const isActiveTip = Boolean(n.is_active_tip);
              const isAbandonedLeaf = Boolean(n.is_leaf && !isActiveTip);
              const labelTop = -n.labelHeight / 2;
              return (
                <g
                  key={n.checkpoint_id}
                  transform={`translate(${x}, ${y})`}
                  className="cursor-pointer"
                  onClick={() => {
                    setSelectedId(n.checkpoint_id);
                    setForkNote("");
                  }}
                >
                  {isSelected && <circle r={13} fill={style.color} opacity={0.18} />}
                  <circle r={7} fill={isActiveTip ? style.color : "#fffeff"} stroke={style.color} strokeWidth={2} />
                  {n.has_pending_interrupt && (
                    <g transform="translate(9, -9)">
                      <circle r={6} fill="#b45309" />
                      <Pause x={-3} y={-3} width={6} height={6} color="#fff" />
                    </g>
                  )}
                  <foreignObject x={LABEL_OFFSET} y={labelTop} width={labelWidth} height={n.labelHeight}>
                    <div
                      className="flex items-start gap-1 text-[10.5px] leading-[14px]"
                      style={{ color: "var(--theme-main-text)", width: labelWidth, minHeight: n.labelHeight }}
                    >
                      {n.node === "agent_node" || n.node === "armory_node" || n.node === "subagent_gate"
                         ? <img src="/brain_icon.svg" alt="" width={10} height={10} className="mt-[1px] h-2.5 w-2.5 shrink-0" />
                        : <Icon className="mt-[1px] h-2.5 w-2.5 shrink-0" style={{ color: style.color }} />}
                      <span className="min-w-0 flex-1 whitespace-normal break-words">{n.labelText}</span>
                      {isActiveTip && (
                        <span className="shrink-0 rounded bg-[#010101] px-1 py-[1px] text-[8px] font-semibold uppercase text-white">
                          tip
                        </span>
                      )}
                      {isAbandonedLeaf && (
                        <span className="shrink-0 rounded border px-1 py-[1px] text-[8px] font-medium uppercase opacity-50">
                          branch
                        </span>
                      )}
                    </div>
                  </foreignObject>
                </g>
              );
            })}
          </svg>
        )}
      </div>

      {selected && (
        <CheckpointActionPanel
          node={selected}
          detailOverride={selectedDetail || undefined}
          forkNote={forkNote}
          onForkNoteChange={setForkNote}
          busy={busyId === selected.checkpoint_id}
          onRewind={() => handleRewind(selected.checkpoint_id)}
          onFork={() => handleFork(selected.checkpoint_id)}
        />
      )}    </div>
  );
}
