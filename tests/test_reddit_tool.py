import json
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, ConfigDict

from src.tools.reddit_tool import RedditTool


class DummySubmission:
    def __init__(
        self,
        id,
        title,
        selftext,
        score,
        num_comments,
        url,
        subreddit,
        created_utc,
        author="alice",
        permalink="",
        subreddit_name_prefixed=None,
        over_18=False,
        spoiler=False,
        removed_by_category=None,
    ):
        self.id = id
        self.title = title
        self.selftext = selftext
        self.score = score
        self.num_comments = num_comments
        self.url = url
        self.permalink = permalink
        self.subreddit = subreddit
        self.subreddit_name_prefixed = subreddit_name_prefixed
        self.created_utc = created_utc
        self.author = author
        self.over_18 = over_18
        self.spoiler = spoiler
        self.removed_by_category = removed_by_category


class DummySubreddit:
    def __init__(self, items):
        self._items = items

    def search(self, query, limit, sort, time_filter=None):
        # Return first `limit` items
        return self._items[:limit]


class DummyRedditClient:
    def __init__(self, mapping):
        self._mapping = mapping

    def subreddit(self, name):
        if name not in self._mapping:
            raise Exception("subreddit not found")
        return self._mapping[name]


@pytest.fixture
def settings():
    class S:
        class API:
            reddit_client_id = "id"
            reddit_client_secret = "secret"

        api = API()

    return S()


def _model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Return a dictionary representation compatible with Pydantic v1/v2."""

    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


def test_reddit_tool_returns_normalized_results(monkeypatch, settings):
    items = [
        DummySubmission(
            "a1",
            "**T1**",
            "body1 with [link](http://example.com) and u/example",
            10,
            2,
            " http://x/1 ",
            "python",
            1_600_000_000,
            author="alice",
            permalink=" /r/python/comments/a1 ",
            over_18=True,
        ),
        DummySubmission(
            "a2",
            "T2",
            "",
            5,
            0,
            "http://x/2",
            "python",
            1_600_000_100,
            author=None,
            subreddit_name_prefixed="r/python",
        ),
    ]

    client = DummyRedditClient({"python": DummySubreddit(items), "learnprogramming": DummySubreddit([]), "programming": DummySubreddit([])})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    # Use "body" as query since it appears in the test data, testing relevance filtering
    results = tool._run("body", subreddits=["python", "learnprogramming", "programming"], limit=5, per_subreddit=2)

    assert isinstance(results, list)
    # With relevance filtering, only posts matching "body" query are returned (1 post)
    assert len(results) == 1
    # Markdown has been stripped and user mention normalised.
    assert results[0]["title"] == "T1"
    assert results[0]["text"] == "body1 with link and @example"
    assert results[0]["upvotes"] == 10
    assert results[0]["comments"] == 2
    assert results[0]["author"] == "alice"
    assert results[0]["permalink"] == "/r/python/comments/a1"
    assert results[0]["url"] == "http://x/1"
    assert results[0]["content_flags"] == ["nsfw"]
    # Note: Second post (T2) is filtered out due to relevance check since it doesn't contain "body"


def test_reddit_tool_handles_empty_and_errors(monkeypatch, settings):
    # subreddit raising on access
    def broken_subreddit(name):
        raise Exception("boom")

    client = MagicMock()
    client.subreddit.side_effect = broken_subreddit
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    results = tool._run("q", subreddits=["nope"], limit=5, per_subreddit=2)

    # Should gracefully return empty list on persistent errors
    assert results == []


def test_reddit_tool_sorting_by_relevance(monkeypatch, settings):
    items = [
        DummySubmission("a1", "High", "b", 100, 50, "u1", "python", 1),
        DummySubmission("a2", "Low", "b", 1, 0, "u2", "python", 1),
    ]
    client = DummyRedditClient({"python": DummySubreddit(items), "learnprogramming": DummySubreddit([]), "programming": DummySubreddit([])})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    results = tool._run("q", subreddits=["python"], limit=10, per_subreddit=10)

    assert results[0]["title"] == "High"
    assert results[1]["title"] == "Low"


def test_subreddit_coercion_for_non_string_objects(monkeypatch, settings):
    # Submission.subreddit is an object (not a string); ensure it's coerced to str
    class FakeSubObj:
        def __str__(self):
            return "r/fakesub"

    items = [
        DummySubmission("b1", "Title", "b", 1, 0, "u", FakeSubObj(), 1600000000, author="bob"),
    ]

    client = DummyRedditClient({"python": DummySubreddit(items), "learnprogramming": DummySubreddit([]), "programming": DummySubreddit([])})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    results = tool._run("q", subreddits=["python"], limit=10, per_subreddit=10)

    assert len(results) == 1
    assert results[0]["subreddit"] == "r/fakesub"


def test_normalized_schema_matches_pydantic_model(monkeypatch, settings):
    class RedditPost(BaseModel):
        model_config = ConfigDict(extra="forbid")

        id: str
        title: str
        text: str
        url: str
        author: str
        subreddit: str
        permalink: str
        created_at: str
        upvotes: int
        comments: int
        content_flags: list[str]

    items = [
        DummySubmission(
            "c1",
            "SchemaTest",
            "body",
            7,
            3,
            "http://example.com/1",
            "python",
            1_600_000_200,
            author="charlie",
            removed_by_category="moderator",
        ),
    ]

    client = DummyRedditClient({"python": DummySubreddit(items)})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    results = tool._run("q", subreddits=["python"], limit=5, per_subreddit=5)

    assert results, "Expected at least one normalized result"
    validated = RedditPost(**results[0])
    model_dict = _model_to_dict(validated)
    serialized = json.dumps(model_dict)

    assert json.loads(serialized) == model_dict


def test_relevance_filtering_removes_irrelevant_posts(monkeypatch, settings):
    """Test that posts not matching the query are filtered out."""
    items = [
        DummySubmission("r1", "Bug in checkout", "Users can't complete checkout", 10, 5, "u1", "ecommerce", 1),
        DummySubmission("r2", "General business advice", "How to grow your business", 20, 10, "u2", "entrepreneur", 1),
        DummySubmission("r3", "Checkout issues with Stripe", "Payment failures during checkout", 15, 8, "u3", "webdev", 1),
    ]
    
    client = DummyRedditClient({"ecommerce": DummySubreddit(items)})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)
    
    tool = RedditTool.from_settings(settings)
    # Search for "checkout" - should filter out the general business advice post
    results = tool._run("checkout problems", subreddits=["ecommerce"], limit=10, per_subreddit=10)
    
    # Should get 2 posts that mention "checkout", not the general business one
    assert len(results) == 2
    titles = [r["title"] for r in results]
    assert "Bug in checkout" in titles
    assert "Checkout issues with Stripe" in titles
    assert "General business advice" not in titles
