"""Core LangChain agent implementation for pain point discovery."""

from __future__ import annotations

from typing import Any, Dict, List

from langchain.agents import AgentExecutor
from langchain.schema import BaseMessage

from config.settings import settings
from src.agent.orchestrator import build_agent_executor


def create_agent() -> AgentExecutor:
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

    executor = create_agent()
    result = executor.invoke({"input": query})
    return _normalize_response(result)


def _normalize_response(raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize the raw agent output into the project JSON schema."""

    return {
        "query": raw_result.get("query", ""),
        "pain_points": raw_result.get("pain_points", []),
        "metadata": raw_result.get(
            "metadata",
            {
                "total_sources_searched": 0,
                "execution_time": 0.0,
                "api_costs": 0.0,
            },
        ),
    }


def stream_agent(query: str) -> List[BaseMessage]:
    """Stream the agent's intermediate messages for interactive UIs."""

    executor = create_agent()
    return list(executor.stream({"input": query}))
