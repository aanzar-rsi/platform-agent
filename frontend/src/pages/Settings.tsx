import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
// import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Settings as SettingsIcon, Brain, Sliders, Cpu, Zap, Save, RefreshCw, Check, AlertCircle, Info, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";
import HeaderNavbar from "@/components/HeaderNavbar";
import Breadcrumb from "@/components/Breadcrumb";
import { applyAppTheme } from "@/lib/theme";

export default function Settings({ embedded = false }: { embedded?: boolean }) {
  const { user, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState("agent");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Agent parameters from main.py
  const [agentConfig, setAgentConfig] = useState({
    name: "MCPAgent",
    llm_type: "bedrock",
    temperature: "0.1",
    top_p: "0.1",
    max_replans: "20",
    short_term_memory_size: "10",
    short_term_memory_token_limit: "1000",
    enable_logging: true,
    log_level: "INFO",
    enable_streaming: true,
    idle_threshold_seconds: "120"
  });

  const [modelConfig, setModelConfig] = useState({
    model_default: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    model_agent: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    model_planning: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    model_respond: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    model_summarize: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    model_evaluation: "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
  });

  const [internalTools, setInternalTools] = useState([
    { name: "get_long_term_memory", enabled: true, description: "Retrieve user's long-term memory data" },
    { name: "update_long_term_memory", enabled: true, description: "Update user's long-term memory" },
    { name: "list_user_sessions", enabled: true, description: "List all user conversation sessions" },
    { name: "get_chat_session", enabled: true, description: "Retrieve specific chat session details" }
  ]);

  const availableModels = {
    bedrock: [
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
      "amazon.nova-pro-v1:0"
    ],
    openai: [
      "gpt-4o",
      "gpt-4o-mini",
      "gpt-4-turbo-2024-04-09",
      "o1-mini-2024-09-12",
      "o1-preview-2024-09-12"
    ]
  };

  // Load preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true);
        const { preferencesAPI } = await import('../lib/api');
        const response = await preferencesAPI.get();
        if (response.success && response.preferences) {
          const prefs = response.preferences as any;
          const agent = (prefs.agent || {}) as Record<string, any>;
          const ac = prefs.agent_config || agent;

          if (ac && typeof ac === 'object') {
            setAgentConfig({
              name: ac.name || "MCPAgent",
              llm_type: ac.llm_type || "bedrock",
              temperature: String(ac.temperature ?? 0.1),
              top_p: String(ac.top_p ?? 0.1),
              max_replans: String(ac.max_replans ?? 20),
              short_term_memory_size: String(ac.short_term_memory_size ?? 10),
              short_term_memory_token_limit: String(ac.short_term_memory_token_limit ?? 1000),
              enable_logging: ac.enable_logging ?? true,
              log_level: ac.log_level || "INFO",
              enable_streaming: ac.enable_streaming ?? true,
              idle_threshold_seconds: String(ac.idle_threshold_seconds ?? 120),
            });
            if (ac.model) {
              setModelConfig((prev) => ({
                ...prev,
                model_default: ac.model.default || prev.model_default,
                model_agent: ac.model.agent || ac.model.default || prev.model_agent,
                model_planning: ac.model.planning || ac.model.default || prev.model_planning,
                model_respond: ac.model.respond || ac.model.default || prev.model_respond,
                model_summarize: ac.model.summarize || ac.model.default || prev.model_summarize,
                model_evaluation: ac.model.evaluation || ac.model.default || prev.model_evaluation,
              }));
            }
          }

          // Always keep the canonical chat theme — do not apply light/dark/system
          // from prefs (those names have no CSS and diverge per browser).
          applyAppTheme();
          if (prefs.console_mode) {
            localStorage.setItem('eva_chat_view_mode', prefs.console_mode === 'advanced' ? 'advanced' : 'beginner');
          }
        }
      } catch (error) {
        console.error('Failed to load preferences:', error);
      } finally {
        setLoading(false);
        setHasChanges(false);
      }
    };

    if (isAuthenticated) {
      loadPreferences();
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    // Mark as changed whenever config changes (but not on initial load)
    if (!loading) {
      setHasChanges(true);
    }
  }, [agentConfig, modelConfig, internalTools, loading]);

  const handleSaveAll = async () => {
    setSaving(true);
    try {
      const { preferencesAPI } = await import('../lib/api');

      const agentConfigForAPI = {
        name: agentConfig.name,
        llm_type: agentConfig.llm_type,
        model: {
          default: modelConfig.model_default,
          agent: modelConfig.model_agent,
          planning: modelConfig.model_planning,
          respond: modelConfig.model_respond,
          summarize: modelConfig.model_summarize,
          evaluation: modelConfig.model_evaluation,
        },
        temperature: parseFloat(agentConfig.temperature),
        top_p: parseFloat(agentConfig.top_p),
        max_replans: parseInt(agentConfig.max_replans),
        short_term_memory_size: parseInt(agentConfig.short_term_memory_size),
        short_term_memory_token_limit: parseInt(agentConfig.short_term_memory_token_limit),
        enable_logging: agentConfig.enable_logging,
        log_level: agentConfig.log_level,
        enable_streaming: agentConfig.enable_streaming,
        idle_threshold_seconds: parseInt(agentConfig.idle_threshold_seconds),
      };

      // Persist into preferences.agent (client2.0 shape)
      await preferencesAPI.update({ agent: agentConfigForAPI });

      toast.success("All settings saved successfully!");
      setHasChanges(false);
    } catch (error: any) {
      console.error('Save error:', error);
      toast.error(`Failed to save settings: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleResetToDefaults = () => {
    if (confirm("Are you sure you want to reset all settings to defaults? This action cannot be undone.")) {
      setAgentConfig({
        name: "MCPAgent",
        llm_type: "bedrock",
        temperature: "0.1",
        top_p: "0.1",
        max_replans: "20",
        short_term_memory_size: "10",
        short_term_memory_token_limit: "1000",
        enable_logging: true,
        log_level: "INFO",
        enable_streaming: true,
        idle_threshold_seconds: "120"
      });
      setModelConfig({
        model_default: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        model_agent: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        model_planning: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        model_respond: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        model_summarize: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        model_evaluation: "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
      });
      toast.success("Settings reset to defaults");
      setHasChanges(false);
    }
  };

  const toggleTool = (toolName: string) => {
    setInternalTools(tools =>
      tools.map(tool =>
        tool.name === toolName ? { ...tool, enabled: !tool.enabled } : tool
      )
    );
    const tool = internalTools.find(t => t.name === toolName);
    toast.success(`${toolName} ${tool?.enabled ? 'disabled' : 'enabled'}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <RefreshCw className="h-10 w-10 animate-spin text-brand relative" />
          </div>
          <p className="text-gray-900 text-sm">Loading preferences...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={embedded ? "h-full overflow-y-auto" : "min-h-screen"}>
      {!embedded && <HeaderNavbar variant="app" isAuthenticated={isAuthenticated} />}
      {!embedded && <Breadcrumb items={[
        { label: "Chat", path: "/" },
        { label: "Settings", path: "/settings" }
      ]} />}

      <div className={`container max-w-[90%] mx-auto px-6 mb-10 ${embedded ? "pt-8" : "pt-32"}`}>
        <h1 className="text-3xl font-bold text-[#171717] mb-6">Settings</h1>
        <div className="flex items-center justify-end gap-2 mb-6">
          {hasChanges && (
            <Badge variant="outline" className="border-yellow-600 text-yellow-600 bg-yellow-500/10">
              <AlertCircle className="h-3 w-3 mr-1" />
              Unsaved Changes
            </Badge>
          )}
          <Button
            variant="outline"
            onClick={handleResetToDefaults}
            className="text-[#171717] border-2 border-[#171717]/30 text-sm hover:bg-[#171717] hover:text-white shadow-xl rounded-xl"
          >
            <RefreshCw className="h-4 w-4" />
            Reset to Defaults
          </Button>
          <Button
            onClick={handleSaveAll}
            disabled={saving || !hasChanges}
            className="bg-[#171717] hover:bg-[#171717]/90 transition-all text-white border-0 shadow-xl rounded-xl"
          >
            {saving ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save All Changes
          </Button>
        </div>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="mb-8 grid w-full grid-cols-4 gap-4">
            {[
              { value: "agent", label: "Agent Config", icon: Cpu },
              { value: "llm", label: "LLM Models", icon: Brain },
              { value: "memory", label: "Memory", icon: Brain },
              { value: "tools", label: "Internal Tools", icon: Sliders },
            ].map(({ value, label, icon: Icon }) => {

              const triggerBase = "py-3 gap-2 border border-brand hover:bg-brand/30"
              const triggerActive = "bg-brand text-black hover:bg-brand/80"

              return (
                <TabsTrigger
                  key={value}
                  value={value}
                  className={cn(
                    triggerBase,
                    activeTab === value && triggerActive
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </TabsTrigger>
              )
            })}
          </TabsList>

          {/* Agent Configuration */}
          <TabsContent value="agent" className="space-y-6">
            {/* Basic Configuration */}
            <Card className="backdrop-blur-sm border-gray-400">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-gray-900">
                      <Cpu className="h-5 w-5 text-brand" />
                      Basic Configuration
                    </CardTitle>
                    <CardDescription className="text-gray-900 mt-1">
                      Core agent identity and behavior
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="border-gray-600 text-gray-600 bg-gray-200">
                    <Sparkles className="h-3 w-3 mr-1" />
                    Essential
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-gray-600">Agent Name</Label>
                    <Input
                      id="name"
                      value={agentConfig.name}
                      onChange={(e) => setAgentConfig({ ...agentConfig, name: e.target.value })}
                      className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                      placeholder="e.g., MCPAgent"
                    />
                    <p className="text-xs text-gray-900 flex items-center gap-1">
                      <Info className="h-3 w-3" />
                      Unique identifier for this agent instance
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="llm_type" className="text-gray-600 font-medium">LLM Provider</Label>
                    <select
                      id="llm_type"
                      value={agentConfig.llm_type}
                      onChange={(e) => setAgentConfig({ ...agentConfig, llm_type: e.target.value })}
                      className="w-full rounded-md border border-gray-500 text-gray-900 p-2 text-sm focus:border-brand focus:outline-none font-mono"
                    >
                      <option value="bedrock">AWS Bedrock</option>
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic</option>
                    </select>
                    <p className="text-xs text-gray-900 flex items-center gap-1">
                      <Info className="h-3 w-3" />
                      Primary LLM service provider
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* LLM Parameters */}
            <Card className="backdrop-blur-sm border-gray-400">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-gray-900">
                      <Sliders className="h-5 w-5 text-brand" />
                      LLM Parameters
                    </CardTitle>
                    <CardDescription className="text-gray-900 mt-1">
                      Fine-tune model behavior and response quality
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="llm_type" className="text-gray-600">Temperature</Label>
                      <Badge variant="outline" className="border-gray-600 text-gray-600 text-xs">
                        {agentConfig.temperature}
                      </Badge>
                    </div>
                    <Input
                      id="temperature"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={agentConfig.temperature}
                      onChange={(e) => setAgentConfig({ ...agentConfig, temperature: e.target.value })}
                      className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                    />
                    <p className="text-xs text-gray-600">
                      Controls randomness. Lower = more focused, Higher = more creative
                    </p>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="top_p" className="text-gray-600">Top P</Label>
                      <Badge variant="outline" className="border-gray-600 text-gray-600 text-xs">
                        {agentConfig.top_p}
                      </Badge>
                    </div>
                    <Input
                      id="top_p"
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={agentConfig.top_p}
                      onChange={(e) => setAgentConfig({ ...agentConfig, top_p: e.target.value })}
                      className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                    />
                    <p className="text-xs text-gray-600">
                      Nucleus sampling. Controls diversity of responses
                    </p>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="max_replans" className="text-gray-600">Max Replans</Label>
                      <Badge variant="outline" className="border-gray-600 text-gray-600 text-xs">
                        {agentConfig.max_replans}
                      </Badge>
                    </div>
                    <Input
                      id="max_replans"
                      type="number"
                      min="0"
                      max="100"
                      value={agentConfig.max_replans}
                      onChange={(e) => setAgentConfig({ ...agentConfig, max_replans: e.target.value })}
                      className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                    />
                    <p className="text-xs text-gray-600">
                      Maximum replanning attempts when execution fails
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* System Options */}
            <Card className="backdrop-blur-sm border-gray-400">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-gray-900">
                      <Zap className="h-5 w-5 text-brand" />
                      System Options
                    </CardTitle>
                    <CardDescription className="text-gray-900 mt-1">
                      Logging, streaming, and performance settings
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-5 rounded-lg border border-gray-400">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`h-2 w-2 rounded-full ${agentConfig.enable_logging ? 'bg-green-500 animate-pulse' : 'bg-neutral-600'}`}></div>
                        <div>
                          <div className="font-medium text-sm text-gray-900">Enable Logging</div>
                          <p className="text-xs text-gray-900">Track agent operations and debugging</p>
                        </div>
                      </div>
                      <Button
                        variant={agentConfig.enable_logging ? "default" : "outline"}
                        size="sm"
                        onClick={() => setAgentConfig({ ...agentConfig, enable_logging: !agentConfig.enable_logging })}
                        className={agentConfig.enable_logging ? "bg-green-600 hover:bg-green-700 text-white min-w-15" : "bg-neutral-800 border-neutral-700 text-neutral-300 min-w-15"}
                      >
                        {agentConfig.enable_logging ? "ON" : "OFF"}
                      </Button>
                    </div>
                    {agentConfig.enable_logging && (
                      <div className="space-y-2 mt-3 pt-3 border-t border-neutral-800">
                        <Label htmlFor="log_level" className="text-xs text-neutral-400">Log Level</Label>
                        <select
                          id="log_level"
                          value={agentConfig.log_level}
                          onChange={(e) => setAgentConfig({ ...agentConfig, log_level: e.target.value })}
                          className="w-full rounded-md border border-gray-500 text-gray-900 p-2 text-sm focus:border-brand focus:outline-none font-mono"
                        >
                          <option value="DEBUG">DEBUG</option>
                          <option value="INFO">INFO</option>
                          <option value="WARNING">WARNING</option>
                          <option value="ERROR">ERROR</option>
                        </select>
                      </div>
                    )}
                  </div>
                  <div className="p-5 rounded-lg border border-gray-400">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`h-2 w-2 rounded-full ${agentConfig.enable_streaming ? 'bg-green-500 animate-pulse' : 'bg-neutral-600'}`}></div>
                        <div>
                          <div className="font-medium text-sm text-gray-900">Enable Streaming</div>
                          <p className="text-xs text-gray-900">Stream LLM responses in real-time</p>
                        </div>
                      </div>
                      <Button
                        variant={agentConfig.enable_streaming ? "default" : "outline"}
                        size="sm"
                        onClick={() => setAgentConfig({ ...agentConfig, enable_streaming: !agentConfig.enable_streaming })}
                        className={agentConfig.enable_streaming ? "bg-green-600 hover:bg-green-700 text-white min-w-15" : "bg-neutral-800 border-neutral-700 text-neutral-300 min-w-15"}
                      >
                        {agentConfig.enable_streaming ? "ON" : "OFF"}
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="idle_threshold" className="text-gray-900">Idle Threshold (seconds)</Label>
                      <Badge variant="outline" className="border-gray-600 text-gray-600 text-xs">
                        {agentConfig.idle_threshold_seconds}s
                      </Badge>
                    </div>
                    <Input
                      id="idle_threshold"
                      type="number"
                      min="30"
                      max="600"
                      value={agentConfig.idle_threshold_seconds}
                      onChange={(e) => setAgentConfig({ ...agentConfig, idle_threshold_seconds: e.target.value })}
                      className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                    />
                    <p className="text-xs text-gray-900">
                      Time before agent considers session idle
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* LLM Models */}
          <TabsContent value="llm" className="space-y-6">
            <Card className="backdrop-blur-sm border-gray-400">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-gray-900">
                      <Zap className="h-5 w-5 text-brand" />
                      LLM Model Configuration
                    </CardTitle>
                    <CardDescription className="text-gray-900 mt-1">
                      Configure different models for specific agent tasks
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="border-gray-600 text-gray-600 bg-gray-200">
                    Provider: {agentConfig.llm_type}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {[
                    {
                      key: "model_default",
                      label: "Default Model",
                      icon: Sparkles,
                      description: "Used when no specific model is configured",
                      badge: "Fallback",
                    },
                    {
                      key: "model_agent",
                      label: "Agent Decision",
                      icon: Cpu,
                      description: "Evaluates queries and decides response strategy",
                    },
                    {
                      key: "model_planning",
                      label: "Planning",
                      icon: Sliders,
                      description: "Creates multi-step execution plans",
                    },
                    {
                      key: "model_respond",
                      label: "Response",
                      icon: Zap,
                      description: "Generates final user-facing responses",
                    },
                    {
                      key: "model_summarize",
                      label: "Summarization",
                      icon: Brain,
                      description: "Summarizes memory and conversations",
                    },
                    {
                      key: "model_evaluation",
                      label: "Evaluation",
                      icon: Check,
                      description: "Evaluates execution success and quality",
                    },
                  ].map(
                    ({ key, label, icon: Icon, description, badge }) => {

                      const cardBase = "space-y-3 p-4 rounded-lg border border-gray-400"
                      const selectBase = "w-full rounded-md border border-gray-400 text-gray-900 p-2.5 text-sm focus:border-brand focus:outline-none font-mono"

                      return (
                        <div key={key} className={cardBase}>
                          <div className="mb-2 flex items-center justify-between">
                            <Label
                              htmlFor={key}
                              className="flex items-center gap-2 font-medium text-gray-900"
                            >
                              <Icon className="h-4 w-4 text-brand" />
                              {label}
                            </Label>

                            {badge && (
                              <Badge
                                variant="outline"
                                className="border-gray-600 bg-gray-200 text-gray-600"
                              >
                                {badge}
                              </Badge>
                            )}
                          </div>

                          <select
                            id={key}
                            value={modelConfig[key]}
                            onChange={(e) =>
                              setModelConfig({
                                ...modelConfig,
                                [key]: e.target.value,
                              })
                            }
                            className={selectBase}
                          >
                            {availableModels[
                              agentConfig.llm_type as keyof typeof availableModels
                            ]?.map((model) => (
                              <option key={model} value={model}>
                                {model}
                              </option>
                            ))}
                          </select>

                          <p className="text-xs text-gray-900">{description}</p>
                        </div>
                      )
                    }
                  )}
                </div>
              </CardContent>

            </Card>
          </TabsContent>

          {/* Memory Configuration */}
          <TabsContent value="memory" className="space-y-6">
            <Card className="backdrop-blur-sm border-gray-400">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-gray-900">
                      <Zap className="h-5 w-5 text-brand" />
                      Memory Configuration
                    </CardTitle>
                    <CardDescription className="text-gray-900 mt-1">
                      Configure how the agent stores and manages conversation memory
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="border-gray-600 text-gray-600 bg-gray-200">
                    <Brain className="h-3 w-3 mr-1" />
                    Cognitive
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3 p-4 rounded-lg border border-gray-400">
                    <div className="flex items-center justify-between mb-2">
                      <Label htmlFor="memory_size" className="text-gray-600">Short-Term Memory Size</Label>
                      <Badge variant="outline" className="border-gray-600 text-gray-600 bg-gray-200">
                        {agentConfig.short_term_memory_size} messages
                      </Badge>
                    </div>
                    <Input
                      id="memory_size"
                      type="number"
                      min="1"
                      max="50"
                      value={agentConfig.short_term_memory_size}
                      onChange={(e) => setAgentConfig({ ...agentConfig, short_term_memory_size: e.target.value })}
                      className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                    />
                    <p className="text-xs text-gray-900">
                      Number of recent messages retained in active context
                    </p>
                  </div>
                  <div className="space-y-3 p-4 rounded-lg border border-gray-400">
                    <div className="flex items-center justify-between mb-2">
                      <Label htmlFor="memory_size" className="text-gray-600">Token Limit</Label>
                      <Badge variant="outline" className="border-gray-600 text-gray-600 bg-gray-200">
                        {agentConfig.short_term_memory_token_limit} tokens
                      </Badge>
                    </div>
                    <Input
                      id="token_limit"
                      type="number"
                      min="100"
                      max="10000"
                      step="100"
                      value={agentConfig.short_term_memory_token_limit}
                      onChange={(e) => setAgentConfig({ ...agentConfig, short_term_memory_token_limit: e.target.value })}
                      className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                    />
                    <p className="text-xs text-gray-900">
                      Maximum tokens before automatic summarization
                    </p>
                  </div>
                </div>

                <div className="p-5 rounded-lg border border-yellow-600 bg-yellow-100">
                  <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-yellow-600 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <h4 className="font-medium text-yellow-600 text-sm">Memory Management</h4>
                      <p className="text-xs text-yellow-600 leading-relaxed">
                        When short-term memory exceeds the configured limits, older messages are automatically
                        summarized and stored in long-term memory. This ensures efficient context management
                        while preserving important information.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Internal Tools */}
          <TabsContent value="tools" className="space-y-6">
            <Card className="backdrop-blur-sm border-gray-400">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-gray-900">
                      <Zap className="h-5 w-5 text-brand" />
                      Internal Tools
                    </CardTitle>
                    <CardDescription className="text-gray-900 mt-1">
                      Enable or disable built-in agent capabilities
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="border-gray-600 text-gray-600 bg-gray-200">
                    {internalTools.filter(t => t.enabled).length}/{internalTools.length} Active
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {internalTools.map((tool) => (
                    <div
                      key={tool.name}
                      className="group p-5 rounded-lg border border-brand bg-linear-to-b from-white to-brand/10 hover:bg-brand/10 transition-all"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4 flex-1">
                          <div className={`h-10 w-10 rounded-lg flex items-center justify-center transition-colors ${tool.enabled
                            ? 'bg-green-500/20 border border-green-800'
                            : 'bg-gray-300 border border-gray-700'
                            }`}>
                            <Zap className={`h-5 w-5 ${tool.enabled ? 'text-green-800' : 'text-gray-700'}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="font-semibold text-gray-900 text-sm font-mono">{tool.name}</h3>
                              {tool.enabled ? (
                                <Badge className="bg-green-600 text-white text-xs px-2 py-0.5">
                                  <Check className="h-3 w-3 mr-1" />
                                  Active
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="border-gray-600 text-gray-600 text-xs px-2 py-0.5">
                                  Inactive
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-900">{tool.description}</p>
                          </div>
                        </div>
                        <Button
                          variant={tool.enabled ? "default" : "outline"}
                          size="sm"
                          onClick={() => toggleTool(tool.name)}
                          className={tool.enabled
                            ? "bg-green-600 hover:bg-green-700 text-white min-w-20"
                            : "bg-gray-300 border-gray-500 text-gray-900 hover:bg-gray-400 min-w-20"
                          }
                        >
                          {tool.enabled ? "Enabled" : "Disabled"}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 p-5 rounded-lg border border-neutral-900 bg-neutral-100">
                  <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-neutral-900 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <h4 className="font-medium text-neutral-900 text-sm">About Internal Tools</h4>
                      <p className="text-xs text-neutral-900 leading-relaxed">
                        Internal tools provide core functionality to the agent such as memory management
                        and session handling. Disabling tools may limit the agent's capabilities. Only
                        disable if you understand the implications.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
