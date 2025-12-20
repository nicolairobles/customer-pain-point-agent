"""Utilities for building and configuring the LangChain agent executor."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence

from config.settings import Settings


def build_agent_executor(settings: Settings) -> Any:
    """Construct an Agent executor configured with project tools and prompts.

    LangChain imports are deferred until this function is called so that the
    module can be imported in environments with incompatible LangChain
    versions (tests, static analysis, etc.). If LangChain is missing or the
    public API changed, an informative ImportError is raised.
    """

    try:
        import langchain as _langchain
        from langchain.agents import create_react_agent  # type: ignore
        from langchain_core.callbacks.base import BaseCallbackHandler  # type: ignore
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # type: ignore
    except Exception as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "Failed to import required classes from langchain. This can happen if the package is not "
            "installed or if the installed version is incompatible with this code. Ensure `langchain>=1.0.7,<2` "
            "is available in your environment."
        ) from exc

    # Log LangChain version for diagnostic purposes when the agent is built.
    try:
        _lc_ver = getattr(_langchain, "__version__", None)
        if _lc_ver is None:
            try:
                from importlib import metadata as _metadata

                _lc_ver = _metadata.version("langchain")
            except Exception:
                _lc_ver = "unknown"
        import logging

        logging.getLogger(__name__).info("Using langchain version=%s", _lc_ver)
    except Exception:
        # Version logging is diagnostic only.
        pass

    tools = _load_tools(settings)
    llm = _build_llm(settings)
    telemetry_handler = _TelemetryCallbackHandler()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant that researches customer pain points using the provided tools."),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    instrumented_tools = _attach_telemetry(tools, telemetry_handler)
    agent_graph = create_react_agent(llm=llm, tools=instrumented_tools, prompt=prompt)
    return _AgentRunner(agent_graph, settings, telemetry_handler)


def _load_tools(settings: Settings) -> List[Any]:
    """Instantiate tool set with shared configuration."""

    return list(_iter_tools(settings))


def _iter_tools(settings: Settings) -> Iterable[Any]:
    """Yield configured LangChain tools for the agent.

    Import tool implementations here to avoid triggering their module-level
    side-effects (pydantic model construction) during test collection.
    """

    from src.tools.reddit_tool import RedditTool
    from src.tools.google_search_tool import GoogleSearchTool

    tool_settings = getattr(settings, "tools", None)

    def is_enabled(flag: str) -> bool:
        if tool_settings is None:
            return True
        return getattr(tool_settings, flag, True)

    if is_enabled("reddit_enabled"):
        yield RedditTool.from_settings(settings)

    if is_enabled("google_search_enabled"):
        yield GoogleSearchTool.from_settings(settings)


def _build_llm(settings: Settings) -> Any:
    """Instantiate an LLM backed by the OpenAIService wrapper (settings-driven)."""

    try:
        from langchain_core.language_models.llms import LLM  # type: ignore
    except Exception as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "LangChain LLM base class not available. Confirm `langchain` satisfies project constraints."
        ) from exc

    from src.services import OpenAIService

    class OpenAIServiceLLM(LLM):
        """Adapter to make OpenAIService compatible with LangChain agents."""

        def __init__(self, service: OpenAIService):
            super().__init__()
            self._service = service
            self._settings = service_settings

        @property
        def _llm_type(self) -> str:
            return "openai-service"

        @property
        def _identifying_params(self) -> Dict[str, Any]:
            llm_settings = self._settings
            return {
                "model": llm_settings.model,
                "temperature": llm_settings.temperature,
                "max_output_tokens": llm_settings.max_output_tokens,
            }

        def _call(self, prompt: str, stop: List[str] | None = None, run_manager: Any = None, **kwargs: Any) -> str:
            # OpenAIService does not currently accept stop tokens; emulate simple stop behavior locally.
            result = self._service.generate(prompt)
            text = result.text
            if stop:
                for token in stop:
                    if token in text:
                        text = text.split(token)[0]
                        break
            return text

    service_settings = settings.llm
    service = OpenAIService.from_settings(settings)
    return OpenAIServiceLLM(service)


class _AgentRunner:
    """Lightweight adapter exposing invoke/stream on the LangGraph agent."""

    def __init__(self, agent_graph: Any, settings: Settings, telemetry_handler: Any | None = None) -> None:
        self._agent = agent_graph
        self._recursion_limit = max(1, settings.agent.max_iterations)
        self._telemetry_handler = telemetry_handler
        self._settings = settings

    def invoke(self, payload: Dict[str, Any]) -> Any:
        result = self._agent.invoke(payload, config={"recursion_limit": self._recursion_limit})
        if not isinstance(result, Mapping):
            return result

        raw_items = _collect_tool_items(result)
        if not raw_items or not self._settings.api.openai_api_key:
            return result

        pain_points = _extract_structured_pain_points(raw_items)
        if not pain_points:
            return result

        enriched: Dict[str, Any] = dict(result)
        enriched["pain_points"] = pain_points
        metadata = enriched.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        metadata["total_sources_searched"] = int(metadata.get("total_sources_searched", 0)) + len(raw_items)
        enriched["metadata"] = metadata
        return enriched

    def stream(self, payload: Dict[str, Any]):
        yield from self._agent.stream(payload, config={"recursion_limit": self._recursion_limit})

    def get_used_tools(self) -> List[str]:
        """Return a unique list of tool names observed via telemetry."""

        handler = self._telemetry_handler
        used = getattr(handler, "used_tools", None)
        if not used:
            return []
        return sorted({str(name) for name in used if name})


def _attach_telemetry(tools: Iterable[Any], handler: Any) -> List[Any]:
    """Attach telemetry callbacks to each tool instance."""

    instrumented: List[Any] = []
    for tool in tools:
        callbacks = list(getattr(tool, "callbacks", []) or [])
        callbacks.append(handler)
        try:
            tool.callbacks = callbacks
        except Exception:
            # If assignment fails, proceed without callbacks to avoid breaking execution.
            pass
        instrumented.append(tool)
    return instrumented


class _TelemetryCallbackHandler:
    """Lightweight logger for tool invocation events (non-sensitive)."""

    def __init__(self) -> None:
        import logging

        self._log = logging.getLogger(__name__)
        self.used_tools: set[str] = set()

    def on_tool_start(self, serialized: Dict[str, Any] | None = None, input_str: str | None = None, **kwargs: Any) -> None:
        tool_name = (serialized or {}).get("name", "<unknown>")
        summary = _summarize_input(input_str)
        self._log.info("tool_start name=%s input=%s", tool_name, summary)
        if tool_name and tool_name != "<unknown>":
            self.used_tools.add(str(tool_name))

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        self._log.info("tool_end output_type=%s", type(output).__name__)


def _summarize_input(input_str: Any) -> str:
    """Return a minimal, non-sensitive summary of tool input."""

    if input_str is None:
        return "<none>"
    if isinstance(input_str, dict):
        return f"dict_keys={list(input_str.keys())}"
    if isinstance(input_str, str):
        preview = input_str[:80].replace("\n", " ")
        return f"str(len={len(input_str)} preview='{preview}')"
    return f"type={type(input_str).__name__}"


def _collect_tool_items(result: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """Extract raw tool outputs from common LangChain/LangGraph result shapes."""

    collected: List[Mapping[str, Any]] = []

    steps = result.get("intermediate_steps", [])
    if isinstance(steps, list):
        for entry in steps:
            if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                continue
            _action, observation = entry
            if isinstance(observation, list):
                for item in observation:
                    if isinstance(item, Mapping):
                        collected.append(item)

    messages = result.get("messages", [])
    if isinstance(messages, list):
        for message in messages:
            msg_type = getattr(message, "type", None)
            if msg_type != "tool":
                continue
            artifact = getattr(message, "artifact", None)
            if isinstance(artifact, list):
                for item in artifact:
                    if isinstance(item, Mapping):
                        collected.append(item)

    return collected


def _extract_structured_pain_points(items: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Convert tool results into extractor documents and return JSON-serializable pain points."""

    from src.extractors.pain_point_extractor import extract_pain_points

    documents = [_coerce_item_to_document(item) for item in items]
    documents = [doc for doc in documents if doc is not None]
    if not documents:
        return []

    points = extract_pain_points(documents)
    rendered: List[Dict[str, Any]] = []
    for point in points:
        if hasattr(point, "model_dump"):
            rendered.append(point.model_dump())  # type: ignore[attr-defined]
        else:
            rendered.append(point.dict())  # type: ignore[attr-defined]
    return rendered


def _coerce_item_to_document(item: Mapping[str, Any]) -> Dict[str, Any] | None:
    """Map a normalized tool payload into the extractor's expected document schema."""

    url = str(item.get("url") or item.get("permalink") or "").strip()
    if not url:
        return None

    platform = str(item.get("platform") or "unknown").strip() or "unknown"
    author = str(item.get("author") or "").strip()
    timestamp = str(item.get("created_at") or item.get("timestamp") or "").strip()

    title = str(item.get("title") or "").strip()
    text = str(item.get("text") or item.get("content") or "").strip()

    combined = "\n\n".join([part for part in (title, text) if part])

    return {
        "platform": platform,
        "author": author,
        "timestamp": timestamp,
        "url": url,
        "summary": title,
        "content": combined,
    }
