"""Lightweight guard against reintroducing retired frontend chat/WS contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "frontend/src/lib/api.ts").read_text(encoding="utf-8")
WS = (ROOT / "frontend/src/lib/websocket.ts").read_text(encoding="utf-8")


def main() -> None:
    for retired in ("'/chats", "`/chats", "'/tools'", "'/mcp/servers", "'/subagents'", "/subagents/studio"):
        assert retired not in API, retired
    for current in ("'/agents'", "'/armory/tools'", "'/armory/mcp'", "'/armory/subagents'"):
        assert current in API, current
    for message in ("run.start", "run.stop", "run.resume", "session.ready", "llm.token"):
        assert message in WS, message
    for retired in ("client.query", "client.stop_generation"):
        assert retired not in WS, retired
    chat_view = (ROOT / "frontend/src/components/EnhancedChatView.tsx").read_text(
        encoding="utf-8"
    )
    interrupt_prompt = (ROOT / "frontend/src/components/InterruptPrompt.tsx").read_text(
        encoding="utf-8"
    )
    assert 'kind === "question"' in interrupt_prompt
    assert "<InterruptPrompt" in chat_view
    assert "resumeRun(value)" in chat_view
    print("PASS frontend/backend contract checks")


if __name__ == "__main__":
    main()
