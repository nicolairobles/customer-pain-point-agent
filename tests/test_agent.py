"""Tests for agent orchestration."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from config.settings import AgentSettings, Settings
from src.agent import orchestrator, pain_point_agent


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


def _install_fake_langchain(monkeypatch: pytest.MonkeyPatch, call_log: dict[str, Any]) -> None:
    """Inject minimal LangChain stubs into sys.modules for orchestrator."""

    fake_langchain = types.SimpleNamespace(__version__="0.0.test")

    class FakeReactAgent:
        def __init__(self, llm=None, tools=None, prompt=None):
            self.tools = tools or []
            self.llm = llm
            self.prompt = prompt

        def invoke(self, payload: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
            call_log["invoke_config"] = config
            return {
                "tools": [getattr(t, "name", "<anon>") for t in self.tools],
                "llm_type": getattr(self.llm, "_llm_type", "unknown"),
                "payload": payload,
                "recursion_limit": (config or {}).get("recursion_limit"),
            }

        def stream(self, payload: dict[str, Any], config: dict[str, Any] | None = None):
            call_log["stream_config"] = config
            yield {"event": "start", "payload": payload}
            yield {"event": "end"}

    def fake_create_react_agent(llm=None, tools=None, prompt=None):
        call_log.update({"tools": tools, "llm": llm, "prompt": prompt})
        return FakeReactAgent(llm=llm, tools=tools, prompt=prompt)

    class FakeChatPromptTemplate:
        def __init__(self, messages):
            self.messages = messages

        @classmethod
        def from_messages(cls, messages):
            return cls(messages)

    class FakeMessagesPlaceholder:
        def __init__(self, variable_name):
            self.variable_name = variable_name

    class FakeLLM:
        @property
        def _llm_type(self) -> str:
            return "fake"

        def _call(self, prompt: str, stop=None, run_manager=None, **kwargs: Any) -> str:
            return prompt

    fake_agents = types.SimpleNamespace(create_react_agent=fake_create_react_agent)
    fake_prompts = types.SimpleNamespace(ChatPromptTemplate=FakeChatPromptTemplate, MessagesPlaceholder=FakeMessagesPlaceholder)
    fake_llms_base = types.SimpleNamespace(LLM=FakeLLM)

    monkeypatch.setitem(sys.modules, "langchain", fake_langchain)
    monkeypatch.setitem(sys.modules, "langchain.agents", fake_agents)
    monkeypatch.setitem(sys.modules, "langchain_core", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "langchain_core.prompts", fake_prompts)
    monkeypatch.setitem(sys.modules, "langchain_core.language_models", types.SimpleNamespace(llms=fake_llms_base))
    monkeypatch.setitem(sys.modules, "langchain_core.language_models.llms", fake_llms_base)


def test_build_agent_executor_invokes_initialize_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    call_log: dict[str, Any] = {}
    _install_fake_langchain(monkeypatch, call_log)

    # Avoid hitting real OpenAI; stub the LLM and tool loader.
    class DummyLLM:
        _llm_type = "dummy"

    dummy_tool = types.SimpleNamespace(name="dummy_tool")

    monkeypatch.setattr(orchestrator, "_build_llm", lambda settings: DummyLLM())
    monkeypatch.setattr(orchestrator, "_load_tools", lambda settings: [dummy_tool])

    settings = Settings(agent=AgentSettings(max_iterations=3, verbose=True))

    executor = orchestrator.build_agent_executor(settings)

    result = executor.invoke({"input": "hello"})
    assert result["tools"] == ["dummy_tool"]
    assert result["recursion_limit"] == 3
    assert call_log["prompt"]
    assert call_log["tools"] == [dummy_tool]
    assert call_log["llm"]._llm_type == "dummy"


def test_agent_stream_interface(monkeypatch: pytest.MonkeyPatch) -> None:
    call_log: dict[str, Any] = {}
    _install_fake_langchain(monkeypatch, call_log)

    class DummyLLM:
        _llm_type = "dummy"

    dummy_tool = types.SimpleNamespace(name="stream_tool")

    monkeypatch.setattr(orchestrator, "_build_llm", lambda settings: DummyLLM())
    monkeypatch.setattr(orchestrator, "_load_tools", lambda settings: [dummy_tool])

    settings = Settings(agent=AgentSettings(max_iterations=2, verbose=False))
    executor = orchestrator.build_agent_executor(settings)

    events = list(executor.stream({"input": "stream-test"}))
    assert events[0]["event"] == "start"
    assert events[-1]["event"] == "end"
    assert call_log["stream_config"]["recursion_limit"] == 2


def test_run_agent_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke test: run_agent returns structured metadata without raising."""

    class DummyExecutor:
        def __init__(self) -> None:
            self.invocations: list[dict[str, Any]] = []

        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            self.invocations.append(payload)
            return {
                "query": payload.get("input", ""),
                "pain_points": [{"text": "sample"}],
                "metadata": {"total_sources_searched": 3, "execution_time": 0.12, "api_costs": 0.0},
            }

    dummy_executor = DummyExecutor()
    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: dummy_executor)

    result = pain_point_agent.run_agent("smoke-test query")

    assert result["query"] == "smoke-test query"
    assert result["pain_points"]
    assert "metadata" in result
    assert result["metadata"]["total_sources_searched"] == 3


def test_agent_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate tool failure and ensure agent surfaces a friendly error."""

    class FailingExecutor:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("tool boom")

    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: FailingExecutor())

    with pytest.raises(RuntimeError, match="tool boom"):
        pain_point_agent.run_agent("failure-query")
