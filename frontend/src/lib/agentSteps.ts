import type { AgentStep, ChildAgentCallEvent, SubagentCallEvent, SubagentProgressEvent, ToolCallEvent } from "@/types/backend";

export function formatReadablePayload(value: unknown) {
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

export function appendReasoningStep(steps: AgentStep[], text: string) {
  const last = steps[steps.length - 1];
  if (last?.type === "reasoning") last.content += text;
  else steps.push({ type: "reasoning", content: text });
}

export function appendToolStarted(steps: AgentStep[], tool: ToolCallEvent) {
  steps.push({ type: "tool", tool });
}

export function updateToolFinished(steps: AgentStep[], name: string, update: Partial<ToolCallEvent>) {
  const step = [...steps].reverse().find((item) => item.type === "tool" && item.tool.tool_name === name && item.tool.status === "running");
  if (step?.type === "tool") Object.assign(step.tool, update);
}

export function appendSubagentStarted(steps: AgentStep[], subagent: SubagentCallEvent) {
  steps.push({ type: "subagent", subagent });
}

export function appendSubagentProgress(steps: AgentStep[], name: string, event: SubagentProgressEvent) {
  const step = [...steps].reverse().find((item) => item.type === "subagent" && item.subagent.agent_name === name && item.subagent.status === "running");
  if (step?.type === "subagent") step.subagent.progress.push(event);
}

export function updateSubagentFinished(steps: AgentStep[], name: string, update: Partial<SubagentCallEvent>) {
  const step = [...steps].reverse().find((item) => item.type === "subagent" && item.subagent.agent_name === name && item.subagent.status === "running");
  if (step?.type === "subagent") Object.assign(step.subagent, update);
}

export function appendChildStarted(steps: AgentStep[], child: ChildAgentCallEvent) {
  steps.push({ type: "child_agent", child });
}

export function appendChildProgress(steps: AgentStep[], childId: string | undefined, event: SubagentProgressEvent) {
  if (!childId) return;
  const step = [...steps].reverse().find(
    (item) => item.type === "child_agent" && item.child.status === "running" &&
      item.child.child_agent_id === childId
  );
  if (step?.type !== "child_agent") return;
  const child = step.child;
  const last = child.progress[child.progress.length - 1];
  if (event.kind === "reasoning" && last?.kind === "reasoning" && !last.reasoningDone) {
    last.message = `${last.message || ""}${event.message || ""}`;
  } else {
    child.progress.push(event);
  }
}

export function updateChildFinished(steps: AgentStep[], childId: string | undefined, update: Partial<ChildAgentCallEvent>) {
  if (!childId) return;
  const step = [...steps].reverse().find(
    (item) => item.type === "child_agent" && item.child.status === "running" &&
      item.child.child_agent_id === childId
  );
  if (step?.type !== "child_agent") return;
  const last = step.child.progress[step.child.progress.length - 1];
  if (last?.kind === "reasoning" && !last.reasoningDone) {
    last.reasoningDone = true;
    if (!last.status) last.status = "completed";
    if (!last.step) last.step = "reasoning";
  }
  Object.assign(step.child, update);
}

export function stepsFromLegacyMetadata(metadata?: { reasoning?: string; tools?: ToolCallEvent[]; steps?: AgentStep[] }) {
  if (metadata?.steps?.length) return metadata.steps;
  const steps: AgentStep[] = [];
  if (metadata?.reasoning) steps.push({ type: "reasoning", content: metadata.reasoning });
  for (const tool of metadata?.tools || []) steps.push({ type: "tool", tool });
  return steps;
}
