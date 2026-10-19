"""
Internal tool for web search.

Primary provider : Brave Search API  (set BRAVE_SEARCH_API_KEY in .env)
Fallback provider: DuckDuckGo web search via ddgs library (no key required, full results)
"""

import os
from typing import Dict, Any, List, Literal, TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import tool

if TYPE_CHECKING:
    from ddgs import DDGS as DDGSClass


def _import_requests():
    try:
        import requests
        return requests
    except ImportError:
        return None


def _import_ddgs() -> "DDGSClass | None":
    try:
        from ddgs import DDGS
        return DDGS
    except ImportError:
        return None

_BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
_DEFAULT_TIMEOUT = 15


def _brave_search(query: str, count: int, country: str, search_lang: str) -> Dict[str, Any]:
    requests = _import_requests()
    if requests is None:
        return {"success": False, "provider": "brave", "error": "requests library is not installed. Run: pip install requests", "results": []}

    api_key = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()
    if not api_key:
        return {"success": False, "provider": "brave", "error": "BRAVE_SEARCH_API_KEY is not set.", "results": []}

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": count,
        "country": country,
        "search_lang": search_lang,
        "text_decorations": False,
        "spellcheck": True,
    }

    try:
        resp = requests.get(_BRAVE_ENDPOINT, headers=headers, params=params, timeout=_DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        return {"success": False, "provider": "brave", "error": f"HTTP {resp.status_code}: {resp.text[:300]}", "results": []}
    except requests.exceptions.Timeout:
        return {"success": False, "provider": "brave", "error": "Request timed out.", "results": []}
    except Exception as e:
        return {"success": False, "provider": "brave", "error": str(e), "results": []}

    web_results = data.get("web", {}).get("results", [])
    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "description": r.get("description", ""),
            "age": r.get("age"),
        }
        for r in web_results
    ]

    return {
        "success": True,
        "provider": "brave",
        "query": query,
        "total_results": len(results),
        "results": results,
        "error": None,
    }


def _ddg_search(query: str, count: int) -> Dict[str, Any]:
    """DuckDuckGo web search via ddgs library — no key required, full search results."""
    DDGS = _import_ddgs()
    if DDGS is None:
        return {
            "success": False,
            "provider": "duckduckgo",
            "error": "ddgs library is not installed. Run: pip install ddgs",
            "results": [],
        }

    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=count))
        
        if not search_results:
            return {
                "success": False,
                "provider": "duckduckgo",
                "query": query,
                "error": "No results returned for this query.",
                "results": [],
            }
        
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "description": r.get("body", ""),
                "source": "DuckDuckGo",
            }
            for r in search_results
        ]

        return {
            "success": True,
            "provider": "duckduckgo",
            "query": query,
            "total_results": len(results),
            "results": results,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "provider": "duckduckgo",
            "error": f"DuckDuckGo search failed: {str(e)}",
            "results": [],
        }


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class WebSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=400, description="The search query.")
    count: int = Field(10, ge=1, le=20, description="Number of results to return (1–20).")
    country: str = Field("us", description="2-letter country code for result localisation (e.g. 'us', 'gb', 'in').")
    search_lang: str = Field("en", description="Language code for results (e.g. 'en', 'fr', 'de').")
    provider: Literal["auto", "brave", "duckduckgo"] = Field(
        "auto",
        description=(
            "'auto' uses Brave if BRAVE_SEARCH_API_KEY is set, otherwise DuckDuckGo. "
            "'brave' forces Brave (requires API key). "
            "'duckduckgo' forces the free DuckDuckGo web search (no API key required)."
        ),
    )

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        if len(v) != 2 or not v.isalpha():
            raise ValueError("country must be a 2-letter ISO country code (e.g. 'us', 'gb').")
        return v.lower()

    @field_validator("search_lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 5 or not v.replace("-", "").isalpha():
            raise ValueError("search_lang must be a valid language code (e.g. 'en', 'fr', 'zh-cn').")
        return v.lower()


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

@tool("web_search", args_schema=WebSearchArgs)
def web_search(
    query: str,
    count: int = 10,
    country: str = "us",
    search_lang: str = "en",
    provider: str = "auto",
) -> Dict[str, Any]:
    """Search the web and return a list of results with titles, URLs, and descriptions.

    Uses Brave Search (set BRAVE_SEARCH_API_KEY in .env) for full web search results.
    Falls back to DuckDuckGo web search (via ddgs library) when no API key is configured —
    provides full web search results without requiring any API keys.
    """
    has_brave_key = bool(os.environ.get("BRAVE_SEARCH_API_KEY", "").strip())

    if provider == "auto":
        provider = "brave" if has_brave_key else "duckduckgo"

    if provider == "brave":
        return _brave_search(query, count, country, search_lang)

    return _ddg_search(query, count)


if __name__ == "__main__":
    import json
    result = web_search.invoke({"query": "latest advancements in AI agents", "count": 5})
    print(json.dumps(result, indent=2))
