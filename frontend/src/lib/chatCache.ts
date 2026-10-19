import type { Message } from "@/types/backend";

export type CachedChat = {
  title: string;
  messages: Message[];
  rollbackCheckpointId: string | null;
};

const cache = new Map<string, CachedChat>();

export function getCachedChat(chatId: string) {
  return cache.get(chatId);
}

export function setCachedChat(chatId: string, chat: CachedChat) {
  cache.set(chatId, chat);
}
