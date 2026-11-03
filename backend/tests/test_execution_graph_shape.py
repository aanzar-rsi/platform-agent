from src.agent.graph import agent_app


def _edges():
    return {(edge.source, edge.target) for edge in agent_app.get_graph().edges}


def test_security_and_collection_nodes_have_one_outgoing_edge():
    edges = _edges()
    expected = {
        "input_security_gate": "execution_dispatcher",
        "result_collector": "output_security_gate",
        "output_security_gate": "execution_dispatcher",
        "context_selector": "execution_dispatcher",
    }
    for source, target in expected.items():
        assert {edge_target for edge_source, edge_target in edges if edge_source == source} == {target}


def test_all_new_data_producers_share_the_collector():
    edges = _edges()
    for producer in ("armory_node", "child_agent_node", "collect_child", "human_input"):
        assert (producer, "result_collector") in edges


def test_legacy_hidden_execution_nodes_are_removed():
    nodes = set(agent_app.get_graph().nodes)
    assert "planned_step" not in nodes
    assert "plan_dispatcher" not in nodes
    assert "phase_collector" not in nodes
