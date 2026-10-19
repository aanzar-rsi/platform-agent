import type { AgentStep, CheckpointTreeNode, Message, ToolCallEvent } from "@/types/backend";

type HistoryMessage = Partial<Message> & { role?: string; content?: string };

export function mapHistoryMessages(history: HistoryMessage[], _executionHistory: Array<Record<string, unknown>> = []): Message[] {
  return history
    .filter((message) => message.role && typeof message.content === "string")
    .map((message, index) => ({
      ...message,
      message_id: message.message_id || `history-${index}`,
      role: message.role!,
      content: message.content!,
    }));
}

export function assistantAnswerContent(message: Message) {
  return message.content;
}

export function freezeAssistantTurn(messages: Message[], assistant: Pick<Message, "content" | "checkpoint_id" | "metadata">) {
  const next = [...messages];
  if (next[next.length - 1]?.role === "assistant") next.pop();
  next.push({
    message_id: `assistant-${Date.now()}`,
    role: "assistant",
    content: assistant.content,
    checkpoint_id: assistant.checkpoint_id,
    metadata: assistant.metadata,
  });
  return next;
}

export function excludeInFlightAssistantTurn(messages: Message[], isLoading: boolean) {
  return isLoading && messages[messages.length - 1]?.role === "assistant" ? messages.slice(0, -1) : messages;
}

export function mapStepsToCheckpoints(steps: AgentStep[], checkpoints: CheckpointTreeNode[]) {
  const map = new Map<number, string>();
  for (let index = 0; index < steps.length && index < checkpoints.length; index += 1) {
    map.set(index, checkpoints[index].checkpoint_id);
  }
  return map;
}

export function toolFromHistory(value: unknown): ToolCallEvent | null {
  return value && typeof value === "object" ? value as ToolCallEvent : null;
}
