"""Utilities for building and configuring the LangChain agent executor."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from config.settings import Settings


def build_agent_executor(settings: Settings) -> Any:
    """Construct an AgentExecutor configured with project tools and prompts.

    LangChain imports are deferred until this function is called so that the
    module can be imported in environments with incompatible LangChain
    versions (tests, static analysis, etc.). If LangChain is missing or the
    public API changed, an informative ImportError is raised.
    """

    try:
        import langchain as _langchain
        from langchain.agents import AgentExecutor, initialize_agent  # type: ignore
        from langchain.tools import BaseTool  # type: ignore
    except Exception as exc:  # pragma: no cover - environment specific
        # Be explicit about likely causes: missing package, incompatible
        # version, or changes to the public API. `requirements.txt` already
        # contains a broad constraint (`langchain>=0.0.200,<1`), so if you've
        # installed from a newer or older source, check the installed
        # `langchain.__version__` and confirm it matches the project's
        # compatibility. Pin a known-working version if necessary.
        raise ImportError(
            "Failed to import required classes from langchain. This can happen if "
            "the package is not installed, or the installed `langchain` version is "
            "incompatible with this code. Check `pip show langchain` (or inspect "
            "`langchain.__version__`) and ensure it satisfies the project's constraint "
            "(e.g. `langchain>=0.0.200,<1`). If needed, pin/install a compatible "
            "version in your environment."
        ) from exc

    # Log LangChain version for diagnostic purposes when the agent is built.
    try:
        _lc_ver = getattr(_langchain, "__version__", None)
        if _lc_ver is None:
            # Fallback to importlib.metadata if available
            try:
                from importlib import metadata as _metadata

                _lc_ver = _metadata.version("langchain")
            except Exception:
                _lc_ver = "unknown"
        import logging

        logging.getLogger(__name__).info("Using langchain version=%s", _lc_ver)
    except Exception:
        # Version logging is purely diagnostic; never block agent construction if
        # telemetry lookups fail (e.g., metadata missing in constrained envs).
        pass

    tools = _load_tools(settings)
    llm = _build_llm(settings)
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent="zero-shot-react-description",
        verbose=settings.agent.verbose,
        max_iterations=max(1, settings.agent.max_iterations),
        handle_parsing_errors=True,
    )
    return agent


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

    yield RedditTool.from_settings(settings)
    yield TwitterTool.from_settings(settings)
    yield GoogleSearchTool.from_settings(settings)


def _build_llm(settings: Settings) -> Any:
    """Instantiate an LLM backed by the OpenAIService wrapper (settings-driven)."""

    try:
        from langchain.llms.base import LLM  # type: ignore
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
