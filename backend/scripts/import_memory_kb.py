"""Opt-in backfill of owner-provenanced legacy learner chunks into the KB.

Run from backend/: .venv/bin/python scripts/import_memory_kb.py --uid <user-uuid> --dry-run
"""

from __future__ import annotations

import argparse
import json

from api.db.repositories.users import UserRepository
from src.agent import kb
from src.agent.agent_core import default_policy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uid", required=True, help="Verified owner UUID; imports only this user's records")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not UserRepository().get_by_uid(args.uid):
        parser.error("Unknown user")
    print(json.dumps(kb.import_legacy(args.uid, default_policy().memory, dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
