"""Tests for external source tools."""

from __future__ import annotations

import pytest

from config.settings import settings
from src.tools.google_search_tool import GoogleSearchTool
from src.tools.reddit_tool import RedditTool
from src.tools.twitter_tool import TwitterTool


def test_tool_factory_methods() -> None:
    """Ensure each tool can be instantiated from settings."""

    assert isinstance(RedditTool.from_settings(settings), RedditTool)
    assert isinstance(TwitterTool.from_settings(settings), TwitterTool)
    assert isinstance(GoogleSearchTool.from_settings(settings), GoogleSearchTool)


@pytest.mark.parametrize(
    "tool_class",
    [RedditTool, TwitterTool, GoogleSearchTool],
)
def test_tool_run_not_implemented(tool_class) -> None:
    """Placeholder ensuring run methods raise not implemented until defined."""

    tool = tool_class.from_settings(settings)
    with pytest.raises(NotImplementedError):
        tool.run("sample query")
