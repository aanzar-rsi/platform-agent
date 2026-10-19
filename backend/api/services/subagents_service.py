from __future__ import annotations



from typing import Any



from src.subagents.registry import get_subagents




class SubagentsService:

    def list_catalog(self, uid: str | None = None) -> dict[str, Any]:

        specs = get_subagents(uid)

        subagents = [

            {

                "name": spec.name,

                "display_name": spec.display_name,

                "description": spec.description,

                "when_to_use": spec.when_to_use,

                "scope": spec.scope,

                "availability": spec.availability,

                "tools": list(spec.tools),

                "source": getattr(spec, "source", "builtin"),

                "agent_id": getattr(spec, "agent_id", None),

                "status": getattr(spec, "status", None),

                "enabled": getattr(spec, "enabled", True),

            }

            for spec in specs

        ]

        return {

            "subagents": subagents,

            "counts": {"subagents": len(subagents)},

        }
