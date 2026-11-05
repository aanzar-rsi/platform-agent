"""Verify Preflight controls what the merged planner may see and execute."""

import json
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import HumanMessage
from langgraph.graph import END

from src.agent.edges.routing import route_from_preflight
from src.agent.nodes import agentnode
from src.agent.nodes.input_security_gate import input_security_gate_node
from src.agent.nodes.output_security_gate import output_security_gate_node
from src.agent.nodes.preflight import preflight_node


REQUEST = {"request_id": "65f0a1b2c3d4e5f607182901", "query": "Read my quotations", "query_type": "chat"}


def _preflight_state():
    return {"planner_request": REQUEST, "preloaded_context": {}, "messages": [HumanMessage(content=REQUEST["query"])]}


def test_governed_context_reaches_planner_and_only_approved_tools_are_usable():
    identity = SimpleNamespace(decision="allow", reason_code="identity_resolved", context={
        "user_id": "u1", "tenant_id": "t1", "role_id": "r1", "permissions": ["quotation.read"],
        "policy_version": 1,
        "tenant_policy": {"permission_domains": {"quotation": "procurement"}},
    })
    admission = SimpleNamespace(decision="allow", reason_code="admission_passed", context={"checks": {}})
    governed = SimpleNamespace(decision="allow", reason_code="context_ready", details={
        "maximum_sensitivity": "INTERNAL",
    }, items=(), planner_context=lambda: {
        "items": [{"kind": "episodic", "content": "Use the approved quotation search", "trust": "assumption"}],
        "memory_references": [], "reduced": False, "degradations": [],
    })
    resources = [SimpleNamespace(type="tool", name="approved", description="Read quotations",
                                 target=SimpleNamespace(remote_name="READ_QUOTE")),
                 SimpleNamespace(type="tool", name="hidden", description="Write quotations",
                                 target=SimpleNamespace(remote_name="WRITE_QUOTE"))]
    with patch("src.agent.nodes.preflight.node.resolve_preflight_identity", return_value=identity), \
         patch("src.agent.nodes.preflight.node.evaluate_admission", return_value=admission), \
         patch("src.agent.nodes.preflight.node.authorize_request", return_value=SimpleNamespace(
             decision="allow", reason_code="business_authorized", required=("quotation.read",),
             held=("quotation.read",))), \
         patch("src.agent.nodes.preflight.node.load_governed_context", return_value=governed), \
         patch("src.agent.nodes.preflight.node.Armory.list", return_value=resources), \
         patch("src.agent.nodes.preflight.node.resource_allowed", side_effect=lambda _type, name, **_kwargs: name == "approved"), \
         patch("src.agent.nodes.preflight.node._audit_or_deny", return_value=("audit-1", None)):
        approved = preflight_node(_preflight_state(), {})

    assert approved["planner_context"]["authorization"]["permissions_needed"] == ["quotation.read"]
    assert approved["planner_context"]["domain"] == "procurement"
    assert [item["name"] for item in approved["planner_context"]["resources"]] == ["approved"]
    assert route_from_preflight(approved) == "input_security_gate"

    state = {**_preflight_state(), **approved, "execution_history": [], "execution_memory": {},
             "context_memory": {}, "planner_mode": True}
    with patch.object(agentnode.Armory, "list", return_value=resources), \
         patch.object(agentnode, "_safe_learned_experiences", return_value="(none)"), \
         patch.object(agentnode, "call_llm_stream", return_value=iter(["<action>exit</action><reasoning>Done</reasoning><data>Done</data>"])) as stream:
        result = agentnode.agent_node(state, {"configurable": {"owner_id": "u1"}})
    prompt = stream.call_args.args[0]
    assert "Use the approved quotation search" in prompt
    assert "quotation.read" in prompt
    assert "armory.tool.approved" in prompt
    assert "armory.tool.hidden" not in prompt
    assert result["planner_resources"] == [{"type": "tool", "name": "approved"}]

    plan = {"phases": [{"sequence": 1, "steps": [{"id": "s1", "action": "armory_call",
             "resource_type": "tool", "name": "hidden", "parameters": {}, "task": "Run hidden tool"}]}]}
    response = {**state, "planner_response": "<action>continue</action><reasoning>Need data</reasoning>"
                f"<task>read</task><data>{json.dumps(plan)}</data>",
                "planner_response_type": "planner", "planner_resources": result["planner_resources"]}
    rejected = input_security_gate_node(response)
    assert rejected["planned_phases"][0]["steps"][0]["command"]["action"] == "replan"
    assert "unavailable armory resource" in rejected["planner_error"]["message"]


def test_preflight_denial_never_reaches_planner_or_executor():
    with patch("src.agent.nodes.preflight.node.resolve_preflight_identity", return_value=SimpleNamespace(
        decision="deny", reason_code="tenant_membership_missing", message="Access denied", context={})), \
         patch("src.agent.nodes.preflight.node._audit_or_deny", return_value=("audit-1", None)):
        denied = preflight_node(_preflight_state(), {})
    assert route_from_preflight(denied) == END
    assert denied["planner_context"] == {}
    with patch.object(agentnode, "call_llm_stream") as stream:
        result = agentnode.agent_node({**_preflight_state(), **denied, "execution_history": []})
    stream.assert_not_called()
    assert result["next_step"]["action"] == "finish"


def test_executor_results_gain_verified_provenance_before_planner_exposure():
    state = {"execution_history": [], "execution_memory": {}, "context_memory": None,
             "planned_phase_index": 0, "planned_phases": [{"sequence": 1, "steps": [{"id": "s1"}]}],
             "planner_context": {"identity": {"user_id": "u1", "tenant_id": "t1"}, "context": {
                 "items": [], "maximum_sensitivity": "INTERNAL", "token_budget": 1500}},
             "executor_output": {"action_id": "a1", "source": "dispatch_batch", "phase": 1,
                 "steps": [{"id": "s1", "results": [{"kind": "armory_result", "value": "verified result",
                     "success": True, "name": "approved", "task": "read", "metadata": {"resource_type": "tool"}}]}]}}
    update = output_security_gate_node(state, {"configurable": {"owner_id": "u1"}})
    assert update["planner_context"]["context"]["items"][0]["content"] == "verified result"
    entry = next(iter(update["execution_memory"].values()))
    assert (entry["owner_user_id"], entry["tenant_id"]) == ("u1", "t1")
