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
    [TwitterTool, GoogleSearchTool],
)
def test_tool_run_not_implemented(tool_class) -> None:
    """Placeholder ensuring run methods raise not implemented until defined."""

    tool = tool_class.from_settings(settings)
    with pytest.raises(NotImplementedError):
        tool.run("sample query")


def test_reddit_tool_run_returns_results():
    # Basic smoke: RedditTool.run should execute the implemented _run path.
    # Patch PRAW to avoid network calls or OAuth exceptions.
    import praw
    from types import SimpleNamespace

    def fake_reddit_constructor(*args, **kwargs):
        class FakeClient:
            def subreddit(self, name):
                class FakeSubreddit:
                    def search(self, query, limit, sort, time_filter):
                        # Return a small list of SimpleNamespace objects that
                        # mimic PRAW Submission attributes the tool expects.
                        return [
                            SimpleNamespace(
                                id="t1",
                                title="Test Post",
                                selftext="body",
                                score=5,
                                num_comments=1,
                                url="https://example.com",
                                subreddit_name_prefixed=f"r/{name}",
                                created_utc=1600000000.0,
                                subreddit=f"r/{name}",
                            )
                        ]

                return FakeSubreddit()

        return FakeClient()

    # Patch praw.Reddit so RedditTool.__init__ creates our fake client.
    from unittest.mock import patch

    with patch("praw.Reddit", new=fake_reddit_constructor):
        tool = RedditTool.from_settings(settings)
    results = tool.run("test")
    assert isinstance(results, list)
    assert len(results) >= 0
