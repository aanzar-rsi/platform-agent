from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent.preflight.identity_resolver import resolve_preflight_identity


class TestPreflightIdentityResolver(unittest.TestCase):
    def test_denies_missing_auth_context(self):
        out = resolve_preflight_identity({"configurable": {"owner_id": "", "session_id": ""}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "auth_context_missing")

    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_missing_membership(self, membership):
        membership.return_value = None
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "tenant_membership_missing")

    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_inactive_membership(self, membership):
        membership.return_value = {"tenant_id": "t1", "role_id": "r1", "status": "inactive"}
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "tenant_user_inactive")

    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_missing_tenant_id(self, membership):
        membership.return_value = {"tenant_id": "", "role_id": "r1", "status": "active"}
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "tenant_not_found")

    @patch("src.agent.preflight.repository.get_tenant_record")
    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_missing_tenant_record(self, membership, tenant):
        membership.return_value = {"tenant_id": "t1", "role_id": "r1", "status": "active"}
        tenant.return_value = None
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "tenant_not_found")

    @patch("src.agent.preflight.repository.get_tenant_record")
    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_inactive_tenant(self, membership, tenant):
        membership.return_value = {"tenant_id": "t1", "role_id": "r1", "status": "active"}
        tenant.return_value = {"tenant_id": "t1", "status": "suspended"}
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "tenant_inactive")

    @patch("src.agent.preflight.repository.get_tenant_record")
    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_missing_role_id(self, membership, tenant):
        membership.return_value = {"tenant_id": "t1", "role_id": "", "status": "active"}
        tenant.return_value = {"tenant_id": "t1", "status": "active"}
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "role_missing")

    @patch("src.agent.preflight.repository.get_role_record")
    @patch("src.agent.preflight.repository.get_tenant_record")
    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_missing_role_record(self, membership, tenant, role):
        membership.return_value = {"tenant_id": "t1", "role_id": "r1", "status": "active"}
        tenant.return_value = {"tenant_id": "t1", "status": "active"}
        role.return_value = None
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "role_not_found")

    @patch("src.agent.preflight.repository.get_role_record")
    @patch("src.agent.preflight.repository.get_tenant_record")
    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_inactive_role(self, membership, tenant, role):
        membership.return_value = {"tenant_id": "t1", "role_id": "r1", "status": "active"}
        tenant.return_value = {"tenant_id": "t1", "status": "active"}
        role.return_value = {"role_id": "r1", "tenant_id": "t1", "name": "Analyst", "status": "inactive"}
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "role_inactive")

    @patch("src.agent.preflight.repository.get_active_permission_codes")
    @patch("src.agent.preflight.repository.get_role_record")
    @patch("src.agent.preflight.repository.get_tenant_record")
    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_denies_when_role_has_no_permissions(self, membership, tenant, role, permissions):
        membership.return_value = {"tenant_id": "t1", "role_id": "r1", "status": "active"}
        tenant.return_value = {"tenant_id": "t1", "status": "active"}
        role.return_value = {"role_id": "r1", "tenant_id": "t1", "name": "Analyst", "status": "active"}
        permissions.return_value = []
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "deny")
        self.assertEqual(out.reason_code, "permissions_missing")

    @patch("src.agent.preflight.repository.get_active_permission_codes")
    @patch("src.agent.preflight.repository.get_role_record")
    @patch("src.agent.preflight.repository.get_tenant_record")
    @patch("src.agent.preflight.repository.get_tenant_user_membership")
    def test_allows_active_membership_tenant_role_permissions(self, membership, tenant, role, permissions):
        membership.return_value = {"tenant_id": "t1", "role_id": "r1", "status": "active"}
        tenant.return_value = {"tenant_id": "t1", "status": "active", "policy": {"max_query_chars": 10000}}
        role.return_value = {"role_id": "r1", "tenant_id": "t1", "name": "Analyst", "status": "active"}
        permissions.return_value = ["quotation.read", "quotation.compare"]
        out = resolve_preflight_identity({"configurable": {"owner_id": "u1", "session_id": "s1"}})
        self.assertEqual(out.decision, "allow")
        self.assertEqual(out.reason_code, "identity_resolved")
        self.assertEqual(out.context["tenant_id"], "t1")
        self.assertEqual(out.context["role_id"], "r1")
        self.assertEqual(out.context["permissions"], ["quotation.read", "quotation.compare"])
        self.assertTrue(out.context["tenant_policy_loaded"])
        self.assertIn("max_query_chars", out.context["tenant_policy"])


if __name__ == "__main__":
    unittest.main()
