"""CLI theme - one place for every terminal color/style used by the CLI.

Keys are semantic (what a piece of text *means*) rather than literal
colors, so the look of the whole CLI can be tuned from a single dict.
"""

THEME = {
    # Roles
    "user.prompt": "bold cyan",
    "assistant": "none",
    "assistant.title": "bold bright_cyan",

    # Agent internals
    "thinking": "dim italic gray62",
    "status": "dim",
    "tool.call": "bold bright_blue",
    "tool.args": "dim",
    "tool.ok": "green",
    "tool.fail": "red",
    "subagent": "bold magenta",
    "context": "dim yellow",

    # Decoration & feedback
    "rule": "dim",
    "muted": "dim",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    "banner": "bold cyan",
}

# Keys that must always be present (guards against accidental deletions).
REQUIRED_THEME_KEYS = frozenset(
    {
        "user.prompt",
        "assistant",
        "assistant.title",
        "thinking",
        "status",
        "tool.call",
        "tool.args",
        "tool.ok",
        "tool.fail",
        "subagent",
        "context",
        "rule",
        "muted",
        "warning",
        "error",
        "info",
        "banner",
    }
)