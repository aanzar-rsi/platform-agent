"""
Tool for decomposing a user query into a structured, multi-dimensional breakdown.
"""

import sys
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

try:
    from src.models.llm_client import call_llm
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.models.llm_client import call_llm


_SYSTEM_PROMPT = """You are a query analyst. Your job is to decompose a user query into a rich, structured breakdown that gives an AI agent full situational awareness before it acts.

Return ONLY valid JSON matching this exact schema:

{
  "original_query": "<the query as given>",
  "intent": "<the core goal — what the user actually wants to achieve>",
  "sub_tasks": ["<discrete step 1>", "<discrete step 2>", ...],
  "assumptions": ["<what you are assuming is true>", ...],
  "ambiguities": ["<what is unclear or could be interpreted multiple ways>", ...],
  "constraints": ["<implicit or explicit limits — time, format, scope, etc.>", ...],
  "context_needed": ["<what background info would help answer this better>", ...],
  "output_format": "<what kind of output the user likely expects — e.g. a list, a report, code, a number>",
  "complexity": "<low | medium | high>",
  "suggested_approach": "<a short description of the best strategy to fulfil this query>"
}

Be specific. Avoid generic filler. If the query is short, infer reasonable context from it."""


class DecomposeQueryArgs(BaseModel):
    query: str = Field(..., min_length=1, description="The user query to decompose.")
    extra_context: Optional[List[str]] = Field(
        None,
        description="Optional list of context strings about the user or situation (e.g. role, data source, prior steps).",
    )


@tool("decompose_query", args_schema=DecomposeQueryArgs)
def decompose_query(query: str, extra_context: Optional[List[str]] = None) -> Dict[str, Any]:
    """Decompose a user query into a structured multi-dimensional breakdown.

    Produces intent, sub-tasks, assumptions, ambiguities, constraints, required
    context, expected output format, complexity level, and a suggested approach.
    Use this before planning or executing complex requests to build full situational
    awareness of what the user actually needs.
    """
    prompt = f"Query: {query}"
    if extra_context:
        joined = "\n".join(f"- {item}" for item in extra_context)
        prompt += f"\n\nExtra context:\n{joined}"

    try:
        result = call_llm(prompt, system_prompt=_SYSTEM_PROMPT, temperature=0.3, output_type="json")
    except Exception as e:
        return {"success": False, "error": f"LLM call failed: {e}", "decomposition": None}

    if not isinstance(result, dict):
        return {"success": False, "error": "LLM returned unexpected output format.", "decomposition": None}

    return {"success": True, "error": None, "decomposition": result}


if __name__ == "__main__":
    import json
    result = decompose_query.invoke({
        "query": "Summarise last quarter's sales performance and flag any anomalies",
        "extra_context": ["The user is a finance analyst.", "Working with CRM data exports."]
    })
    print(json.dumps(result, indent=2))