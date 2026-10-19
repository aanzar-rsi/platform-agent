// MCP helper — registry + tools catalog from client2.0 API
import { getAccessToken, healthAPI, mcpAPI, toolsAPI } from './api';

const API_HOST = (import.meta.env.VITE_API_URL || 'http://localhost:5000').replace(/\/$/, '');

export interface MCPTool {
  name: string;
  description: string;
  inputSchema?: any;
  parameters?: Array<{
    name: string;
    type?: string;
    description?: string;
    required?: boolean;
  }>;
  server_id?: string;
  server_name?: string;
}

export interface MCPPrompt {
  name: string;
  description?: string;
  arguments?: any[];
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

export async function pingBackend(timeoutMs = 3000): Promise<boolean> {
  try {
    const live = await Promise.race([
      healthAPI.live().then(() => true),
      new Promise<boolean>((resolve) => setTimeout(() => resolve(false), timeoutMs)),
    ]);
    return live;
  } catch {
    return false;
  }
}

export async function fetchToolsCatalog(): Promise<{ internal: MCPTool[]; mcp: MCPTool[] }> {
  void getAccessToken;
  void API_HOST;
  try {
    const catalog = await toolsAPI.list();
    return {
      internal: (catalog.internal || []).map((t) => ({
        name: t.name,
        description: t.description || '',
        parameters: t.parameters,
      })),
      mcp: (catalog.mcp || []).map((t) => ({
        name: t.name,
        description: t.description || '',
        parameters: t.parameters,
        server_id: t.server_id,
        server_name: t.server_name,
      })),
    };
  } catch {
    return { internal: [], mcp: [] };
  }
}

/** @deprecated use fetchToolsCatalog — returns MCP section only */
export async function fetchMCPTools(): Promise<MCPTool[]> {
  try {
    await mcpAPI.listServers();
  } catch {
    /* ignore */
  }
  const { mcp } = await fetchToolsCatalog();
  return mcp;
}

export async function fetchMCPPrompts(): Promise<MCPPrompt[]> {
  return [];
}

export async function fetchMCPResources(): Promise<MCPResource[]> {
  return [];
}
