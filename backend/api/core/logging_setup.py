from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    trace_logger = logging.getLogger("agent.trace")
    trace_logger.handlers = [handler for handler in trace_logger.handlers
                             if not isinstance(handler, logging.NullHandler)]
    trace_logger.propagate = True
    trace_logger.setLevel(logging.INFO)

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
