import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({ getAccessToken: () => "token" }));

import { AgentWebSocketClient } from "@/lib/websocket";

class FakeWebSocket {
  static OPEN = 1;
  static instances: FakeWebSocket[] = [];
  readyState = FakeWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  send() {}
  close() {
    this.readyState = 3;
  }
}

describe("AgentWebSocketClient", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    FakeWebSocket.instances = [];
    vi.stubGlobal("WebSocket", FakeWebSocket);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("cancels a scheduled reconnect when intentionally disconnected", () => {
    const client = new AgentWebSocketClient("chat-1");
    client.connect();
    const socket = FakeWebSocket.instances[0];

    socket.onclose?.({} as CloseEvent);
    client.disconnect();
    vi.runAllTimers();

    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("reconnects against the execution announced by run.started", () => {
    const client = new AgentWebSocketClient("chat-1");
    client.connect(9, "old-execution");
    const socket = FakeWebSocket.instances[0];
    socket.onmessage?.({
      data: JSON.stringify({
        type: "run.started",
        execution_id: "new-execution",
        seq: 1,
        payload: { execution_id: "new-execution", query: "hello" },
      }),
    });

    socket.onclose?.({} as CloseEvent);
    vi.advanceTimersByTime(1000);

    expect(FakeWebSocket.instances[1].url).toContain("execution_id=new-execution");
    expect(FakeWebSocket.instances[1].url).toContain("after_seq=1");
  });
});
