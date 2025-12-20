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
    assert set(normalized.keys()) == {"query", "pain_points", "metadata", "output"}


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

    def fake_create_react_agent(llm=None, model=None, tools=None, prompt=None):
        # Simulate older LangChain signature that rejects the newer `model` kwarg so we exercise the
        # fallback path in orchestrator.build_agent_executor.
        if model is not None:
            call_log["model_attempted"] = True
            raise TypeError("create_react_agent() got an unexpected keyword argument 'model'")

        resolved_llm = llm or model
        call_log.update({"tools": tools, "llm": resolved_llm, "model": model, "prompt": prompt})
        return FakeReactAgent(llm=resolved_llm, tools=tools, prompt=prompt)

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

    # Avoid hitting the QueryProcessor/Analyst OpenAI calls in unit tests.
    from src.agent.query_processor import QueryAnalysis

    executor._query_processor.analyze = lambda q: QueryAnalysis(  # type: ignore[attr-defined]
        refined_query=q, search_terms=["hello"], subreddits=["python"], context_notes=""
    )
    executor._analyst.review = lambda _analysis, _research_output: "final"  # type: ignore[attr-defined]

    result = executor.invoke({"input": "hello"})
    assert result["output"] == "final"
    assert result["metadata"]["total_sources_searched"] == 0
    assert call_log["model_attempted"] is True
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

    from src.agent.query_processor import QueryAnalysis

    executor._query_processor.analyze = lambda q: QueryAnalysis(  # type: ignore[attr-defined]
        refined_query=q, search_terms=["stream"], subreddits=["python"], context_notes=""
    )

    events = list(executor.stream({"input": "stream-test"}))
    assert events[0]["event"] == "start"
    assert any(event.get("event") == "end" for event in events)
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


def test_run_agent_retries_transient_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Transient failures should be retried with exponential backoff."""

    class FlakyExecutor:
        def __init__(self) -> None:
            self.invocations = 0

        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            self.invocations += 1
            if self.invocations == 1:
                raise RuntimeError("transient")
            return {
                "query": payload.get("input", ""),
                "pain_points": [{"text": "ok"}],
                "metadata": {"total_sources_searched": 1, "execution_time": 0.01, "api_costs": 0.0},
            }

    executor = FlakyExecutor()
    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: executor)

    sleeps: list[float] = []
    monkeypatch.setattr(pain_point_agent.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = pain_point_agent.run_agent("transient test")

    assert executor.invocations == 2
    assert sleeps == [1.0]
    assert result["metadata"]["total_sources_searched"] == 1


def test_run_agent_stops_after_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Persistent failures should return a structured error payload after retries."""

    class AlwaysFailExecutor:
        def __init__(self) -> None:
            self.invocations = 0

        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            self.invocations += 1
            raise RuntimeError("boom")

    executor = AlwaysFailExecutor()
    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: executor)

    sleeps: list[float] = []
    monkeypatch.setattr(pain_point_agent.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = pain_point_agent.run_agent("will fail")

    assert executor.invocations == 3
    assert sleeps == [1.0, 2.0]
    assert result["error"]["type"] == "RuntimeError"
    assert result["error"]["remediation"]


def test_run_agent_rejects_invalid_query() -> None:
    """Input validation should block empty or non-string queries before invocation."""

    with pytest.raises(ValidationError):
        pain_point_agent.run_agent("")  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        pain_point_agent.run_agent("   ")

    with pytest.raises(ValidationError):
        pain_point_agent.run_agent(None)  # type: ignore[arg-type]


def test_run_agent_rejects_overlong_query() -> None:
    """Queries exceeding max words should raise validation error."""

    long_query = " ".join(["word"] * 51)

    with pytest.raises(ValidationError):
        pain_point_agent.run_agent(long_query)


def test_run_agent_normalizes_missing_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Normalization should backfill defaults when the agent omits fields."""

    class PartialExecutor:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {"metadata": {"execution_time": 1.5}}

    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: PartialExecutor())

    result = pain_point_agent.run_agent("singleword")

    assert result["query"] == "singleword"
    assert result["pain_points"] == []
    assert result["metadata"]["execution_time"] >= 0.0
    assert result["metadata"]["total_sources_searched"] == 0
    assert result["metadata"]["api_costs"] == 0.0
    assert result["metadata"]["tools_used"] == []


def test_run_agent_merges_telemetry_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tools observed via telemetry should be surfaced in metadata."""

    class ToolAwareExecutor:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {"metadata": {"tools_used": ["metadata_tool"]}}

        def get_used_tools(self) -> list[str]:
            return ["reddit", "Google_Search", "reddit"]

    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: ToolAwareExecutor())

    result = pain_point_agent.run_agent("tool merge")

    tools = result["metadata"]["tools_used"]
    assert set(tools) == {"reddit", "google_search", "metadata_tool"}


def test_stream_agent_yields_events(monkeypatch: pytest.MonkeyPatch) -> None:
    """Streamed events should be yielded progressively with a completion summary."""

    class StreamingExecutor:
        def __init__(self) -> None:
            self.payloads: list[dict[str, Any]] = []

        def stream(self, payload: dict[str, Any]):
            self.payloads.append(payload)
            yield {"event": "chunk", "data": 1}
            yield {"event": "chunk", "data": 2}

    executor = StreamingExecutor()
    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: executor)

    events = list(pain_point_agent.stream_agent("stream query"))

    assert executor.payloads[0]["input"] == "stream query"
    assert events[0]["event"] == "chunk"
    assert events[1]["event"] == "chunk"
    assert events[-1]["event"] == "complete"
    assert "execution_time" in events[-1]["metadata"]
    assert events[-1]["metadata"]["tools_used"] == []


def test_stream_agent_surfaces_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Streaming failures should emit a structured error event instead of raising."""

    class FailingStreamExecutor:
        def __init__(self) -> None:
            self.calls = 0

        def stream(self, payload: dict[str, Any]):
            self.calls += 1
            raise RuntimeError("stream failure")

        def get_used_tools(self) -> list[str]:
            return ["stream_tool"]

    executor = FailingStreamExecutor()
    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: executor)

    events = list(pain_point_agent.stream_agent("stream failure"))

    assert executor.calls == 1
    assert len(events) == 1
    error_event = events[0]
    assert error_event["event"] == "error"
    assert error_event["error"]["type"] == "RuntimeError"
    assert "execution_time" in error_event["metadata"]
    assert error_event["metadata"]["tools_used"] == ["stream_tool"]


def test_agent_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate tool failure and ensure agent surfaces a structured error."""

    class FailingExecutor:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("tool boom")

    monkeypatch.setattr(pain_point_agent, "create_agent", lambda: FailingExecutor())

    result = pain_point_agent.run_agent("failure-query")
    error = result["error"]
    assert "tool boom" in error["message"]
    assert error["type"] == "RuntimeError"
    assert error["remediation"]


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

    class DummyGoogleSearchTool(BaseDummyTool):
        name = "google"

    monkeypatch.setitem(sys.modules, "src.tools.reddit_tool", types.SimpleNamespace(RedditTool=DummyRedditTool))
    monkeypatch.setitem(
        sys.modules, "src.tools.google_search_tool", types.SimpleNamespace(GoogleSearchTool=DummyGoogleSearchTool)
    )

    settings = Settings(tools=ToolSettings(reddit_enabled=False, google_search_enabled=True))
    tools = list(orchestrator._load_tools(settings))
    instrumented = orchestrator._attach_telemetry(tools, orchestrator._TelemetryCallbackHandler())

    names = [t.name for t in instrumented]
    assert "reddit" not in names
    assert names == ["google"]

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

    dummy_module = types.SimpleNamespace(RedditTool=BaseDummyTool, GoogleSearchTool=BaseDummyTool)
    monkeypatch.setitem(sys.modules, "src.tools.reddit_tool", dummy_module)
    monkeypatch.setitem(sys.modules, "src.tools.google_search_tool", dummy_module)

    settings = Settings(tools=ToolSettings(reddit_enabled=False, google_search_enabled=False))
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
