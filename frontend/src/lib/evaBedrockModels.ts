/** Bedrock model IDs (aligned with `client/utils/llm_tools.py` bedrock_models) for per-node dropdowns. */
export const EVA_BEDROCK_MODEL_IDS: string[] = [
  "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "us.anthropic.claude-opus-4-1-20250805-v1:0",
  "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
  "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
  "anthropic.claude-3-haiku-20240307-v1:0",
  "us.meta.llama4-maverick-17b-instruct-v1:0",
  "us.meta.llama4-scout-17b-instruct-v1:0",
  "qwen.qwen3-32b-v1:0",
  "qwen.qwen3-coder-30b-a3b-v1:0",
  "openai.gpt-oss-20b-1:0",
  "openai.gpt-oss-120b-1:0",
  "amazon.nova-pro-v1:0",
];

export type NodeModelKey =
  | "decision"
  | "respond"
  | "summarize"
  | "planner"
  | "evaluation"
  | "step_critic";

export const NODE_MODEL_LABELS: Record<NodeModelKey, string> = {
  decision: "Decision (plan vs direct)",
  respond: "Final response",
  summarize: "Memory / summarize",
  planner: "Planner (steps)",
  evaluation: "Evaluation",
  step_critic: "Step critic",
};
