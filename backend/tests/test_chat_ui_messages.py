from langchain_core.messages import AIMessage, HumanMessage

from api.services.chat_service import _ui_messages


def test_internal_run_messages_are_folded_into_final_assistant_message():
    messages = [
        HumanMessage(content="Weather today?"),
        AIMessage(
            content="Need a location",
            additional_kwargs={
                "ui_hidden": True,
                "ui_step": {"type": "reasoning", "content": "Need a location"},
            },
        ),
        HumanMessage(
            content="Hyderabad, India",
            additional_kwargs={
                "ui_hidden": True,
                "ui_step": {"type": "reasoning", "content": "User response: Hyderabad, India"},
            },
        ),
        AIMessage(
            content="Tool result",
            additional_kwargs={
                "ui_hidden": True,
                "ui_step": {"type": "tool", "tool": {"tool_name": "web_search"}},
            },
        ),
        AIMessage(content="It is 31 C and partly cloudy."),
    ]

    visible = _ui_messages(messages, [])

    assert [(message["role"], message["content"]) for message in visible] == [
        ("user", "Weather today?"),
        ("assistant", "It is 31 C and partly cloudy."),
    ]
    assert visible[1]["metadata"]["steps"] == [
        {"type": "reasoning", "content": "Need a location"},
        {"type": "reasoning", "content": "User response: Hyderabad, India"},
        {"type": "tool", "tool": {"tool_name": "web_search"}},
    ]
