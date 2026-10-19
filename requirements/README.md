# Requirements Implementation Order

Use this order for reliable delivery:

1. `01_AGENTCORE_REQUIREMENTS.md`
2. `02_TRACE_SCHEMA.md`
3. `03_MEMORY_PHASE_1_REQUIREMENTS.md`
4. `04_MEMORY_PHASE_2_GOVERNANCE_REQUIREMENTS.md`

Rationale:
- AgentCore contracts and lifecycle come first.
- Tracing comes next so all later work is observable.
- Memory Phase 1 adds the usable memory model and retrieval path.
- Memory Phase 2 adds governance, promotion approvals, and advanced controls.

`99_MEMORY_FULL_DRAFT_REFERENCE.md` is background and the ChromaDB KB design/migration plan. Where older examples in that reference conflict, the numbered requirements above take precedence.

## Other requirement artifacts

- `db_requirements.md` — database-specific requirement notes.
- `notes/` — migrated implementation/migration summaries and quick references.
