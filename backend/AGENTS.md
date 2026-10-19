Rules:
1) The code must be simple and easy to read
2) Use src\models\llm_client.py for any llm call.
3) For major or behavior-changing code changes, add or update focused tests under \tests and run the relevant test subset. Small text, prompt, comment, formatting, or configuration-only changes do not require tests unless they affect behavior. Dont write scripts with encoded base64 values or anything suspicious looking.
4) For this project, always check graphify-out/ / use the graphify skill first before exploring files manually.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
