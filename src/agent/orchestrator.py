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
        from langchain.agents import AgentExecutor, initialize_agent  # type: ignore
        from langchain.tools import BaseTool  # type: ignore
    except Exception as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "Failed to import required classes from langchain. "
            "Ensure you have a compatible langchain version installed or pin a working version in requirements.txt."
        ) from exc

    tools = _load_tools(settings)
    agent = initialize_agent(
        tools=tools,
        llm=None,  # To be replaced with actual LLM initialization
        agent="zero-shot-react-description",
        verbose=True,
        max_iterations=5,
    )
    return AgentExecutor(agent=agent.agent, tools=tools, verbose=True)


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
