from api.app import create_app


def test_armory_agent_route_contract():
    paths = create_app().openapi()["paths"]
    routes = {(method.upper(), path) for path, operations in paths.items() for method in operations}

    expected = {
        ("GET", "/v1/armory"),
        ("GET", "/v1/armory/tools"),
        ("GET", "/v1/armory/mcp"),
        ("GET", "/v1/armory/subagents"),
        ("GET", "/v1/agents"),
        ("POST", "/v1/agents"),
        ("GET", "/v1/agents/{agent_id}"),
        ("GET", "/v1/agents/{agent_id}/armory"),
        ("GET", "/v1/agents/{agent_id}/armory/tools"),
        ("GET", "/v1/agents/{agent_id}/armory/mcp"),
        ("GET", "/v1/agents/{agent_id}/armory/subagents"),
        ("GET", "/v1/agents/{agent_id}/memory"),
        ("GET", "/v1/agents/{agent_id}/analytics"),
        ("GET", "/v1/analytics"),
        ("GET", "/v1/memory"),
        ("GET", "/v1/health"),
        ("GET", "/v1/live"),
    }
    assert expected <= routes

    retired_prefixes = ("/v1/chats", "/v1/tools", "/v1/mcp", "/v1/subagents")
    assert not any(path.startswith(retired_prefixes) for _, path in routes)
