import { describe, expect, it } from "vitest";

import { appendChildProgress, updateChildFinished } from "@/lib/agentSteps";
import type { AgentStep } from "@/types/backend";


describe("agentSteps child routing", () => {
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
