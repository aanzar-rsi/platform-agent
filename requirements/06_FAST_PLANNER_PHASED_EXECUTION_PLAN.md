# Fast/Planner Prompt Split and Phased Plan Execution

## Objective

Reduce per-loop LLM prompt overhead in `agent_node` while enabling richer planning output (up to N steps with ordered execution phases).

## Decisions

1. Planner returns **up to N steps** (`max_plan_steps`), not exactly N.
2. Execution ordering uses **ordered phases**:
   - phases run sequentially
   - steps inside a phase are logically parallel
3. Prompt selection:
   - use **fast prompt** when:
     - first request in an `AgentCore`
     - user query length `< 10`
   - otherwise use **planner prompt**
4. Capability section is renamed to **armory** and can include any resource type.

## Implementation status and next wave

### Prompt layer

- Add `src/prompts/fast_agent.txt`
- Add `src/prompts/planner_agent.txt`
- Keep `agentnode.txt` as legacy fallback during migration.
- Add prompt-loader support for fast/planner prompt rendering.

### Agent execution model

- Add parser support for a planner-provided phased plan.
- Persist phased plan state in graph state keys:
  - `planned_phases`
  - `planned_phase_index`
  - `phase_step_results` (reducer channel, reset by the collector)
- Dispatch each phase from state without calling the planner between steps or phases.

## Strict plan and parallel phases

- Validate the entire plan with Pydantic before accepting any steps; no truncation or silent dropping.
- Require unique IDs, consecutive phase numbers, known actions, available resources, and dependencies only on prior phases.
- Keep `finish` last and `ask_user` alone in its phase; reject unsupported parallel mutation/approval paths.
- A `plan_dispatcher` sends independent tool/subagent steps through LangGraph `Send` in parallel. Branches reuse existing executor logic and input validation.
- Parallel branches use isolated input snapshots and a reducer for per-step outcomes; one `phase_collector` merges history, messages, execution memory, and context memory in plan order. No branch may write shared state directly.
- Failures or a newly received user turn invalidate remaining steps and return to the planner. Interrupts must resume the same step without duplicating side effects.

## Runtime configuration

- Add `max_plan_steps` to agent runtime preferences.
- Thread through `configurable` runtime for use in planner prompt rendering.

## Armory shape in prompts

Armory prompt content is organized as:

- tools
- subagents
- child agent actions (`spawn_children`, `collect_child`)
- control actions (`context_select`, `ask_user`, `finish`)

## Parsing contract

### Fast prompt

- Can emit normal single-step XML actions.
- Can escalate to planner via:
  - `<action>plan</action>` with empty or minimal payload.

### Planner prompt

- Emits `<action>plan</action>` and `<steps_json>...</steps_json>`
- `steps_json` contains ordered `phases` and per-phase `steps`.
- Agent validates the complete payload against `max_plan_steps` before execution.

## Validation rules

- Reject malformed plan JSON.
- Reject unknown actions and unavailable resources, duplicate step IDs, invalid references, non-consecutive phases, and plans exceeding `max_plan_steps`.
- On invalid output, request a corrected plan or return a visible error; do not execute a partial plan.

## Compatibility

- Existing single-step XML flow remains supported.
- Existing executor nodes are reused.
- Existing route/action names are preserved.

## Test plan

- Prompt template contract tests for `fast_agent` and `planner_agent`.
- Agent-node parsing tests for `plan` action and step dispatch.
- Regression tests for legacy single-step XML parsing.
- End-to-end smoke: planner produces phases, agent dispatches step-by-step.
- Parallel fan-out, reducer merge, dependency resolution, failure/replan, interrupt/resume, and API/CLI phase/step events.
