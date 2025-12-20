"""Tests for external source tools."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from config.settings import settings
from src.tools.google_search_tool import GoogleSearchTool
from src.tools.reddit_tool import RedditTool


def _json_schema(model_cls):
    """Return a Pydantic JSON schema across v1/v2."""

    if hasattr(model_cls, "model_json_schema"):
        return model_cls.model_json_schema()
    return model_cls.schema()


def test_tool_factory_methods() -> None:
    """Ensure each tool can be instantiated from settings."""

    assert isinstance(RedditTool.from_settings(settings), RedditTool)
    assert isinstance(GoogleSearchTool.from_settings(settings), GoogleSearchTool)


@pytest.mark.parametrize(
    "tool_class",
    [GoogleSearchTool],
)
def test_tool_run_not_implemented(tool_class) -> None:
    """Placeholder ensuring run methods raise not implemented until defined."""

    tool = tool_class.from_settings(settings)
    with pytest.raises(NotImplementedError):
        tool.run({"query": "sample query"})


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
    results = tool.run({"query": "test"})
    assert isinstance(results, list)
    assert len(results) == 1
    payload = results[0]
    assert payload["title"] == "Test Post"
    assert payload["text"] == "body with link"
    assert payload["url"] == "https://example.com"
    assert payload["created_at"].endswith("+00:00")
    assert "nsfw" in payload["content_flags"]


def test_tool_arg_schemas_are_defined_and_strict() -> None:
    reddit_tool = RedditTool.from_settings(settings)
    reddit_schema = _json_schema(reddit_tool.args_schema)
    reddit_props = reddit_schema["properties"]

    assert reddit_tool.name == "reddit_search"
    assert reddit_tool.description
    assert reddit_schema["required"] == ["query"]
    assert reddit_props["subreddits"]["type"] == "array"
    assert reddit_props["limit"]["maximum"] == 20
    assert reddit_props["per_subreddit"]["maximum"] == 25
    time_filter_enum = reddit_props["time_filter"].get("enum") or reddit_props["time_filter"].get("anyOf", [{}])[0].get("enum")
    assert set(time_filter_enum) == {"hour", "day", "week", "month", "year", "all"}

    with pytest.raises(ValidationError):
        reddit_tool.run({"query": "q", "unknown": "noop"})

    for tool_class in (GoogleSearchTool,):
        tool = tool_class.from_settings(settings)
        schema = _json_schema(tool.args_schema)
        props = schema["properties"]

        assert tool.description
        assert schema["required"] == ["query"]
        assert list(props.keys()) == ["query"]
        assert props["query"]["type"] == "string"
        with pytest.raises(ValidationError):
            tool.run({"query": "q", "unexpected": True})
