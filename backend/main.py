#!/usr/bin/env python3
"""Boot the agent.

Usage (from the v2 project root):
    python main.py          # start the API server
    python main.py --cli    # start the interactive agent CLI
"""

from __future__ import annotations

import sys


def main() -> None:
    if "--cli" in sys.argv[1:]:
        from src.agent.graph import run_cli

        run_cli()
    else:
        from api.main import run

        run()


if __name__ == "__main__":
    main()
