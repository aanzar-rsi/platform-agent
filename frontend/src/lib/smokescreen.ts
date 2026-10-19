import type { SubagentProgressEvent } from "@/types/backend";

export type SmokeScriptId = "build";

type SmokeSink = {
  onNode(node: string | null): void;
  onReasoning(text: string): void;
  onOutput(text: string): void;
  onSubagentStarted(payload: { agent_name: string; task?: string; tool_args?: unknown }): void;
  onSubagentStep(payload: { agent_name: string; event: SubagentProgressEvent }): void;
  onSubagentFinished(payload: { agent_name: string; task?: string; result?: string; success?: boolean }): void;
  onToolStarted(payload: { tool_name: string; task?: string; tool_args?: unknown }): void;
  onToolFinished(payload: { tool_name: string; task?: string; tool_args?: unknown; result?: string; success?: boolean }): void;
};

export function matchSmokeScript(_message: string, _context: { chatId: string; hasAttachments: boolean }): SmokeScriptId | null {
  return null;
}

export async function playSmokeScript(_script: SmokeScriptId, sink: SmokeSink, signal: AbortSignal) {
  if (!signal.aborted) sink.onOutput("Smoke test complete.");
  return { stopped: signal.aborted };
}

export function markSmokeBuildCompleted(_chatId: string) {}
