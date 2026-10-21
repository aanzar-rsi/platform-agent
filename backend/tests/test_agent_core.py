"""AgentCore policy and independent-child behavior without a live database."""

import threading
import time
import uuid

import pytest

from src.agent.agent_core import AgentCore, ChildRunner, Memory, Policy, default_policy, intersect_policy


def armory(*, tools=(), subagents=()):
    return {
        "resources": {
            "tools": [{"type": "tool", "name": name, "enabled": True} for name in tools],
            "subagents": [{"type": "subagent", "name": name, "enabled": True} for name in subagents],
        },
        "groups": {"tools": {"enabled": True}, "subagents": {"enabled": True}},
    }


def enabled(policy, group):
    return [item["name"] for item in policy["resources"].get(group, []) if item.get("enabled", True)]


class FakeAgents:
    def __init__(self):
        self.agents = {}
        self.executions = {}
        self.entries = {}
        self.lock = threading.RLock()

    def get(self, agent_id):
        return self.agents.get(agent_id)

    def child(self, parent_id, policy, *, max_depth, parent_execution_id=None, max_children=None):
        with self.lock:
            parent = self.get(parent_id)
            if parent["depth"] >= max_depth:
                raise ValueError("child_not_allowed")
            row = {**parent, "agent_id": str(uuid.uuid4()), "owner_id": parent_id,
                   "owner_type": "agent", "parent_agent_id": parent_id, "state": "open",
                   "depth": parent["depth"] + 1, "policy": policy}
            self.agents[row["agent_id"]] = row
            return row

    def start_execution(self, agent_id, *, execution_id=None, parent_execution_id=None):
        with self.lock:
            if any(run["agent_id"] == agent_id and run["state"] in ("running", "interrupted")
                   for run in self.executions.values()):
                raise ValueError("already_running")
            if self.agents[agent_id]["state"] == "closed":
                raise ValueError("agent_closed")
            row = {"execution_id": execution_id or str(uuid.uuid4()), "agent_id": agent_id, "state": "running",
                   "parent_execution_id": parent_execution_id, "result": None, "error": None}
            self.executions[row["execution_id"]] = row
            return row

    def update_policy(self, agent_id, field, scope, *, uid, expected_version):
        with self.lock:
            agent = self.agents[agent_id]
            if agent["state"] != "open":
                raise ValueError("agent_closed")
            if agent["policy_version"] != expected_version:
                raise ValueError("policy_conflict")
            if str(agent["owner_id"]) != uid or agent["owner_type"] != "user":
                raise PermissionError("policy_update_denied")
            agent["policy"] = {**agent["policy"], field: scope}
            agent["policy_version"] += 1
            return agent

    def finish_execution(self, execution_id, state, *, result=None, error=None):
        with self.lock:
            self.executions[execution_id].update(state=state, result=result, error=error)

    def active_execution(self, agent_id):
        return next((row for row in self.executions.values() if row["agent_id"] == agent_id
                     and row["state"] in ("running", "interrupted")), None)

    def latest_execution(self, agent_id):
        return next((row for row in reversed(list(self.executions.values())) if row["agent_id"] == agent_id), None)

    def children(self, parent_execution_id):
        return [{**self.agents[row["agent_id"]], "execution_state": row["state"]}
                for row in list(self.executions.values()) if row["parent_execution_id"] == parent_execution_id]

    def child_outcome(self, parent_id, parent_execution_id, child_id):
        row = self.latest_execution(child_id)
        return row if row and row["parent_execution_id"] == parent_execution_id and self.agents[child_id]["parent_agent_id"] == parent_id else None

    def close(self, agent_id):
        with self.lock:
            if self.active_execution(agent_id):
                raise ValueError("agent_busy")
            self.agents[agent_id]["state"] = "closed"
            return self.agents[agent_id]

    def append_message(self, agent_id, execution_id, content, **kwargs):
        if self.agents[agent_id]["state"] == "closed":
            raise ValueError("agent_closed")
        self.entries.setdefault(agent_id, []).append({"content": content, **kwargs})

    def messages(self, agent_id):
        return self.entries.get(agent_id, [])


def parent_core(repo):
    agent_id = str(uuid.uuid4())
    row = {"agent_id": agent_id, "owner_id": str(uuid.uuid4()), "owner_type": "user",
           "parent_agent_id": None,
           "latest_session_id": None, "depth": 0, "state": "open", "policy_version": 1,
           "policy": default_policy().as_dict()}
    repo.agents[agent_id] = row
    row["policy_ceiling"] = default_policy().as_dict()
    return AgentCore(row, repo)


def test_policy_intersection_and_memory_identity():
    parent = Policy(armory(tools=("read_file",), subagents=("worker",)), default_policy().memory, {}, {})
    requested = Policy(armory(tools=("read_file", "execute_bash"), subagents=("worker", "admin")),
                       {"read": ["USER", "TENANT", "AGENT"], "write": ["USER", "AGENT"],
                        "tenant_id": "forged"}, {}, {})
    effective = intersect_policy(parent, requested)
    assert enabled(effective.armory, "tools") == ["read_file"]
    assert enabled(effective.armory, "subagents") == ["worker"]
    assert effective.memory["read"] == ["USER", "AGENT"]
    assert effective.memory["write"] == ["USER"]
    assert effective.memory["tenant_id"] is None
    memory = Memory(effective.memory, "authenticated", repository=type("Repo", (), {"get": lambda s, uid: [{"key": "name", "value": uid}]})())
    assert memory.retrieve("name") == [{"key": "name", "value": "authenticated"}]
    with pytest.raises(PermissionError):
        memory.retrieve(scope="TENANT")


def test_user_agent_spawns_with_inherited_or_narrowed_policy():
    repo = FakeAgents()
    parent = parent_core(repo)
    parent.run()
    runner = ChildRunner(repo, workers=1)
    try:
        inherited = runner.spawn_child(parent, "first", lambda task, ctx: "ok", {})
        assert runner.await_child(inherited.child_agent_id) == "ok"
        assert set(enabled(repo.get(inherited.child_agent_id)["policy"]["armory"], "tools")) == set(enabled(parent.policy.armory, "tools"))
        narrowed = runner.spawn_child(parent, "second", lambda task, ctx: "ok", {},
                                     requested_policy=Policy(armory(tools=("read_file",)), {}, {}, {}))
        assert runner.await_child(narrowed.child_agent_id) == "ok"
        assert enabled(repo.get(narrowed.child_agent_id)["policy"]["armory"], "tools") == ["read_file"]
        assert set(repo.get(narrowed.child_agent_id)["policy"]["memory"]["read"]) == set(parent.policy.memory["read"])
    finally:
        runner.pool.shutdown(wait=True)


def test_nonblocking_children_and_one_run_per_agent():
    repo = FakeAgents()
    parent = parent_core(repo)
    parent.run()
    gate = threading.Event()
    def slow(task, context):
        gate.wait(1)
        return task
    runner = ChildRunner(repo, workers=2, max_children=2, max_depth=1, timeout=2)
    try:
        first = runner.spawn_child(parent, "first", slow, {})
        second = runner.spawn_child(parent, "second", lambda task, ctx: "done", {})
        assert second.future.result(timeout=1) == "done"
        with pytest.raises(TimeoutError):
            runner.await_child(first.child_agent_id, timeout=0.01)
        with pytest.raises(ValueError, match="child_limit"):
            runner.spawn_child(parent, "third", lambda task, ctx: task, {})
        with pytest.raises(ValueError, match="already_running"):
            parent.run()
        with pytest.raises(ValueError, match="agent_busy"):
            AgentCore(repo.get(first.child_agent_id), repo).close()
        gate.set()
        assert runner.await_child(first.child_agent_id, timeout=2) == "first"
        assert repo.get(first.child_agent_id)["state"] == "closed"
        with pytest.raises(ValueError, match="agent_closed"):
            AgentCore(repo.get(first.child_agent_id), repo).run()
        parent.finish("completed")
        parent.run()
        parent.finish("completed")
    finally:
        gate.set()
        runner.pool.shutdown(wait=True)


def test_policy_updates_and_interrupted_close():
    repo = FakeAgents()
    agent = parent_core(repo)
    with pytest.raises(PermissionError):
        agent.update_armory_policy(armory(tools=("new_tool",)), uid=agent.id.owner_id, expected_version=1)
    agent.update_armory_policy(armory(tools=("read_file",)), uid=agent.id.owner_id, expected_version=1)
    assert agent.policy.version == 2
    with pytest.raises(ValueError, match="policy_conflict"):
        agent.update_memory_policy({"read": ["USER"]}, uid=agent.id.owner_id, expected_version=1)
    agent.update_memory_policy({"read": ["USER"]}, uid=agent.id.owner_id, expected_version=2)
    assert agent.policy.version == 3
    agent.update_memory_policy({"read": ["USER", "AGENT"]}, uid=agent.id.owner_id, expected_version=3)
    agent.update_armory_policy(agent.record["policy_ceiling"]["armory"],
                               uid=agent.id.owner_id, expected_version=4)
    assert agent.policy.version == 5
    with pytest.raises(PermissionError):
        agent.update_memory_policy({"tenant_id": "forged"}, uid=agent.id.owner_id, expected_version=5)
    with pytest.raises(ValueError, match="invalid_armory_policy"):
        agent.update_armory_policy({"resources": []}, uid=agent.id.owner_id, expected_version=5)
    execution_id = agent.run()
    agent.finish("interrupted")
    with pytest.raises(ValueError, match="agent_busy"):
        agent.close()
    repo.finish_execution(execution_id, "cancelled")
    agent.close()
    agent.close()
    with pytest.raises(ValueError, match="agent_closed"):
        agent.run()
    with pytest.raises(ValueError, match="agent_closed"):
        agent.update_armory_policy({}, uid=agent.id.owner_id, expected_version=5)


def test_tenant_policy_can_be_disabled_and_restored_to_trusted_ceiling():
    repo = FakeAgents()
    agent = parent_core(repo)
    agent.record["policy"]["memory"].update(tenant_id="trusted", read=["USER", "TENANT"])
    agent.record["policy_ceiling"]["memory"].update(tenant_id="trusted", read=["USER", "TENANT"])
    agent.update_memory_policy({"tenant_id": None}, uid=agent.id.owner_id, expected_version=1)
    agent.update_memory_policy({"tenant_id": "trusted"}, uid=agent.id.owner_id, expected_version=2)
    assert agent.policy.memory["tenant_id"] == "trusted"


def test_child_result_requires_parent_lineage():
    repo = FakeAgents()
    parent = parent_core(repo)
    parent.run()
    runner = ChildRunner(repo, workers=1)
    try:
        handle = runner.spawn_child(parent, "task", lambda task, ctx: "done", {})
        assert runner.await_child(handle.child_agent_id, parent_agent_id=parent.id.agent_id,
                                   parent_execution_id=parent.active_execution_id) == "done"
        with pytest.raises(PermissionError, match="child_not_owned"):
            runner.await_child(handle.child_agent_id, parent_agent_id=str(uuid.uuid4()),
                                parent_execution_id=parent.active_execution_id)
    finally:
        runner.pool.shutdown(wait=True)


def test_cancelled_running_child_cannot_commit_result():
    repo = FakeAgents()
    parent = parent_core(repo)
    parent.run()
    started, release = threading.Event(), threading.Event()

    def slow(task, context):
        started.set()
        release.wait(1)
        return "must not commit"

    runner = ChildRunner(repo, workers=1, timeout=2)
    try:
        handle = runner.spawn_child(parent, "task", slow, {})
        assert started.wait(1)
        assert runner.cancel(handle.child_agent_id)
        release.set()
        with pytest.raises(RuntimeError, match="InterruptedError"):
            runner.await_child(handle.child_agent_id)
        assert repo.latest_execution(handle.child_agent_id)["state"] == "cancelled"
        assert repo.get(handle.child_agent_id)["state"] == "closed"
        assert not any(entry["content"] == "must not commit" for entry in repo.entries[handle.child_agent_id])
    finally:
        release.set()
        runner.pool.shutdown(wait=True)


def test_child_reasoning_stays_in_child_stream():
    from src.agent.subagent_stream import reset_child_callback, set_child_callback
    from src.agent.token_stream import emit_token, reset_token_callback, set_token_callback

    repo = FakeAgents()
    parent = parent_core(repo)
    parent.run()
    runner = ChildRunner(repo, workers=1)
    parent_tokens = []
    child_events = []
    parent_token = set_token_callback(lambda text, channel: parent_tokens.append((text, channel)))
    child_token = set_child_callback(lambda name, event: child_events.append((name, event)))
    try:
        handle = runner.spawn_child(
            parent,
            "task",
            lambda task, ctx: (emit_token("child-think", "reasoning"), emit_token("child-out", "output"), "done")[2],
            {},
        )
        assert runner.await_child(handle.child_agent_id) == "done"
    finally:
        reset_child_callback(child_token)
        reset_token_callback(parent_token)
        runner.pool.shutdown(wait=True)

    assert parent_tokens == []
    kinds = [event.get("kind") for _, event in child_events]
    assert kinds[:3] == ["start", "reasoning", "complete"]
    assert child_events[1][1].get("message") == "child-think"
