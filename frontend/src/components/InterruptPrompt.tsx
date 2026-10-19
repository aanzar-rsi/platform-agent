import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Check, HelpCircle, IdCard, Pause, Wrench, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { PendingInterrupt } from "@/types/backend";

function formatArgs(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

const PRIMARY_BTN =
  "bg-[#010101] text-white hover:bg-[#262626] hover:text-white disabled:opacity-50";

interface InterruptPromptProps {
  interrupt: PendingInterrupt;
  /** Send a resume value back over the WebSocket (`run.resume`). */
  onSubmit: (value: unknown) => void;
  busy?: boolean;
  /** Render inside an assistant bubble (no outer page margins). */
  embedded?: boolean;
}

export default function InterruptPrompt({ interrupt, onSubmit, busy, embedded }: InterruptPromptProps) {
  const [note, setNote] = useState("");
  const [declineReason, setDeclineReason] = useState("");
  const [showDecline, setShowDecline] = useState(false);

  const { payload } = interrupt;
  const kind = interrupt.kind || payload.kind || "paused";

  const submitApprove = useCallback(
    () => onSubmit({ approved: true, note: note.trim() || undefined }),
    [note, onSubmit]
  );
  const submitDecline = useCallback(
    () => onSubmit({ approved: false, reason: declineReason.trim() || "User declined" }),
    [declineReason, onSubmit]
  );
  const submitText = useCallback(() => onSubmit(note.trim()), [note, onSubmit]);
  const submitResume = useCallback(
    () => onSubmit(note.trim() ? { note: note.trim() } : {}),
    [note, onSubmit]
  );

  const isConfirmKind = kind === "confirm_tool" || kind === "confirm_create_agent";

  useEffect(() => {
    if (busy || showDecline || !isConfirmKind) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Enter" || e.shiftKey || e.isComposing) return;
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === "TEXTAREA" || tag === "INPUT" || tag === "SELECT") return;
      e.preventDefault();
      e.stopPropagation();
      submitApprove();
    };

    window.addEventListener("keydown", onKeyDown, true);
    return () => window.removeEventListener("keydown", onKeyDown, true);
  }, [busy, isConfirmKind, showDecline, submitApprove]);

  let icon = <Pause className="h-4 w-4" />;
  let title = "Run paused";
  let accent = "var(--theme-accent)";

  if (kind === "confirm_tool") {
    icon = <Wrench className="h-4 w-4" />;
    title = `Confirm action: ${payload.tool_name || "tool"}`;
    accent = "#b45309";
  } else if (kind === "question") {
    icon = <HelpCircle className="h-4 w-4" />;
    title = "PlatformAgent needs more information";
  } else if (kind === "confirm_agent_studio") {
    icon = <HelpCircle className="h-4 w-4" />;
    title = "AgentStudio needs clarification";
  } else if (kind === "confirm_create_agent") {
    icon = <IdCard className="h-4 w-4" />;
    title = `Confirm new agent: ${payload.agent_card?.name || "untitled"}`;
    accent = "#b45309";
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={
        embedded
          ? "mt-3 overflow-hidden rounded-xl border"
          : "mx-6 mb-3 overflow-hidden rounded-2xl border shadow-sm"
      }
      style={{ borderColor: accent, backgroundColor: embedded ? "rgba(0,0,0,0.02)" : "#fffeff" }}
    >
      <div
        className="flex items-center gap-2 border-b px-4 py-2.5"
        style={{ backgroundColor: "rgba(180,83,9,0.06)", borderColor: "var(--theme-border)" }}
      >
        <span style={{ color: accent }}>{icon}</span>
        <span className="text-sm font-semibold text-gray-900">{title}</span>
        {kind === "paused" && (
          <span className="ml-auto shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-yellow-700"
            style={{ backgroundColor: "rgba(180,83,9,0.1)" }}>
            paused
          </span>
        )}
      </div>

      <div className="space-y-3 px-4 py-3">
        {kind === "paused" && (
          <>
            <p className="text-sm text-gray-700">
              Execution is paused. Resume as-is, or add a new instruction/thought for PlatformAgent to consider before continuing.
            </p>
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Optional — tell PlatformAgent what to do differently before resuming…"
              className="min-h-[70px] resize-none text-sm"
            />
            <div className="flex justify-end gap-2">
              <Button size="sm" disabled={busy} onClick={submitResume} className={PRIMARY_BTN}>
                <Check className="mr-1 h-3.5 w-3.5" />
                Resume
              </Button>
            </div>
          </>
        )}

        {kind === "confirm_tool" && (
          <>
            {payload.task && <p className="text-sm text-gray-700">{payload.task}</p>}
            {payload.tool_args != null && (
              <pre className="max-h-40 overflow-auto rounded-md border px-2.5 py-2 text-[11px] leading-relaxed text-gray-700"
                style={{ borderColor: "var(--theme-border)", backgroundColor: "var(--theme-card-bg)" }}>
                {formatArgs(payload.tool_args)}
              </pre>
            )}
            {payload.paused && (
              <p className="text-[11px] italic text-yellow-700">
                A pause was also requested — approving/declining will resume the run.
              </p>
            )}
            {showDecline ? (
              <div className="space-y-2">
                <Textarea
                  value={declineReason}
                  onChange={(e) => setDeclineReason(e.target.value)}
                  placeholder="Why are you declining? (optional)"
                  className="min-h-[60px] resize-none text-sm"
                />
                <div className="flex justify-end gap-2">
                  <Button size="sm" variant="ghost" disabled={busy} onClick={() => setShowDecline(false)}>
                    Back
                  </Button>
                  <Button size="sm" variant="destructive" disabled={busy} onClick={submitDecline}>
                    <X className="mr-1 h-3.5 w-3.5" />
                    Confirm decline
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex justify-end gap-2">
                <Button size="sm" variant="outline" disabled={busy} onClick={() => setShowDecline(true)}>
                  <X className="mr-1 h-3.5 w-3.5" />
                  Decline
                </Button>
                <Button size="sm" disabled={busy} onClick={submitApprove} className={PRIMARY_BTN}>
                  <Check className="mr-1 h-3.5 w-3.5" />
                  Approve &amp; run
                </Button>
              </div>
            )}
          </>
        )}

        {(kind === "question" || kind === "confirm_agent_studio") && (
          <>
            <p className="text-sm text-gray-700">{payload.prompt || payload.task || "PlatformAgent has a question."}</p>
            {Array.isArray(payload.questions) && payload.questions.length > 0 && (
              <ul className="list-disc space-y-0.5 pl-5 text-sm text-gray-700">
                {payload.questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            )}
            {Array.isArray(payload.options) && payload.options.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {payload.options.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => onSubmit(opt)}
                    disabled={busy}
                    className="rounded-full border px-3 py-1 text-xs font-medium text-gray-700 hover:bg-[#f8f8f6]"
                    style={{ borderColor: "var(--theme-border)" }}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Type your answer…"
              className="min-h-[70px] resize-none text-sm"
            />
            <div className="flex justify-end gap-2">
              <Button size="sm" disabled={busy || !note.trim()} onClick={submitText} className={PRIMARY_BTN}>
                <Check className="mr-1 h-3.5 w-3.5" />
                Send answer
              </Button>
            </div>
          </>
        )}

        {kind === "confirm_create_agent" && (
          <>
            <div className="flex items-center gap-2 text-sm text-gray-700">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-yellow-600" />
              <span>AgentStudio finished building this agent — save it to your subagents?</span>
            </div>
            {payload.agent_card && (
              <div className="rounded-md border px-3 py-2 text-[11px] leading-relaxed"
                style={{ borderColor: "var(--theme-border)", backgroundColor: "var(--theme-card-bg)" }}>
                <div className="font-semibold text-gray-800">{payload.agent_card.name}</div>
                {payload.agent_card.description && (
                  <p className="mt-0.5 text-gray-600">{payload.agent_card.description}</p>
                )}
                {payload.agent_card.function_name && (
                  <div className="mt-1 font-mono text-gray-500">{payload.agent_card.function_name}()</div>
                )}
              </div>
            )}
            {showDecline ? (
              <div className="space-y-2">
                <Textarea
                  value={declineReason}
                  onChange={(e) => setDeclineReason(e.target.value)}
                  placeholder="Why are you declining? (optional)"
                  className="min-h-[60px] resize-none text-sm"
                />
                <div className="flex justify-end gap-2">
                  <Button size="sm" variant="ghost" disabled={busy} onClick={() => setShowDecline(false)}>
                    Back
                  </Button>
                  <Button size="sm" variant="destructive" disabled={busy} onClick={submitDecline}>
                    <X className="mr-1 h-3.5 w-3.5" />
                    Confirm decline
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex justify-end gap-2">
                <Button size="sm" variant="outline" disabled={busy} onClick={() => setShowDecline(true)}>
                  <X className="mr-1 h-3.5 w-3.5" />
                  Don&apos;t save
                </Button>
                <Button size="sm" disabled={busy} onClick={submitApprove} className={PRIMARY_BTN}>
                  <Check className="mr-1 h-3.5 w-3.5" />
                  Save agent
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}
