from src.agent.nodes.agentnode import _parse_parameters, _parse_response


def test_parse_parameters_strips_cdata_wrapper_from_steps_json():
    parsed = _parse_parameters("<steps_json><![CDATA[{\"phases\": []}]]></steps_json>")
    assert parsed["steps_json"] == '{"phases": []}'


def test_parse_response_accepts_tool_tag_as_tool_name():
    update = _parse_response(
        """
        <planner_exit>False</planner_exit>
        <action>tool_call</action>
        <data><tool>web_search</tool><parameters><query>Tokyo weather</query></parameters></data>
        """,
        turn_start=False,
    )
    assert update["next_step"]["tool_name"] == "web_search"
