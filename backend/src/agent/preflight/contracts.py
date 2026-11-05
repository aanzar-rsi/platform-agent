"""Typed contracts shared by governed Preflight context stages."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class GovernedMemoryReference:
    """Identify one governed memory version without exposing its content."""

    chunk_id: str
    version_id: str
    scope: str
    provenance: str = "episodic_memory"


@dataclass(frozen=True)
class GovernedContextItem:
    """Represent planner-safe context with explicit trust and provenance."""

    reference_id: str
    kind: str
    content: Any
    source: dict[str, Any]
    sensitivity: str
    provenance: str
    trust: str = "assumption"
    confirmed: bool = False
    score: float | None = None
    complete: bool = True

    def as_dict(self) -> dict[str, Any]:
        """Serialize a governed context item for graph state."""

        return asdict(self)


@dataclass(frozen=True)
class GovernedContextResult:
    """Return the governed context package and its Preflight decision."""

    decision: str
    reason_code: str
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    items: tuple[GovernedContextItem, ...] = ()
    memory_references: tuple[GovernedMemoryReference, ...] = ()
    reduced: bool = False
    degradations: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def planner_context(self, *, maximum_sensitivity: str | None = None) -> dict[str, Any]:
        """Build the planner-safe context section without raw audit metadata."""

        context = {
            "items": [item.as_dict() for item in self.items],
            "memory_references": [asdict(reference) for reference in self.memory_references],
            "reduced": self.reduced,
            "degradations": list(self.degradations),
        }
        if maximum_sensitivity:
            context["maximum_sensitivity"] = maximum_sensitivity
        return context
