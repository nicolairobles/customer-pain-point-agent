import time
from unittest.mock import MagicMock

import pytest

from src.tools.reddit_tool import RedditTool


class DummySubmission:
    def __init__(self, id, title, selftext, score, num_comments, url, subreddit, created_utc):
        self.id = id
        self.title = title
        self.selftext = selftext
        self.score = score
        self.num_comments = num_comments
        self.url = url
        self.subreddit = subreddit
        self.created_utc = created_utc


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


def test_reddit_tool_returns_normalized_results(monkeypatch, settings):
    # Prepare dummy data
    items = [
        DummySubmission("a1", "T1", "body1", 10, 2, "http://x/1", "python", 1600000000),
        DummySubmission("a2", "T2", "body2", 5, 0, "http://x/2", "python", 1600000100),
    ]

    client = DummyRedditClient({"python": DummySubreddit(items), "learnprogramming": DummySubreddit([]), "programming": DummySubreddit([])})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    results = tool._run("test-query", subreddits=["python", "learnprogramming", "programming"], limit=5, per_subreddit=2)

    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["title"] == "T1"
    assert results[0]["upvotes"] == 10
    assert results[0]["comments"] == 2


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
        DummySubmission("b1", "Title", "b", 1, 0, "u", FakeSubObj(), 1600000000),
    ]

    client = DummyRedditClient({"python": DummySubreddit(items), "learnprogramming": DummySubreddit([]), "programming": DummySubreddit([])})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    results = tool._run("q", subreddits=["python"], limit=10, per_subreddit=10)

    assert len(results) == 1
    assert results[0]["subreddit"] == "r/fakesub"
