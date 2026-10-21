// WebSocket client for client2.0 chat protocol
import { getAccessToken } from '@/lib/api';

const WS_HOST = (import.meta.env.VITE_WS_URL || 'ws://localhost:5000').replace(/\/$/, '');

export interface WsEnvelope {
  v?: number;
  type: string;
  id?: string;
  agent_id?: string;
  seq?: number | null;
  ts?: string;
  payload: Record<string, unknown>;
  epoch?: number;
  execution_id?: string;
}

export type ServerEventType =
  | 'session.ready'
  | 'run.started'
  | 'node.started'
  | 'node.finished'
  | 'llm.token'
  | 'llm.cache_hit'
  | 'llm.done'
  | 'tool.started'
  | 'tool.finished'
  | 'subagent.started'
  | 'subagent.step'
  | 'subagent.finished'
  | 'child.started'
  | 'child.step'
  | 'child.finished'
  | 'plan.created'
  | 'plan.phase.started'
  | 'plan.phase.finished'
  | 'plan.step.started'
  | 'plan.step.finished'
  | 'checkpoint.created'
  | 'run.completed'
  | 'run.interrupted'
  | 'run.error'
  | 'error'
  | 'pong';

export interface AgentWebSocketHandlers {
  onSessionReady?: (payload: {
    execution_id?: string | null;
    status?: string;
    latest_sequence?: number;
    current_state?: Record<string, unknown>;
    last_seq: number;
    run_active: boolean;
    backlog_count: number;
    epoch: number;
  }) => void;
  onRunStarted?: (payload: { execution_id: string; query: string; checkpoint_id?: string; resumed?: boolean }) => void;
  onNodeStarted?: (payload: { node: string }) => void;
  onNodeFinished?: (payload: { node: string; next_step?: Record<string, unknown> }) => void;
  onLlmToken?: (payload: {
    text: string;
    channel: 'reasoning' | 'output' | string;
    child_agent_id?: string;
    agent_id?: string;
  }) => void;
  onLlmCacheHit?: (payload: {
    mode?: string;
    model_id?: string;
    output_type?: string | null;
    source_call_id?: string;
    cache_key?: string;
  }) => void;
  onLlmDone?: (payload: { channel?: string }) => void;
  onToolStarted?: (payload: { tool_name: string; tool_args?: unknown; task?: string }) => void;
  onToolFinished?: (payload: {
    tool_name: string;
    tool_args?: unknown;
    task?: string;
    result?: string;
    success?: boolean;
  }) => void;
  onSubagentStarted?: (payload: { agent_name: string; tool_args?: unknown; task?: string }) => void;
  onSubagentStep?: (payload: {
    agent_name: string;
    event: { step: string; message: string; status: string; ts?: string; kind?: string; detail?: unknown };
  }) => void;
  onSubagentFinished?: (payload: {
    agent_name: string;
    task?: string;
    result?: string;
    success?: boolean;
  }) => void;
  onChildStarted?: (payload: { agent_name: string; child_agent_id?: string; task?: string; child_calls?: unknown }) => void;
  onChildStep?: (payload: {
    agent_name: string;
    child_agent_id?: string;
    event: { step: string; message: string; status: string; ts?: string; kind?: string; detail?: unknown };
  }) => void;
  onChildFinished?: (payload: {
    agent_name: string;
    child_agent_id?: string;
    task?: string;
    result?: string;
    success?: boolean;
  }) => void;
  onPlanCreated?: (payload: { phases: unknown[]; step_count: number }) => void;
  onPlanPhaseStarted?: (payload: { sequence: number; steps: unknown[] }) => void;
  onPlanPhaseFinished?: (payload: { sequence: number; failed: boolean; step_ids: string[] }) => void;
  onPlanStepStarted?: (payload: { id: string; sequence: number; action: string; name: string; task: string }) => void;
  onPlanStepFinished?: (payload: { id: string; sequence: number; action: string; success: boolean; result?: unknown }) => void;
  onCheckpointCreated?: (payload: { checkpoint_id: string; rollback?: boolean }) => void;
  onRunCompleted?: (payload: {
    execution_id: string;
    stopped: boolean;
    answer?: string | null;
    checkpoint_id?: string;
    /** True when this is the tail-end of a run that was preempted by a fork
     * (not a manual Stop) — the frontend should silently drop it and wait
     * for the fork's own `run.started` instead of finalizing it. */
    superseded?: boolean;
  }) => void;
  onRunInterrupted?: (payload: {
    execution_id?: string;
    interrupt_id?: string | null;
    kind?: string;
    payload?: Record<string, unknown>;
    checkpoint_id?: string | null;
  }) => void;
  onRunError?: (payload: { execution_id?: string; message: string }) => void;
  onError?: (payload: { message: string }) => void;
  onOpen?: () => void;
  onClose?: (ev: CloseEvent) => void;
  onReconnect?: (attempt: number) => void;
}

export class AgentWebSocketClient {
  private ws: WebSocket | null = null;
  private agentId: string;
  private handlers: AgentWebSocketHandlers;
  private lastSeq = 0;
  private seqByExecution = new Map<string, number>();
  private epoch = 0;
  private intentionalClose = false;
  private reconnectAttempts = 0;
  private maxReconnect = 8;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private executionId: string | null = null;
  private requestedAfterSeq = 0;

  constructor(agentId: string, handlers: AgentWebSocketHandlers = {}) {
    this.agentId = agentId;
    this.handlers = handlers;
  }

  get connected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get currentEpoch() {
    return this.epoch;
  }

  get currentSeq() {
    return this.currentCursor();
  }

  private currentCursor() {
    if (this.executionId) return this.seqByExecution.get(this.executionId) ?? 0;
    return this.lastSeq;
  }

  connect(afterSeq?: number, executionId?: string | null) {
    this.intentionalClose = false;
    this.stopReconnect();
    const token = getAccessToken();
    if (!token) {
      this.handlers.onError?.({ message: 'Missing access token' });
      return;
    }

    const seq = afterSeq ?? this.currentCursor();
    this.requestedAfterSeq = Math.max(0, seq);
    if (executionId !== undefined) this.executionId = executionId;
    const qs = new URLSearchParams({ token });
    if (seq > 0) qs.set('after_seq', String(seq));
    if (executionId) qs.set('execution_id', executionId);

    const url = `${WS_HOST}/v1/ws/agents/${encodeURIComponent(this.agentId)}?${qs.toString()}`;
    if (this.ws) {
      try {
        this.ws.onclose = null;
        this.ws.close();
      } catch {
        /* ignore */
      }
    }

    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => {
      if (this.ws !== ws) return;
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.handlers.onOpen?.();
    };

    ws.onmessage = (ev) => {
      if (this.ws !== ws) return;
      let msg: WsEnvelope;
      try {
        msg = JSON.parse(ev.data);
      } catch {
        return;
      }
      this.applyMessage(msg);
    };

    ws.onclose = (ev) => {
      if (this.ws !== ws) return;
      this.stopTimers();
      this.handlers.onClose?.(ev);
      if (!this.intentionalClose && this.reconnectAttempts < this.maxReconnect) {
        this.reconnectAttempts += 1;
        this.handlers.onReconnect?.(this.reconnectAttempts);
        const delay = Math.min(1000 * 2 ** (this.reconnectAttempts - 1), 15000);
        this.reconnectTimer = setTimeout(() => {
          this.reconnectTimer = null;
          if (!this.intentionalClose) this.connect(this.currentCursor(), this.executionId);
        }, delay);
      }
    };

    ws.onerror = () => {
      // onclose will fire after
    };
  }

  disconnect() {
    this.intentionalClose = true;
    this.stopTimers();
    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        /* ignore */
      }
      this.ws = null;
    }
  }

  private send(type: string, payload: Record<string, unknown> = {}) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false;
    this.ws.send(JSON.stringify({ type, payload }));
    return true;
  }

  startRun(query: string, checkpointId?: string) {
    const payload: Record<string, unknown> = { query };
    if (checkpointId) payload.checkpoint_id = checkpointId;
    return this.send('run.start', payload);
  }

  stopRun() {
    return this.send('run.stop', {});
  }

  /** Cooperative pause — the run stops cleanly at the next node boundary and
   * raises a `run.interrupted` (kind: "paused") once it takes effect. */
  pauseRun() {
    return this.send('run.pause', {});
  }

  /** Resume a run that's paused on a pending interrupt. `value` is whatever
   * the interrupt expects: free text for a question/pause note, or
   * `{ approved: boolean, reason?: string }` for a confirmation. */
  resumeRun(value: unknown) {
    return this.send('run.resume', { value });
  }

  rollback(checkpointId: string) {
    return this.send('run.rollback', { checkpoint_id: checkpointId });
  }

  ping() {
    return this.send('ping', {});
  }

  /** Compat alias used by older call sites */
  sendQuery(query: string, _promptId?: string, _tune?: unknown) {
    return this.startRun(query);
  }

  sendStopGeneration() {
    return this.stopRun();
  }

  private applyMessage(msg: WsEnvelope) {
    if (typeof msg.epoch === 'number' && msg.type !== 'session.ready' && msg.type !== 'pong') {
      if (msg.epoch < this.epoch) return; // stale epoch
      if (msg.epoch > this.epoch) this.epoch = msg.epoch;
    }

    const payload = (msg.payload || {}) as Record<string, unknown>;

    switch (msg.type as ServerEventType | string) {
      case 'session.ready': {
        const ready = {
          execution_id: (payload.execution_id as string | undefined) ?? null,
          status: (payload.status as string | undefined) ?? undefined,
          latest_sequence: Number(payload.latest_sequence ?? payload.last_seq ?? 0),
          current_state: (payload.current_state as Record<string, unknown> | undefined) ?? {},
          last_seq: Number(payload.last_seq ?? 0),
          run_active: Boolean(payload.run_active),
          backlog_count: Number(payload.backlog_count ?? 0),
          epoch: Number(payload.epoch ?? 0),
        };
        this.epoch = ready.epoch;
        this.executionId = ready.execution_id;
        if (ready.execution_id) {
          const prev = this.seqByExecution.get(ready.execution_id) ?? 0;
          const baseline = Math.max(prev, this.requestedAfterSeq);
          this.seqByExecution.set(ready.execution_id, baseline);
          this.lastSeq = baseline;
        } else {
          this.lastSeq = Math.max(this.lastSeq, this.requestedAfterSeq);
        }
        this.handlers.onSessionReady?.(ready);
        break;
      }
      default: {
        if (typeof msg.seq === 'number' && msg.seq > 0) {
          const eventExecutionId = msg.execution_id ?? this.executionId;
          if (eventExecutionId) {
            const last = this.seqByExecution.get(eventExecutionId) ?? 0;
            if (msg.seq <= last) return;
            this.seqByExecution.set(eventExecutionId, msg.seq);
            if (eventExecutionId === this.executionId) this.lastSeq = msg.seq;
          } else {
            if (msg.seq <= this.lastSeq) return;
            this.lastSeq = msg.seq;
          }
        }
      }
    }

    switch (msg.type as ServerEventType | string) {
      case 'run.started':
        if (typeof payload.execution_id === 'string' && payload.execution_id) {
          this.executionId = payload.execution_id;
          this.lastSeq = this.seqByExecution.get(payload.execution_id) ?? 0;
        }
        this.handlers.onRunStarted?.(payload as any);
        break;
      case 'node.started':
        this.handlers.onNodeStarted?.(payload as any);
        break;
      case 'node.finished':
        this.handlers.onNodeFinished?.(payload as any);
        break;
      case 'llm.token':
        this.handlers.onLlmToken?.(payload as any);
        break;
      case 'llm.cache_hit':
        this.handlers.onLlmCacheHit?.(payload as any);
        break;
      case 'llm.done':
        this.handlers.onLlmDone?.(payload as any);
        break;
      case 'tool.started':
        this.handlers.onToolStarted?.(payload as any);
        break;
      case 'tool.finished':
        this.handlers.onToolFinished?.(payload as any);
        break;
      case 'subagent.started':
        this.handlers.onSubagentStarted?.(payload as any);
        break;
      case 'subagent.step':
        this.handlers.onSubagentStep?.(payload as any);
        break;
      case 'subagent.finished':
        this.handlers.onSubagentFinished?.(payload as any);
        break;
      case 'child.started':
        this.handlers.onChildStarted?.(payload as any);
        break;
      case 'child.step':
        this.handlers.onChildStep?.(payload as any);
        break;
      case 'child.finished':
        this.handlers.onChildFinished?.(payload as any);
        break;
      case 'plan.created':
        this.handlers.onPlanCreated?.(payload as any);
        break;
      case 'plan.phase.started':
        this.handlers.onPlanPhaseStarted?.(payload as any);
        break;
      case 'plan.phase.finished':
        this.handlers.onPlanPhaseFinished?.(payload as any);
        break;
      case 'plan.step.started':
        this.handlers.onPlanStepStarted?.(payload as any);
        break;
      case 'plan.step.finished':
        this.handlers.onPlanStepFinished?.(payload as any);
        break;
      case 'checkpoint.created':
        this.handlers.onCheckpointCreated?.(payload as any);
        break;
      case 'run.completed':
        this.handlers.onRunCompleted?.(payload as any);
        break;
      case 'run.interrupted':
        this.handlers.onRunInterrupted?.(payload as any);
        break;
      case 'run.error':
        this.handlers.onRunError?.({
          execution_id: payload.execution_id as string | undefined,
          message: String(payload.message ?? 'Run error'),
        });
        break;
      case 'error':
        this.handlers.onError?.({ message: String(payload.message ?? 'Error') });
        break;
      case 'pong':
        break;
      default:
        break;
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.pingTimer = setInterval(() => this.ping(), 25000);
  }

  private stopHeartbeat() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private stopReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private stopTimers() {
    this.stopHeartbeat();
    this.stopReconnect();
  }
}

export function createWebSocketClient(
  chatId: string,
  _userId: string | undefined,
  handlers: AgentWebSocketHandlers,
  _consoleMode?: string
) {
  return new AgentWebSocketClient(chatId, handlers);
}

export default AgentWebSocketClient;
