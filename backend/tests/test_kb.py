"""Memory authorization, post-index revalidation, and governance gates."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.agent import kb


U1, U2 = str(uuid.uuid4()), str(uuid.uuid4())
POLICY = {"read": ["USER", "TENANT", "AGENT"], "write": ["USER"], "tenant_id": "acme"}


def publisher_policy(*, allow_admin_promotion: bool = True) -> dict:
    return {
        "read": ["USER", "AGENT"], "write": ["USER", "AGENT"],
        "promote": ["AGENT"], "publish": ["AGENT"],
        "allow_admin_promotion": allow_admin_promotion,
        "chunks": {"workflow": {
            "enabled": True, "read": ["USER", "AGENT"], "write": ["USER", "AGENT"],
            "promote": ["AGENT"], "allow_admin_promotion": allow_admin_promotion,
        }},
    }


@pytest.fixture(autouse=True)
def _reset_chroma_flag():
    kb._chroma_failed = False
    yield
    kb._chroma_failed = False


class Cursor:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class Conn:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def transaction(self):
        return self

    def execute(self, sql, params=()):
        self.queries.append((sql, params))
        return Cursor(self.rows.get(params[0], []) if params else [])


class Collection:
    def __init__(self):
        self.metadata = {"embedding_model": kb._model(), "embedding_dimensions": 2}
        self.calls = []

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return {"ids": [["v_good", "v_other", "v_old", "v_revoked"]],
                "distances": [[0.1, 0.1, 0.1, 0.1]]}


def row(uid=U1, *, scope="USER", tenant=None, version="v_good", status="ACTIVE"):
    return {"chunk_id": "chk_one", "chunk_type": "workflow", "scope": scope,
            "owner_user_id": uid if scope == "USER" else None, "tenant_id": tenant,
            "status": status, "version_status": status, "active_version_id": version,
            "version_id": version, "content": "helpful", "memory_weight": 0.5,
            "expires_at": None, "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc), "metadata": {}}


def test_search_prefilters_then_revalidates_authority():
    collection = Collection()
    conn = Conn({"v_good": [row()], "v_other": [row(U2)],
                 "v_old": [row(version="v_new")], "v_revoked": [row(version="v_revoked", status="REVOKED")]})
    with patch.object(kb, "_collection", return_value=collection), patch.object(kb, "_vector", return_value=[1., 0.]), \
         patch.object(kb, "get_connection", return_value=conn):
        hits = kb.search(U1, {"read": ["USER"]}, "query")
    assert [hit["active_version_id"] for hit in hits] == ["v_good"]
    assert collection.calls[0]["where"] == {"$and": [
        {"owner_user_id": U1}, {"chunk_type": {"$in": sorted(kb.TYPES)}},
    ]}


def test_no_tenant_means_no_tenant_query():
    collection = Collection()
    with patch.object(kb, "_collection", return_value=collection), patch.object(kb, "_vector", return_value=[1., 0.]):
        assert kb.search(U1, {"read": ["TENANT"], "tenant_id": None}, "query") == []
    assert not collection.calls


def test_tenant_query_uses_trusted_policy_filter():
    collection = Collection()
    conn = Conn({"v_good": [row(scope="TENANT", tenant="acme")],
                 "v_other": [row(scope="TENANT", tenant="other")]})
    with patch.object(kb, "_collection", return_value=collection), patch.object(kb, "_vector", return_value=[1., 0.]), \
         patch.object(kb, "get_connection", return_value=conn):
        hits = kb.search(U1, {"read": ["TENANT"], "tenant_id": "acme"}, "query")
    assert [hit["active_version_id"] for hit in hits] == ["v_good"]
    assert collection.calls[0]["where"] == {"$and": [
        {"tenant_id": "acme"}, {"chunk_type": {"$in": sorted(kb.TYPES)}},
    ]}


def test_search_returns_empty_when_chroma_unavailable():
    kb._chroma_failed = False
    with patch.object(kb, "_collection", side_effect=RuntimeError("chroma down")), \
         patch.object(kb, "_vector", return_value=[1.0, 0.0]):
        assert kb.search(U1, {"read": ["USER"]}, "query") == []
    assert kb._chroma_failed


def test_sync_index_skips_when_chroma_unavailable():
    kb._chroma_failed = False
    with patch.object(kb, "_collection", side_effect=RuntimeError("chroma down")):
        assert kb.sync_index() == 0
    assert kb._chroma_failed


def test_scope_validation_and_visibility():
    with pytest.raises(PermissionError):
        kb._authorized(U1, {"write": ["AGENT"]}, "AGENT", "write")
    with pytest.raises(PermissionError):
        kb._authorized(U1, {"read": ["TENANT"], "tenant_id": None}, "TENANT", "read")
    with pytest.raises(PermissionError):
        kb._authorized("forged", POLICY, "USER", "read")
    assert not kb._visible(row(U2), U1, POLICY)
    assert not kb._visible(row(scope="TENANT", tenant="other"), U1, POLICY)
    assert kb._visible(row(scope="TENANT", tenant="acme"), U1, POLICY)


def test_governance_admin_and_sanitization():
    request = {"request_id": "pr_1", "state": "APPROVAL_PENDING", "requested_by": U1,
               "source_chunk_id": "chk_one", "source_version_id": "v_good", "to_scope": "AGENT",
               "proposed_content": "Contact admin@example.com", "target_tenant_id": None}
    conn = Conn({"pr_1": [request], "chk_one": [dict(row(), sensitivity="INTERNAL")]})
    with pytest.raises(PermissionError, match="admin_required"):
        kb.review_promotion(U2, "user", "pr_1", approve=True, policy=POLICY)
    with patch.object(kb, "get_connection", return_value=conn), patch.object(kb, "_row", return_value=dict(row(), sensitivity="INTERNAL")):
        with pytest.raises(ValueError, match="generalization_required"):
            kb.review_promotion(U2, "admin", "pr_1", approve=True,
                                policy=publisher_policy())
        with pytest.raises(ValueError, match="generalization_required"):
            kb.review_promotion(U1, "admin", "pr_1", approve=True,
                                policy=publisher_policy())


def test_publication_requires_chunk_admin_promotion_permission():
    assert kb._publication_allowed(publisher_policy(), chunk_type="workflow", target_scope="AGENT")
    assert not kb._publication_allowed(
        publisher_policy(allow_admin_promotion=False), chunk_type="workflow", target_scope="AGENT"
    )


@pytest.mark.parametrize("private_content", [
    "customer_id=acme-123",
    "tenant_name=Acme",
    "host=db.internal",
    "database=customer_prod",
])
def test_agent_publication_privacy_patterns(private_content):
    assert kb._PRIVATE.search(private_content)


def test_expiry_requires_known_retention_class():
    with pytest.raises(ValueError, match="invalid_retention_class"):
        kb.set_expiry(U1, "admin", "chk_one", publisher_policy(), None,
                      retention_class="FOREVER")


def test_promoted_target_visibility_and_revocation():
    target = row(scope="AGENT", version="v_target")
    assert kb._visible(target, U2, {"read": ["AGENT"]})
    assert not kb._visible({**target, "status": "REVOKED"}, U2, {"read": ["AGENT"]})
    assert not kb._visible(target, U2, {"read": ["USER"]})


def test_postgres_chroma_roundtrip():
    """Use rollback-only database writes and an ephemeral in-memory Chroma index."""
    import chromadb

    from api.db.postgres import get_connection

    with get_connection() as real:
        users = real.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 2").fetchall()
    if len(users) < 2:
        pytest.skip("two existing users required for KB integration")
    owner, other = (str(r["user_id"]) for r in users)
    client = chromadb.EphemeralClient()
    collections = {scope: client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
                   for scope, name in kb.COLLECTIONS.items()}
    policy = {"read": ["USER", "AGENT"], "write": ["USER"], "tenant_id": None}
    # A single connection holds the transaction so no test rows survive the check.
    with get_connection() as conn:
        with patch.object(kb, "get_connection", return_value=type("Lease", (), {
            "__enter__": lambda self: conn, "__exit__": lambda self, *_: None})()), \
             patch.object(kb, "_collection", side_effect=lambda scope: collections[scope]), \
             patch.object(kb, "_vector", side_effect=lambda text: [1., 0.] if 'alpha' in text else [0., 1.]), \
             patch.object(kb, "_model", return_value="test-2"):
            with conn.transaction(force_rollback=True):
                created = kb.write(owner, policy, "alpha procedure", search_text="alpha")
                assert len(kb.search(owner, policy, "alpha")) == 1
                assert kb.search(other, policy, "alpha") == []
                newer = kb.write(owner, policy, "alpha revised", chunk_id=created["chunk_id"])
                history = kb.history(owner, policy, created["chunk_id"])
                assert len(history["versions"]) == 2
                assert history["active_version_index"] == 1
                assert kb.search(owner, policy, "alpha")[0]["active_version_id"] == newer["active_version_id"]
                assert kb.search(other, policy, "alpha") == []


def test_admin_promotion_roundtrip():
    """A different admin activates one generalized target; retries keep the same target."""
    import chromadb

    from api.db.postgres import get_connection

    with get_connection() as real:
        users = real.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 2").fetchall()
    if len(users) < 2:
        pytest.skip("two existing users required")
    owner, admin = (str(r["user_id"]) for r in users)
    client = chromadb.EphemeralClient()
    collections = {scope: client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
                   for scope, name in kb.COLLECTIONS.items()}
    policy = {"read": ["USER", "AGENT"], "write": ["USER"], "tenant_id": None}
    publisher = publisher_policy()
    with get_connection() as conn:
        with patch.object(kb, "get_connection", return_value=type("Lease", (), {
            "__enter__": lambda self: conn, "__exit__": lambda self, *_: None})()), \
             patch.object(kb, "_collection", side_effect=lambda scope: collections[scope]), \
             patch.object(kb, "_vector", return_value=[1., 0.]), patch.object(kb, "_model", return_value="test-2"):
            with conn.transaction(force_rollback=True):
                source = kb.write(owner, policy, "private customer procedure")
                request = kb.request_promotion(owner, policy, source["chunk_id"], "AGENT",
                    idempotency_key=str(uuid.uuid4()), proposed_content="Reusable operational procedure")
                assert request["state"] == "APPROVAL_PENDING"
                result = kb.review_promotion(admin, "admin", request["request_id"], approve=True, policy=publisher)
                again = kb.review_promotion(admin, "admin", request["request_id"], approve=True, policy=publisher)
                assert again["target_chunk_id"] == result["target_chunk_id"]
                assert [x["chunk_id"] for x in kb.search(admin, publisher, "procedure") if x["scope"] == "AGENT"] == [result["target_chunk_id"]]
                expiry = kb.set_expiry(admin, "admin", result["target_chunk_id"], publisher, None,
                                       retention_class="STANDARD")
                assert expiry["retention_class"] == "STANDARD"
                kb.revoke(admin, "admin", result["target_chunk_id"], publisher)
                assert all(x["chunk_id"] != result["target_chunk_id"] for x in kb.search(admin, publisher, "procedure"))
                assert kb.history(owner, policy, source["chunk_id"])["status"] == "ACTIVE"

                private_source = kb.write(owner, policy, "customer-specific database procedure")
                private_request = kb.request_promotion(
                    owner, policy, private_source["chunk_id"], "AGENT",
                    idempotency_key=str(uuid.uuid4()), proposed_content="database=customer_prod",
                )
                with pytest.raises(ValueError, match="generalization_required"):
                    kb.review_promotion(admin, "admin", private_request["request_id"], approve=True,
                                        policy=publisher)
                assert kb.promotion_detail(admin, "admin", private_request["request_id"])["state"] == "PROMOTION_FAILED"
                assert kb.history(owner, policy, private_source["chunk_id"])["status"] == "ACTIVE"
