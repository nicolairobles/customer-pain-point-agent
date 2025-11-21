"""Utilities for building and configuring the LangChain agent executor."""

from __future__ import annotations

from typing import Any, Iterable, List

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
    """Instantiate a chat LLM from settings, tolerant of LangChain API variants."""

    try:
        # Newer LangChain versions split providers; try the bundled one first.
        try:
            from langchain.chat_models import ChatOpenAI  # type: ignore
        except Exception:
            from langchain_openai import ChatOpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "ChatOpenAI is not available. Install the appropriate provider "
            "(e.g., `langchain` with OpenAI extras or `langchain-openai`)."
        ) from exc

    base_kwargs = {
        "temperature": settings.llm.temperature,
        "openai_api_key": settings.api.openai_api_key or None,
    }

    variants = [
        {"model": settings.llm.model, "max_tokens": settings.llm.max_output_tokens, "timeout": settings.llm.request_timeout_seconds},
        {"model_name": settings.llm.model, "max_tokens": settings.llm.max_output_tokens, "request_timeout": settings.llm.request_timeout_seconds},
        {"model": settings.llm.model},
        {"model_name": settings.llm.model},
    ]

    last_error: Exception | None = None
    for variant in variants:
        try:
            return ChatOpenAI(**{**base_kwargs, **variant})
        except TypeError as exc:
            last_error = exc
            continue

    raise TypeError(
        "Unable to construct ChatOpenAI with provided settings; please verify "
        "the installed LangChain/OpenAI provider version."
    ) from last_error
