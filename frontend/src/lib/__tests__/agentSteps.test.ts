import { describe, expect, it } from "vitest";

import {
  appendChildStarted,
  appendChildProgress,
  updateChildFinished,
  updateSubagentFinished,
  updateToolFinished,
} from "@/lib/agentSteps";
import type { AgentStep } from "@/types/backend";


describe("agentSteps child routing", () => {
  it("keeps one child card across duplicate starts without losing progress or completion", () => {
    const steps: AgentStep[] = [];
    for (let index = 1; index <= 3; index++) {
      appendChildStarted(steps, { id: `child-${index}`, child_agent_id: `child-${index}`,
        agent_name: "child_agent", status: "running", progress: [] });
      appendChildProgress(steps, `child-${index}`, { step: "search", message: `work ${index}`, status: "in_progress" });
      appendChildStarted(steps, { id: `child-${index}`, child_agent_id: `child-${index}`,
        agent_name: "child_agent", task: `task ${index}`, status: "running", progress: [] });
    }
    updateChildFinished(steps, "child-1", { status: "done", result: "finished" });
    appendChildStarted(steps, { id: "child-1", child_agent_id: "child-1",
      agent_name: "child_agent", status: "running", progress: [] });
    expect(steps).toHaveLength(3);
    expect(steps.map((step) => step.type === "child_agent" && step.child.task)).toEqual(["task 1", "task 2", "task 3"]);
    expect(steps[0].type === "child_agent" && steps[0].child.progress[0].message).toBe("work 1");
    expect(steps[0].type === "child_agent" && steps[0].child.status).toBe("done");
  });
  it("updates only matching child id and merges reasoning deltas", () => {
    const steps: AgentStep[] = [
      {
        type: "child_agent",
        child: {
          id: "c1",
          child_agent_id: "child-1",
          agent_name: "child_agent",
          status: "running",
          progress: [],
        },
      },
      {
        type: "child_agent",
        child: {
          id: "c2",
          child_agent_id: "child-2",
          agent_name: "child_agent",
          status: "running",
          progress: [],
        },
      },
    ];

    appendChildProgress(steps, "child-1", {
      step: "reasoning",
      status: "in_progress",
      kind: "reasoning",
      message: "hello",
      reasoningDone: false,
    });
    appendChildProgress(steps, "child-1", {
      step: "reasoning",
      status: "in_progress",
      kind: "reasoning",
      message: " world",
      reasoningDone: false,
    });
    appendChildProgress(steps, undefined, {
      step: "collect",
      status: "in_progress",
      message: "ignored",
    });

    const child1 = steps[0].type === "child_agent" ? steps[0].child : null;
    const child2 = steps[1].type === "child_agent" ? steps[1].child : null;
    expect(child1?.progress).toHaveLength(1);
    expect(child1?.progress[0].message).toBe("hello world");
    expect(child2?.progress).toHaveLength(0);

    updateChildFinished(steps, "child-1", { status: "done", success: true });
    expect(child1?.status).toBe("done");
    expect(child1?.progress[0].reasoningDone).toBe(true);
  });
});

describe("agentSteps action correlation", () => {
  it("finishes only the matching repeated tool and subagent call", () => {
    const steps: AgentStep[] = [
      { type: "tool", tool: { id: "tool-1", tool_name: "lookup", status: "running" } },
      { type: "tool", tool: { id: "tool-2", tool_name: "lookup", status: "running" } },
      {
        type: "subagent",
        subagent: { id: "agent-1", agent_name: "researcher", status: "running", progress: [] },
      },
      {
        type: "subagent",
        subagent: { id: "agent-2", agent_name: "researcher", status: "running", progress: [] },
      },
    ];

    updateToolFinished(steps, "lookup", { status: "done", result: "two" }, "tool-2");
    updateSubagentFinished(steps, "researcher", { status: "done", result: "one" }, "agent-1");

    expect(steps[0].type === "tool" && steps[0].tool.status).toBe("running");
    expect(steps[1].type === "tool" && steps[1].tool.result).toBe("two");
    expect(steps[2].type === "subagent" && steps[2].subagent.result).toBe("one");
    expect(steps[3].type === "subagent" && steps[3].subagent.status).toBe("running");
  });
});
