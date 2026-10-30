// API client for client2.0 FastAPI (/v1)
import axios, { AxiosInstance, AxiosError } from 'axios';
import type { CheckpointTreeNode } from '@/types/backend';

const API_HOST = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const API_BASE_URL = API_HOST.replace(/\/$/, '').replace(/\/v1$/, '') + '/v1';

const TOKEN_KEY = 'eva_access_token';
const USER_KEY = 'agent_user';
const AUTH_SESSION_KEY = 'agent_session_id';

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function clearAuthStorage() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(AUTH_SESSION_KEY);
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
});

function requestAuthHeader(config: { headers?: unknown } | undefined): string | undefined {
  const headers = config?.headers as Record<string, unknown> | undefined;
  if (!headers) return undefined;
  const auth = headers.Authorization ?? headers.authorization;
  return typeof auth === 'string' ? auth : undefined;
}

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || '';
      // Bootstrap and login handle these; never wipe a fresh token here.
      if (url.includes('/auth/login') || url.includes('/auth/me')) {
        return Promise.reject(error);
      }

      const requestAuth = requestAuthHeader(error.config);
      const currentToken = getAccessToken();
      const staleRequest =
        !!requestAuth &&
        !!currentToken &&
        requestAuth !== `Bearer ${currentToken}`;

      if (requestAuth && currentToken && !staleRequest) {
        clearAuthStorage();
        window.dispatchEvent(new Event('eva:unauthorized'));
      }
    }
    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UserOut {
  uid: string;
  user_name?: string;
  email?: string;
  name?: string;
  role?: string;
  created_at?: string;
  last_login?: string;
}

export interface LoginRequest {
  identifier: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  session_id: string;
  user: UserOut;
}

export interface ChatOut {
  agent_id: string;
  owner_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  deleted: boolean;
  rollback_checkpoint_id: string | null;
}

export interface ChatMessage {
  role: string;
  content: string;
  checkpoint_id?: string | null;
  metadata?: Record<string, unknown>;
}

export interface ChatDetailOut extends ChatOut {
  messages: ChatMessage[];
  execution_history?: Array<Record<string, unknown>>;
  latest_execution?: {
    execution_id: string;
    status: string;
    latest_sequence: number;
    current_state?: Record<string, unknown>;
    result?: string | null;
    error?: string | null;
  } | null;
  preloaded_context?: {
    user?: Record<string, unknown>;
    preferences?: Record<string, unknown>;
    memory?: MemoryEntry[];
    mcp_servers?: MCPServer[];
  };
}

export interface AgentPolicy {
  armory: {
    version: number;
    confirm_tools: boolean;
    groups: Record<string, { enabled: boolean }>;
    resources: Record<string, Array<{ type: string; name: string; enabled: boolean }>>;
    tools?: string[];
    subagents?: string[];
  };
  memory: {
    version: number;
    enabled: boolean;
    tenant_id: string | null;
    read: string[];
    write: string[];
    promote: string[];
    publish: string[];
    confirm_before_extracting: boolean;
    allow_admin_promotion: boolean;
    chunks: Record<string, {
      enabled: boolean;
      read: string[];
      write: string[];
      promote: string[];
      confirm_before_extracting: boolean;
      allow_admin_promotion: boolean;
    }>;
  };
  guardrails: Record<string, unknown>;
  observability: Record<string, unknown>;
}

export interface AgentPolicyResponse {
  policy: AgentPolicy;
  ceiling: AgentPolicy;
  version: number;
}

export interface CheckpointOut {
  checkpoint_id: string;
  timestamp: string | null;
  current_task: string | null;
  message_snippet: string | null;
  parent_checkpoint_id: string | null;
}

export interface MemoryEntry {
  key: string;
  value: string;
  category: string;
  updated_at?: string | null;
}

export interface UserPreferences {
  theme: string;
  console_mode: string;
  agent: Record<string, unknown>;
}

export interface MCPServer {
  id: string;
  name: string;
  url: string;
  command?: string;
  transport?: 'stdio' | 'streamable_http' | 'sse';
  args?: string[];
  env?: Record<string, string>;
  connection_error?: string;
  connection_logs?: Array<{ timestamp: string; level: string; message: string }>;
  tools_count?: number;
  connected?: boolean;
  metadata?: Record<string, unknown>;
  auth?: MCPLoginAuth;
  created_at?: string;
  updated_at?: string;
  // Compat fields used by older UI
  description?: string;
  timeout?: number;
  retry_attempts?: number;
  retry_delay?: number;
  enabled?: boolean;
  connection_status?: 'connected' | 'disconnected' | 'error';
  is_connected?: boolean;
  last_connected?: string;
}

export interface MCPLoginAuth {
  login_url: string;
  username: string;
  password?: string;
  use_agent_credentials?: boolean;
  username_field?: string;
  password_field?: string;
  token_field?: string;
  password_configured?: boolean;
}

export interface HealthResponse {
  status: string;
  agent_ready: boolean;
  active_ws: number;
  active_runs: number;
  dependencies: Record<string, boolean>;
  warnings: string[];
}

export interface LiveResponse {
  ok: boolean;
  status: string;
  dependencies: Record<string, boolean>;
  warnings: string[];
}

export interface AnalyticsTokenBreakdown {
  input: number;
  output: number;
  cached_input: number;
  cache_creation: number;
  reasoning: number;
  audio_input: number;
  audio_output: number;
  other: number;
  total: number;
}

export interface AnalyticsCostBreakdown {
  actual: number;
  estimated: number;
  total: number;
}

export interface AnalyticsModelSummary {
  model: string;
  calls: number;
  tokens: AnalyticsTokenBreakdown;
  cost_usd: AnalyticsCostBreakdown;
}

export interface AnalyticsSummary {
  scope: {
    type: "agent" | "user" | "global";
    uid: string | null;
    agent_id: string | null;
    from: string | null;
    to: string | null;
  };
  llm: {
    calls: {
      total: number;
      successful: number;
      failed: number;
      cached: number;
    };
    tokens: AnalyticsTokenBreakdown;
    cost_usd: AnalyticsCostBreakdown;
    models: AnalyticsModelSummary[];
  };
  agent: {
    messages: {
      total: number;
      human: number;
      ai: number;
      system: number;
      tool: number;
      other: number;
    };
    context: {
      latest: {
        total_tokens: number;
        components: Record<string, { tokens: number; percentage: number }>;
      };
      aggregate: {
        samples: number;
        average_tokens: number;
        maximum_tokens: number;
        component_tokens: Record<string, number>;
        component_percentages: Record<string, number>;
      };
    };
    planner: {
      invocations: number;
      plans_created: number;
      steps_created: number;
      steps_completed: number;
      steps_failed: number;
      retries: number;
      tokens: { input: number; output: number; overhead: number };
      current_plan_overhead: {
        total_tokens: number;
        tool_definitions: number;
        completed_steps: number;
        current_steps: number;
        remaining_steps: number;
        other: number;
      };
    };
    armory: {
      configured: {
        tools: number;
        mcp_servers: number;
        mcp_tools: number;
        subagents: number;
      };
      invocations: { tools: number; subagents: number };
      failures: {
        tools: number;
        subagents: number;
        authorization: number;
        mcp_connection: number;
      };
      by_resource: Array<Record<string, unknown>>;
    };
    memory: {
      extraction_attempts: number;
      extraction_failures: number;
      chunks_extracted: number;
      chunks_promoted: number;
      reads: number;
      writes: number;
    };
    runtime: {
      runs: number;
      successful_runs: number;
      failed_runs: number;
      cancelled_runs: number;
      total_ms: number;
      average_ms: number;
      maximum_ms: number;
      splits: {
        planning_ms: number;
        llm_ms: number;
        tool_ms: number;
        subagent_ms: number;
        memory_ms: number;
        checkpoint_ms: number;
        other_ms: number;
      };
    };
  };
  agents?: {
    total: number;
    active: number;
    deleted: number;
    with_runs: number;
  };
  uid?: string | null;
  agent_id?: string | null;
  by_type?: Record<string, number>;
  total_events?: number;
}

// Legacy request shapes kept so call sites compile; ignored by server where N/A
export interface ChatCreateRequest {
  user_id?: string;
  chat_name?: string;
  title?: string;
}

export interface UserChatsRequest {
  user_id?: string;
}

export type ChatEditRequest =
  | { operation: 'delete_chat'; agent_id: string; user_id?: string }
  | { operation: 'delete_chat'; delete_all: true; user_id?: string }
  | { operation: 'delete_message'; message_id: string }
  | { operation: 'edit_message'; message_id: string; new_content: string };

export interface MCPServerCreateRequest {
  name: string;
  url?: string;
  command?: string;
  transport?: 'stdio' | 'streamable_http' | 'sse';
  args?: string[];
  env?: Record<string, string>;
  description?: string;
  metadata?: Record<string, unknown>;
  timeout?: number;
  retry_attempts?: number;
  retry_delay?: number;
  enabled?: boolean;
  auth?: MCPLoginAuth | null;
}

export interface MCPServerUpdateRequest {
  name?: string;
  url?: string;
  command?: string;
  transport?: 'stdio' | 'streamable_http' | 'sse';
  args?: string[];
  env?: Record<string, string>;
  metadata?: Record<string, unknown>;
  description?: string;
  enabled?: boolean;
  auth?: MCPLoginAuth | null;
}

export interface MCPServerDetails {
  server_id: string;
  server_name: string;
  server_url: string;
  connected: boolean;
  tools?: Array<{ name: string; description?: string; parameters?: any }>;
  prompts?: Array<{ name: string; description?: string; arguments?: any[] }>;
  resources?: Array<{ uri: string; name?: string; description?: string; mimeType?: string }>;
  message?: string;
  tools_error?: string;
  prompts_error?: string;
  resources_error?: string;
  logs?: Array<{ timestamp: string; level: string; message: string }>;
}

export interface CatalogTool {
  name: string;
  description?: string;
  server_id?: string;
  server_name?: string;
  parameters?: Array<{
    name: string;
    type?: string;
    description?: string;
    required?: boolean;
  }>;
}

export interface ToolsCatalogResponse {
  internal: CatalogTool[];
  mcp: CatalogTool[];
  counts?: { internal: number; mcp: number };
}

export interface CatalogSubagent {
  name: string;
  display_name?: string;
  description?: string;
  when_to_use?: string;
  scope?: string;
  availability?: string;
  tools?: string[];
  source?: "builtin" | "agent_studio" | string;
  agent_id?: string | null;
  status?: string | null;
  enabled?: boolean;
}

export interface SubagentsCatalogResponse {
  subagents: CatalogSubagent[];
  counts?: { subagents: number };
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export const authAPI = {
  login: async (request: LoginRequest | { user_id: string; password: string; create_if_not_exists?: boolean }): Promise<LoginResponse & { success: boolean; user_data?: UserOut; message: string }> => {
    const identifier = 'identifier' in request ? request.identifier : request.user_id;
    const response = await apiClient.post<LoginResponse>('/auth/login', {
      identifier,
      password: request.password,
    });
    const data = response.data;
    return {
      ...data,
      success: true,
      user_data: data.user,
      message: 'logged in',
    };
  },

  logout: async (_request?: { user_id?: string }) => {
    const response = await apiClient.post('/auth/logout');
    return response.data;
  },

  me: async (): Promise<UserOut> => {
    const response = await apiClient.get<UserOut>('/auth/me');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Agents
// ---------------------------------------------------------------------------

function normalizeChat(c: ChatOut) {
  return {
    ...c,
    owner_id: c.owner_id,
    session_name: c.title,
    title: c.title,
    last_activity: c.updated_at,
  };
}

export const agentsAPI = {
  getPolicy: async (agentId: string): Promise<AgentPolicyResponse> =>
    (await apiClient.get<AgentPolicyResponse>(`/agents/${agentId}/armory`)).data,

  updatePolicy: async (agentId: string, expectedVersion: number,
    change: { armory?: Partial<AgentPolicy['armory']>; memory?: Partial<AgentPolicy['memory']> }): Promise<AgentPolicyResponse> =>
    (await apiClient.patch<AgentPolicyResponse>(`/agents/${agentId}/${change.memory ? 'memory' : 'armory'}`,
      { expected_version: expectedVersion, ...change })).data,

  listMemoryExtractionRequests: async (agentId: string, state?: string) =>
    (await apiClient.get<Array<Record<string, unknown>>>(`/agents/${agentId}/memory/extraction-requests`, { params: { state } })).data,

  reviewMemoryExtractionRequest: async (agentId: string, requestId: string, approve: boolean, reason = "") =>
    (await apiClient.post<Record<string, unknown>>(
      `/agents/${agentId}/memory/extraction-requests/${requestId}`,
      { approve, reason },
    )).data,

  create: async (request: ChatCreateRequest) => {
    const response = await apiClient.post<ChatOut>('/agents', {
      title: request.title ?? request.chat_name,
    });
    const chat = response.data;
    return {
      success: true,
      agent_id: chat.agent_id,
      chat,
      message: 'created',
    };
  },

  list: async (request: UserChatsRequest = {}) => {
    const response = await apiClient.get<ChatOut[]>('/agents');
    const chats = response.data.map(normalizeChat);
    return {
      success: true,
      chats,
      sessions: chats,
      session_count: chats.length,
      message: 'ok',
    };
  },

  /** No longer required by client2.0 — kept as no-op for call-site compatibility */
  load: async (_request: { user_id?: string; agent_id: string }) => {
    return { success: true, message: 'ok' };
  },

  get: (() => {
    type ChatGetResult = {
      success: boolean;
      data: ReturnType<typeof normalizeChat> & {
        messages: Array<{ message_id: string; role: string; content: string; timestamp: number }>;
        execution_history: unknown[];
        latest_execution?: ChatDetailOut['latest_execution'];
        preloaded_context?: unknown;
        rollback_checkpoint_id?: string | null;
      };
      message: string;
    };
    const inflight = new Map<string, Promise<ChatGetResult>>();
    return async (_user_id: string | undefined, agent_id: string, _depth?: string) => {
      const pending = inflight.get(agent_id);
      if (pending) return pending;

      const request = (async () => {
        const response = await apiClient.get<ChatDetailOut>(`/agents/${agent_id}`);
        const detail = response.data;
        return {
          success: true,
          data: {
            ...normalizeChat(detail),
            messages: (detail.messages || []).map((m, i) => ({
              message_id: `${agent_id}_${i}`,
              role:
                m.role === 'human' || m.role === 'user'
                  ? 'user'
                  : m.role === 'ai' || m.role === 'assistant'
                    ? 'assistant'
                    : m.role,
              content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
              checkpoint_id: m.checkpoint_id,
              metadata: m.metadata,
              timestamp: Date.now(),
            })),
            execution_history: detail.execution_history || [],
            latest_execution: detail.latest_execution || null,
            preloaded_context: detail.preloaded_context,
            rollback_checkpoint_id: detail.rollback_checkpoint_id,
          },
          message: 'ok',
        };
      })();

      inflight.set(agent_id, request);
      try {
        return await request;
      } finally {
        inflight.delete(agent_id);
      }
    };
  })(),

  update: async (agent_id: string, body: { title?: string }) => {
    const response = await apiClient.patch<ChatOut>(`/agents/${agent_id}`, body);
    return { success: true, chat: normalizeChat(response.data) };
  },

  remove: async (agent_id: string) => {
    const response = await apiClient.delete(`/agents/${agent_id}`);
    return response.data;
  },

  edit: async (request: ChatEditRequest) => {
    if (request.operation === 'delete_chat') {
      if ('delete_all' in request && request.delete_all) {
        const listed = await agentsAPI.list({});
        await Promise.all((listed.chats || []).map((c: { agent_id: string }) => agentsAPI.remove(c.agent_id)));
        return { success: true, message: 'deleted all' };
      }
      if ('agent_id' in request) {
        return agentsAPI.remove(request.agent_id);
      }
    }
    // delete_message / edit_message not supported by client2.0
    return { success: false, message: 'operation not supported' };
  },

  listCheckpoints: async (agent_id: string): Promise<CheckpointOut[]> => {
    const response = await apiClient.get<CheckpointOut[]>(`/agents/${agent_id}/checkpoints`);
    return response.data;
  },

  listCheckpointTree: async (agent_id: string): Promise<CheckpointTreeNode[]> => {
    const response = await apiClient.get<CheckpointTreeNode[]>(`/agents/${agent_id}/checkpoints/tree`);
    return response.data;
  },

  rollback: async (agent_id: string, checkpoint_id: string) => {
    const response = await apiClient.post(`/agents/${agent_id}/rollback`, { checkpoint_id });
    return response.data;
  },

  getArmoryTools: async (agentId: string): Promise<ToolsCatalogResponse> =>
    (await apiClient.get<ToolsCatalogResponse>(`/agents/${agentId}/armory/tools`)).data,

  getArmoryMcp: async (agentId: string): Promise<Record<string, unknown>[]> =>
    (await apiClient.get<Record<string, unknown>[]>(`/agents/${agentId}/armory/mcp`)).data,

  getArmorySubagents: async (agentId: string): Promise<SubagentsCatalogResponse> =>
    (await apiClient.get<SubagentsCatalogResponse>(`/agents/${agentId}/armory/subagents`)).data,

  getMemory: async (agentId: string) =>
    (await apiClient.get<{
      entries: MemoryEntry[];
      extraction_requests: Array<Record<string, unknown>>;
      policy: AgentPolicy['memory'];
    }>(`/agents/${agentId}/memory`)).data,

  getAnalytics: async (agentId: string): Promise<AnalyticsSummary> =>
    (await apiClient.get<AnalyticsSummary>(`/agents/${agentId}/analytics`)).data,
};

export const sessionAPI = agentsAPI;

// ---------------------------------------------------------------------------
// Memory
// ---------------------------------------------------------------------------

export const memoryAPI = {
  get: async (_request?: { user_id?: string; sections?: string[] }) => {
    const response = await apiClient.get<MemoryEntry[]>('/memory');
    const entries = response.data || [];
    const memory: Record<string, string> = {};
    for (const e of entries) memory[e.key] = e.value;
    return { success: true, memory, entries };
  },

  update: async (request: { user_id?: string; memory: Record<string, unknown>; entries?: MemoryEntry[] }) => {
    const entries =
      request.entries ??
      Object.entries(request.memory || {}).map(([key, value]) => ({
        key,
        value: typeof value === 'string' ? value : JSON.stringify(value),
        category: 'general',
      }));
    const response = await apiClient.put<MemoryEntry[]>('/memory', { entries });
    return { success: true, entries: response.data };
  },

  addEntry: async (entry: { key: string; value: string; category?: string }) => {
    const response = await apiClient.post<MemoryEntry>('/memory/entries', entry);
    return response.data;
  },

  clear: async (_request?: { user_id?: string }) => {
    const response = await apiClient.delete('/memory');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Preferences
// ---------------------------------------------------------------------------

export const preferencesAPI = {
  get: async (_user_id?: string): Promise<{ success: boolean; preferences: UserPreferences }> => {
    const response = await apiClient.get<UserPreferences>('/preferences');
    return { success: true, preferences: response.data };
  },

  update: async (request: {
    user_id?: string;
    updates?: Partial<UserPreferences>;
    theme?: string;
    console_mode?: string;
    agent?: Record<string, unknown>;
    merge?: boolean;
  }) => {
    const body = request.updates
      ? request.updates
      : {
          theme: request.theme,
          console_mode: request.console_mode,
          agent: request.agent,
        };
    const response = await apiClient.put<UserPreferences>('/preferences', body);
    return { success: true, message: 'updated', preferences: response.data };
  },

  updateAgentConfig: async (request: { user_id?: string; config_updates: Record<string, unknown> }) => {
    const current = await preferencesAPI.get();
    const agent = { ...(current.preferences.agent || {}), ...request.config_updates };
    return preferencesAPI.update({ agent });
  },

  setEnabledServers: async () => ({ success: true, message: 'not supported in v1' }),
  setSelectedTools: async () => ({ success: true, message: 'not supported in v1' }),
  addInstruction: async () => ({ success: true, message: 'not supported in v1' }),
  removeInstruction: async () => ({ success: true, message: 'not supported in v1' }),
  updateUIPreferences: async (_user_id: string, ui_updates: { theme?: string }) => {
    return preferencesAPI.update({ theme: ui_updates.theme });
  },
};

// ---------------------------------------------------------------------------
// Tools catalog
// ---------------------------------------------------------------------------

export const toolsAPI = {
  list: async (): Promise<ToolsCatalogResponse> => {
    const response = await apiClient.get<ToolsCatalogResponse>('/armory/tools');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Subagents catalog
// ---------------------------------------------------------------------------

export const subagentsAPI = {
  list: async (): Promise<SubagentsCatalogResponse> => {
    const response = await apiClient.get<SubagentsCatalogResponse>('/armory/subagents');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// MCP servers and live connections
// ---------------------------------------------------------------------------

function normalizeMcp(s: Record<string, unknown>): MCPServer {
  const connected = Boolean(s.connected);
  return {
    id: String(s.id),
    name: String(s.name ?? ''),
    url: String(s.url ?? ''),
    command: s.command as string | undefined,
    transport: s.transport as MCPServer['transport'],
    args: (s.args as string[]) || [],
    env: (s.env as Record<string, string>) || {},
    connection_error: s.connection_error as string | undefined,
    connection_logs: s.connection_logs as MCPServer['connection_logs'],
    tools_count: Number(s.tools_count || 0),
    connected,
    metadata: (s.metadata as Record<string, unknown>) || {},
    auth: s.auth as MCPLoginAuth | undefined,
    created_at: s.created_at as string | undefined,
    updated_at: s.updated_at as string | undefined,
    enabled: s.enabled !== false,
    is_connected: connected,
    connection_status: connected ? 'connected' : 'disconnected',
    description: typeof (s.metadata as any)?.description === 'string' ? (s.metadata as any).description : undefined,
  };
}

export const mcpAPI = {
  listServers: async (): Promise<{ success: boolean; servers: MCPServer[]; count: number }> => {
    const response = await apiClient.get<Record<string, unknown>[]>('/armory/mcp');
    const servers = (response.data || []).map(normalizeMcp);
    return { success: true, servers, count: servers.length };
  },

  getServer: async (server_id: string) => {
    const { servers } = await mcpAPI.listServers();
    const server = servers.find((s) => s.id === server_id);
    return { success: !!server, server: server! };
  },

  createServer: async (request: MCPServerCreateRequest) => {
    const response = await apiClient.post<Record<string, unknown>>('/armory/mcp', {
      name: request.name,
      url: request.url,
      command: request.command,
      transport: request.transport,
      args: request.args,
      env: request.env,
      enabled: request.enabled,
      auth: request.auth,
      metadata: {
        ...(request.metadata || {}),
        ...(request.description ? { description: request.description } : {}),
      },
    });
    return { success: true, message: 'created', server: normalizeMcp(response.data) };
  },

  updateServer: async (server_id: string, request: MCPServerUpdateRequest) => {
    const response = await apiClient.patch<Record<string, unknown>>(`/armory/mcp/${server_id}`, {
      name: request.name,
      url: request.url,
      command: request.command,
      transport: request.transport,
      args: request.args,
      env: request.env,
      enabled: request.enabled,
      auth: request.auth,
      metadata: request.metadata ?? (request.description ? { description: request.description } : undefined),
    });
    return { success: true, message: 'updated', server: normalizeMcp(response.data) };
  },

  deleteServer: async (server_id: string) => {
    const response = await apiClient.delete(`/armory/mcp/${server_id}`);
    return { success: true, ...(response.data || {}), message: 'deleted' };
  },

  connectServer: async (server_id: string) => {
    const response = await apiClient.post<{ success: boolean; message: string; tools_count: number; tools: string[]; logs: Array<{ timestamp: string; level: string; message: string }> }>(`/armory/mcp/${server_id}/connect`);
    return response.data;
  },

  disconnectServer: async (server_id?: string) => {
    if (server_id) {
      const response = await apiClient.post<{ success: boolean; message: string }>(`/armory/mcp/${server_id}/disconnect`);
      return response.data;
    }
    const { servers } = await mcpAPI.listServers();
    await Promise.all(servers.filter((s) => s.connected).map((s) => mcpAPI.disconnectServer(s.id)));
    return { success: true, message: 'All disconnected' };
  },

  connectAll: async () => {
    const { servers } = await mcpAPI.listServers();
    const results = [];
    for (const s of servers) {
      try {
        await mcpAPI.connectServer(s.id);
        results.push({ server_id: s.id, server_name: s.name, success: true, message: 'ok' });
      } catch {
        results.push({ server_id: s.id, server_name: s.name, success: false, message: 'failed' });
      }
    }
    return {
      success: true,
      connected: results.some((r) => r.success),
      successful_connections: results.filter((r) => r.success).length,
      total_servers: servers.length,
      tools_count: 0,
      results,
    };
  },

  getServerDetails: async (server_id: string, _include_details = true) => {
    const { server } = await mcpAPI.getServer(server_id);
    const response = await apiClient.get<MCPServerDetails>(`/armory/mcp/${server_id}`);
    const details = response.data;
    return { success: true, server, details };
  },

  getStatus: async () => {
    const { servers } = await mcpAPI.listServers();
    const connected = servers.filter((s) => s.connected);
    return {
      success: true,
      connected: connected.length > 0,
      server_url: connected[0]?.url,
      tools_count: connected.reduce((count, s) => count + (s.tools_count || 0), 0),
      tools: [] as string[],
      message: `${connected.length} connected`,
    };
  },

  importConfig: async (config: unknown) => {
    const response = await apiClient.post<{ success: boolean; count: number; created: MCPServer[] }>('/armory/mcp/import', config);
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Health / Analytics
// ---------------------------------------------------------------------------

export const healthAPI = {
  check: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  },
  live: async (): Promise<LiveResponse> => {
    const response = await apiClient.get<LiveResponse>('/live');
    return response.data;
  },
  info: async () => ({ name: 'PlatformAgent Agent API', version: 'v1' }),
};

// ---------------------------------------------------------------------------
// Experience (learned tool advice)
// ---------------------------------------------------------------------------

export interface ExperienceChunk {
  id: string;
  type?: string;
  embed_text?: string;
  advice?: string;
  metadata?: {
    uid?: string;
    source_agent_id?: string;
    user_query?: string;
    prior_task?: string;
    prior_tool?: string;
    observed_tool?: string;
    tool_args?: Record<string, unknown>;
    result_summary?: string;
    outcome?: string;
    learning?: string;
    created_at?: string;
    [key: string]: unknown;
  };
}

export interface ExperienceGraphNode {
  id: string;
  kind: 'tool' | 'experience';
  label: string;
  count?: number;
  tool?: string;
  outcome?: string;
  agent_id?: string;
  created_at?: string;
}

export interface ExperienceGraphLink {
  source: string;
  target: string;
  weight: number;
  kind: 'transition' | 'belongs';
}

export interface ExperienceResponse {
  chunks: ExperienceChunk[];
  graph: {
    nodes: ExperienceGraphNode[];
    links: ExperienceGraphLink[];
    stats: {
      total: number;
      tools: number;
      chats: number;
      outcomes: Record<string, number>;
      tool_breakdown: { tool: string; count: number }[];
    };
  };
  scope: string;
}

export const experienceAPI = {
  list: async (scope: 'user' | 'all' = 'user'): Promise<ExperienceResponse> => {
    const response = await apiClient.get<ExperienceResponse>('/experience', {
      params: { scope },
    });
    return response.data;
  },

  get: async (chunkId: string) => {
    const response = await apiClient.get<{ chunk?: ExperienceChunk; error?: string }>(
      `/experience/${chunkId}`,
    );
    return response.data;
  },
};

export interface KBChunk {
  chunk_id: string;
  chunk_type: string;
  scope: 'USER' | 'TENANT' | 'AGENT';
  content: string;
  memory_weight: number;
  status: string;
  active_version_id: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
  score?: number;
}

export interface KBPromotion {
  request_id: string;
  source_chunk_id: string | null;
  source_version_id: string | null;
  from_scope: KBChunk['scope'];
  to_scope: 'TENANT' | 'AGENT';
  target_tenant_id: string | null;
  proposed_content: string;
  state: string;
  target_chunk_id: string | null;
  reason: string | null;
  created_at: string;
}

export interface KBAudit {
  action: string;
  actor_user_id: string | null;
  chunk_id: string | null;
  version_id: string | null;
  request_id: string | null;
  created_at: string;
}

export const kbAPI = {
  list: async (scope?: KBChunk['scope']): Promise<KBChunk[]> =>
    (await apiClient.get<KBChunk[]>('/kb/chunks', { params: { scope } })).data,
  search: async (q: string): Promise<KBChunk[]> =>
    (await apiClient.get<KBChunk[]>('/kb/search', { params: { q } })).data,
  history: async (id: string): Promise<KBChunk & { versions: Array<{ version_id: string; content: string; created_at: string; status: string }>; active_version_index: number }> =>
    (await apiClient.get(`/kb/chunks/${encodeURIComponent(id)}/history`)).data,
  create: async (content: string, chunk_type = 'workflow'): Promise<KBChunk> =>
    (await apiClient.post<KBChunk>('/kb/chunks', { content, chunk_type })).data,
  append: async (chunk: KBChunk, content: string): Promise<KBChunk> =>
    (await apiClient.post<KBChunk>(`/kb/chunks/${encodeURIComponent(chunk.chunk_id)}/versions`,
      { content, chunk_type: chunk.chunk_type, memory_weight: chunk.memory_weight })).data,
  request: async (id: string, target_scope: 'AGENT' | 'TENANT', proposed_content: string): Promise<KBPromotion> =>
    (await apiClient.post<KBPromotion>(`/kb/chunks/${encodeURIComponent(id)}/promotions`,
      { target_scope, proposed_content }, { headers: { 'Idempotency-Key': crypto.randomUUID() } })).data,
  promotions: async (): Promise<KBPromotion[]> =>
    (await apiClient.get<KBPromotion[]>('/kb/promotions')).data,
  promotion: async (id: string): Promise<KBPromotion> =>
    (await apiClient.get<KBPromotion>(`/kb/promotions/${encodeURIComponent(id)}`)).data,
  audit: async (): Promise<KBAudit[]> =>
    (await apiClient.get<KBAudit[]>('/kb/audit')).data,
  review: async (id: string, approve: boolean, reason = ''): Promise<KBPromotion> =>
    (await apiClient.post<KBPromotion>(`/kb/promotions/${encodeURIComponent(id)}/review`, { approve, reason })).data,
  cancel: async (id: string): Promise<KBPromotion> =>
    (await apiClient.post<KBPromotion>(`/kb/promotions/${encodeURIComponent(id)}/cancel`)).data,
  revoke: async (id: string): Promise<void> => {
    await apiClient.post(`/kb/chunks/${encodeURIComponent(id)}/revoke`);
  },
  demote: async (id: string): Promise<void> => {
    await apiClient.post(`/kb/chunks/${encodeURIComponent(id)}/demote`);
  },
  expiry: async (id: string, expires_at: string | null): Promise<void> => {
    await apiClient.post(`/kb/chunks/${encodeURIComponent(id)}/expiry`, { expires_at });
  },
};

export interface UsageAnalyticsResponse {
  success: boolean;
  analytics: {
    user_id: string;
    generated_at: string;
    date_range: Record<string, unknown>;
    sessions: {
      total: number;
      active: number;
      total_messages: number;
      average_messages_per_session: number;
      average_duration_seconds: number;
      total_duration_seconds: number;
    };
    tokens: {
      total_input: number;
      total_output: number;
      total: number;
      average_per_session: { input: number; output: number; total: number };
      by_session: Record<string, number>;
    };
    summary: AnalyticsSummary;
  };
}

export const analyticsAPI = {
  getSummary: async (): Promise<AnalyticsSummary> => {
    const response = await apiClient.get<AnalyticsSummary>('/analytics');
    return response.data;
  },

  /** Compat wrapper for Dashboard which expects the old rich shape */
  getUsageAnalytics: async (_request?: { user_id?: string; metrics?: string[] }): Promise<UsageAnalyticsResponse> => {
    const summary = await analyticsAPI.getSummary();
    const sessionTotal = summary.agent.runtime.runs || 0;
    const messageTotal = summary.agent.messages.total || 0;
    const inputTokens = summary.llm.tokens.input || 0;
    const outputTokens = summary.llm.tokens.output || 0;
    const allTokens = summary.llm.tokens.total || inputTokens + outputTokens;
    const avgMessages = sessionTotal > 0 ? Number((messageTotal / sessionTotal).toFixed(2)) : 0;
    const totalDurationSeconds = Math.floor((summary.agent.runtime.total_ms || 0) / 1000);
    const avgDurationSeconds = sessionTotal > 0
      ? Number((totalDurationSeconds / sessionTotal).toFixed(2))
      : 0;
    return {
      success: true,
      analytics: {
        user_id: summary.scope.uid || '',
        generated_at: new Date().toISOString(),
        date_range: {},
        sessions: {
          total: sessionTotal,
          active: summary.agents?.active || 0,
          total_messages: messageTotal,
          average_messages_per_session: avgMessages,
          average_duration_seconds: avgDurationSeconds,
          total_duration_seconds: totalDurationSeconds,
        },
        tokens: {
          total_input: inputTokens,
          total_output: outputTokens,
          total: allTokens,
          average_per_session: {
            input: sessionTotal > 0 ? Math.round(inputTokens / sessionTotal) : 0,
            output: sessionTotal > 0 ? Math.round(outputTokens / sessionTotal) : 0,
            total: sessionTotal > 0 ? Math.round(allTokens / sessionTotal) : 0,
          },
          by_session: {},
        },
        summary,
      },
    };
  },
};

// Data stacking — no backend in v1; keep stubs so unused pages compile
export const dataStackingAPI = {
  processQuery: async () => ({ success: false, message: 'not available in v1' }),
  connectDataSource: async () => ({ success: false, message: 'not available in v1' }),
  listDataSources: async () => ({ success: true, data_sources: [] as unknown[] }),
  disconnectDataSource: async () => ({ success: false, message: 'not available in v1' }),
};

export const userAPI = {
  getSummary: async () => ({ success: true }),
};

export const filesAPI = {
  pick: async (
    mode: "files" | "directory",
    multiple = true
  ): Promise<{ paths: string[]; cancelled: boolean }> => {
    const response = await apiClient.post<{ paths: string[]; cancelled: boolean }>("/files/pick", {
      mode,
      multiple,
    });
    return response.data;
  },
};

export default apiClient;
