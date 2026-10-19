export type ChatAttachment = {
  id: string;
  name: string;
  path: string;
  kind: "file" | "directory";
};

const marker = "\n\n[Attachments: ";

export function newAttachment(path: string, kind: ChatAttachment["kind"]): ChatAttachment {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    name: path.split(/[/\\]/).filter(Boolean).pop() || path,
    path,
    kind,
  };
}

export function formatMessageWithAttachments(message: string, paths: string[]) {
  return paths.length ? `${message}${marker}${paths.join(" | ")}]` : message;
}

export function parseMessageWithAttachments(content: string) {
  const index = content.lastIndexOf(marker);
  if (index === -1 || !content.endsWith("]")) return { displayText: content, attachments: [] };
  return {
    displayText: content.slice(0, index),
    attachments: content.slice(index + marker.length, -1).split(" | ").filter(Boolean),
  };
}

export function resolveFilePath(file: File) {
  return file.name;
}

export function resolveDirectoryPath(files: FileList | File[]) {
  const file = Array.from(files)[0] as File & { webkitRelativePath?: string };
  return file?.webkitRelativePath?.split("/")[0] || "";
}
