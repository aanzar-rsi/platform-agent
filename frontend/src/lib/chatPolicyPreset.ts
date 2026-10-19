export interface NewChatPolicyPreset {
  armory?: Record<string, unknown>;
  memory?: Record<string, unknown>;
}

const POLICY_PRESET_KEY = "eva_new_chat_policy_preset";

export function getNewChatPolicyPreset(): NewChatPolicyPreset | null {
  try {
    const raw = localStorage.getItem(POLICY_PRESET_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    return parsed as NewChatPolicyPreset;
  } catch {
    return null;
  }
}

export function setNewChatPolicyPreset(preset: NewChatPolicyPreset): void {
  localStorage.setItem(POLICY_PRESET_KEY, JSON.stringify(preset));
}

export function clearNewChatPolicyPreset(): void {
  localStorage.removeItem(POLICY_PRESET_KEY);
}
