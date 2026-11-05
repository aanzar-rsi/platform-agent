"""Business permission resolution and execution boundaries."""

import pytest
from unittest.mock import patch

from src.agent.preflight.authorization import (
    authorize_child_task, authorize_request, check_resource_execution, evaluate_request_readiness,
    resource_allowed, resolve_business_intent, verify_child_scope, verify_parent_spawn,
)


CATALOG = [
    {"code": "quotation.read", "description": "View supplier quotations"},
    {"code": "purchase_order.create", "description": "Create purchase orders"},
]
POLICY = {
    "permission_domains": {"quotation": "procurement", "purchase_order": "procurement"},
}
IDENTITY = {"tenant_id": "a" * 24, "tenant_policy": POLICY, "permissions": ["quotation.read"]}


def test_classifier_only_accepts_catalog_codes():
    with patch("src.models.llm_client.call_llm", return_value={
        "codes": ["purchase_order.create"], "ambiguous": False, "question": ""
    }) as call:
        assert resolve_business_intent("create an order", CATALOG)[0] == ["purchase_order.create"]
    assert call.call_args.kwargs["output_type"] == "json"
    assert call.call_args.kwargs["temperature"] == 0.0


def test_classifier_rejects_invented_permission():
    with patch("src.models.llm_client.call_llm", return_value={
        "codes": ["purchase_order.approve"], "ambiguous": False, "question": ""
    }):
        try:
            resolve_business_intent("approve", CATALOG)
        except ValueError:
            pass
        else:
            raise AssertionError("invented permission was accepted")


def test_classifier_rejects_inconsistent_ambiguity():
    with patch("src.models.llm_client.call_llm", return_value={
        "codes": ["quotation.read"], "ambiguous": True, "question": "Which?"
    }):
        try:
            resolve_business_intent("handle quotes", CATALOG)
        except ValueError:
            pass
        else:
            raise AssertionError("ambiguous intent with selected action was accepted")


def test_request_is_denied_if_any_required_permission_is_missing():
    with patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.resolve_business_intent", return_value=(
             ["quotation.read", "purchase_order.create"], "")):
        result = authorize_request("view and create", IDENTITY, {})
    assert result.decision == "deny"
    assert result.reason_code == "permission_denied"


def test_ambiguous_request_gets_clarification():
    with patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.resolve_business_intent", return_value=([], "View or create?")):
        result = authorize_request("handle orders", IDENTITY, {})
    assert result.decision == "clarify"
    assert result.message == "View or create?"


def test_allowed_request_carries_needed_and_held_permissions():
    with patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.resolve_business_intent", return_value=(["quotation.read"], "")):
        result = authorize_request("view quotations", IDENTITY, {})
    assert result.decision == "allow"
    assert result.required == ("quotation.read",)
    assert result.held == ("quotation.read",)


def test_configured_domain_requires_explicit_mapping():
    with patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.resolve_business_intent", return_value=(["quotation.read"], "")):
        result = authorize_request("view quotations", {
            **IDENTITY, "tenant_policy": {"allowed_domains": ["procurement"]},
        }, {})
    assert result.reason_code == "domain_not_allowed"


def test_unmapped_business_tool_and_disabled_tool_are_not_available():
    mapping = {"permission_code": "purchase_order.create"}
    with patch("src.agent.preflight.authorization.repository.get_bapi_for_resource", return_value=None):
        assert not resource_allowed("tool", "mcp_unmapped", tenant_id="a" * 24,
                                    remote_name="BAPI_UNKNOWN", tenant_policy=POLICY,
                                    held={"purchase_order.create"}, required={"purchase_order.create"})
    with patch("src.agent.preflight.authorization.repository.get_bapi_for_resource", return_value=mapping):
        assert resource_allowed("tool", "mcp_purchase_order_create", tenant_id="a" * 24,
                                remote_name="BAPI_PO_CREATE", tenant_policy=POLICY,
                                held={"purchase_order.create"}, required={"purchase_order.create"})
        assert not resource_allowed("tool", "mcp_purchase_order_create", tenant_id="a" * 24,
                                    remote_name="BAPI_PO_CREATE",
                                    tenant_policy={**POLICY, "disabled_tools": ["mcp_purchase_order_create"]},
                                    held={"purchase_order.create"}, required={"purchase_order.create"})
    assert not resource_allowed("tool", "execute_bash", tenant_id="a" * 24, tenant_policy=POLICY,
                                held={"purchase_order.create"}, required={"purchase_order.create"})


def test_execution_rechecks_revoked_grants():
    current = {"tenant_id": "a" * 24, "role_id": "b" * 24,
               "membership_status": "active", "tenant_status": "active", "role_status": "active",
               "agent_state": "open", "agent_policy_version": 2, "tenant_policy": POLICY}
    with patch("src.agent.preflight.authorization.repository.get_current_authorization", return_value=current), \
         patch("src.agent.preflight.authorization.repository.get_active_auth_session", return_value={"session_id": "s"}), \
         patch("src.agent.preflight.authorization.repository.get_active_permission_codes", return_value=[]), \
         patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG):
        try:
            check_resource_execution(user_id="u", agent_id="a", session_id="s", resource_type="tool",
                                     resource_name="mcp_purchase_order_create", required=["purchase_order.create"],
                                     tenant_id="a" * 24, role_id="b" * 24, policy_version=2)
        except PermissionError:
            pass
        else:
            raise AssertionError("revoked permission was accepted")


def test_execution_rejects_unmapped_resource_even_with_grant():
    current = {"tenant_id": "a" * 24, "role_id": "b" * 24,
               "membership_status": "active", "tenant_status": "active", "role_status": "active",
               "agent_state": "open", "agent_policy_version": 2, "tenant_policy": POLICY}
    with patch("src.agent.preflight.authorization.repository.get_current_authorization", return_value=current), \
         patch("src.agent.preflight.authorization.repository.get_active_auth_session", return_value={"session_id": "s"}), \
         patch("src.agent.preflight.authorization.repository.get_active_permission_codes", return_value=["purchase_order.create"]), \
         patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG):
        try:
            check_resource_execution(user_id="u", agent_id="a", session_id="s", resource_type="tool",
                                     resource_name="mcp_unmapped", required=["purchase_order.create"],
                                     tenant_id="a" * 24, role_id="b" * 24, policy_version=2)
        except PermissionError:
            pass
        else:
            raise AssertionError("unmapped tool was accepted")


def test_parent_spawn_requires_matching_audited_scope_and_live_grants():
    context = {"version": 3, "identity": {"user_id": "u", "tenant_id": "a" * 24, "role_id": "b" * 24},
               "authorization": {"permissions_needed": ["quotation.read"]}, "resources": []}
    config = {"configurable": {"owner_id": "u", "agent_id": "parent", "execution_id": "run",
                              "session_id": "session", "policy_version": 2}}
    current = {"tenant_id": "a" * 24, "role_id": "b" * 24,
               "membership_status": "active", "tenant_status": "active", "role_status": "active",
               "agent_state": "open", "agent_policy_version": 2, "tenant_policy": POLICY}
    with patch("src.agent.preflight.authorization.repository.get_current_authorization", return_value=current), \
         patch("src.agent.preflight.authorization.repository.get_execution_authorization", return_value={"state": "running", "policy_version": 2}), \
         patch("src.agent.preflight.authorization.repository.get_active_auth_session", return_value={"session_id": "session"}), \
         patch("src.agent.preflight.authorization.repository.get_active_permission_codes", return_value=["quotation.read"]), \
         patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.repository.get_parent_decision", return_value={
             "tenant_id": "a" * 24, "role_id": "b" * 24, "decision": "allow",
             "details": {"permissions_needed": ["quotation.read"]}, "candidate_tools": [],
         }) as audit:
        assert verify_parent_spawn(context, config) == ["quotation.read"]
        audit.return_value["details"]["permissions_needed"] = ["quotation.read", "purchase_order.create"]
        with pytest.raises(PermissionError, match="parent_scope_mismatch"):
            verify_parent_spawn(context, config)


def test_child_scope_requires_real_lineage_and_matching_parent_grants():
    values = {"agent_id": "child", "child_agent_id": "child", "execution_id": "child-run",
              "parent_agent_id": "parent", "parent_execution_id": "parent-run", "owner_id": "u",
              "session_id": "session", "policy_version": 2, "parent_policy_version": 3,
              "parent_business_permissions": ["quotation.read"]}
    lineage = {"child_agent_id": "child", "parent_agent_id": "parent", "root_user_id": "u",
               "child_agent_state": "open", "parent_agent_state": "open",
               "child_execution_state": "running", "parent_execution_state": "running",
               "parent_execution_id": "parent-run", "child_policy_version": 2, "parent_policy_version": 3,
               "child_execution_policy_version": 2, "parent_execution_policy_version": 3}
    current = {"tenant_id": "a" * 24, "role_id": "b" * 24,
               "membership_status": "active", "tenant_status": "active", "role_status": "active",
               "agent_state": "open", "agent_policy_version": 3, "tenant_policy": POLICY}
    with patch("src.agent.preflight.authorization.repository.get_child_lineage", return_value=lineage) as link, \
         patch("src.agent.preflight.authorization.repository.get_current_authorization", return_value=current), \
         patch("src.agent.preflight.authorization.repository.get_active_auth_session", return_value={"session_id": "session"}), \
         patch("src.agent.preflight.authorization.repository.get_active_permission_codes", return_value=["quotation.read"]), \
         patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.repository.get_parent_decision", return_value={
             "tenant_id": "a" * 24, "role_id": "b" * 24, "decision": "allow",
             "details": {"permissions_needed": ["quotation.read"]}, "candidate_tools": [],
         }):
        assert verify_child_scope({"configurable": values}, user_id="u", tenant_id="a" * 24,
                                  role_id="b" * 24) == ["quotation.read"]
        link.return_value = {**lineage, "parent_execution_id": "another-run"}
        with pytest.raises(PermissionError, match="child_lineage_invalid"):
            verify_child_scope({"configurable": values}, user_id="u", tenant_id="a" * 24,
                               role_id="b" * 24)


def test_child_task_cannot_expand_parent_permission_scope():
    identity = {**IDENTITY, "permissions": ["quotation.read", "purchase_order.create"]}
    with patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.resolve_business_intent", return_value=(["purchase_order.create"], "")):
        with pytest.raises(PermissionError, match="child_scope_exceeded"):
            authorize_child_task("create order", ["quotation.read"], identity, {})


def test_child_preflight_inherits_parent_ceiling_even_for_general_task():
    identity = {**IDENTITY, "permissions": ["quotation.read", "purchase_order.create"]}
    with patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.resolve_business_intent", return_value=([], "")):
        result = authorize_request("summarize what you found", identity, {}, parent_scope=["quotation.read"])
    assert result.decision == "allow"
    assert result.required == ("quotation.read",)


def test_child_preflight_denies_ambiguous_task_without_interrupting_parent():
    with patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.resolve_business_intent", return_value=([], "Which action?")):
        result = authorize_request("handle order", IDENTITY, {}, parent_scope=["quotation.read"])
    assert result.decision == "deny"
    assert result.reason_code == "child_intent_ambiguous"


def test_child_execution_rechecks_parent_and_child_policy():
    config = {"configurable": {"owner_id": "u", "agent_id": "child", "child_agent_id": "child",
                              "execution_id": "child-run", "parent_agent_id": "parent",
                              "parent_execution_id": "parent-run", "session_id": "session",
                              "policy_version": 2, "parent_policy_version": 3,
                              "parent_business_permissions": ["quotation.read"]}}
    child_policy = {"armory": {"tools": ["system_info"]}}
    parent_policy = {"armory": {"tools": ["system_info"]}}
    current = {"tenant_id": "a" * 24, "role_id": "b" * 24,
               "membership_status": "active", "tenant_status": "active", "role_status": "active",
               "agent_state": "open", "agent_policy_version": 3,
               "agent_policy": parent_policy, "tenant_policy": POLICY}
    lineage = {"child_agent_id": "child", "parent_agent_id": "parent", "root_user_id": "u",
               "child_agent_state": "open", "parent_agent_state": "open",
               "child_execution_state": "running", "parent_execution_state": "running",
               "parent_execution_id": "parent-run", "child_policy_version": 2,
               "parent_policy_version": 3, "child_policy": child_policy,
               "child_execution_policy_version": 2, "parent_execution_policy_version": 3}
    with patch("src.agent.preflight.authorization.repository.get_child_lineage", return_value=lineage), \
         patch("src.agent.preflight.authorization.repository.get_current_authorization", return_value=current), \
         patch("src.agent.preflight.authorization.repository.get_active_auth_session", return_value={"session_id": "session"}), \
         patch("src.agent.preflight.authorization.repository.get_active_permission_codes", return_value=["quotation.read"]), \
         patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.repository.get_parent_decision", return_value={
             "tenant_id": "a" * 24, "role_id": "b" * 24, "decision": "allow",
             "details": {"permissions_needed": ["quotation.read"]},
             "candidate_tools": [{"type": "tool", "name": "system_info"}],
         }):
        check_resource_execution(user_id="u", agent_id="child", session_id="session",
                                 resource_type="tool", resource_name="system_info", required=["quotation.read"],
                                 tenant_id="a" * 24, role_id="b" * 24, policy_version=2, config=config)
        current["agent_policy"] = {"armory": {"tools": []}}
        with pytest.raises(PermissionError, match="parent_resource_revoked"):
            check_resource_execution(user_id="u", agent_id="child", session_id="session",
                                     resource_type="tool", resource_name="system_info", required=["quotation.read"],
                                     tenant_id="a" * 24, role_id="b" * 24, policy_version=2, config=config)


def test_all_held_mapped_bapis_are_visible_regardless_of_request_intent():
    with patch("src.agent.preflight.authorization.repository.get_bapi_for_resource", return_value={
        "permission_code": "purchase_order.create",
    }):
        assert resource_allowed("tool", "mcp_purchase_order_create", tenant_id="a" * 24,
                                remote_name="BAPI_PO_CREATE", tenant_policy=POLICY,
                                held={"purchase_order.create"}, required=set())
        assert not resource_allowed("tool", "mcp_purchase_order_create", tenant_id="a" * 24,
                                    remote_name="BAPI_PO_CREATE", tenant_policy=POLICY,
                                    held={"quotation.read"})


def test_child_tool_must_be_in_parent_approved_resource_list():
    config = {"configurable": {"owner_id": "u", "agent_id": "child", "child_agent_id": "child",
                              "execution_id": "child-run", "parent_agent_id": "parent",
                              "parent_execution_id": "parent-run", "session_id": "session",
                              "policy_version": 2, "parent_policy_version": 3,
                              "parent_business_permissions": ["quotation.read"]}}
    current = {"tenant_id": "a" * 24, "role_id": "b" * 24,
               "membership_status": "active", "tenant_status": "active", "role_status": "active",
               "agent_state": "open", "agent_policy_version": 3,
               "agent_policy": {"armory": {"tools": ["system_info"]}}, "tenant_policy": POLICY}
    lineage = {"child_agent_id": "child", "parent_agent_id": "parent", "root_user_id": "u",
               "child_agent_state": "open", "parent_agent_state": "open",
               "child_execution_state": "running", "parent_execution_state": "running",
               "parent_execution_id": "parent-run", "child_policy_version": 2,
               "parent_policy_version": 3, "child_policy": {"armory": {"tools": ["system_info"]}},
               "child_execution_policy_version": 2, "parent_execution_policy_version": 3}
    with patch("src.agent.preflight.authorization.repository.get_child_lineage", return_value=lineage), \
         patch("src.agent.preflight.authorization.repository.get_current_authorization", return_value=current), \
         patch("src.agent.preflight.authorization.repository.get_active_auth_session", return_value={"session_id": "session"}), \
         patch("src.agent.preflight.authorization.repository.get_active_permission_codes", return_value=["quotation.read"]), \
         patch("src.agent.preflight.authorization.repository.get_tenant_permission_catalog", return_value=CATALOG), \
         patch("src.agent.preflight.authorization.repository.get_parent_decision", return_value={
             "tenant_id": "a" * 24, "role_id": "b" * 24, "decision": "allow",
             "details": {"permissions_needed": ["quotation.read"]}, "candidate_tools": [],
         }):
        with pytest.raises(PermissionError, match="parent_resource_not_approved"):
            check_resource_execution(user_id="u", agent_id="child", session_id="session",
                                     resource_type="tool", resource_name="system_info", required=["quotation.read"],
                                     tenant_id="a" * 24, role_id="b" * 24, policy_version=2, config=config)


def test_readiness_leaves_tool_arguments_to_mcp_schema():
    tenant_policy = {"permission_domains": {"purchase_order": "procurement"}}
    readiness = evaluate_request_readiness(
        "Create purchase order for laptops",
        ["purchase_order.create"],
        tenant_policy,
    )
    assert readiness.decision == "allow"
    assert readiness.reason_code == "request_ready"
    assert readiness.required_fields == ()


def test_readiness_marks_writes_for_concrete_tool_confirmation():
    tenant_policy = {
        "permission_domains": {"purchase_order": "procurement"},
        "confirm_writes": True,
    }
    readiness = evaluate_request_readiness(
        "vendor: Acme Corp create purchase order",
        ["purchase_order.create"],
        tenant_policy,
    )
    assert readiness.decision == "allow"
    assert readiness.reason_code == "request_ready"
    assert readiness.write_requires_confirmation is True
