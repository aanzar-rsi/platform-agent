import { useEffect, useState } from "react";
import { toast } from "sonner";
import { agentsAPI, type AgentPolicy, type AgentPolicyResponse } from "@/lib/api";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";

export default function AgentPolicyPanel({ agentId }: { agentId: string | null }) {
  const [data, setData] = useState<AgentPolicyResponse | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setData(null);
    if (!agentId) return;
    let active = true;
    agentsAPI.getPolicy(agentId).then((result) => {
      if (active) setData(result);
    }).catch(() => { if (active) toast.error("Could not load agent policy"); });
    return () => { active = false; };
  }, [agentId]);

  const save = async (change: { armory?: Partial<AgentPolicy["armory"]>; memory?: Partial<AgentPolicy["memory"]> }) => {
    if (!agentId || !data) return;
    setSaving(true);
    try {
      setData(await agentsAPI.updatePolicy(agentId, data.version, change));
    } catch {
      toast.error("Policy update failed; refresh to see the latest version");
      agentsAPI.getPolicy(agentId).then(setData).catch(() => undefined);
    } finally {
      setSaving(false);
    }
  };

  if (!agentId) return <p className="p-4 text-sm">Send your first message to create this agent.</p>;
  if (!data) return <p className="p-4 text-sm">Loading policy…</p>;

  const { policy, ceiling } = data;
  const groups = Object.keys(policy.armory.resources || {}).sort();

  const toggleGroup = (group: string, checked: boolean) => {
    void save({ armory: { groups: { ...policy.armory.groups, [group]: { enabled: checked } } } });
  };

  const toggleResource = (group: string, name: string, checked: boolean) => {
    const next = (policy.armory.resources[group] || []).map((resource) =>
      resource.name === name ? { ...resource, enabled: checked } : resource,
    );
    void save({ armory: { resources: { ...policy.armory.resources, [group]: next } } });
  };

  const toggleScope = (field: "read" | "write" | "promote" | "publish", scope: string, checked: boolean) => {
    const current = policy.memory[field] || [];
    const next = checked ? Array.from(new Set([...current, scope])) : current.filter((s) => s !== scope);
    void save({ memory: { [field]: next } as Partial<AgentPolicy["memory"]> });
  };

  const allScopes = ["USER", "TENANT", "AGENT"];
  const promoteScopes = ["TENANT", "AGENT"];

  return <div className="space-y-5 overflow-y-auto p-4 text-gray-900" aria-label="Agent policy">
    <p className="text-xs text-gray-500">Agent {agentId} · policy version {data.version}</p>
    <section className="space-y-3 rounded-lg border p-3">
      <h3 className="font-semibold">Armory · editable</h3>
      {groups.map((group) => <div key={group} className="space-y-2 rounded border p-2">
        <label className="flex items-center gap-2 text-xs font-semibold">
          <Checkbox disabled={saving} checked={!!policy.armory.groups[group]?.enabled}
            onCheckedChange={(checked) => toggleGroup(group, !!checked)} />
          {group}
        </label>
        {(policy.armory.resources[group] || []).map((resource) => <label key={`${group}:${resource.name}`}
          className="flex items-center gap-2 text-xs break-all pl-4">
          <Checkbox disabled={saving || !policy.armory.groups[group]?.enabled}
            checked={resource.enabled}
            onCheckedChange={(checked) => toggleResource(group, resource.name, !!checked)} />
          {resource.name}
        </label>)}
      </div>)}
      <p className="text-xs">Tool confirmation: {policy.armory.confirm_tools ? "Required" : "Optional"}</p>
      <Button type="button" size="sm" variant="outline" disabled={saving}
        onClick={() => void save({ armory: { confirm_tools: !policy.armory.confirm_tools } })}>
        {policy.armory.confirm_tools ? "Make optional" : "Require confirmation"}
      </Button>
    </section>
    <section className="space-y-3 rounded-lg border p-3">
      <h3 className="font-semibold">Memory · editable</h3>
      <label className="flex items-center gap-2 text-xs">
        <Checkbox disabled={saving} checked={policy.memory.enabled}
          onCheckedChange={(checked) => void save({ memory: { enabled: !!checked } })} />
        Enabled
      </label>
      <fieldset className="space-y-1">
        <legend className="text-xs font-semibold">Read scopes</legend>
        {allScopes.map((scope) => <label key={`read:${scope}`} className="flex items-center gap-2 text-xs">
          <Checkbox disabled={saving} checked={policy.memory.read.includes(scope)}
            onCheckedChange={(checked) => toggleScope("read", scope, !!checked)} />{scope}
        </label>)}
      </fieldset>
      <fieldset className="space-y-1">
        <legend className="text-xs font-semibold">Write scopes</legend>
        {allScopes.map((scope) => <label key={`write:${scope}`} className="flex items-center gap-2 text-xs">
          <Checkbox disabled={saving} checked={policy.memory.write.includes(scope)}
            onCheckedChange={(checked) => toggleScope("write", scope, !!checked)} />{scope}
        </label>)}
      </fieldset>
      <fieldset className="space-y-1">
        <legend className="text-xs font-semibold">Promote targets</legend>
        {promoteScopes.map((scope) => <label key={`promote:${scope}`} className="flex items-center gap-2 text-xs">
          <Checkbox disabled={saving} checked={policy.memory.promote.includes(scope)}
            onCheckedChange={(checked) => toggleScope("promote", scope, !!checked)} />{scope}
        </label>)}
      </fieldset>
      <label className="flex items-center gap-2 text-xs">
        <Checkbox disabled={saving} checked={policy.memory.confirm_before_extracting}
          onCheckedChange={(checked) => void save({ memory: { confirm_before_extracting: !!checked } })} />
        Confirm before extracting
      </label>
      <label className="flex items-center gap-2 text-xs">
        <Checkbox disabled={saving} checked={policy.memory.allow_admin_promotion}
          onCheckedChange={(checked) => void save({ memory: { allow_admin_promotion: !!checked } })} />
        Allow admin promotion path
      </label>
      <div className="space-y-2">
        <p className="text-xs font-semibold">Chunk rules</p>
        {Object.entries(policy.memory.chunks || {}).map(([chunkType, chunk]) => <div key={chunkType} className="rounded border p-2 text-xs space-y-1">
          <label className="flex items-center gap-2">
            <Checkbox disabled={saving} checked={chunk.enabled}
              onCheckedChange={(checked) => void save({ memory: { chunks: { ...policy.memory.chunks, [chunkType]: { ...chunk, enabled: !!checked } } } })} />
            {chunkType}
          </label>
          <p>read: {chunk.read.join(", ") || "none"}</p>
          <p>write: {chunk.write.join(", ") || "none"}</p>
        </div>)}
      </div>
      <p className="text-xs">Tenant: {policy.memory.tenant_id || "None"}</p>
      <Button type="button" size="sm" variant="outline" disabled={saving}
        onClick={() => void save({ memory: { tenant_id: policy.memory.tenant_id ? null : (ceiling.memory.tenant_id || null) } })}>
        {policy.memory.tenant_id ? "Disable tenant" : "Restore tenant"}
      </Button>
    </section>
    {(["guardrails", "observability"] as const).map((section) => <section key={section} className="rounded-lg border p-3">
      <h3 className="font-semibold capitalize">{section} · view only</h3>
      {Object.entries(policy[section]).map(([key, value]) =>
        <p key={key} className="text-xs">{key}: {String(value)}</p>)}
    </section>)}
  </div>;
}
