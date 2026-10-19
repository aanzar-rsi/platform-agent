import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";

const getMock = vi.fn();
const createMock = vi.fn();
const rollbackMock = vi.fn();
const listCheckpointsMock = vi.fn();
const preferencesGetMock = vi.fn();
const preferencesUpdateMock = vi.fn();

const startRunMock = vi.fn(() => true);
const stopRunMock = vi.fn(() => true);
const resumeRunMock = vi.fn(() => true);
const connectMock = vi.fn();
const disconnectMock = vi.fn();

let wsHandlers: Record<string, Function> = {};

vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { user_id: "u1", uid: "u1", name: "Ahad" },
    isAuthenticated: true,
  }),
}));

vi.mock("@/lib/api", () => ({
  agentsAPI: {
    get: (...args: any[]) => getMock(...args),
    create: (...args: any[]) => createMock(...args),
    rollback: (...args: any[]) => rollbackMock(...args),
    listCheckpoints: (...args: any[]) => listCheckpointsMock(...args),
  },
  preferencesAPI: {
    get: (...args: any[]) => preferencesGetMock(...args),
    update: (...args: any[]) => preferencesUpdateMock(...args),
  },
}));

vi.mock("@/lib/websocket", () => ({
  createWebSocketClient: (_id: string, _uid: string, handlers: any) => {
    wsHandlers = handlers;
    return {
      connect: connectMock,
      disconnect: disconnectMock,
      startRun: startRunMock,
      stopRun: stopRunMock,
      resumeRun: resumeRunMock,
      get connected() {
        return true;
      },
    };
  },
  AgentWebSocketClient: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));

vi.mock("@/components/LiquidEther", () => ({
  default: () => <div data-testid="liquid-ether" />,
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    h2: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

import EnhancedChatView from "@/components/EnhancedChatView";

describe("EnhancedChatView", () => {
  beforeEach(() => {
    wsHandlers = {};
    getMock.mockReset();
    createMock.mockReset();
    rollbackMock.mockReset();
    listCheckpointsMock.mockReset();
    preferencesGetMock.mockReset();
    preferencesUpdateMock.mockReset();
    startRunMock.mockReset();
    startRunMock.mockReturnValue(true);
    stopRunMock.mockReset();
    resumeRunMock.mockReset();
    resumeRunMock.mockReturnValue(true);
    connectMock.mockReset();
    disconnectMock.mockReset();

    preferencesGetMock.mockResolvedValue({
      success: true,
      preferences: { theme: "light", console_mode: "basic", agent: {} },
    });
    getMock.mockResolvedValue({
      success: true,
      data: {
        title: "Test Chat",
        messages: [
          { role: "user", content: "Hello", message_id: "m1" },
          {
            role: "assistant",
            content: "Hi there",
            message_id: "m2",
            checkpoint_id: "cp_tip",
            metadata: { reasoning: "thought" },
          },
        ],
        rollback_checkpoint_id: null,
      },
    });
    listCheckpointsMock.mockResolvedValue([
      { checkpoint_id: "cp_tip", parent_checkpoint_id: "cp_parent", timestamp: null, current_task: null, message_snippet: null },
      { checkpoint_id: "cp_parent", parent_checkpoint_id: null, timestamp: null, current_task: null, message_snippet: null },
    ]);
    rollbackMock.mockResolvedValue({ success: true, checkpoint_id: "cp_parent" });
  });

  it("loads chat history and connects websocket", async () => {
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(getMock).toHaveBeenCalledWith("u1", "chat_1");
      expect(connectMock).toHaveBeenCalled();
      expect(screen.getByText("Hello")).toBeInTheDocument();
      expect(screen.getByText("Hi there")).toBeInTheDocument();
      expect(screen.getByText("Test Chat")).toBeInTheDocument();
    });
  });

  it("ignores stale WS backlog when session reopens with run_active=false", async () => {
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 10, run_active: false, backlog_count: 3, epoch: 1 });
      wsHandlers.onLlmToken?.({ text: "stale reasoning", channel: "reasoning" });
      wsHandlers.onRunStarted?.({ execution_id: "old", query: "old query" });
    });

    expect(screen.queryByText(/Agent activity/i)).not.toBeInTheDocument();
    expect(screen.queryByText("stale reasoning")).not.toBeInTheDocument();
    expect(screen.queryByText("Thinking…")).not.toBeInTheDocument();
  });

  it("does not duplicate assistant bubble when resuming an active run from history", async () => {
    getMock.mockResolvedValue({
      success: true,
      data: {
        title: "Test Chat",
        messages: [
          { role: "user", content: "Find the secret", message_id: "m1" },
          {
            role: "assistant",
            content: "The user wants to find a secret message inside the attached file.",
            message_id: "m2",
            metadata: {
              steps: [
                {
                  type: "reasoning",
                  content: "The user wants to find a secret message inside the attached file.",
                },
              ],
            },
          },
        ],
        rollback_checkpoint_id: null,
      },
    });

    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("Find the secret")).toBeInTheDocument());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 5, run_active: true, backlog_count: 2, epoch: 1 });
    });

    expect(screen.queryAllByText(/secret message inside the attached file/i)).toHaveLength(0);
    expect(screen.getAllByText("Thinking…")).toHaveLength(1);
  });

  it("does not wipe the live turn on node.finished(finish) before run.completed", async () => {
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 0, run_active: true, backlog_count: 0, epoch: 1 });
      wsHandlers.onRunStarted?.({ execution_id: "r1", query: "Keep me visible" });
      wsHandlers.onLlmToken?.({ text: "Partial answer", channel: "output" });
    });

    expect(await screen.findByText("Keep me visible")).toBeInTheDocument();
    expect(screen.getByText("Partial answer")).toBeInTheDocument();

    // Stale/empty history — the old bug finalized here and blanked the UI.
    getMock.mockResolvedValueOnce({
      success: true,
      data: { title: "Test Chat", messages: [], rollback_checkpoint_id: null },
    });

    await act(async () => {
      wsHandlers.onNodeFinished?.({
        node: "agent_node",
        next_step: { action: "finish" },
      });
    });

    expect(screen.getByText("Keep me visible")).toBeInTheDocument();
    expect(screen.getByText("Partial answer")).toBeInTheDocument();
    expect(getMock.mock.calls.length).toBe(1);
  });

  it("streams tokens into live bubble then finalizes on run.completed", async () => {
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 0, run_active: true, backlog_count: 0, epoch: 1 });
      wsHandlers.onRunStarted?.({ execution_id: "r1", query: "Next?" });
      wsHandlers.onLlmToken?.({ text: "Rea", channel: "reasoning" });
      wsHandlers.onLlmToken?.({ text: "Ans", channel: "output" });
      wsHandlers.onToolStarted?.({ tool_name: "clock", tool_args: {} });
      wsHandlers.onToolFinished?.({ tool_name: "clock", result: "12:00", success: true });
    });

    expect(await screen.findByText(/Ans/)).toBeInTheDocument();
    expect(screen.getByText("Rea")).toBeInTheDocument();
    expect(screen.getByText("clock")).toBeInTheDocument();
    expect(screen.queryByText(/Agent activity/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Reasoning$/i)).not.toBeInTheDocument();

    getMock.mockResolvedValueOnce({
      success: true,
      data: {
        title: "Test Chat",
        messages: [
          { role: "user", content: "Hello" },
          { role: "assistant", content: "Hi there", checkpoint_id: "cp_tip" },
          { role: "user", content: "Next?" },
          { role: "assistant", content: "Ans", checkpoint_id: "cp_new" },
        ],
        rollback_checkpoint_id: null,
      },
    });

    await act(async () => {
      await wsHandlers.onRunCompleted?.({
        execution_id: "r1",
        stopped: false,
        answer: "Ans",
        checkpoint_id: "cp_new",
      });
    });

    await waitFor(() => expect(getMock.mock.calls.length).toBeGreaterThan(1));
  });

  it("keeps child reasoning scoped to the matching child card", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 0, run_active: true, backlog_count: 0, epoch: 1 });
      wsHandlers.onRunStarted?.({ execution_id: "r-child", query: "delegate" });
      wsHandlers.onChildStarted?.({
        agent_name: "child_agent",
        child_agent_id: "child-1",
        task: "Investigate child marker",
      });
      wsHandlers.onLlmToken?.({ text: "child-only-reasoning", channel: "reasoning", child_agent_id: "child-1" });
      wsHandlers.onChildStep?.({
        agent_name: "child_agent",
        child_agent_id: "child-1",
        event: { step: "collect", message: "Collecting", status: "in_progress" },
      });
      wsHandlers.onChildFinished?.({
        agent_name: "child_agent",
        child_agent_id: "child-1",
        result: "child done",
        success: true,
      });
    });

    expect(screen.queryByText("Thinking…")).not.toBeInTheDocument();
    expect(screen.getAllByText("Investigate child marker").length).toBeGreaterThan(0);
    expect(screen.getByText("child-1")).toBeInTheDocument();

    await user.click(screen.getByTitle("Show child details"));
  });

  it("ignores run.completed for a different execution id while parent run is active", async () => {
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 0, run_active: true, backlog_count: 0, epoch: 1 });
      wsHandlers.onRunStarted?.({ execution_id: "parent-run", query: "delegate then summarize" });
      wsHandlers.onChildStarted?.({
        agent_name: "child_agent",
        child_agent_id: "child-1",
        task: "Collect facts",
      });
      wsHandlers.onChildFinished?.({
        agent_name: "child_agent",
        child_agent_id: "child-1",
        result: "facts ready",
        success: true,
      });
      wsHandlers.onRunCompleted?.({
        execution_id: "child-run",
        stopped: false,
        answer: "wrong completion",
      });
    });

    expect(screen.getByText("delegate then summarize")).toBeInTheDocument();
    expect(screen.queryByText("wrong completion")).not.toBeInTheDocument();
    expect(screen.getAllByText("Collect facts").length).toBeGreaterThan(0);
  });

  it("keeps an interrupt answer visible while the run resumes", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 0, run_active: true, backlog_count: 0, epoch: 1 });
      wsHandlers.onRunStarted?.({ execution_id: "r1", query: "Weather today?" });
      wsHandlers.onLlmToken?.({ text: "I need a location.", channel: "reasoning" });
      wsHandlers.onRunInterrupted?.({
        execution_id: "r1",
        kind: "question",
        payload: { prompt: "Which location?" },
      });
    });

    await user.type(screen.getByPlaceholderText("Type your answer…"), "Hyderabad, India");
    await user.click(screen.getByRole("button", { name: "Send answer" }));

    expect(screen.getByText("User response: Hyderabad, India")).toBeInTheDocument();
    expect(screen.queryByText("Which location?")).not.toBeInTheDocument();
  });

  it("stop button calls run.stop while loading", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 0, run_active: true, backlog_count: 0, epoch: 1 });
      wsHandlers.onRunStarted?.({ execution_id: "r1", query: "go" });
    });

    const stopBtn = await screen.findByTitle("Stop");
    await user.click(stopBtn);
    expect(stopRunMock).toHaveBeenCalled();
  });

  it("stop freezes streamed answer instead of reverting to older history", async () => {
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 0, run_active: true, backlog_count: 0, epoch: 1 });
      wsHandlers.onRunStarted?.({ execution_id: "r1", query: "Find secret" });
      wsHandlers.onLlmToken?.({ text: "Earlier thinking step", channel: "reasoning" });
      wsHandlers.onLlmToken?.({ text: "Secret is ABC", channel: "output" });
    });

    expect(await screen.findByText("Secret is ABC")).toBeInTheDocument();

    getMock.mockResolvedValueOnce({
      success: true,
      data: {
        title: "Test Chat",
        messages: [
          { role: "user", content: "Find secret" },
          {
            role: "assistant",
            content: "Earlier thinking step that should not replace the stream",
            message_id: "stale",
          },
        ],
        rollback_checkpoint_id: null,
      },
    });

    await act(async () => {
      await wsHandlers.onRunCompleted?.({
        execution_id: "r1",
        stopped: true,
        answer: null,
        checkpoint_id: "cp_stop",
      });
    });

    await waitFor(() => {
      expect(screen.getByText("Secret is ABC")).toBeInTheDocument();
      expect(
        screen.queryByText("Earlier thinking step that should not replace the stream")
      ).not.toBeInTheDocument();
    });
  });

  it("shows a cache badge on live and finalized assistant turns when llm cache was used", async () => {
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(connectMock).toHaveBeenCalled());

    await act(async () => {
      wsHandlers.onSessionReady?.({ last_seq: 0, run_active: true, backlog_count: 0, epoch: 1 });
      wsHandlers.onRunStarted?.({ execution_id: "r-cache", query: "cached query" });
      wsHandlers.onLlmCacheHit?.({ source_call_id: "call-1", model_id: "gpt-5" });
      wsHandlers.onLlmToken?.({ text: "Cached answer", channel: "output" });
    });

    expect(await screen.findByText("cache")).toBeInTheDocument();

    getMock.mockResolvedValueOnce({
      success: true,
      data: {
        title: "Test Chat",
        messages: [
          { role: "user", content: "cached query" },
          {
            role: "assistant",
            content: "Cached answer",
            checkpoint_id: "cp_cache",
            metadata: { cache_hit: true },
          },
        ],
        rollback_checkpoint_id: null,
      },
    });

    await act(async () => {
      await wsHandlers.onRunCompleted?.({
        execution_id: "r-cache",
        stopped: false,
        answer: "Cached answer",
        checkpoint_id: "cp_cache",
      });
    });

    await waitFor(() => {
      expect(screen.getAllByText("cache").length).toBeGreaterThan(0);
      expect(screen.getByText("Cached answer")).toBeInTheDocument();
    });
  });

  it("regenerate rolls back to parent checkpoint and restarts", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("Hi there")).toBeInTheDocument());

    const regen = screen.getByTitle("Regenerate");
    await user.click(regen);

    await waitFor(() => {
      expect(rollbackMock).toHaveBeenCalledWith("chat_1", "cp_parent");
      expect(startRunMock).toHaveBeenCalledWith("Hello");
    });
  });

  it("edit & rewind truncates and arms rollback", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("Hello")).toBeInTheDocument());

    const edit = screen.getByTitle("Edit & rewind");
    await user.click(edit);

    await waitFor(() => {
      expect(rollbackMock).toHaveBeenCalled();
      expect(screen.queryByText("Hi there")).not.toBeInTheDocument();
    });
  });

  it("shows cached chat immediately while websocket connects", async () => {
    const { setCachedChat } = await import("@/lib/chatCache");
    setCachedChat("chat_1", {
      title: "Cached Chat",
      messages: [{ role: "user", content: "Cached hello", message_id: "m0" }],
      rollbackCheckpointId: null,
    });

    render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );

    expect(screen.getByText("Cached hello")).toBeInTheDocument();
    expect(screen.queryByTestId("chat-loading")).not.toBeInTheDocument();
    await waitFor(() => expect(connectMock).toHaveBeenCalled());
  });

  it("does not flash welcome state while switching chats", async () => {
    const { rerender } = render(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_1" />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("Hello")).toBeInTheDocument());

    getMock.mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                success: true,
                data: {
                  title: "Chat 2",
                  messages: [{ role: "user", content: "Other chat", message_id: "m3" }],
                  rollback_checkpoint_id: null,
                },
              }),
            100
          )
        )
    );

    rerender(
      <MemoryRouter>
        <EnhancedChatView sessionId="chat_2" />
      </MemoryRouter>
    );

    expect(screen.getByTestId("chat-loading")).toBeInTheDocument();
    expect(screen.queryByText(/start typing below/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Continue the conversation/i)).not.toBeInTheDocument();

    await waitFor(() => expect(screen.getByText("Other chat")).toBeInTheDocument());
    expect(screen.queryByTestId("chat-loading")).not.toBeInTheDocument();
  });

  it("shows empty-state when no session", async () => {
    render(
      <MemoryRouter>
        <EnhancedChatView sessionId={null} />
      </MemoryRouter>
    );
    expect(await screen.findByText(/start typing below/i)).toBeInTheDocument();
  });

});
