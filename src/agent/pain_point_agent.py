"""Core LangChain agent implementation for pain point discovery."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from config.settings import settings
from src.agent.orchestrator import build_agent_executor
from src.utils.validators import ValidationError, validate_query_length


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
    result = executor.invoke({"input": normalized_query})
    return _normalize_response(result, input_query=normalized_query)


def _normalize_response(raw_result: Mapping[str, Any], input_query: str = "") -> Dict[str, Any]:
    """Normalize the raw agent output into the project JSON schema."""

    metadata_defaults: Dict[str, Any] = {
        "total_sources_searched": 0,
        "execution_time": 0.0,
        "api_costs": 0.0,
    }
    metadata = raw_result.get("metadata", {}) if isinstance(raw_result, Mapping) else {}
    normalized_metadata: Dict[str, Any] = {**metadata_defaults}
    if isinstance(metadata, Mapping):
        normalized_metadata.update(metadata)

    pain_points = raw_result.get("pain_points", []) if isinstance(raw_result, Mapping) else []
    pain_points = pain_points if isinstance(pain_points, list) else []

    normalized_query = input_query or (raw_result.get("query", "") if isinstance(raw_result, Mapping) else "")
    return {
        "query": normalized_query,
        "pain_points": pain_points,
        "metadata": normalized_metadata,
    }


def stream_agent(query: str) -> List[Any]:
    """Stream the agent's intermediate messages for interactive UIs."""

    executor = create_agent()
    return list(executor.stream({"input": query}))


def _validate_query(query: str) -> str:
    """Ensure query is a non-empty string within expected length bounds."""

    if not isinstance(query, str):
        raise ValidationError("Query must be a string.")

    normalized = query.strip()
    if not normalized:
        raise ValidationError("Query cannot be empty.")

    validate_query_length(normalized, min_words=1, max_words=50)
    return normalized
