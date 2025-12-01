"""Utilities for building and configuring the LangChain agent executor."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

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

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant that researches customer pain points using the provided tools."),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent_graph = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return _AgentRunner(agent_graph, settings)


def _load_tools(settings: Settings) -> List[Any]:
    """Instantiate tool set with shared configuration."""

    return list(_iter_tools(settings))


def _iter_tools(settings: Settings) -> Iterable[Any]:
    """Yield configured LangChain tools for the agent.

    Import tool implementations here to avoid triggering their module-level
    side-effects (pydantic model construction) during test collection.
    """

    from src.tools.reddit_tool import RedditTool
    from src.tools.twitter_tool import TwitterTool
    from src.tools.google_search_tool import GoogleSearchTool

    tool_settings = getattr(settings, "tools", None)

    def is_enabled(flag: str) -> bool:
        if tool_settings is None:
            return True
        return getattr(tool_settings, flag, True)

    if is_enabled("reddit_enabled"):
        yield RedditTool.from_settings(settings)

    if is_enabled("twitter_enabled"):
        yield TwitterTool.from_settings(settings)

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

    def __init__(self, agent_graph: Any, settings: Settings) -> None:
        self._agent = agent_graph
        self._recursion_limit = max(1, settings.agent.max_iterations)

    def invoke(self, payload: Dict[str, Any]) -> Any:
        return self._agent.invoke(payload, config={"recursion_limit": self._recursion_limit})

    def stream(self, payload: Dict[str, Any]):
        yield from self._agent.stream(payload, config={"recursion_limit": self._recursion_limit})
