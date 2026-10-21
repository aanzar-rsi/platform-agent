from src.agent.nodes.agentnode import _parse_parameters, _parse_response


def test_parse_parameters_strips_cdata_wrapper_from_steps_json():
    parsed = _parse_parameters("<steps_json><![CDATA[{\"phases\": []}]]></steps_json>")
    assert parsed["steps_json"] == '{"phases": []}'


def test_parse_response_accepts_tool_tag_as_armory_resource_name():
    update = _parse_response(
        """
        <planner_exit>False</planner_exit>
        <action>armory_call</action>
        <data><tool>web_search</tool><parameters><resource_type>tool</resource_type><query>Tokyo weather</query></parameters></data>
        """,
        turn_start=False,
    )
    assert update["next_step"]["resource_type"] == "tool"
    assert update["next_step"]["resource_name"] == "web_search"
    assert update["next_step"]["arguments"] == {"query": "Tokyo weather"}


def test_parse_response_accepts_light_classifier_exit():
    update = _parse_response(
        "<action>exit</action><reasoning>done</reasoning><data>Hello</data>",
        turn_start=False,
    )
    assert update["next_step"] == {"action": "finish", "answer": "Hello"}


def test_parse_response_accepts_planner_exit_action():
    update = _parse_response(
        "<action>planner_exit</action><reasoning>done</reasoning><data>Goodbye</data>",
        turn_start=False,
    )
    assert update["next_step"] == {"action": "finish", "answer": "Goodbye"}


def test_parse_response_accepts_planner_batch_data():
    batch = '{"batch_name":"lookup-1","phases":[]}'
    update = _parse_response(
        f"<action>continue</action><reasoning>lookup needed</reasoning>"
        f"<task>lookup-batch-1</task><data>{batch}</data>",
        turn_start=False,
    )
    assert update["next_step"] == {
        "action": "plan",
        "task": "lookup-batch-1",
        "steps_json": batch,
    }
