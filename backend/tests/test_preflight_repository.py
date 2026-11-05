from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent.preflight.repository import (
    count_recent_tenant_requests_per_minute,
    count_recent_user_requests_per_minute,
    get_active_auth_session,
    get_active_permission_codes,
    get_tenant_permission_catalog,
    get_child_lineage,
    get_parent_decision,
    get_open_conversation_activity,
    get_role_record,
    get_tenant_record,
)


class TestPreflightRepository(unittest.TestCase):
    @patch("src.agent.preflight.repository._fetch_one")
    def test_child_lineage_joins_parent_execution_and_root_user(self, fetch_one):
        get_child_lineage("child", "child-run")
        sql, params = fetch_one.call_args.args
        self.assertIn("parent_run.execution_id = child_run.parent_execution_id", sql)
        self.assertIn("parent_run.agent_id = parent.agent_id", sql)
        self.assertEqual(params, ("child", "child-run"))

    @patch("src.agent.preflight.repository._fetch_one")
    def test_parent_decision_is_scoped_to_execution_agent_and_user(self, fetch_one):
        get_parent_decision("run", "agent", "user")
        sql, params = fetch_one.call_args.args
        self.assertIn("execution_id = %s AND agent_id = %s AND user_id = %s", sql)
        self.assertEqual(params, ("run", "agent", "user"))

    @patch("src.agent.preflight.repository._fetch_all")
    def test_tenant_catalog_includes_descriptions_and_rejects_conflicts(self, fetch_all):
        fetch_all.return_value = [
            {"permission_code": "quotation.read", "description": "View quotations", "description_count": 1},
        ]
        self.assertEqual(get_tenant_permission_catalog("t1"), [
            {"code": "quotation.read", "description": "View quotations"},
        ])
        sql, params = fetch_all.call_args.args
        self.assertIn("p.tenant_id = %s", sql)
        self.assertIn("p.status = 'active'", sql)
        self.assertEqual(params, ("t1",))

    @patch("src.agent.preflight.repository._fetch_one")
    def test_get_role_record_filters_by_role_and_tenant(self, fetch_one):
        fetch_one.return_value = {"role_id": "r1", "tenant_id": "t1", "name": "Analyst", "status": "active"}
        row = get_role_record("r1", "t1")
        self.assertEqual(row["role_id"], "r1")
        sql, params = fetch_one.call_args.args
        self.assertIn("WHERE role_id = %s", sql)
        self.assertIn("AND tenant_id = %s", sql)
        self.assertEqual(params, ("r1", "t1"))

    @patch("src.agent.preflight.repository._fetch_all")
    def test_get_active_permission_codes_normalizes_and_deduplicates(self, fetch_all):
        fetch_all.return_value = [
            {"permission_code": " quotation.read "},
            {"permission_code": "quotation.compare"},
            {"permission_code": "quotation.read"},
            {"permission_code": ""},
            {},
        ]
        out = get_active_permission_codes("r1")
        self.assertEqual(out, ["quotation.compare", "quotation.read"])
        sql, params = fetch_all.call_args.args
        self.assertIn("AS role_grant(permission_id)", sql)
        self.assertIn("%s::text IS NULL", sql)
        self.assertIn("status = 'active'", sql)
        self.assertEqual(params, ("r1", None, None))

    @patch("src.agent.preflight.repository._fetch_one")
    def test_get_tenant_record_includes_policy(self, fetch_one):
        fetch_one.return_value = {"tenant_id": "t1", "status": "active", "policy": {"max_query_chars": 9999}}
        row = get_tenant_record("t1")
        self.assertEqual(row["tenant_id"], "t1")
        sql, params = fetch_one.call_args.args
        self.assertIn("policy", sql)
        self.assertEqual(params, ("t1",))

    @patch("src.agent.preflight.repository._fetch_one")
    def test_get_active_auth_session_filters_revoked_and_expired(self, fetch_one):
        fetch_one.return_value = {"session_id": "s1", "user_id": "u1"}
        row = get_active_auth_session("s1", "u1")
        self.assertEqual(row["session_id"], "s1")
        sql, params = fetch_one.call_args.args
        self.assertIn("revoked_at IS NULL", sql)
        self.assertIn("expires_at > now()", sql)
        self.assertEqual(params, ("s1", "u1"))

    @patch("src.agent.preflight.repository._fetch_one")
    def test_get_open_conversation_activity_filters_open_owner(self, fetch_one):
        fetch_one.return_value = {"last_activity_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00"}
        row = get_open_conversation_activity("a1", "u1")
        self.assertTrue("last_activity_at" in row)
        sql, params = fetch_one.call_args.args
        self.assertIn("state = 'open'", sql)
        self.assertEqual(params, ("a1", "u1"))

    @patch("src.agent.preflight.repository._fetch_one")
    def test_count_recent_user_requests_per_minute(self, fetch_one):
        fetch_one.return_value = {"request_count": 7}
        count = count_recent_user_requests_per_minute("u1")
        self.assertEqual(count, 7)
        sql, params = fetch_one.call_args.args
        self.assertIn("agent_executions", sql)
        self.assertIn("interval '1 minute'", sql)
        self.assertEqual(params, ("u1",))

    @patch("src.agent.preflight.repository._fetch_one")
    def test_count_recent_tenant_requests_per_minute(self, fetch_one):
        fetch_one.return_value = {"request_count": 11}
        count = count_recent_tenant_requests_per_minute("t1")
        self.assertEqual(count, 11)
        sql, params = fetch_one.call_args.args
        self.assertIn("tenant_users", sql)
        self.assertIn("interval '1 minute'", sql)
        self.assertEqual(params, ("t1",))


if __name__ == "__main__":
    unittest.main()
