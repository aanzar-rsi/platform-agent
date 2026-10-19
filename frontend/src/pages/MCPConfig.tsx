import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { useNavigate, useLocation } from "react-router";
import {
  ArrowLeft, Server, RefreshCw, Settings, Plus,
  Trash2, Edit, Power, PowerOff, Wrench, MessageSquare,
  AlertCircle, Upload, ChevronDown, ChevronRight, CheckSquare, Search,
  Activity, Zap, Database, TrendingUp
} from "lucide-react";
import { toast } from "sonner";
import { mcpAPI, MCPServer, MCPServerCreateRequest, MCPServerDetails } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import HeaderNavbar from "@/components/HeaderNavbar";
import Breadcrumb from "@/components/Breadcrumb";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type ViewMode = 'list' | 'add' | 'edit' | 'details';
type ConnectionStatus = 'connected' | 'disconnected' | 'error' | 'connecting';

export default function MCPConfig({ embedded = false }: { embedded?: boolean }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedServerId, setSelectedServerId] = useState<string | null>(null);
  const [serverDetails, setServerDetails] = useState<MCPServerDetails | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [mcpStatus, setMcpStatus] = useState<{ connected: boolean; server_url?: string }>({ connected: false });
  const [enabledTools, setEnabledTools] = useState<Set<string>>(new Set());
  const [importOpen, setImportOpen] = useState(false);
  const [importText, setImportText] = useState<string>(`{\n  "mcpServers": {\n    "Playwright": {\n      "command": "npx",\n      "args": ["-y", "@playwright/mcp@latest"]\n    }\n  }\n}`);
  const [isEditingConfig, setIsEditingConfig] = useState(false);
  const [editConfig, setEditConfig] = useState<MCPServerCreateRequest | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [connectingAll, setConnectingAll] = useState(false);
  const [connectionLogs, setConnectionLogs] = useState<Array<{ timestamp: string; level: string; message: string }>>([]);
  const [collapsedServers, setCollapsedServers] = useState<Set<string>>(new Set());
  const [allToolsByServer, setAllToolsByServer] = useState<Map<string, { serverName: string; tools: any[]; connected: boolean }>>(new Map());
  const [connectionLogsCollapsed, setConnectionLogsCollapsed] = useState(true);
  const [toolSearchQuery, setToolSearchQuery] = useState("");
  const [argsText, setArgsText] = useState('[]');
  const [envText, setEnvText] = useState('{}');
  const [connectionErrors, setConnectionErrors] = useState<Record<string, string>>({});

  // Form state
  const [formData, setFormData] = useState<MCPServerCreateRequest>({
    name: "",
    url: "",
    transport: "streamable_http",
    description: "",
    timeout: 30000,
    retry_attempts: 3,
    retry_delay: 1000,
    enabled: true
  });

  useEffect(() => {
    // Don't auto-connect on initial load - backend handles this during agent startup
    loadServers(false);
    loadMcpStatus();
  }, []);

  useEffect(() => {
    // Check URL parameters for view or edit mode after servers are loaded
    if (servers.length === 0) return;

    const params = new URLSearchParams(location.search);
    const viewId = params.get('view');
    const serverId = params.get('server');
    const addParam = params.get('add');
    const editParam = params.get('edit');

    // Reset to list view if no params and not already in list view
    // Also check if location state has reset flag
    const shouldReset = (location.state as any)?.reset || (!viewId && !serverId && !addParam && !editParam);
    
    if (shouldReset) {
      if (viewMode !== 'list') {
        setViewMode('list');
        setSelectedServerId(null);
        resetForm();
        // Clear the reset flag from state
        if ((location.state as any)?.reset) {
          window.history.replaceState({}, '', location.pathname);
        }
      }
    } else if (viewId && viewId !== selectedServerId) {
      viewDetails(viewId);
    } else if (serverId || editParam) {
      const id = serverId || editParam;
      const server = servers.find(s => s.id === id);
      if (server && viewMode !== 'edit') {
        startEdit(server);
      }
    } else if (addParam && viewMode !== 'add') {
      setViewMode('add');
      resetForm();
    }
  }, [servers, location.search, location.pathname, location.key, location.state]);

  const loadServers = async (ensureConnect = false) => {
    try {
      setLoading(true);
      const response = await mcpAPI.listServers();

      // Refresh MCP status to get current connection state
      await loadMcpStatus();

      setServers(response.servers);

      // Only auto-connect if explicitly requested (not on initial load, backend handles that)
      if (ensureConnect) {
        for (const s of response.servers) {
          if (s.enabled && s.connection_status !== 'connected') {
            try { await mcpAPI.connectServer(s.id); } catch { }
          }
        }
        // Refresh after connecting
        await loadMcpStatus();
        const refreshed = await mcpAPI.listServers();
        setServers(refreshed.servers);
      }

      // If no servers, show add form
      if (response.servers.length === 0) {
        setViewMode('add');
      }
    } catch (error: any) {
      toast.error(`Failed to load servers: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadMcpStatus = async () => {
    try {
      const status = await mcpAPI.getStatus();
      setMcpStatus(status);
    } catch (error) {
      console.log(error)
      // Ignore errors
    }
  };

  const loadServerDetails = async (serverId: string) => {
    try {
      setLoadingDetails(true);
      const detailsResp = await mcpAPI.getServerDetails(serverId, true);

      // Extract details from the updated API response
      const details = (detailsResp.details || {}) as MCPServerDetails;
      const server = detailsResp.server;
      setConnectionLogs(details.logs || []);

      // Set server name and URL from server object
      details.server_name = server.name;
      details.server_url = server.url;

      // Use dynamic is_connected from API
      details.connected = server.is_connected === true;

      setServerDetails(details);
      // Initialize all tools as enabled by default
      if (details.tools) {
        setEnabledTools(new Set(details.tools.map((t: any) => t.name)));
      }

      // Update allToolsByServer map for grouping
      if (details.tools && details.tools.length > 0) {
        setAllToolsByServer(prev => {
          const newMap = new Map(prev);
          newMap.set(serverId, {
            serverName: details.server_name || server.name,
            tools: details.tools || [],
            connected: details.connected || false
          });
          return newMap;
        });
      } else {
        setAllToolsByServer(prev => { const next = new Map(prev); next.delete(serverId); return next; });
      }
    } catch (error: any) {
      toast.error(`Failed to load server details: ${error.message}`);
    } finally {
      setLoadingDetails(false);
    }
  };

  const toggleToolEnabled = (toolName: string) => {
    setEnabledTools(prev => {
      const newSet = new Set(prev);
      if (newSet.has(toolName)) {
        newSet.delete(toolName);
      } else {
        newSet.add(toolName);
      }
      return newSet;
    });
  };

  // const toggleServerCollapse = (serverId: string) => {
  //   setCollapsedServers(prev => {
  //     const newSet = new Set(prev);
  //     if (newSet.has(serverId)) {
  //       newSet.delete(serverId);
  //     } else {
  //       newSet.add(serverId);
  //     }
  //     return newSet;
  //   });
  // };

  // const selectAllToolsForServer = (serverId: string) => {
  //   const serverData = allToolsByServer.get(serverId);
  //   if (!serverData) return;

  //   setEnabledTools(prev => {
  //     const newSet = new Set(prev);
  //     serverData.tools.forEach(tool => {
  //       newSet.add(tool.name);
  //     });
  //     return newSet;
  //   });
  // };

  // const deselectAllToolsForServer = (serverId: string) => {
  //   const serverData = allToolsByServer.get(serverId);
  //   if (!serverData) return;

  //   setEnabledTools(prev => {
  //     const newSet = new Set(prev);
  //     serverData.tools.forEach(tool => {
  //       newSet.delete(tool.name);
  //     });
  //     return newSet;
  //   });
  // };

  // const areAllToolsSelectedForServer = (serverId: string): boolean => {
  //   const serverData = allToolsByServer.get(serverId);
  //   if (!serverData || serverData.tools.length === 0) return false;

  //   return serverData.tools.every(tool => enabledTools.has(tool.name));
  // };

  const handleAddServer = async () => {
    try {
      if (!formData.name || (!formData.url && !formData.command)) {
        toast.error("Name and URL or command are required");
        return;
      }

      const args = JSON.parse(argsText);
      const env = JSON.parse(envText);
      if (!Array.isArray(args) || !args.every(a => typeof a === 'string') || !env || Array.isArray(env) || typeof env !== 'object' || !Object.values(env).every(v => typeof v === 'string')) {
        throw new Error('Arguments must be a JSON string array and environment must be a JSON string map');
      }
      const response = await mcpAPI.createServer({ ...formData, args, env });
      setConnectionLogs(response.server.connection_logs || []);
      if (response.server.connection_logs?.length) setConnectionLogsCollapsed(false);
      if (response.server.connected) toast.success("Server registered and connected");
      else if (formData.enabled === false) toast.success("Server registered (disabled)");
      else {
        setConnectionErrors(prev => ({ ...prev, [response.server.id]: response.server.connection_error || 'Connection failed' }));
        toast.error(`Server registered; connection failed: ${response.server.connection_error}`);
      }
      setViewMode('list');
      resetForm();
      loadServers();
    } catch (error: any) {
      toast.error(`Failed to create server: ${error.message}`);
    }
  };

  const handleUpdateServer = async () => {
    if (!selectedServerId) return;

    try {
      const args = JSON.parse(argsText);
      const env = JSON.parse(envText);
      if (!Array.isArray(args) || !args.every(a => typeof a === 'string') || !env || Array.isArray(env) || typeof env !== 'object' || !Object.values(env).every(v => typeof v === 'string')) {
        throw new Error('Arguments must be a JSON string array and environment must be a JSON string map');
      }
      await mcpAPI.updateServer(selectedServerId, { ...formData, args, env });
      toast.success("Server updated successfully");
      setViewMode('list');
      resetForm();
      setSelectedServerId(null);
      loadServers();
    } catch (error: any) {
      toast.error(`Failed to update server: ${error.message}`);
    }
  };

  const handleDeleteServer = async (serverId: string) => {
    if (!confirm("Are you sure you want to delete this server?")) return;

    try {
      await mcpAPI.deleteServer(serverId);
      toast.success("Server deleted successfully");
      loadServers();
      if (selectedServerId === serverId) {
        setViewMode('list');
        setSelectedServerId(null);
      }
    } catch (error: any) {
      toast.error(`Failed to delete server: ${error.message}`);
    }
  };

  const handleConnect = async (serverId: string) => {
    try {
      setConnecting(true);
      setConnectionLogs([]); // Clear previous logs
      const response = await mcpAPI.connectServer(serverId);
      if (response.logs && response.logs.length > 0) {
        setConnectionLogs(response.logs);
      }
      if (response.success) {
        setConnectionErrors(prev => { const next = { ...prev }; delete next[serverId]; return next; });
        toast.success(response.message);
        await loadMcpStatus();
        await loadServers();
        if (viewMode === 'details' && selectedServerId === serverId) {
          await loadServerDetails(serverId);
        }
      } else {
        setConnectionLogs(response.logs || []);
        setConnectionLogsCollapsed(false);
        toast.error(response.message);
        await loadServers();
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      const message = typeof detail === 'string' ? detail : detail?.message || error.message;
      if (detail?.logs?.length) {
        setConnectionLogs(detail.logs);
        setConnectionLogsCollapsed(false);
      }
      setConnectionErrors(prev => ({ ...prev, [serverId]: message }));
      toast.error(message);
      await loadServers();
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async (serverId?: string) => {
    try {
      setConnecting(true);
      const response = await mcpAPI.disconnectServer(serverId);
      toast.success(response.message);
      await loadMcpStatus();
      await loadServers();
      if (viewMode === 'details' && selectedServerId && (!serverId || serverId === selectedServerId)) {
        await loadServerDetails(selectedServerId);
      }
    } catch (error: any) {
      toast.error(`Failed to disconnect: ${error.message}`);
      await loadServers();
    } finally {
      setConnecting(false);
    }
  };

  const handleConnectAll = async () => {
    try {
      setConnectingAll(true);
      const res = await mcpAPI.listServers();
      const logs: Array<{ timestamp: string; level: string; message: string }> = [];
      for (const s of res.servers) {
        if (s.enabled && s.connection_status !== 'connected') {
          try {
            const response = await mcpAPI.connectServer(s.id);
            logs.push(...(response.logs || []));
          } catch (error: any) {
            const detail = error.response?.data?.detail;
            logs.push(...(detail?.logs || [{ timestamp: new Date().toISOString(), level: 'ERROR', message: typeof detail === 'string' ? detail : detail?.message || error.message }]));
          }
        }
      }
      setConnectionLogs(logs);
      if (logs.length) setConnectionLogsCollapsed(false);
      await loadMcpStatus();
      await loadServers();
    } catch {
      // ignore errors in batch
    } finally {
      setConnectingAll(false);
    }
  };

  const resetForm = () => {
    setArgsText('[]');
    setEnvText('{}');
    setFormData({
      name: "",
      url: "",
      transport: "streamable_http",
      description: "",
      timeout: 30000,
      retry_attempts: 3,
      retry_delay: 1000,
      enabled: true
    });
  };

  const startEdit = (server: MCPServer) => {
    setArgsText(JSON.stringify(server.args || []));
    setEnvText(JSON.stringify(server.env || {}));
    setSelectedServerId(server.id);
    setFormData({
      name: server.name,
      url: server.url,
      transport: server.transport || (server.command ? 'stdio' : 'streamable_http'),
      command: server.command,
      args: server.args,
      env: server.env,
      description: server.description || "",
      timeout: server.timeout,
      retry_attempts: server.retry_attempts,
      retry_delay: server.retry_delay,
      enabled: server.enabled
    });
    setViewMode('edit');
  };

  const viewDetails = async (serverId: string) => {
    setSelectedServerId(serverId);
    setViewMode('details');
    // Load the server's live connection and tool list.
    await loadServerDetails(serverId);
    navigate(`${embedded ? "/agents/mcp-config" : "/mcp-config"}?view=${serverId}`)
  };

  const getConnectionBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return (
          <Badge className="bg-green-700 text-white border-0 shadow-lg shadow-green-500/25 py-1 cursor-default">
            <span className="w-1.5 h-1.5 rounded-full bg-white mr-1.5 animate-pulse"></span>
            Connected
          </Badge>
        );
      case 'error':
        return (
          <Badge className="bg-red-700 text-white border-0 shadow-lg shadow-red-500/25 py-1 cursor-default">
            <span className="w-1.5 h-1.5 rounded-full bg-white mr-1.5"></span>
            Error
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="border-red-500 text-red-500 text-xs px-2 py-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-1.5"></span>
            Disconnected
          </Badge>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <RefreshCw className="h-10 w-10 animate-spin text-brand relative" />
          </div>
          <p className="text-gray-900 text-sm">Loading servers...</p>
        </div>
      </div>
    );
  }

  // Build breadcrumb items based on view mode
  const getBreadcrumbItems = () => {
    const items = [{ label: "Chat", path: "/" }];
    if (viewMode === 'list') {
      items.push({ label: "MCP Config", path: "/mcp-config" });
    } else if (viewMode === 'add') {
      items.push({ label: "MCP Config", path: "/mcp-config" });
      items.push({ label: "Add Server", path: "/mcp-config?add=true" });
    } else if (viewMode === 'edit' && selectedServerId) {
      items.push({ label: "MCP Config", path: "/mcp-config" });
      items.push({ label: "Edit Server", path: `/mcp-config?edit=${selectedServerId}` });
    } else if (viewMode === 'details' && selectedServerId) {
      items.push({ label: "MCP Config", path: "/mcp-config" });
      const server = servers.find(s => s.id === selectedServerId);
      items.push({ label: server?.name || "Server Details", path: `/mcp-config?view=${selectedServerId}` });
    }
    return items;
  };

  return (
    <div className={`${embedded ? "h-full overflow-y-auto" : "min-h-screen"} bg-[#f8f8f6]`}>
      {!embedded && <HeaderNavbar variant="app" isAuthenticated={isAuthenticated} />}
      {!embedded && <Breadcrumb items={getBreadcrumbItems()} />}

      <div className={`container max-w-[90%] mx-auto px-6 mb-10 ${embedded ? "pt-8" : "pt-32"}`}>
        <h1 className="text-3xl font-bold text-[#171717] mb-6">
          {viewMode === 'add' ? 'Add Server' : viewMode === 'edit' ? 'Edit Server' : viewMode === 'details' ? 'Server Details' : 'MCP Config'}
        </h1>
        {viewMode === 'list' && (
          <>
            {/* Server Analytics */}
            <Card className="bg-linear-to-b from-[#fffeff] to-[#f8f8f6] border-2 border-[#171717]/20 rounded-2xl shadow-xl mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-[#171717] text-xl">
                  <Activity className="h-5 w-5 text-[#171717]" />
                  Server Analytics
                </CardTitle>
                <CardDescription className="text-gray-600">
                  Overview of your MCP server infrastructure
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    {
                      title: "Total Servers",
                      value: servers.length,
                      description: `${servers.filter(s => s.enabled).length} enabled`,
                      Icon: Server,
                      color: "text-[#171717]"
                    },
                    {
                      title: "Connected",
                      value: servers.filter(s => s.is_connected).length,
                      description: `${servers.length > 0 ? Math.round((servers.filter(s => s.is_connected).length / servers.length) * 100) : 0}% active`,
                      Icon: Zap,
                      color: "text-green-600"
                    },
                    {
                      title: "Available Tools",
                      value: allToolsByServer.size > 0 
                        ? Array.from(allToolsByServer.values()).reduce((sum, group) => sum + (group.tools?.length || 0), 0)
                        : serverDetails?.tools?.length || 0,
                      description: allToolsByServer.size > 0 
                        ? `${allToolsByServer.size} server${allToolsByServer.size !== 1 ? 's' : ''} loaded`
                        : "View server to see tools",
                      Icon: Wrench,
                      color: "text-neutral-600"
                    },
                    {
                      title: "Last Activity",
                      value: servers.length > 0 && servers.some(s => s.last_connected)
                        ? new Date(Math.max(...servers.filter(s => s.last_connected).map(s => new Date(s.last_connected || 0).getTime()))).toLocaleDateString()
                        : "Never",
                      description: "Most recent connection",
                      Icon: TrendingUp,
                      color: "text-neutral-600"
                    },
                  ].map(({ title, value, description, Icon, color }, index) => (
                    <div
                      key={title}
                      className={`p-4 rounded-2xl border-2 border-[#171717]/20 bg-linear-to-b ${index % 2 === 0 ? 'from-[#fffeff] to-[#f8f8f6]' : 'from-[#f8f8f6] to-[#fffeff]'} hover:border-[#171717]/40 transition-all`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <Icon className={`h-5 w-5 ${color}`} />
                        <div className="text-2xl font-bold text-[#171717]">{value}</div>
                      </div>
                      <div className="text-sm font-medium text-[#171717] mb-1">{title}</div>
                      <div className="text-xs text-gray-600">{description}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons Section */}
            <Card className="bg-linear-to-b from-[#fffeff] to-[#f8f8f6] border-2 border-[#171717]/20 rounded-2xl shadow-xl mb-6">
              <CardContent className="p-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div>
                    <h3 className="text-lg font-semibold text-[#171717] mb-1">Quick Actions</h3>
                    <p className="text-sm text-gray-600">Manage your MCP servers</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      onClick={() => setImportOpen(true)}
                      className="text-[#171717] border-2 border-[#171717]/30 hover:bg-[#171717] hover:text-white shadow-xl rounded-xl px-6"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Import
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleConnectAll}
                      className="text-[#171717] border-2 border-[#171717]/30 hover:bg-[#171717] hover:text-white shadow-xl rounded-xl px-6"
                      disabled={connectingAll}
                    >
                      {connectingAll ? (
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Power className="mr-2 h-4 w-4" />
                      )}
                      {connectingAll ? 'Connecting...' : 'Connect All'}
                    </Button>
                    <Button
                      onClick={() => {
                        resetForm();
                        setViewMode('add');
                      }}
                      className="bg-[#171717] hover:bg-[#171717]/90 transition-all text-white border-0 shadow-xl rounded-xl px-6"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Server
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
        {/* Import Dialog */}
        <Dialog open={importOpen} onOpenChange={setImportOpen}>
          <DialogContent className="bg-linear-to-b from-[#fffeff] to-[#f8f8f6] border-2 border-[#171717]/20 shadow-2xl rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold text-[#171717] flex items-center gap-3">
                <Upload className="h-5 w-5 text-[#171717]" />
                Import mcp.json
              </DialogTitle>
              <DialogDescription className="text-gray-600 text-sm">
                Paste your Cursor-style mcp.json. We'll add stdio servers (command/args/env).
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <Textarea
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                rows={12}
                className="bg-[#fffeff] border-2 border-[#171717]/20 text-[#171717] font-mono focus:border-[#171717]/40 focus:ring-[#171717]/20 transition-all rounded-xl"
              />
              <div className="flex justify-end gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setImportOpen(false)}
                  className="text-[#171717] border-2 border-[#171717]/30 text-sm px-8 hover:bg-[#171717] hover:text-white shadow-xl transition-all rounded-xl"
                >
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    try {
                      const parsed = JSON.parse(importText);
                      const res = await mcpAPI.importConfig(parsed);
                      const failed = res.created.filter(s => !s.connected);
                      if (failed.length) toast.error(`Imported ${res.count} servers; ${failed.length} failed to connect: ${failed.map(s => `${s.name}: ${s.connection_error}`).join('; ')}`);
                      else toast.success(`Imported and connected ${res.count} servers`);
                      for (const server of failed) setConnectionErrors(prev => ({ ...prev, [server.id]: server.connection_error || 'Connection failed' }));
                      setImportOpen(false);
                      loadServers();
                    } catch (e: any) {
                      toast.error(`Import failed: ${e.message}`);
                    }
                  }}
                  className="bg-[#171717] hover:bg-[#171717]/90 text-white border-0 shadow-xl transition-all rounded-xl"
                >
                  Import
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* List View */}
        {viewMode === 'list' && (
          <>
            {servers.length === 0 ? (
              <Card className="bg-linear-to-b from-[#fffeff] to-[#f8f8f6] border-2 border-[#171717]/20 rounded-2xl overflow-hidden relative shadow-xl">
                <CardContent className="pt-12 pb-12 relative">
                  <div className="text-center py-8">
                    <div className="relative inline-block mb-6">
                      <div className="relative p-6 rounded-2xl border-2 border-[#171717]/30 bg-[#fffeff]">
                        <Server className="h-12 w-12 mx-auto text-[#171717]" />
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold text-[#171717] mb-3">No MCP Servers Configured</h3>
                    <p className="text-gray-600 mb-8 max-w-md mx-auto">Get started by adding your first MCP server to enable powerful tools and capabilities</p>
                    <Button
                      onClick={() => setViewMode('add')}
                      className="bg-[#171717] hover:bg-[#171717]/90 transition-all text-white border-0 shadow-xl rounded-xl"
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Add Your First Server
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {servers.map((server, index) => {
                  const isCurrentlyConnected = server.is_connected === true;

                  return (
                    <Card
                      key={server.id}
                      onClick={() => viewDetails(server.id)}
                      className={`p-5 border-2 border-[#171717]/20 bg-linear-to-b ${index % 2 === 0 ? 'from-[#fffeff] to-[#f8f8f6]' : 'from-[#f8f8f6] to-[#fffeff]'} hover:border-[#171717]/40 hover:bg-[#171717]/5 backdrop-blur-sm rounded-2xl shadow-xl transition-all cursor-pointer h-full flex flex-col`}
                    >
                      <CardContent className="relative p-0 flex-1 flex flex-col">
                        <div className="flex-1">
                          <div className="flex items-start justify-between gap-3 mb-3">
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <div className="relative shrink-0">
                                {isCurrentlyConnected ? (
                                  <div className="h-10 w-10 rounded-xl bg-green-600 border-2 border-green-600 flex items-center justify-center">
                                    <Server className="h-5 w-5 text-white" />
                                  </div>
                                ) : (
                                  <div className="h-10 w-10 rounded-xl bg-gray-400 border-2 border-gray-400 flex items-center justify-center">
                                    <Server className="h-5 w-5 text-white" />
                                  </div>
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <h3 className="font-semibold text-[#171717] text-base truncate mb-1">{server.name}</h3>
                                <p className="text-xs text-gray-600 truncate" title={server.url || server.command}>{server.url || `${server.command} ${(server.args || []).join(' ')}`}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => startEdit(server)}
                                className="border-2 border-[#171717]/30 hover:bg-[#171717] text-[#171717] hover:text-white h-7 w-7 p-0 transition-all rounded-lg"
                                title="Edit"
                              >
                                <Edit className="h-3 w-3" />
                              </Button>
                              {isCurrentlyConnected ? (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleDisconnect(server.id)}
                                  className="border-2 border-[#171717]/30 hover:bg-[#171717] text-[#171717] hover:text-white h-7 w-7 p-0 transition-all rounded-lg"
                                  title="Disconnect"
                                >
                                  <PowerOff className="h-3 w-3" />
                                </Button>
                              ) : (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleConnect(server.id)}
                                  className="border-2 border-[#171717]/30 hover:bg-[#171717] text-[#171717] hover:text-white h-7 w-7 p-0 transition-all rounded-lg"
                                  disabled={!server.enabled}
                                  title="Connect"
                                >
                                  <Power className="h-3 w-3" />
                                </Button>
                              )}
                            </div>
                          </div>
                          {server.description && (
                            <p className="text-xs text-gray-600 mb-3 line-clamp-2">{server.description}</p>
                          )}
                          <div className="flex items-center gap-2 flex-wrap text-xs mt-auto pt-3">
                            <div className="flex items-center gap-1 px-2 text-[#171717]/70 py-0.5 rounded border border-[#171717]/30 bg-[#171717]/5">
                              <span className="w-1 h-1 rounded-full bg-[#171717]"></span>
                              <span>{server.timeout}ms</span>
                            </div>
                            <div className="flex items-center gap-1 px-2 text-[#171717]/70 py-0.5 rounded border border-[#171717]/30 bg-[#171717]/5">
                              <span className="w-1 h-1 rounded-full bg-[#171717]"></span>
                              <span>Retries: {server.retry_attempts}</span>
                            </div>
                            {server.last_connected && (
                              <div className="flex items-center gap-1 px-2 text-[#171717]/70 py-0.5 rounded border border-[#171717]/30 bg-[#171717]/5">
                                <span className="w-1 h-1 rounded-full bg-[#171717]"></span>
                                <span>{new Date(server.last_connected).toLocaleDateString()}</span>
                              </div>
                            )}
                          </div>
                        </div>
                          <div className="mt-3 pt-3 border-t border-[#171717]/10">
                            {getConnectionBadge(isCurrentlyConnected ? 'connected' : 'disconnected')}
                            {(connectionErrors[server.id] || server.connection_error) && <p className="text-xs text-red-700 mt-2">{connectionErrors[server.id] || server.connection_error}</p>}
                          </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* Add/Edit Form */}
        {(viewMode === 'add' || viewMode === 'edit') && (
          <Card className="bg-linear-to-b from-[#fffeff] to-[#f8f8f6] border-2 border-[#171717]/20 rounded-2xl shadow-xl overflow-hidden relative">
            <CardHeader className="relative">
              <div className="flex items-center gap-3 mb-2">
                <div className="relative">
                  <Settings className="h-6 w-6 text-[#171717] relative" />
                </div>
                <CardTitle className="text-2xl font-bold text-[#171717]">
                  {viewMode === 'add' ? 'Add New Server' : 'Edit Server'}
                </CardTitle>
              </div>
              <CardDescription className="text-gray-600 text-sm">
                Configure the MCP server connection parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 relative">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-[#171717] font-medium">Server Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="My MCP Server"
                    className="bg-[#fffeff] border-2 border-[#171717]/20 hover:border-[#171717]/40 text-[#171717] placeholder:text-gray-500 rounded-xl"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="url" className="text-[#171717] font-medium">Server URL *</Label>
                  <Input
                    id="url"
                    value={formData.url || ''}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value, command: e.target.value ? undefined : formData.command, transport: e.target.value ? (formData.transport === 'sse' ? 'sse' : 'streamable_http') : formData.transport })}
                    placeholder="http://localhost:8000/mcp"
                    className="bg-[#fffeff] border-2 border-[#171717]/20 hover:border-[#171717]/40 text-[#171717] placeholder:text-gray-500 rounded-xl"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="space-y-2">
                  <Label htmlFor="command">Stdio command (instead of URL)</Label>
                  <Input id="command" value={formData.command || ''}
                    onChange={(e) => setFormData({ ...formData, command: e.target.value, url: e.target.value ? '' : formData.url, transport: e.target.value ? 'stdio' : formData.transport })}
                    placeholder="npx" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="args">Arguments (JSON array)</Label>
                  <Input id="args" value={argsText}
                    onChange={(e) => setArgsText(e.target.value)}
                    placeholder='["-y", "@playwright/mcp"]' />
                </div>
              </div>
              {formData.url && <div className="space-y-2">
                <Label htmlFor="transport">HTTP transport</Label>
                <select id="transport" value={formData.transport === 'sse' ? 'sse' : 'streamable_http'}
                  onChange={(e) => setFormData({ ...formData, transport: e.target.value as 'sse' | 'streamable_http' })}
                  className="w-full rounded-xl border-2 border-[#171717]/20 bg-white p-2 text-[#171717]">
                  <option value="streamable_http">Streamable HTTP</option>
                  <option value="sse">Legacy SSE</option>
                </select>
              </div>}
              <div className="space-y-2">
                <Label htmlFor="env">Environment (JSON object, optional)</Label>
                <Textarea id="env" value={envText} onChange={(e) => setEnvText(e.target.value)}
                  placeholder='{"API_KEY":"value"}' />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description" className="text-[#171717] font-medium">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description of this server"
                  className="bg-[#fffeff] border-2 border-[#171717]/20 hover:border-[#171717]/40 text-[#171717] placeholder:text-gray-500 rounded-xl"
                  rows={3}
                />
              </div>

              <Separator className="bg-[#171717]/10" />

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="space-y-2">
                  <Label htmlFor="timeout" className="text-[#171717] font-medium">Timeout (ms)</Label>
                  <Input
                    id="timeout"
                    type="number"
                    value={formData.timeout}
                    onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) || 30000 })}
                    className="bg-[#fffeff] border-2 border-[#171717]/20 hover:border-[#171717]/40 text-[#171717] placeholder:text-gray-500 rounded-xl"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="retryAttempts" className="text-[#171717] font-medium">Retry Attempts</Label>
                  <Input
                    id="retryAttempts"
                    type="number"
                    value={formData.retry_attempts}
                    onChange={(e) => setFormData({ ...formData, retry_attempts: parseInt(e.target.value) || 3 })}
                    className="bg-[#fffeff] border-2 border-[#171717]/20 hover:border-[#171717]/40 text-[#171717] placeholder:text-gray-500 rounded-xl"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="retryDelay" className="text-[#171717] font-medium">Retry Delay (ms)</Label>
                  <Input
                    id="retryDelay"
                    type="number"
                    value={formData.retry_delay}
                    onChange={(e) => setFormData({ ...formData, retry_delay: parseInt(e.target.value) || 1000 })}
                    className="bg-[#fffeff] border-2 border-[#171717]/20 hover:border-[#171717]/40 text-[#171717] placeholder:text-gray-500 rounded-xl"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-[#171717]/10">
                <Button
                  variant="outline"
                  onClick={() => {
                    setViewMode('list');
                    resetForm();
                    setSelectedServerId(null);
                  }}
                  className="text-[#171717] border-2 border-[#171717]/30 text-sm px-8 hover:bg-[#171717] hover:text-white shadow-xl transition-all rounded-xl"
                >
                  Cancel
                </Button>
                <Button
                  onClick={viewMode === 'add' ? handleAddServer : handleUpdateServer}
                  className="bg-[#171717] hover:bg-[#171717]/90 transition-all text-white border-0 shadow-xl rounded-xl"
                >
                  <Settings className="h-4 w-4" />
                  {viewMode === 'add' ? 'Create Server' : 'Save Changes'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Server Details View */}
        {viewMode === 'details' && serverDetails && (
          <div className="space-y-6">
            {/* Server Header Card */}
            <Card className="bg-linear-to-b from-[#fffeff] to-[#f8f8f6] border-2 border-[#171717]/20 rounded-2xl shadow-xl overflow-hidden relative">
              {/* <div className="absolute inset-0 bg-linear-to-br from-primary-500/5 via-transparent to-transparent"></div> */}
              <CardHeader className="relative pb-4">
                <div className="flex items-start justify-between gap-6">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-4 mb-3">
                      <div className="relative">
                        {/* <div className={`absolute inset-0 ${(serverDetails.connected || mcpStatus.connected) ? 'bg-green-500/20' : 'bg-primary-500/20'} rounded-xl blur-xl`}></div> */}
                        <div className="relative p-3 rounded-xl border border-neutral-700/50">
                          {serverDetails.connected ? (
                            <div className="h-10 w-10 rounded-lg bg-green-800 border border-green-800 flex items-center justify-center">
                              <Server className="h-6 w-6 text-white" />
                            </div>
                          ) : (
                            <div className="h-10 w-10 rounded-lg bg-gray-500 border border-gray-500 flex items-center justify-center">
                              <Server className="h-6 w-6 text-neutral-400" />
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-2xl font-bold text-[#171717] mb-2 flex items-center gap-3">
                          {serverDetails.server_name}
                          {!isEditingConfig && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                const current = servers.find(s => s.id === (selectedServerId || ''));
                                if (current) {
                                  setEditConfig({
                                    name: current.name,
                                    url: current.url,
                                    transport: current.transport || (current.command ? 'stdio' : 'streamable_http'),
                                    command: current.command,
                                    args: current.args,
                                    env: current.env,
                                    description: current.description || '',
                                    timeout: current.timeout,
                                    retry_attempts: current.retry_attempts,
                                    retry_delay: current.retry_delay,
                                    enabled: current.enabled,
                                  });
                                  setArgsText(JSON.stringify(current.args || []));
                                  setEnvText(JSON.stringify(current.env || {}));
                                  setIsEditingConfig(true);
                                }
                              }}
                              className="h-8 w-8 text-[#171717] hover:bg-[#171717]/10 transition-all rounded-lg"
                              title="Edit configuration"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}
                        </CardTitle>
                        <CardDescription className="text-gray-600 break-all font-mono text-sm">
                          {serverDetails.server_url}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {getConnectionBadge(serverDetails.connected ? 'connected' : 'disconnected')}
                      {selectedServerId && (connectionErrors[selectedServerId] || servers.find(s => s.id === selectedServerId)?.connection_error) && <span className="text-sm text-red-700">{connectionErrors[selectedServerId] || servers.find(s => s.id === selectedServerId)?.connection_error}</span>}
                      <Button
                        size="sm"
                        disabled={connecting}
                        onClick={() => serverDetails.connected ? handleDisconnect(selectedServerId || undefined) : (selectedServerId && handleConnect(selectedServerId))}
                        className={
                          serverDetails.connected
                            ? 'bg-red-500 hover:bg-red-700 text-white shadow-lg shadow-red-500/25 transition-all'
                            : 'bg-green-800 hover:bg-green-700 text-white shadow-lg shadow-green-500/25 transition-all'
                        }
                      >
                        {connecting ? (
                          <>
                            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                            Please wait
                          </>
                        ) : serverDetails.connected ? (
                          <>
                            <PowerOff className="h-4 w-4" />
                            Disconnect
                          </>
                        ) : (
                          <>
                            <Power className="h-4 w-4" />
                            Connect
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                  {isEditingConfig && (
                    <div className="flex gap-2 shrink-0">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => { setIsEditingConfig(false); setEditConfig(null); }}
                        className="text-[#171717] border-2 border-[#171717]/30 text-sm px-8 hover:bg-[#171717] hover:text-white shadow-xl rounded-xl"
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        onClick={async () => {
                          if (!selectedServerId || !editConfig) return;
                          try {
                            await mcpAPI.updateServer(selectedServerId, { ...editConfig, args: JSON.parse(argsText), env: JSON.parse(envText) });
                            toast.success('Server updated');
                            setIsEditingConfig(false);
                            setEditConfig(null);
                            await loadServers();
                            await loadServerDetails(selectedServerId);
                          } catch (e: any) {
                            toast.error(`Update failed: ${e.message}`);
                          }
                        }}
                        className="bg-[#171717] hover:bg-[#171717]/90 transition-all text-white border-0 shadow-xl rounded-xl"
                      >
                        Save Changes
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="relative pt-0">
                {!isEditingConfig ? (
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="p-4 rounded-2xl border-2 border-[#171717]/20 bg-[#fffeff] shadow-lg">
                      <div className="text-xs font-semibold text-[#171717] uppercase tracking-wider mb-2">Name</div>
                      <div className="text-base font-medium text-[#171717]">{serverDetails.server_name}</div>
                    </div>
                    <div className="p-4 rounded-2xl border-2 border-[#171717]/20 bg-[#fffeff] shadow-lg">
                      <div className="text-xs font-semibold text-[#171717] uppercase tracking-wider mb-2">Endpoint / command</div>
                      <div className="text-base font-mono text-[#171717] break-all">{serverDetails.server_url}</div>
                    </div>
                    <div className="p-4 rounded-2xl border-2 border-[#171717]/20 bg-[#fffeff] shadow-lg">
                      <div className="text-xs font-semibold text-[#171717] uppercase tracking-wider mb-2">Timeout</div>
                      <div className="text-base font-medium text-[#171717]">{servers.find(s => s.id === selectedServerId)?.timeout} ms</div>
                    </div>
                    <div className="p-4 rounded-2xl border-2 border-[#171717]/20 bg-[#fffeff] shadow-lg">
                      <div className="text-xs font-semibold text-[#171717] uppercase tracking-wider mb-2">Retry Configuration</div>
                      <div className="text-base font-medium text-[#171717]">
                        {servers.find(s => s.id === selectedServerId)?.retry_attempts} × every {servers.find(s => s.id === selectedServerId)?.retry_delay} ms
                      </div>
                    </div>
                    {servers.find(s => s.id === selectedServerId)?.description && (
                      <div className="sm:col-span-2 p-4 rounded-2xl border-2 border-[#171717]/20 bg-[#fffeff] shadow-lg">
                        <div className="text-xs font-semibold text-[#171717] uppercase tracking-wider mb-2">Description</div>
                        <div className="text-sm text-[#171717] leading-relaxed">{servers.find(s => s.id === selectedServerId)?.description}</div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="grid sm:grid-cols-2 gap-5">
                    <div className="space-y-2">
                      <Label className="text-[#171717] font-medium">Name</Label>
                      <Input
                        className="text-[#171717] border-2 border-[#171717]/20 focus:border-[#171717]/40 bg-[#fffeff] transition-all rounded-xl"
                        value={editConfig?.name || ''}
                        onChange={(e) => setEditConfig(prev => ({ ...(prev as any), name: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-[#171717] font-medium">URL</Label>
                      <Input
                        className="text-[#171717] border-2 border-[#171717]/20 focus:border-[#171717]/40 bg-[#fffeff] transition-all rounded-xl"
                        value={editConfig?.url || ''}
                        onChange={(e) => setEditConfig(prev => ({ ...(prev as any), url: e.target.value, command: e.target.value ? undefined : prev?.command, transport: e.target.value ? (prev?.transport === 'sse' ? 'sse' : 'streamable_http') : prev?.transport }))}
                      />
                    </div>
                    {editConfig?.url && <div className="space-y-2">
                      <Label htmlFor="edit-transport">HTTP transport</Label>
                      <select id="edit-transport" value={editConfig.transport === 'sse' ? 'sse' : 'streamable_http'}
                        onChange={(e) => setEditConfig(prev => prev ? { ...prev, transport: e.target.value as 'sse' | 'streamable_http' } : null)}
                        className="w-full rounded-xl border-2 border-[#171717]/20 bg-white p-2 text-[#171717]">
                        <option value="streamable_http">Streamable HTTP</option>
                        <option value="sse">Legacy SSE</option>
                      </select>
                    </div>}
                    <div className="space-y-2">
                      <Label>Stdio command</Label>
                      <Input value={editConfig?.command || ''}
                        onChange={(e) => setEditConfig(prev => ({ ...(prev as any), command: e.target.value, url: e.target.value ? '' : prev?.url, transport: e.target.value ? 'stdio' : prev?.transport }))} />
                    </div>
                    <div className="space-y-2">
                      <Label>Arguments (JSON array)</Label>
                      <Input value={argsText} onChange={(e) => setArgsText(e.target.value)} />
                    </div>
                    <div className="sm:col-span-2 space-y-2">
                      <Label>Environment (JSON object)</Label>
                      <Textarea value={envText} onChange={(e) => setEnvText(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-[#171717] font-medium">Timeout (ms)</Label>
                      <Input
                        type="number"
                        className="text-[#171717] border-2 border-[#171717]/20 focus:border-[#171717]/40 bg-[#fffeff] transition-all rounded-xl"
                        value={editConfig?.timeout || 0}
                        onChange={(e) => setEditConfig(prev => ({ ...(prev as any), timeout: parseInt(e.target.value) || 0 }))}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-[#171717] font-medium">Retry attempts</Label>
                        <Input
                          type="number"
                          className="text-[#171717] border-2 border-[#171717]/20 focus:border-[#171717]/40 bg-[#fffeff] transition-all rounded-xl"
                          value={editConfig?.retry_attempts || 0}
                          onChange={(e) => setEditConfig(prev => ({ ...(prev as any), retry_attempts: parseInt(e.target.value) || 0 }))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-[#171717] font-medium">Retry delay (ms)</Label>
                        <Input
                          type="number"
                          className="text-[#171717] border-2 border-[#171717]/20 focus:border-[#171717]/40 bg-[#fffeff] transition-all rounded-xl"
                          value={editConfig?.retry_delay || 0}
                          onChange={(e) => setEditConfig(prev => ({ ...(prev as any), retry_delay: parseInt(e.target.value) || 0 }))}
                        />
                      </div>
                    </div>
                    <div className="sm:col-span-2 space-y-2">
                      <Label className="text-[#171717] font-medium">Description</Label>
                      <Textarea
                        rows={3}
                        className="text-[#171717] border-2 border-[#171717]/20 focus:border-[#171717]/40 bg-[#fffeff] transition-all resize-none rounded-xl"
                        value={editConfig?.description || ''}
                        onChange={(e) => setEditConfig(prev => ({ ...(prev as any), description: e.target.value }))}
                      />
                    </div>
                  </div>
                )}

                {/* Connection Logs Section */}
                <div className="mt-6 pt-6 border-t border-[#171717]/10">
                  <button
                    onClick={() => setConnectionLogsCollapsed(!connectionLogsCollapsed)}
                    className="flex items-center gap-3 text-[#171717] hover:text-[#171717]/80 transition-colors group w-full text-left mb-3"
                  >
                    <MessageSquare className="h-5 w-5 text-[#171717]" />
                    <div className="flex items-center gap-3 flex-1">
                      <h3 className="font-semibold text-[#171717]">
                        Connection Logs
                        {connectionLogs.length > 0 && (
                          <Badge variant="outline" className="border-[#171717] text-[#171717] bg-[#171717]/10 ml-2 rounded-xl">
                            {connectionLogs.length}
                          </Badge>
                        )}
                      </h3>
                    </div>
                    {connectionLogsCollapsed ? (
                      <ChevronRight className="h-5 w-5 text-[#171717] group-hover:text-[#171717]/80 transition-colors" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-[#171717] group-hover:text-[#171717]/80 transition-colors" />
                    )}
                  </button>
                  {!connectionLogsCollapsed && (
                    <div className="mt-4">
                      {connectionLogs.length === 0 ? (
                        <div className="text-center py-8 rounded-2xl bg-[#fffeff] border-2 border-[#171717]/20">
                          <MessageSquare className="h-10 w-10 mx-auto text-[#171717] mb-3" />
                          <p className="text-[#171717] text-sm">No connection logs available. Click Connect to see connection process logs.</p>
                        </div>
                      ) : (
                        <div className="rounded-2xl border-2 border-[#171717]/20 bg-[#fffeff] p-4 max-h-96 overflow-y-auto shadow-inner">
                          <div className="space-y-2 font-mono text-xs">
                            {connectionLogs.map((log, idx) => {
                              const levelColor = {
                                INFO: 'text-neutral-600',
                                DEBUG: 'text-gray-600',
                                WARNING: 'text-yellow-600',
                                ERROR: 'text-red-600',
                              }[log.level] || 'text-gray-600';

                              const bgColor = {
                                INFO: 'bg-neutral-500/10 border-neutral-500/30',
                                DEBUG: 'bg-gray-500/10 border-gray-500/30',
                                WARNING: 'bg-yellow-500/10 border-yellow-500/30',
                                ERROR: 'bg-red-500/10 border-red-500/30',
                              }[log.level] || 'bg-gray-500/10 border-gray-500/30';

                              return (
                                <div key={idx} className={`flex gap-3 py-2 px-3 rounded-xl border-2 ${bgColor} transition-all`}>
                                  <span className="text-[#171717] shrink-0 text-[10px] pt-0.5">{log.timestamp}</span>
                                  <span className={`shrink-0 font-semibold ${levelColor} min-w-15`}>
                                    [{log.level}]
                                  </span>
                                  <span className="text-[#171717] flex-1 wrap-break-word leading-relaxed">{log.message}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Tools */}
            <Card className="bg-linear-to-b from-[#fffeff] to-[#f8f8f6] border-2 border-[#171717]/20 rounded-2xl shadow-xl overflow-hidden relative">
              <CardHeader className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Wrench className="h-6 w-6 text-[#171717]" />
                    <div>
                      <CardTitle className="flex items-center gap-3 text-[#171717] text-xl">
                        Available Tools
                        <Badge variant="outline" className="border-[#171717] text-[#171717] bg-[#171717]/10 rounded-xl">
                          {serverDetails.tools?.length || 0}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="text-gray-600 text-sm mt-1">
                        {serverDetails.tools?.length || 0} {serverDetails.tools?.length === 1 ? 'tool' : 'tools'} available from this server
                      </CardDescription>
                    </div>
                  </div>
                  {serverDetails.tools && serverDetails.tools.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const allSelected = serverDetails.tools?.every(tool => enabledTools.has(tool.name)) || false;
                        if (allSelected) {
                          serverDetails.tools?.forEach(tool => {
                            setEnabledTools(prev => {
                              const newSet = new Set(prev);
                              newSet.delete(tool.name);
                              return newSet;
                            });
                          });
                        } else {
                          serverDetails.tools?.forEach(tool => {
                            setEnabledTools(prev => new Set(prev).add(tool.name));
                          });
                        }
                      }}
                      className="text-[#171717] border-2 border-[#171717]/30 text-sm px-4 hover:bg-[#171717] hover:text-white shadow-xl rounded-xl"
                      disabled={!serverDetails.connected}
                    >
                      <CheckSquare className="h-4 w-4" />
                      {serverDetails.tools?.every(tool => enabledTools.has(tool.name)) ? 'Deselect All' : 'Select All'}
                    </Button>
                  )}
                </div>
                {serverDetails.tools && serverDetails.tools.length > 0 && (
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[#171717]" />
                    <Input
                      placeholder="Search tools..."
                      value={toolSearchQuery}
                      onChange={(e) => setToolSearchQuery(e.target.value)}
                      className="pl-9 bg-[#fffeff] border-2 border-[#171717]/20 hover:border-[#171717]/40 text-[#171717] placeholder:text-gray-500 rounded-xl"
                    />
                  </div>
                )}
              </CardHeader>
              <CardContent className="relative">
                {loadingDetails ? (
                  <div className="text-center py-16 bg-[#fffeff] rounded-2xl border-2 border-[#171717]/20">
                    <RefreshCw className="h-10 w-10 animate-spin text-[#171717] mx-auto mb-4" />
                    <p className="text-[#171717]">Loading tools...</p>
                  </div>
                ) : serverDetails.tools_error ? (
                  <div className="text-center py-16 bg-[#fffeff] rounded-2xl border-2 border-[#171717]/20">
                    <AlertCircle className="h-10 w-10 text-red-500 mx-auto mb-4" />
                    <p className="text-[#171717]">Error loading tools</p>
                    <p className="text-sm text-gray-600 mt-2">{serverDetails.tools_error}</p>
                  </div>
                ) : serverDetails.tools && serverDetails.tools.length > 0 ? (
                  <div className="grid gap-4">
                    {serverDetails.tools
                      .filter(tool => {
                        if (!toolSearchQuery) return true;
                        const query = toolSearchQuery.toLowerCase();
                        return tool.name.toLowerCase().includes(query) ||
                          tool.description?.toLowerCase().includes(query) ||
                          Object.keys(tool.parameters?.properties || {}).some(param => param.toLowerCase().includes(query));
                      })
                      .map((tool, idx) => {
                        const isEnabled = enabledTools.has(tool.name);
                        const parameters = tool.parameters || {};
                        const isConnected = serverDetails.connected === true;

                        return (
                          <div
                            key={idx}
                            className={`p-5 border-2 backdrop-blur-sm rounded-2xl shadow-xl flex-col gap-2 h-auto transition-all ${
                              !(isConnected && isEnabled) 
                                ? 'pointer-events-none opacity-70 bg-gray-200 border-gray-400' 
                                : `bg-linear-to-b ${idx % 2 === 0 ? 'from-[#fffeff] to-[#f8f8f6]' : 'from-[#f8f8f6] to-[#fffeff]'} hover:border-[#171717]/40 hover:bg-[#171717]/5 border-[#171717]/20 cursor-pointer`
                            }`}
                          >
                            <div className="flex items-start justify-between gap-6">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-3 mb-3">
                                  <div className="relative">
                                    <div className={`relative p-2 rounded-xl ${isEnabled ? 'bg-[#171717] border-2 border-[#171717]' : 'bg-gray-400 border-2 border-gray-400'}`}>
                                      <Wrench className={`h-5 w-5 ${isEnabled ? 'text-white' : 'text-white'}`} />
                                    </div>
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <h4 className="font-bold text-lg text-[#171717] mb-1">{tool.name}</h4>
                                    {!isEnabled && (
                                      <Badge variant="outline" className="border-[#171717]/30 text-[#171717] text-xs bg-[#171717]/10 rounded-xl">
                                        Disabled
                                      </Badge>
                                    )}
                                  </div>
                                </div>

                                {tool.description && (
                                  <p className="text-sm text-[#171717] mb-5 leading-relaxed pl-14">
                                    {tool.description}
                                  </p>
                                )}

                                {Object.keys(parameters).length > 0 && (
                                  <div className="mt-5 pt-5 border-t border-[#171717]/10 pl-14">
                                    <p className="text-xs font-bold text-[#171717] mb-4 uppercase tracking-widest">
                                      Parameters
                                    </p>
                                    <div className="grid gap-3">
                                      {typeof parameters === 'object' && 'properties' in parameters ? (
                                        Object.entries((parameters as any).properties || {}).map(([paramName, paramDef]: [string, any]) => (
                                          <div key={paramName} className="bg-[#fffeff] p-4 rounded-2xl border-2 border-[#171717]/20 hover:border-[#171717]/40 transition-all">
                                            <div className="flex items-center gap-2 mb-3 flex-wrap">
                                              <code className="px-3 py-1.5 bg-[#171717] rounded-xl text-white font-mono text-sm font-semibold border-2 border-[#171717]">
                                                {paramName}
                                              </code>
                                              {paramDef.required && (
                                                <Badge variant="outline" className="border-red-500/50 text-red-600 text-xs px-2 py-1 bg-red-50 rounded-xl">
                                                  required
                                                </Badge>
                                              )}
                                              {paramDef.type && (
                                                <Badge variant="outline" className="border-[#171717]/30 text-[#171717] text-xs px-2 py-1 bg-[#171717]/10 rounded-xl">
                                                  {paramDef.type}
                                                </Badge>
                                              )}
                                            </div>
                                            {paramDef.description && (
                                              <p className="text-[#171717] text-sm leading-relaxed mb-2">
                                                {paramDef.description}
                                              </p>
                                            )}
                                            {paramDef.enum && (
                                              <div className="mt-3 pt-3 border-t border-[#171717]/10">
                                                <p className="text-[#171717] text-xs mb-2 font-semibold">Allowed values:</p>
                                                <div className="flex flex-wrap gap-2">
                                                  {paramDef.enum.map((val: string) => (
                                                    <Badge key={val} variant="outline" className="border-[#171717]/30 text-[#171717] text-xs bg-[#171717]/10 px-2 py-1 rounded-xl">
                                                      {val}
                                                    </Badge>
                                                  ))}
                                                </div>
                                              </div>
                                            )}
                                          </div>
                                        ))
                                      ) : (
                                        <div className="bg-[#fffeff] p-4 rounded-2xl border-2 border-[#171717]/20">
                                          <code className="px-3 py-2 bg-[#171717]/5 rounded-xl text-[#171717] font-mono text-xs block whitespace-pre-wrap border border-[#171717]/20">
                                            {JSON.stringify(parameters, null, 2)}
                                          </code>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>

                              <div className="shrink-0">
                                <div className={`flex flex-col items-center gap-3 p-4 rounded-2xl border-2 border-[#171717]/20 bg-[#fffeff] ${!isEnabled && "bg-gray-200"}`}>
                                  <Checkbox
                                    checked={isEnabled}
                                    onCheckedChange={() => isConnected ? toggleToolEnabled(tool.name) : undefined}
                                    disabled={!isConnected}
                                    className="data-[state=checked]:bg-[#171717] data-[state=checked]:border-[#171717] text-white h-6 w-6"
                                  />
                                  <span className={`text-xs font-medium ${isEnabled ? 'text-[#171717]' : 'text-gray-600'}`}>
                                    {isEnabled ? 'Enabled' : 'Disabled'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                ) : (
                  <div className="text-center py-16 bg-[#fffeff] rounded-2xl border-2 border-[#171717]/20">
                    <Wrench className="h-12 w-12 mx-auto text-[#171717] mb-4" />
                    <p className="text-[#171717]">No tools available</p>
                    <p className="text-sm text-gray-600 mt-2">This server doesn't expose any tools</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
