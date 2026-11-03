import { describe, expect, it } from "vitest";
import { defaultMcpLoginUrl, mcpErrorMessage } from "@/lib/mcpErrors";

describe("mcpErrorMessage", () => {
  it("shows exact FastAPI string details", () => {
    expect(mcpErrorMessage({
      response: { data: { detail: "MCP_CREDENTIALS_KEY is required for login-authenticated servers" } },
    })).toBe("MCP_CREDENTIALS_KEY is required for login-authenticated servers");
  });

  it("formats FastAPI validation details with field paths", () => {
    expect(mcpErrorMessage({
      response: { data: { detail: [{ loc: ["body", "auth", "login_url"], msg: "Field required" }] } },
    })).toBe("auth.login_url: Field required");
  });
});

describe("defaultMcpLoginUrl", () => {
  it("uses auth/login beside the MCP endpoint", () => {
    expect(defaultMcpLoginUrl("http://localhost:8000/mcp")).toBe("http://localhost:8000/mcp/auth/login");
    expect(defaultMcpLoginUrl("https://example.com/api/mcp/")).toBe("https://example.com/api/mcp/auth/login");
  });
});
