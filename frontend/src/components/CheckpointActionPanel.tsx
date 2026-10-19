import {
  GitBranch,
  GitFork,
  MessageSquare,
  RefreshCw,
  Rewind,
  Wrench,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { CheckpointTreeNode } from "@/types/backend";

export const CHECKPOINT_PRIMARY_BTN =
  "bg-[#010101] text-white hover:bg-[#262626] hover:text-white disabled:opacity-50";

const NODE_STYLE: Record<string, { color: string; icon: typeof MessageSquare; label: string }> = {
  start: { color: "#525252", icon: MessageSquare, label: "User message" },
  agent_node: { color: "#fbe232", icon: MessageSquare, label: "Agent" },
  tool_node: { color: "#3d9b7a", icon: Wrench, label: "Tool" },
  subagent_node: { color: "#fbe232", icon: MessageSquare, label: "Subagent" },
  subagent_gate: { color: "#fbe232", icon: MessageSquare, label: "Subagent (confirmed)" },
  context_selector: { color: "#525252", icon: RefreshCw, label: "Context select" },
  unknown: { color: "#737373", icon: GitBranch, label: "Step" },
};

export function checkpointNodeStyle(node?: string | null) {
  return NODE_STYLE[node || "unknown"] || NODE_STYLE.unknown;
}

export function checkpointDetailText(
  node: Pick<CheckpointTreeNode, "current_task" | "message_snippet" | "node">,
  fallback?: string
): string | null {
  const task = node.current_task?.trim();
  const snippet = node.message_snippet?.trim();
  if (task && snippet && task !== snippet) return `${task}\n\n${snippet}`;
  const fromNode = task || snippet;
  if (fromNode) return fromNode;
  const trimmedFallback = fallback?.trim();
  return trimmedFallback || null;
}

interface CheckpointActionPanelProps {
  node: Pick<
    CheckpointTreeNode,
    "checkpoint_id" | "node" | "current_task" | "message_snippet" | "is_active_tip" | "is_leaf"
  >;
  detailOverride?: string;
  forkNote: string;
  onForkNoteChange: (value: string) => void;
  busy?: boolean;
  onRewind: () => void | Promise<void>;
  onFork: () => void | Promise<void>;
  className?: string;
}

/** Rewind / fork card shared by the branch graph and per-step menus. */
export function CheckpointActionPanel({
  node,
  detailOverride,
  forkNote,
  onForkNoteChange,
  busy,
  onRewind,
  onFork,
  className,
}: CheckpointActionPanelProps) {
  const style = checkpointNodeStyle(node.node);
  const Icon = style.icon;
  const detail = checkpointDetailText(node, detailOverride);

  return (
    <div
      className={className ?? "rounded-xl border p-3 text-xs shadow-sm"}
      style={{ borderColor: "var(--theme-border)", backgroundColor: "var(--theme-card-bg)" }}
      onPointerDown={(e) => e.stopPropagation()}
    >
      <div className="mb-1.5 flex items-center gap-1.5 font-semibold" style={{ color: style.color }}>
        {node.node === "agent_node" || node.node === "subagent_node" || node.node === "subagent_gate"
           ? <img src="/brain_icon.svg" alt="" width={14} height={14} className="h-3.5 w-3.5" />
          : <Icon className="h-3.5 w-3.5" />}
        {style.label}
        {node.is_active_tip && <span className="opacity-50">· active tip</span>}
        {node.is_leaf && !node.is_active_tip && (
          <span className="opacity-50">· abandoned branch</span>
        )}
      </div>
      {detail && <p className="mb-2 whitespace-pre-wrap break-words opacity-70">{detail}</p>}
      <Textarea
        value={forkNote}
        onChange={(e) => onForkNoteChange(e.target.value)}
        placeholder="Optional — describe the new direction to explore from here…"
        className="mb-2 min-h-[56px] resize-none text-xs"
      />
      <div className="flex justify-end gap-1.5">
        <Button
          size="sm"
          variant="outline"
          className="h-7 px-2 text-[11px]"
          disabled={busy}
          onClick={() => void onRewind()}
        >
          <Rewind className="mr-1 h-3 w-3" />
          Rewind here
        </Button>
        <Button
          size="sm"
          className={`h-7 px-2 text-[11px] ${CHECKPOINT_PRIMARY_BTN}`}
          disabled={busy}
          onClick={() => void onFork()}
        >
          <GitFork className="mr-1 h-3 w-3" />
          Fork &amp; explore
        </Button>
      </div>
    </div>
  );
}
