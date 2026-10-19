export function titleFromFirstMessage(message: string) {
  const title = message.trim().replace(/\s+/g, " ");
  return title.length > 40 ? `${title.slice(0, 37)}...` : title || "New chat";
}
