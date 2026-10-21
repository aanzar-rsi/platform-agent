import os
import sys

# Allow running directly or as a module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import Dict
from src.models.llm_client import call_llm, count_tokens


# (input_limit, output_limit) in tokens
_MODEL_LIMITS: Dict[str, tuple] = {

    ## AWS Bedrock Models
    # Claude models
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0": (200_000, 64_000),
    "us.anthropic.claude-opus-4-1-20250805-v1:0":   (200_000, 32_000),
    "us.anthropic.claude-sonnet-4-20250514-v1:0":   (200_000, 64_000),
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0": (200_000, 64_000),
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": (200_000,  8_192),
    "anthropic.claude-3-haiku-20240307-v1:0":        (200_000,  4_096),
    # Meta Llama models
    "us.meta.llama4-maverick-17b-instruct-v1:0": (1_000_000, 8_192),
    "us.meta.llama4-scout-17b-instruct-v1:0":   (10_000_000, 8_192),
    # Qwen models
    "qwen.qwen3-32b-v1:0":           (128_000, 8_192),
    "qwen.qwen3-coder-30b-a3b-v1:0": (128_000, 8_192),
    # OpenAI models (via Bedrock)
    "openai.gpt-oss-20b-1:0":  (128_000, 16_384),
    "openai.gpt-oss-120b-1:0": (128_000, 16_384),
    # Amazon Nova models
    "amazon.nova-pro-v1:0": (300_000, 5_120),

    ## LITELLM gateway models
    "gpt-5.3-codex": (128_000, 16_384),
    "gpt-6-sol": (128_000, 16_384),
    "gpt-5.6-terra": (128_000, 16_384),
    "gpt-5-nano": (128_000, 16_384),
    "gpt-5.6-sol": (128_000, 16_384),
    "gpt-5.6-luna": (128_000, 16_384),
    "gpt-6-astra": (128_000, 16_384),
    "gpt-6-luna": (128_000, 16_384),
}

_SUMMARISE_SYSTEM_PROMPT = "You are a concise summariser. Summarise the given text clearly and briefly."


def _get_limits(model_id: str) -> tuple:
    """Return (input_limit, output_limit) for a model, falling back to safe defaults."""
    return _MODEL_LIMITS.get(model_id, (128_000, 8_192))


def _context_stats(token_count: int, limit: int) -> Dict:
    remaining = max(0, limit - token_count)
    percent_used = round(min(100.0, (token_count / limit) * 100), 2)
    return {
        "tokens_used": token_count,
        "token_limit": limit,
        "tokens_remaining": remaining,
        "percent_used": percent_used,
        "percent_remaining": round(100.0 - percent_used, 2),
        "is_near_limit": percent_used >= 80.0,
        "is_over_limit": token_count > limit,
    }


def summarise(text: str, model_id: str = "gpt-4o") -> str:
    """Summarise the given text using the LLM."""
    return call_llm(text, system_prompt=_SUMMARISE_SYSTEM_PROMPT, model_id=model_id)


def input_context_checker(prompt: str, model_id: str) -> Dict:
    """Check how much of a model's input context window the prompt consumes.

    Returns token counts, limit, remaining capacity, and fill percentage.
    """
    input_limit, _ = _get_limits(model_id)
    token_count = count_tokens(prompt)["input"]
    return {"model": model_id, "window": "input", **_context_stats(token_count, input_limit)}


def output_context_checker(output: str, model_id: str) -> Dict:
    """Check how much of a model's output context window a response consumes.

    Returns token counts, limit, remaining capacity, and fill percentage.
    """
    _, output_limit = _get_limits(model_id)
    token_count = count_tokens("", output)["output"]
    return {"model": model_id, "window": "output", **_context_stats(token_count, output_limit)}


if __name__ == "__main__":
    model = "gpt-4o"
    sample = "The quick brown fox jumps over the lazy dog. " * 100

    print("Input check:", input_context_checker(sample, model))
    print("Output check:", output_context_checker(sample, model))
    print("Summary:", summarise(sample, model))