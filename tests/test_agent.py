"""Tests for agent orchestration."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from config.settings import AgentSettings, Settings, ToolSettings
from src.agent import orchestrator, pain_point_agent
from src.utils.validators import ValidationError


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
    fake_callbacks_base = types.SimpleNamespace(BaseCallbackHandler=object)

    monkeypatch.setitem(sys.modules, "langchain", fake_langchain)
    monkeypatch.setitem(sys.modules, "langchain.agents", fake_agents)
    monkeypatch.setitem(sys.modules, "langchain_core", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "langchain_core.prompts", fake_prompts)
    monkeypatch.setitem(sys.modules, "langchain_core.language_models", types.SimpleNamespace(llms=fake_llms_base))
    monkeypatch.setitem(sys.modules, "langchain_core.language_models.llms", fake_llms_base)
    monkeypatch.setitem(sys.modules, "langchain_core.callbacks", types.SimpleNamespace(base=fake_callbacks_base))
    monkeypatch.setitem(sys.modules, "langchain_core.callbacks.base", fake_callbacks_base)


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


def test_run_agent_rejects_invalid_query() -> None:
    """Input validation should block empty or non-string queries before invocation."""

    with pytest.raises(ValidationError):
        pain_point_agent.run_agent("")  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        pain_point_agent.run_agent("   ")

    with pytest.raises(ValidationError):
        pain_point_agent.run_agent(None)  # type: ignore[arg-type]


def test_run_agent_normalizes_missing_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Normalization should backfill defaults when the agent omits fields."""

    class PartialExecutor:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {"metadata": {"execution_time": 1.5}}

    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: PartialExecutor())

    result = pain_point_agent.run_agent("singleword")

    assert result["query"] == "singleword"
    assert result["pain_points"] == []
    assert result["metadata"]["execution_time"] == 1.5
    assert result["metadata"]["total_sources_searched"] == 0
    assert result["metadata"]["api_costs"] == 0.0


def test_agent_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate tool failure and ensure agent surfaces a friendly error."""

    class FailingExecutor:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("tool boom")

    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: FailingExecutor())

    with pytest.raises(RuntimeError, match="tool boom"):
        pain_point_agent.run_agent("failure-query")


def test_tool_toggles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tool enable flags control registry output."""

    import types

    class BaseDummyTool:
        description = "dummy"

        def __init__(self, name: str) -> None:
            self.name = name
            self.callbacks = []

        @classmethod
        def from_settings(cls, _settings):
            return cls(cls.name)  # type: ignore[attr-defined]

    class DummyRedditTool(BaseDummyTool):
        name = "reddit"

    class DummyTwitterTool(BaseDummyTool):
        name = "twitter"

    class DummyGoogleSearchTool(BaseDummyTool):
        name = "google"

    monkeypatch.setitem(sys.modules, "src.tools.reddit_tool", types.SimpleNamespace(RedditTool=DummyRedditTool))
    monkeypatch.setitem(sys.modules, "src.tools.twitter_tool", types.SimpleNamespace(TwitterTool=DummyTwitterTool))
    monkeypatch.setitem(
        sys.modules, "src.tools.google_search_tool", types.SimpleNamespace(GoogleSearchTool=DummyGoogleSearchTool)
    )

    settings = Settings(tools=ToolSettings(reddit_enabled=False, twitter_enabled=True, google_search_enabled=True))
    tools = list(orchestrator._load_tools(settings))
    instrumented = orchestrator._attach_telemetry(tools, orchestrator._TelemetryCallbackHandler())

    names = [t.name for t in instrumented]
    assert "reddit" not in names
    assert names == ["twitter", "google"]

    assert all(any(cb.__class__.__name__ == "_TelemetryCallbackHandler" for cb in t.callbacks) for t in instrumented)


def test_tool_registry_all_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registry should be empty when all tool flags are disabled."""

    import types

    class BaseDummyTool:
        description = "dummy"
        name = "dummy"

        def __init__(self) -> None:
            self.callbacks = []

        @classmethod
        def from_settings(cls, _settings):
            return cls()

    dummy_module = types.SimpleNamespace(RedditTool=BaseDummyTool, TwitterTool=BaseDummyTool, GoogleSearchTool=BaseDummyTool)
    monkeypatch.setitem(sys.modules, "src.tools.reddit_tool", dummy_module)
    monkeypatch.setitem(sys.modules, "src.tools.twitter_tool", dummy_module)
    monkeypatch.setitem(sys.modules, "src.tools.google_search_tool", dummy_module)

    settings = Settings(tools=ToolSettings(reddit_enabled=False, twitter_enabled=False, google_search_enabled=False))
    tools = list(orchestrator._load_tools(settings))

    assert tools == []


def test_telemetry_logging_sanitizes_input(caplog: pytest.LogCaptureFixture) -> None:
    """Telemetry should log tool events with sanitized input metadata."""

    handler = orchestrator._TelemetryCallbackHandler()

    with caplog.at_level("INFO", logger="src.agent.orchestrator"):
        handler.on_tool_start({"name": "sample_tool"}, {"secret": "should_not_show"})
        handler.on_tool_end(output={"result": "ok"})

    messages = [record.message for record in caplog.records]
    assert any("tool_start" in msg and "dict_keys" in msg for msg in messages)
    # Ensure sensitive values are not logged.
    assert all("should_not_show" not in msg for msg in messages)
    assert any("tool_end" in msg and "dict" in msg for msg in messages)
