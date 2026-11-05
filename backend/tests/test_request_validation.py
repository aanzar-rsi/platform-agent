from api.core.request_validation import (
    RequestValidationError,
    build_request_id,
    validate_run_start_payload,
)


def test_validate_run_start_payload_defaults_query_type_to_chat():
    req = validate_run_start_payload(
        {"query": "  hello  "},
        request_id="",
        uid="u1",
        session_id="s1",
    )
    assert req.query == "hello"
    assert req.query_type == "chat"
    assert len(req.request_id) == 24
    assert all(c in "0123456789abcdef" for c in req.request_id)


def test_validate_run_start_payload_rejects_unsupported_query_type():
    try:
        validate_run_start_payload(
            {"query": "hello", "query_type": "search"},
            request_id="65f0a1b2c3d4e5f607182901",
            uid="u1",
            session_id="s1",
        )
    except RequestValidationError as exc:
        assert exc.payload.code == "query_type_invalid"
    else:
        raise AssertionError("expected RequestValidationError")


def test_validate_run_start_payload_rejects_oversized_query():
    too_large = "a" * 11
    try:
        validate_run_start_payload(
            {"query": too_large},
            request_id="65f0a1b2c3d4e5f607182901",
            uid="u1",
            session_id="s1",
            max_query_chars=10,
        )
    except RequestValidationError as exc:
        assert exc.payload.code == "query_too_large"
        assert exc.payload.status == 413
    else:
        raise AssertionError("expected RequestValidationError")


def test_validate_run_start_payload_rejects_missing_auth_context():
    try:
        validate_run_start_payload(
            {"query": "hello"},
            request_id="65f0a1b2c3d4e5f607182901",
            uid="u1",
            session_id=None,
        )
    except RequestValidationError as exc:
        assert exc.payload.code == "auth_context_missing"
        assert exc.payload.status == 401
    else:
        raise AssertionError("expected RequestValidationError")


def test_build_request_id_generates_object_id_when_invalid():
    raw = "not-an-object-id"
    rid = build_request_id(raw)
    assert len(rid) == 24
    assert all(c in "0123456789abcdef" for c in rid)


def test_validate_run_start_payload_rejects_invalid_object_id_request_id():
    try:
        validate_run_start_payload(
            {"query": "hello"},
            request_id="req_1",
            uid="u1",
            session_id="s1",
        )
    except RequestValidationError as exc:
        assert exc.payload.code == "request_id_invalid"
        assert exc.payload.status == 422
    else:
        raise AssertionError("expected RequestValidationError")


def test_validate_run_start_payload_rejects_non_string_query():
    try:
        validate_run_start_payload(
            {"query": {"text": "hello"}},
            request_id="65f0a1b2c3d4e5f607182901",
            uid="u1",
            session_id="s1",
        )
    except RequestValidationError as exc:
        assert exc.payload.code == "query_invalid"
    else:
        raise AssertionError("expected RequestValidationError")
