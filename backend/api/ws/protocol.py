"""WebSocket protocol helpers."""

from __future__ import annotations

# Client → server
CLIENT_RUN_START = "run.start"
CLIENT_RUN_STOP = "run.stop"
CLIENT_RUN_ROLLBACK = "run.rollback"
CLIENT_RUN_PAUSE = "run.pause"
CLIENT_RUN_RESUME = "run.resume"
CLIENT_PING = "ping"

# Server → client
SESSION_READY = "session.ready"
RUN_STARTED = "run.started"
RUN_COMPLETED = "run.completed"
RUN_ERROR = "run.error"
RUN_INTERRUPTED = "run.interrupted"
NODE_STARTED = "node.started"
NODE_FINISHED = "node.finished"
LLM_TOKEN = "llm.token"
LLM_CACHE_HIT = "llm.cache_hit"
LLM_DONE = "llm.done"
TOOL_STARTED = "tool.started"
TOOL_FINISHED = "tool.finished"
SUBAGENT_STARTED = "subagent.started"
SUBAGENT_STEP = "subagent.step"
SUBAGENT_FINISHED = "subagent.finished"
CHILD_STARTED = "child.started"
CHILD_STEP = "child.step"
CHILD_FINISHED = "child.finished"
CHECKPOINT_CREATED = "checkpoint.created"
PONG = "pong"
ERROR = "error"
