// Backend API types

export interface User {
  uid?: string;
  user_id: string;
  user_name?: string;
  name?: string;
  email?: string;
  role?: string;
  created_at?: string;
  last_login?: string;
}

export interface Chat {
  [x: string]: any;
  agent_id: string;
  user_id?: string;
  uid?: string;
  title?: string;
  session_name?: string;
  created_at: string;
  updated_at?: string;
  last_activity?: string;
  lastMessageAt?: number;
  deleted?: boolean;
  rollback_checkpoint_id?: string | null;
}

export type Session = Chat;

export interface UIResource {
  uri: string;
  mimeType: 'text/html' | 'text/uri-list' | 'application/vnd.mcp-ui.remote-dom';
  text?: string;
  blob?: string;
}

export interface ToolCallEvent {
  id: string;
  tool_name: string;
  task?: string;
  tool_args?: unknown;
  result?: string;
  success?: boolean;
  status: 'running' | 'done' | 'error';
}

export type SubagentProgressKind = 'status' | 'reasoning' | 'log' | 'card' | 'test_plan' | 'test_results';

export interface AgentCardPermissions {
  read?: boolean;
  write?: boolean;
  execute?: boolean;
}

export interface AgentCardPayload {
  agent_id?: string;
  name?: string;
  owner?: string;
  intent?: string;
  description?: string;
  capabilities?: string[];
  function_name?: string;
  input_schema?: Array<{ name?: string; type?: string; description?: string; required?: boolean }>;
  output_schema?: { type?: string; description?: string };
  permissions?: AgentCardPermissions;
  tools_used?: string[];
  model?: { provider?: string; uses_llm?: boolean };
  constraints?: { timeout_seconds?: number; max_retries?: number };
  status?: string;
  version?: number;
}

export interface AgentTestCasePayload {
  name?: string;
  kind?: string;
  input_kwargs?: Record<string, unknown>;
  expectation_type?: string;
  expected?: unknown;
}

export interface AgentTestResultPayload extends AgentTestCasePayload {
  passed?: boolean;
  actual?: unknown;
  raw_error?: string | null;
  error?: string | null;
  reason?: string;
  duration_ms?: number;
}

export interface SubagentProgressEvent {
  step: string;
  message: string;
  status: string;
  ts?: string;
  /** Rendering hint: a short phase update, a growing reasoning block, or a terminal-style log line. */
  kind?: SubagentProgressKind;
  /** Optional structured extra payload (code preview, test rows, notes, etc). */
  detail?: unknown;
  /** True once a reasoning block has finished streaming (no more deltas coming). */
  reasoningDone?: boolean;
}

export interface SubagentCallEvent {
  id: string;
  agent_name: string;
  child_agent_id?: string;
  task?: string;
  tool_args?: unknown;
  result?: string;
  success?: boolean;
  status: 'running' | 'done' | 'error';
  progress: SubagentProgressEvent[];
  /** Client-side timestamp (ms) when the subagent started, used for a live elapsed timer. */
  startedAt?: number;
  /** Client-side timestamp (ms) when the subagent finished. */
  endedAt?: number;
}

export type ChildAgentCallEvent = SubagentCallEvent;

export type AgentStep =
  | { type: 'reasoning'; content: string }
  | { type: 'tool'; tool: ToolCallEvent }
  | { type: 'subagent'; subagent: SubagentCallEvent }
  | { type: 'child_agent'; child: ChildAgentCallEvent };

export interface Message {
  _id?: string;
  sessionId?: string;
  _creationTime?: number;
  message_id?: string;
  session_id?: string;
  agent_id?: string;
  user_id?: string;
  role: 'user' | 'assistant' | string;
  content: string;
  timestamp?: number;
  toolCalls?: string[];
  ui_resources?: UIResource[];
  checkpoint_id?: string | null;
  metadata?: {
    reasoning?: string;
    tools?: ToolCallEvent[];
    steps?: AgentStep[];
    cache_hit?: boolean;
    stopped?: boolean;
    execution_id?: string;
    // Legacy planning fields kept optional so old archived UIs don't crash if referenced
    used_planning?: boolean;
    planning_data?: any;
    advanced_events?: any;
    execution_results?: any[];
    [key: string]: unknown;
  };
}

export interface CheckpointInfo {
  checkpoint_id: string;
  timestamp: string | null;
  current_task: string | null;
  message_snippet: string | null;
  parent_checkpoint_id: string | null;
}

/** A node in the branch tree — see GET /agents/{id}/checkpoints/tree */
export interface CheckpointTreeNode extends CheckpointInfo {
  node?: string | null;
  is_leaf?: boolean;
  /** The checkpoint that is the current graph head (the live answer path). */
  is_active_tip?: boolean;
  has_pending_interrupt?: boolean;
}

export type InterruptKind =
  | 'paused'
  | 'confirm_tool'
  | 'question'
  | 'confirm_agent_studio'
  | 'confirm_create_agent'
  | string;

/** Payload of a `run.interrupted` event — drives the InterruptPrompt UI. */
export interface PendingInterrupt {
  execution_id?: string;
  interrupt_id?: string | null;
  kind: InterruptKind;
  checkpoint_id?: string | null;
  payload: {
    kind?: InterruptKind;
    node?: string;
    prompt?: string;
    question?: string;
    options?: string[];
    tool_name?: string;
    tool_args?: unknown;
    task?: string;
    agent_name?: string;
    questions?: string[];
    agent_card?: AgentCardPayload;
    test_report?: unknown;
    paused?: boolean;
    confirm_required?: boolean;
    [key: string]: unknown;
  };
}

/** Loose memory map used by InfoPanel / Memory page */
export type Memory = Record<string, any>;
