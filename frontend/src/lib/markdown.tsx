import type { Components } from "react-markdown";

export const markdownLinkComponent: Components = {
  a: ({ children, ...props }) => <a {...props} target="_blank" rel="noreferrer">{children}</a>,
};

export function stabilizeMarkdownLinks(content: string) {
  return content;
}
