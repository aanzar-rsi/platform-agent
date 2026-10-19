"""Uvicorn entrypoint: from client2.0 run  python -m api.main  (workers=1)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# client2.0 root on sys.path so `import api` and `import src` both work
_CLIENT_ROOT = Path(__file__).resolve().parents[1]
if str(_CLIENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_CLIENT_ROOT))

os.environ.setdefault("EVA_SKIP_VENV_REEXEC", "1")

from api.app import create_app
from api.core.config import get_settings

app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    # Hard constraint: process-local packet queues require a single worker
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1,
    )


if __name__ == "__main__":
    run()
