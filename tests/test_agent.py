"""Tests for agent orchestration."""

from __future__ import annotations

import pytest

from src.agent import pain_point_agent


def test_normalize_response_structure() -> None:
    """Ensure the normalization helper returns the expected keys."""

    raw = {
        "query": "test",
        "pain_points": [],
        "metadata": {"total_sources_searched": 0, "execution_time": 0.0, "api_costs": 0.0},
    }
    normalized = pain_point_agent._normalize_response(raw)  # pylint: disable=protected-access
    assert set(normalized.keys()) == {"query", "pain_points", "metadata"}


@pytest.mark.skip(reason="Requires LangChain agent configuration")
def test_run_agent_placeholder() -> None:
    """Placeholder test for future agent execution."""

    assert pain_point_agent
