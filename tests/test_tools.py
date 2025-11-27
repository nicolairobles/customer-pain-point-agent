"""Tests for external source tools."""

from __future__ import annotations

import pytest

from config.settings import APISettings, Settings, settings
from src.tools.google_search_tool import GoogleSearchTool
from src.tools.reddit_tool import RedditTool
from src.tools.twitter_tool import TwitterTool


def _install_fake_google_client(monkeypatch):
    """Provide a minimal googleapiclient stub so initialization succeeds."""

    import sys
    import types

    discovery_module = types.ModuleType("googleapiclient.discovery")

    def fake_build(name, version, developerKey=None):
        class FakeService:
            def cse(self):
                class FakeCSE:
                    def list(self, **kwargs):
                        class FakeRequest:
                            def execute(self):
                                return {"items": []}

                        return FakeRequest()

                return FakeCSE()

        return FakeService()

    discovery_module.build = fake_build

    errors_module = types.ModuleType("googleapiclient.errors")

    class FakeHttpError(Exception):
        pass

    errors_module.HttpError = FakeHttpError

    root_module = types.ModuleType("googleapiclient")
    root_module.discovery = discovery_module
    root_module.errors = errors_module

    monkeypatch.setitem(sys.modules, "googleapiclient", root_module)
    monkeypatch.setitem(sys.modules, "googleapiclient.discovery", discovery_module)
    monkeypatch.setitem(sys.modules, "googleapiclient.errors", errors_module)


def test_tool_factory_methods(monkeypatch) -> None:
    """Ensure each tool can be instantiated from settings."""

    _install_fake_google_client(monkeypatch)
    google_settings = Settings(
        api=APISettings(
            google_search_api_key="dummy-key",
            google_search_engine_id="dummy-cx",
        )
    )

    assert isinstance(RedditTool.from_settings(settings), RedditTool)
    assert isinstance(TwitterTool.from_settings(settings), TwitterTool)
    assert isinstance(GoogleSearchTool.from_settings(google_settings), GoogleSearchTool)


@pytest.mark.parametrize(
    "tool_class",
    [TwitterTool],
)
def test_tool_run_not_implemented(tool_class) -> None:
    """Placeholder ensuring run methods raise not implemented until defined."""

    tool = tool_class.from_settings(settings)
    with pytest.raises(NotImplementedError):
        tool.run("sample query")


def test_reddit_tool_run_returns_results(monkeypatch):
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
                                title="**Test** Post",
                                selftext="body with [link](https://example.com)",
                                score=5,
                                num_comments=1,
                                url=" https://example.com ",
                                subreddit_name_prefixed=f"r/{name}",
                                created_utc=1600000000.0,
                                subreddit=f"r/{name}",
                                author=None,
                                permalink="/r/test/comments/t1",
                                over_18=True,
                                spoiler=False,
                                removed_by_category=None,
                            )
                        ]

                return FakeSubreddit()

        return FakeClient()

    # Patch praw.Reddit so RedditTool.__init__ creates our fake client.
    monkeypatch.setattr(praw, "Reddit", fake_reddit_constructor)

    tool = RedditTool.from_settings(settings)
    results = tool.run("test")
    assert isinstance(results, list)
    assert len(results) == 1
    payload = results[0]
    assert payload["title"] == "Test Post"
    assert payload["text"] == "body with link"
    assert payload["url"] == "https://example.com"
    assert payload["created_at"].endswith("+00:00")
    assert "nsfw" in payload["content_flags"]
