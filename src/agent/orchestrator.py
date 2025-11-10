"""Utilities for building and configuring the LangChain agent executor."""

from __future__ import annotations

from typing import Iterable, List

from langchain.agents import AgentExecutor, initialize_agent
from langchain.tools import BaseTool

from config.settings import Settings
from src.tools.google_search_tool import GoogleSearchTool
from src.tools.reddit_tool import RedditTool
from src.tools.twitter_tool import TwitterTool


def build_agent_executor(settings: Settings) -> AgentExecutor:
    """Construct an AgentExecutor configured with project tools and prompts."""

    tools = _load_tools(settings)
    agent = initialize_agent(
        tools=tools,
        llm=None,  # To be replaced with actual LLM initialization
        agent="zero-shot-react-description",
        verbose=True,
        max_iterations=5,
    )
    return AgentExecutor(agent=agent.agent, tools=tools, verbose=True)


def _load_tools(settings: Settings) -> List[BaseTool]:
    """Instantiate tool set with shared configuration."""

    return list(_iter_tools(settings))


def _iter_tools(settings: Settings) -> Iterable[BaseTool]:
    """Yield configured LangChain tools for the agent."""

    yield RedditTool.from_settings(settings)
    yield TwitterTool.from_settings(settings)
    yield GoogleSearchTool.from_settings(settings)
