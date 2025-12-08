"""Core LangChain agent implementation for pain point discovery."""

from __future__ import annotations

import time
from time import perf_counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from config.settings import settings
from src.agent.orchestrator import build_agent_executor
from src.utils.validators import ValidationError, validate_query_length

_MAX_RETRY_ATTEMPTS = 3
_INITIAL_BACKOFF_SECONDS = 1.0
_BACKOFF_MULTIPLIER = 2.0


def create_agent() -> Any:
    """Instantiate and return the configured LangChain agent executor."""

    return build_agent_executor(settings)


def run_agent(query: str) -> Dict[str, Any]:
    """Execute the agent for the provided query and return structured results.

    Args:
        query: Natural language question describing the customer pain points to
            investigate.

    Returns:
        A dictionary payload matching the defined JSON schema.
    """

    normalized_query = _validate_query(query)
    executor = create_agent()

    backoff = _INITIAL_BACKOFF_SECONDS
    start_time = perf_counter()
    result: Mapping[str, Any] | Dict[str, Any] | None = None
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRY_ATTEMPTS):
        try:
            result = executor.invoke({"input": normalized_query})
            break
        except ValidationError:
            raise
        except Exception as exc:
            last_error = exc
            if attempt < _MAX_RETRY_ATTEMPTS - 1:
                time.sleep(backoff)
                backoff *= _BACKOFF_MULTIPLIER
    duration_seconds = perf_counter() - start_time

    tools_used: Sequence[str] = []
    if hasattr(executor, "get_used_tools"):
        tools_used = getattr(executor, "get_used_tools")()

    if result is None and last_error is not None:
        return _normalize_response(
            {},
            input_query=normalized_query,
            duration_seconds=duration_seconds,
            tools_used=tools_used,
            error=_build_error_payload(last_error),
        )

    assert result is not None  # for type checkers
    return _normalize_response(result, input_query=normalized_query, duration_seconds=duration_seconds, tools_used=tools_used)


def _normalize_response(
    raw_result: Mapping[str, Any],
    input_query: str = "",
    duration_seconds: float | None = None,
    tools_used: Sequence[str] | None = None,
    error: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Normalize the raw agent output into the project JSON schema."""

    metadata_defaults: Dict[str, Any] = {
        "total_sources_searched": 0,
        "api_costs": 0.0,
        "tools_used": list(tools_used or []),
    }
    metadata = raw_result.get("metadata", {}) if isinstance(raw_result, Mapping) else {}
    normalized_metadata: Dict[str, Any] = {**metadata_defaults}
    if isinstance(metadata, Mapping):
        normalized_metadata.update(metadata)

    normalized_metadata["execution_time"] = duration_seconds if duration_seconds is not None else float(
        normalized_metadata.get("execution_time", 0.0)
    )

    tools: List[str] = []
    seen_tools: set[str] = set()
    for name in list(tools_used or []) + list(normalized_metadata.get("tools_used") or []):
        if not isinstance(name, str):
            continue
        cleaned = name.strip()
        if not cleaned:
            continue
        lower = cleaned.lower()
        if lower in seen_tools:
            continue
        seen_tools.add(lower)
        tools.append(lower)
    normalized_metadata["tools_used"] = tools

    pain_points = raw_result.get("pain_points", []) if isinstance(raw_result, Mapping) else []
    pain_points = pain_points if isinstance(pain_points, list) else []

    normalized_error: Dict[str, Any] | None = None
    if error:
        remediation = error.get("remediation", []) if isinstance(error, Mapping) else []
        remediation_list = [tip for tip in remediation if isinstance(tip, str) and tip.strip()]
        normalized_error = {
            "message": str(error.get("message", "Unexpected error occurred.")),
            "type": str(error.get("type", "")),
            "remediation": remediation_list or _default_remediation(),
        }

    normalized_query = input_query or (raw_result.get("query", "") if isinstance(raw_result, Mapping) else "")
    response: Dict[str, Any] = {
        "query": normalized_query,
        "pain_points": pain_points,
        "output": raw_result.get("output") if isinstance(raw_result, Mapping) else None,
        "metadata": normalized_metadata,
    }
    if normalized_error:
        response["error"] = normalized_error
    return response


def stream_agent(query: str) -> Iterable[Any]:
    """Stream the agent's intermediate messages for interactive UIs."""

    normalized_query = _validate_query(query)
    executor = create_agent()

    start_time = perf_counter()
    try:
        for event in executor.stream({"input": normalized_query}):
            yield event
        duration = perf_counter() - start_time
        tools_used: Sequence[str] = []
        if hasattr(executor, "get_used_tools"):
            tools_used = getattr(executor, "get_used_tools")()
        summary = _normalize_response({}, input_query=normalized_query, duration_seconds=duration, tools_used=tools_used)
        yield {"event": "complete", "metadata": summary["metadata"], "query": normalized_query}
    except ValidationError:
        raise
    except Exception as exc:
        duration = perf_counter() - start_time
        tools_used = getattr(executor, "get_used_tools")() if hasattr(executor, "get_used_tools") else []
        summary = _normalize_response({}, input_query=normalized_query, duration_seconds=duration, tools_used=tools_used)
        yield {
            "event": "error",
            "query": normalized_query,
            "error": _build_error_payload(exc),
            "metadata": summary["metadata"],
        }


def _validate_query(query: str) -> str:
    """Ensure query is a non-empty string within expected length bounds."""

    if not isinstance(query, str):
        raise ValidationError("Query must be a string.")

    normalized = query.strip()
    if not normalized:
        raise ValidationError("Query cannot be empty.")

    validate_query_length(normalized, min_words=1, max_words=50)
    return normalized


def _build_error_payload(error: Exception) -> Dict[str, Any]:
    """Construct a structured error payload with remediation suggestions."""

    return {
        "message": str(error),
        "type": error.__class__.__name__,
        "remediation": _default_remediation(),
    }


def _default_remediation() -> List[str]:
    """Default remediation tips for agent failures."""

    return [
        "Rephrase the query to be between 1 and 50 words (3-10 words recommended for best results) and try again.",
        "Verify API credentials and rate limits for connected data sources.",
        "Wait a moment and retry in case of transient service issues.",
    ]
