import json
from collections import OrderedDict
import logging
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Generator, Iterable, Optional, Union

from openai import OpenAI

from src.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = settings.llm_model_id

# Reused across calls (module-level singleton) so every LLM call doesn't
# re-pay client construction overhead.
_client_lock = threading.Lock()
_client: Optional[OpenAI] = None

# Size of the slices a cached response is replayed in under MOCK_LLM_CALL,
# kept small so reasoning blocks flush progressively as on a live call.
_REPLAY_CHUNK_CHARS = 24
_RECENT_CACHE_MAX = 512
_recent_cache_lock = threading.Lock()
_recent_cache: "OrderedDict[str, Dict[str, str]]" = OrderedDict()


def _gateway_client() -> OpenAI:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = OpenAI(base_url=settings.llm_gateway_url, api_key=settings.llm_gateway_api_key)
    return _client


def count_tokens(input_text: str, output_text: str = "") -> Dict[str, int]:
    """Estimate token counts for input and output text (~4 chars per token)."""

    def _count(text: str) -> int:
        return max(1, len(text) // 4) if text else 0

    input_tokens = _count(input_text)
    output_tokens = _count(output_text)
    return {
        "input": input_tokens,
        "output": output_tokens,
        "total": input_tokens + output_tokens,
    }


def _parse_json_response(text: str) -> Any:
    """Parse a JSON response, tolerating a ```json ... ``` code fence wrapper."""
    raw = (text or "").strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw)
    if fence:
        raw = fence.group(1)
    return json.loads(raw)


def _build_messages(prompt: str, system_prompt: Optional[str]) -> list[dict]:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return messages


def _apply_output_type_instruction(system_prompt: Optional[str], output_type: str) -> Optional[str]:
    if output_type == "markup":
        markup_instr = "Always respond in valid Markup format with proper tags"
        return f"{system_prompt}\n\n{markup_instr}" if system_prompt else markup_instr
    if output_type == "json":
        json_instr = (
            "Respond ONLY with valid, raw JSON. "
            "Do not include markup codeblocks like ```json ... ``` or any pre-text/post-text."
        )
        return f"{system_prompt}\n\n{json_instr}" if system_prompt else json_instr
    return system_prompt


def _dump(obj: Any) -> Dict[str, Any]:
    """Best-effort dict from an OpenAI SDK model (or anything dict-like)."""
    for attr in ("model_dump", "dict"):
        method = getattr(obj, attr, None)
        if callable(method):
            try:
                return method()
            except Exception:
                pass
    if isinstance(obj, dict):
        return obj
    return {}


def _estimated_usage(system_prompt: Optional[str], prompt: str, response_text: str) -> Dict[str, Any]:
    counts = count_tokens((system_prompt or "") + "\n" + (prompt or ""), response_text or "")
    return {
        "prompt_tokens": counts["input"],
        "completion_tokens": counts["output"],
        "total_tokens": counts["total"],
    }


def _headers_dict(raw: Any) -> Dict[str, str]:
    try:
        return {str(k).lower(): str(v) for k, v in dict(raw.headers).items()}
    except Exception:
        return {}


def _extract_cost(headers: Dict[str, str]) -> Optional[float]:
    value = headers.get("x-litellm-response-cost")
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _usage_of(obj: Any) -> Optional[Dict[str, Any]]:
    usage = getattr(obj, "usage", None)
    if usage is None:
        return None
    dumped = _dump(usage)
    return dumped or None


@dataclass
class ProviderSyncResult:
    content: str
    usage: Optional[Dict[str, Any]]
    cost_usd: Optional[float]
    provider_model: Optional[str]
    response_headers: Dict[str, Any]
    raw_response: Dict[str, Any]


@dataclass
class ProviderStreamResult:
    stream: Iterable[Any]
    response_headers: Dict[str, Any]


class BaseLLMProvider:
    name = "base"

    def complete(self, *, model_id: str, temperature: float, messages: list[dict]) -> ProviderSyncResult:
        raise NotImplementedError

    def open_stream(self, *, model_id: str, temperature: float, messages: list[dict]) -> ProviderStreamResult:
        raise NotImplementedError

    def stream_chunk_usage(self, chunk: Any) -> Optional[Dict[str, Any]]:
        return None

    def stream_chunk_text(self, chunk: Any) -> Optional[str]:
        return None

    def stream_provider_model(self, headers: Dict[str, Any]) -> Optional[str]:
        return None


class LiteLLMProvider(BaseLLMProvider):
    name = "litellm"

    @staticmethod
    def _is_temperature_unsupported(exc: Exception) -> bool:
        msg = str(exc).lower()
        return "temperature" in msg and (
            "unsupported value" in msg
            or "does not support" in msg
            or "only the default (1)" in msg
        )

    def _create_with_temperature_fallback(
        self,
        create,
        *,
        model_id: str,
        temperature: float,
        messages: list[dict],
        **extra_kwargs: Any,
    ):
        kwargs: Dict[str, Any] = {
            "model": model_id,
            "temperature": temperature,
            "messages": messages,
            **extra_kwargs,
        }
        try:
            return create(**kwargs)
        except Exception as exc:
            if not self._is_temperature_unsupported(exc):
                raise
            logger.info(
                "Model %s rejected temperature=%s; retrying with provider default temperature",
                model_id,
                temperature,
            )
            kwargs.pop("temperature", None)
            return create(**kwargs)

    def complete(self, *, model_id: str, temperature: float, messages: list[dict]) -> ProviderSyncResult:
        raw = self._create_with_temperature_fallback(
            _gateway_client().chat.completions.with_raw_response.create,
            model_id=model_id,
            temperature=temperature,
            messages=messages,
        )
        headers = _headers_dict(raw)
        response = raw.parse()
        content = response.choices[0].message.content or ""
        return ProviderSyncResult(
            content=content,
            usage=_usage_of(response),
            cost_usd=_extract_cost(headers),
            provider_model=getattr(response, "model", None),
            response_headers=headers,
            raw_response=_dump(response),
        )

    def open_stream(self, *, model_id: str, temperature: float, messages: list[dict]) -> ProviderStreamResult:
        create = _gateway_client().chat.completions.with_raw_response.create
        try:
            raw = self._create_with_temperature_fallback(
                create,
                model_id=model_id,
                temperature=temperature,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True},
            )
        except Exception as exc:
            if "stream_options" not in str(exc):
                raise
            raw = self._create_with_temperature_fallback(
                create,
                model_id=model_id,
                temperature=temperature,
                messages=messages,
                stream=True,
            )
        return ProviderStreamResult(stream=raw.parse(), response_headers=_headers_dict(raw))

    def stream_chunk_usage(self, chunk: Any) -> Optional[Dict[str, Any]]:
        return _usage_of(chunk)

    def stream_chunk_text(self, chunk: Any) -> Optional[str]:
        return chunk.choices[0].delta.content if chunk.choices else None

    def stream_provider_model(self, headers: Dict[str, Any]) -> Optional[str]:
        return headers.get("x-litellm-model-id")


def _provider_registry() -> Dict[str, BaseLLMProvider]:
    return {
        "litellm": LiteLLMProvider(),
    }


def _provider_name() -> str:
    return str(getattr(settings, "llm_provider", "litellm") or "litellm").strip().lower()


def _build_provider() -> BaseLLMProvider:
    name = _provider_name()
    provider = _provider_registry().get(name)
    if provider:
        return provider
    return _provider_registry()["litellm"]


def _log_llm_request(
    *,
    prompt: str,
    system_prompt: Optional[str],
    model_id: str,
    temperature: float,
    mode: str,
    output_type: Optional[str] = None,
) -> None:
    try:
        from src.utils.agent_logger import log_llm_request

        log_llm_request(
            mode=mode,
            model_id=model_id,
            temperature=temperature,
            output_type=output_type,
            system_prompt=system_prompt or "",
            prompt=prompt or "",
            tokens=count_tokens(
                (system_prompt or "") + "\n" + (prompt or ""),
            ),
        )
    except Exception:
        pass


def _log_llm_response(
    *,
    prompt: str,
    system_prompt: Optional[str],
    model_id: str,
    response_text: str,
    mode: str,
    output_type: Optional[str] = None,
    summary: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        from src.utils.agent_logger import log_llm_response

        log_llm_response(
            mode=mode,
            model_id=model_id,
            output_type=output_type,
            response=response_text,
            tokens=count_tokens(
                (system_prompt or "") + "\n" + (prompt or ""),
                response_text or "",
            ),
            **(summary or {}),
        )
    except Exception:
        pass


def _emit_cache_hit_event(
    *,
    mode: str,
    model_id: str,
    output_type: Optional[str],
    source_call_id: str,
    cache_key: str,
) -> None:
    try:
        from src.agent.token_stream import emit_cache_hit

        emit_cache_hit(
            {
                "mode": mode,
                "model_id": model_id,
                "output_type": output_type,
                "source_call_id": source_call_id,
                "cache_key": cache_key,
            }
        )
    except Exception:
        pass


def _emit_lifecycle(event: str, *, call_id: str, mode: str, model_id: str,
                    output_type: Optional[str] = None, **extra: Any) -> None:
    try:
        from src.agent.token_stream import emit_lifecycle
        from src.utils.trace import current_ids

        source = {key: value for key, value in current_ids().items()
                  if key in {"agent_id", "child_agent_id", "execution_id"} and value}
        emit_lifecycle(event, {
            "call_id": call_id,
            "mode": mode,
            "model_id": model_id,
            "output_type": output_type,
            **source,
            **extra,
        })
    except Exception:
        pass


def _cache_key(
    *, model_id: str, system_prompt: Optional[str], prompt: str, output_type: Optional[str], temperature: float
) -> str:
    try:
        from src.utils.llm_logger import build_cache_key

        return build_cache_key(
            model_id=model_id,
            system_prompt=system_prompt,
            prompt=prompt,
            output_type=output_type,
            temperature=temperature,
        )
    except Exception:
        return ""


def _record(**kwargs: Any) -> None:
    try:
        from src.utils.llm_logger import build_record, record_llm_call

        record_llm_call(build_record(**kwargs))
    except Exception:
        pass


def _new_call_id() -> str:
    try:
        from src.utils.llm_logger import new_call_id

        return new_call_id()
    except Exception:
        import uuid

        return str(uuid.uuid4())


def _replay(
    *,
    cache_key: str,
    mode: str,
    model_id: str,
    system_prompt: Optional[str],
    prompt: str,
    output_type: Optional[str],
    temperature: float,
    call_id: str,
) -> Optional[str]:
    if not settings.mock_llm_call or not cache_key:
        return None
    with _recent_cache_lock:
        local = _recent_cache.get(cache_key)
        if local and local.get("response_text") is not None:
            _recent_cache.move_to_end(cache_key)
            hit = {
                "call_id": local.get("call_id", ""),
                "response_text": local["response_text"],
                "model_id": local.get("model_id") or model_id,
            }
        else:
            hit = None
    if not hit:
        try:
            from src.utils.llm_logger import lookup_cached_response

            hit = lookup_cached_response(cache_key)
        except Exception:
            return None
    try:
        if hit and hit.get("response_text") is not None:
            with _recent_cache_lock:
                _recent_cache[cache_key] = {
                    "call_id": str(hit.get("call_id") or ""),
                    "response_text": str(hit["response_text"]),
                    "model_id": str(hit.get("model_id") or model_id),
                }
                _recent_cache.move_to_end(cache_key)
                while len(_recent_cache) > _RECENT_CACHE_MAX:
                    _recent_cache.popitem(last=False)
    except Exception:
        pass
    if not hit:
        return None

    response_text = hit["response_text"]
    try:
        from src.utils.agent_logger import log_event

        log_event(
            "llm.cache_hit",
            mode=mode,
            model_id=model_id,
            output_type=output_type,
            source_call_id=hit["call_id"],
            cache_key=cache_key,
        )
    except Exception:
        pass
    _emit_cache_hit_event(
        mode=mode,
        model_id=model_id,
        output_type=output_type,
        source_call_id=hit["call_id"],
        cache_key=cache_key,
    )
    logger.info(
        "LLM cache hit: mode=%s model=%s source_call_id=%s",
        mode,
        model_id,
        hit["call_id"],
    )

    _record(
        call_id=call_id,
        mode=mode,
        model_id=model_id,
        output_type=output_type,
        temperature=temperature,
        cache_key=cache_key,
        system_prompt=system_prompt,
        prompt=prompt,
        response_text=response_text,
        usage={},
        cost_usd=0.0,
        cached=True,
        source_call_id=hit["call_id"],
        latency_ms=0,
    )
    return response_text


def _remember_cache_seed(*, cache_key: str, call_id: str, model_id: str, response_text: str) -> None:
    if not cache_key or not response_text:
        return
    with _recent_cache_lock:
        _recent_cache[cache_key] = {
            "call_id": call_id,
            "response_text": response_text,
            "model_id": model_id,
        }
        _recent_cache.move_to_end(cache_key)
        while len(_recent_cache) > _RECENT_CACHE_MAX:
            _recent_cache.popitem(last=False)


def _replay_chunks(text: str) -> Generator[str, None, None]:
    for i in range(0, len(text), _REPLAY_CHUNK_CHARS):
        yield text[i : i + _REPLAY_CHUNK_CHARS]


class LLMClient:
    def __init__(self, *, provider: Optional[BaseLLMProvider] = None, default_model: str = DEFAULT_MODEL) -> None:
        self.provider = provider or _build_provider()
        self.default_model = default_model

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_type: str = "text",
        model_id: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Union[str, Dict[str, Any]]:
        model = model_id or self.default_model
        call_id = _new_call_id()
        effective_system_prompt = _apply_output_type_instruction(system_prompt, output_type)

        cache_key = _cache_key(
            model_id=model,
            system_prompt=effective_system_prompt,
            prompt=prompt,
            output_type=output_type,
            temperature=temperature,
        )

        _log_llm_request(
            prompt=prompt,
            system_prompt=effective_system_prompt,
            model_id=model,
            temperature=temperature,
            mode="sync",
            output_type=output_type,
        )
        _emit_lifecycle("llm.started", call_id=call_id, mode="sync", model_id=model,
                        output_type=output_type)

        started = time.monotonic()

        try:
            replayed = _replay(
                cache_key=cache_key,
                mode="sync",
                model_id=model,
                system_prompt=effective_system_prompt,
                prompt=prompt,
                output_type=output_type,
                temperature=temperature,
                call_id=call_id,
            )
            if replayed is not None:
                parsed = _parse_json_response(replayed) if output_type == "json" else replayed
                _emit_lifecycle("llm.done", call_id=call_id, mode="sync", model_id=model,
                                output_type=output_type, cached=True, latency_ms=0)
                return parsed

            messages = _build_messages(prompt, effective_system_prompt)
            result = self.provider.complete(model_id=model, temperature=temperature, messages=messages)
            latency_ms = int((time.monotonic() - started) * 1000)

            usage = result.usage
            usage_estimated = usage is None
            if usage_estimated:
                usage = _estimated_usage(effective_system_prompt, prompt, result.content)

            parsed = _parse_json_response(result.content) if output_type == "json" else result.content

            _record(
                call_id=call_id,
                mode="sync",
                model_id=model,
                output_type=output_type,
                temperature=temperature,
                cache_key=cache_key,
                system_prompt=effective_system_prompt,
                prompt=prompt,
                response_text=result.content,
                usage=usage,
                usage_estimated=usage_estimated,
                cost_usd=result.cost_usd,
                provider_model=result.provider_model,
                response_headers=result.response_headers,
                raw_response=result.raw_response,
                latency_ms=latency_ms,
            )
            _remember_cache_seed(
                cache_key=cache_key,
                call_id=call_id,
                model_id=model,
                response_text=result.content,
            )

            _log_llm_response(
                prompt=prompt,
                system_prompt=effective_system_prompt,
                model_id=model,
                response_text=str(parsed) if output_type == "json" else result.content,
                mode="sync",
                output_type=output_type,
                summary={
                    "call_id": call_id,
                    "usage": usage,
                    "usage_estimated": usage_estimated,
                    "cost_usd": result.cost_usd,
                    "latency_ms": latency_ms,
                    "provider": self.provider.name,
                },
            )
            _emit_lifecycle("llm.done", call_id=call_id, mode="sync", model_id=model,
                            output_type=output_type, latency_ms=latency_ms)
            return parsed
        except Exception as exc:
            _record(
                call_id=call_id,
                mode="sync",
                model_id=model,
                output_type=output_type,
                temperature=temperature,
                cache_key=cache_key,
                system_prompt=effective_system_prompt,
                prompt=prompt,
                status="error",
                error=str(exc),
                latency_ms=int((time.monotonic() - started) * 1000),
            )
            try:
                from src.utils.agent_logger import log_event

                log_event("llm.error", mode="sync", model_id=model, message=str(exc), call_id=call_id)
            except Exception:
                pass
            _emit_lifecycle("llm.error", call_id=call_id, mode="sync", model_id=model,
                            output_type=output_type, message=str(exc),
                            latency_ms=int((time.monotonic() - started) * 1000))
            raise

    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        model = model_id or self.default_model
        call_id = _new_call_id()
        cache_key = _cache_key(
            model_id=model,
            system_prompt=system_prompt,
            prompt=prompt,
            output_type=None,
            temperature=temperature,
        )

        _log_llm_request(
            prompt=prompt,
            system_prompt=system_prompt,
            model_id=model,
            temperature=temperature,
            mode="stream",
        )
        _emit_lifecycle("llm.started", call_id=call_id, mode="stream", model_id=model)

        started = time.monotonic()

        buffer_parts: list[str] = []
        stream_usage: Optional[Dict[str, Any]] = None
        try:
            replayed = _replay(
                cache_key=cache_key,
                mode="stream",
                model_id=model,
                system_prompt=system_prompt,
                prompt=prompt,
                output_type=None,
                temperature=temperature,
                call_id=call_id,
            )
            if replayed is not None:
                yield from _replay_chunks(replayed)
                _emit_lifecycle("llm.done", call_id=call_id, mode="stream", model_id=model,
                                cached=True, latency_ms=0)
                return

            messages = _build_messages(prompt, system_prompt)
            opened = self.provider.open_stream(model_id=model, temperature=temperature, messages=messages)
            headers = opened.response_headers
            for chunk in opened.stream:
                chunk_usage = self.provider.stream_chunk_usage(chunk)
                if chunk_usage:
                    stream_usage = chunk_usage
                delta = self.provider.stream_chunk_text(chunk)
                if delta:
                    buffer_parts.append(delta)
                    yield delta

            content = "".join(buffer_parts)
            latency_ms = int((time.monotonic() - started) * 1000)
            usage_estimated = stream_usage is None
            usage = stream_usage or _estimated_usage(system_prompt, prompt, content)
            cost_usd = _extract_cost(headers)

            try:
                from src.agent.token_stream import emit_usage

                emit_usage(
                    {
                        **usage,
                        "usage_estimated": usage_estimated,
                        "model_id": model,
                        "latency_ms": latency_ms,
                        "cost_usd": cost_usd,
                    }
                )
            except Exception:
                pass

            _record(
                call_id=call_id,
                mode="stream",
                model_id=model,
                output_type=None,
                temperature=temperature,
                cache_key=cache_key,
                system_prompt=system_prompt,
                prompt=prompt,
                response_text=content,
                usage=usage,
                usage_estimated=usage_estimated,
                cost_usd=cost_usd,
                provider_model=self.provider.stream_provider_model(headers),
                response_headers=headers,
                latency_ms=latency_ms,
            )
            _remember_cache_seed(
                cache_key=cache_key,
                call_id=call_id,
                model_id=model,
                response_text=content,
            )

            _log_llm_response(
                prompt=prompt,
                system_prompt=system_prompt,
                model_id=model,
                response_text=content,
                mode="stream",
                summary={
                    "call_id": call_id,
                    "usage": usage,
                    "usage_estimated": usage_estimated,
                    "cost_usd": cost_usd,
                    "latency_ms": latency_ms,
                    "provider": self.provider.name,
                },
            )
            _emit_lifecycle("llm.done", call_id=call_id, mode="stream", model_id=model,
                            latency_ms=latency_ms)
        except Exception as exc:
            partial = "".join(buffer_parts)
            _record(
                call_id=call_id,
                mode="stream",
                model_id=model,
                output_type=None,
                temperature=temperature,
                cache_key=cache_key,
                system_prompt=system_prompt,
                prompt=prompt,
                response_text=partial,
                status="error",
                error=str(exc),
                latency_ms=int((time.monotonic() - started) * 1000),
            )
            try:
                from src.utils.agent_logger import log_event

                log_event(
                    "llm.error",
                    mode="stream",
                    model_id=model,
                    message=str(exc),
                    partial_response=partial,
                    call_id=call_id,
                )
            except Exception:
                pass
            _emit_lifecycle("llm.error", call_id=call_id, mode="stream", model_id=model,
                            message=str(exc), partial_response=partial,
                            latency_ms=int((time.monotonic() - started) * 1000))
            raise


_default_client = LLMClient()


def call_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    output_type: str = "text",
    model_id: str = DEFAULT_MODEL,
    temperature: float = 0.7,
) -> Union[str, Dict[str, Any]]:
    return _default_client.call(
        prompt,
        system_prompt=system_prompt,
        output_type=output_type,
        model_id=model_id,
        temperature=temperature,
    )


def call_llm_stream(
    prompt: str,
    system_prompt: Optional[str] = None,
    model_id: str = DEFAULT_MODEL,
    temperature: float = 0.7,
) -> Generator[str, None, None]:
    return _default_client.stream(
        prompt,
        system_prompt=system_prompt,
        model_id=model_id,
        temperature=temperature,
    )
