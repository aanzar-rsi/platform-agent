import { useCallback } from "react";
import { Cpu, Sliders, Sparkles, MessageSquareText } from "lucide-react";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { BEDROCK_MODELS, DEFAULT_MODEL, formatModelLabel } from "@/lib/availableModels";
import type { ChatTuneSettings } from "@/components/EnhancedChatView";

export type AgentMode = "basic" | "intermediate" | "advanced";

const AGENT_MODES: { id: AgentMode; label: string; description: string }[] = [
  { id: "basic", label: "Basic", description: "Simple, guided responses" },
  { id: "intermediate", label: "Intermediate", description: "Balanced tool use and reasoning" },
  { id: "advanced", label: "Advanced", description: "Full agent capabilities" },
];

interface AgentSettingsPanelProps {
  settings: ChatTuneSettings;
  onSettingsChange: (settings: ChatTuneSettings) => void;
}

function patchSettings(
  settings: ChatTuneSettings,
  patch: Partial<ChatTuneSettings>
): ChatTuneSettings {
  return { ...settings, ...patch };
}

export default function AgentSettingsPanel({
  settings,
  onSettingsChange,
}: AgentSettingsPanelProps) {
  const model = settings.model || DEFAULT_MODEL;
  const agentMode = (settings.agentMode as AgentMode | undefined) ?? "basic";

  const update = useCallback(
    (patch: Partial<ChatTuneSettings>) => {
      onSettingsChange(patchSettings(settings, patch));
    },
    [onSettingsChange, settings]
  );

  return (
    <div
      className="mb-3 rounded-2xl border px-4 py-3 shadow-sm"
      style={{ borderColor: "var(--theme-border)", backgroundColor: "#f8f8f6" }}
    >
      <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-gray-500">
        <Sliders className="h-3.5 w-3.5" />
        Agent settings
      </div>

      <div className="space-y-4">
        {/* Mode */}
        <section className="space-y-2">
          <div className="flex items-center gap-2 text-[11px] font-medium text-gray-500">
            <Sparkles className="h-3 w-3" />
            Mode
          </div>
          <div
            className="grid grid-cols-3 gap-1 rounded-xl border p-0.5"
            style={{ borderColor: "var(--theme-border)", backgroundColor: "#f5f5f5" }}
          >
            {AGENT_MODES.map((mode) => (
              <Button
                key={mode.id}
                type="button"
                variant="ghost"
                size="sm"
                className={cn(
                  "h-8 rounded-lg px-2 text-[11px] font-medium",
                  agentMode === mode.id
                    ? "bg-white text-[#010101] shadow-sm ring-1 ring-[var(--theme-accent)]/30"
                    : "text-gray-500 hover:bg-white/60 hover:text-gray-800"
                )}
                onClick={() => update({ agentMode: mode.id })}
              >
                {mode.label}
              </Button>
            ))}
          </div>
        </section>

        {/* Model + params row */}
        <div className="grid gap-3 sm:grid-cols-2">
          <section className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-[11px] font-medium text-gray-500">
              <Cpu className="h-3 w-3" />
              Model
            </div>
            <select
              value={model}
              onChange={(e) => update({ model: e.target.value })}
              className="h-8 w-full rounded-xl border bg-white px-2.5 text-xs text-[#010101] outline-none focus-visible:ring-1 focus-visible:ring-[var(--theme-accent)]"
              style={{ borderColor: "var(--theme-border)" }}
            >
              {BEDROCK_MODELS.map((id) => (
                <option key={id} value={id}>
                  {formatModelLabel(id)}
                </option>
              ))}
            </select>
          </section>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label htmlFor="agent-temperature" className="text-[10px] text-gray-500">
                Temperature
              </Label>
              <Input
                id="agent-temperature"
                type="number"
                min={0}
                max={2}
                step={0.1}
                placeholder="0.7"
                value={settings.temperature}
                onChange={(e) => update({ temperature: e.target.value })}
                className="h-8 rounded-xl text-xs"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="agent-top-p" className="text-[10px] text-gray-500">
                Top P
              </Label>
              <Input
                id="agent-top-p"
                type="number"
                min={0}
                max={1}
                step={0.05}
                placeholder="0.9"
                value={settings.topP ?? ""}
                onChange={(e) => update({ topP: e.target.value })}
                className="h-8 rounded-xl text-xs"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="agent-top-k" className="text-[10px] text-gray-500">
                Top K
              </Label>
              <Input
                id="agent-top-k"
                type="number"
                min={0}
                step={1}
                placeholder="250"
                value={settings.topK ?? ""}
                onChange={(e) => update({ topK: e.target.value })}
                className="h-8 rounded-xl text-xs"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="agent-max-tokens" className="text-[10px] text-gray-500">
                Max tokens
              </Label>
              <Input
                id="agent-max-tokens"
                type="number"
                min={1}
                step={256}
                placeholder="4096"
                value={settings.maxTokens}
                onChange={(e) => update({ maxTokens: e.target.value })}
                className="h-8 rounded-xl text-xs"
              />
            </div>
          </div>
        </div>

        {/* Instructions */}
        <section className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-gray-500">
            <MessageSquareText className="h-3 w-3" />
            Additional instructions
          </div>
          <Textarea
            id="agent-instructions"
            placeholder="e.g. Be concise, prefer bullet points, always cite sources…"
            value={settings.instructions}
            onChange={(e) => update({ instructions: e.target.value })}
            className="min-h-[64px] resize-none rounded-xl text-xs"
            rows={2}
          />
        </section>
      </div>
    </div>
  );
}
