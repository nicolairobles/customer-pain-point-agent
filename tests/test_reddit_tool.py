import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, field_validator

from src.tools.reddit_tool import RedditTool


class DummySubmission:
    """Simple stand-in for a PRAW submission filled with controllable fields."""

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
        *,
        author=None,
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
        self.subreddit = subreddit
        self.subreddit_name_prefixed = subreddit_name_prefixed
        self.created_utc = created_utc
        self.author = author
        self.permalink = permalink
        self.over_18 = over_18
        self.spoiler = spoiler
        self.removed_by_category = removed_by_category


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "reddit"


def _load_fixture_submissions():
    """Return DummySubmission objects from the JSON fixtures."""

    payload = json.loads((FIXTURE_DIR / "submissions.json").read_text())
    submissions = []
    for entry in payload:
        submissions.append(
            DummySubmission(
                entry["id"],
                entry["title"],
                entry["selftext"],
                entry["score"],
                entry["num_comments"],
                entry["url"],
                entry["subreddit"],
                entry["created_utc"],
                author=entry["author"],
                permalink=entry["permalink"],
                over_18=entry["over_18"],
                spoiler=entry["spoiler"],
                removed_by_category=entry["removed_by_category"],
            )
        )
    return submissions


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
        DummySubmission(
            "a1",
            "**T1**",
            "body1 with [link](http://example.com) and u/example",
            10,
            2,
            " http://x/1 ",
            "python",
            1_600_000_000,
            author="user_a",
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
    results = tool._run("test-query", subreddits=["python", "learnprogramming", "programming"], limit=5, per_subreddit=2)

    assert isinstance(results, list)
    assert len(results) == 2
    # Markdown has been stripped and user mention normalised.
    assert results[0]["title"] == "T1"
    assert "@" in results[0]["text"]
    assert results[0]["upvotes"] == 10
    assert results[0]["comments"] == 2
    # ISO 8601 timestamp for downstream processing.
    assert results[0]["created_at"].endswith("+00:00")
    # NSFW flag should render as a content warning.
    assert "nsfw" in results[0]["content_flags"]
    # URLs are trimmed.
    assert results[0]["url"] == "http://x/1"
    # Author defaults gracefully when Reddit reports a deleted author.
    assert results[1]["author"] == "unknown-author"
    # Subreddit stays as provided string when already plain text.
    assert results[1]["subreddit"] == "python"


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


def test_reddit_tool_parses_fixture_payload(monkeypatch, settings):
    """Fixture-backed regression to ensure sanitisation rules remain intact."""

    items = _load_fixture_submissions()
    client = DummyRedditClient({"test": DummySubreddit(items)})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    results = tool._run("fixture", subreddits=["test"], limit=5, per_subreddit=5)

    assert len(results) == 2

    first = results[0]
    assert first["title"] == "Fixture title with link"
    assert first["text"] == "Fixture body with @example mention"
    assert first["permalink"] == "/r/test/comments/abc123/fixture/"
    assert first["content_flags"] == ["spoiler"]

    second = results[1]
    assert "nsfw" in second["content_flags"] and "removed" in second["content_flags"]
    assert second["author"] == "unknown-author"


def test_merge_and_sort_skips_blank_ids(settings):
    tool = RedditTool.from_settings(settings)
    merged = tool._merge_and_sort(
        [
            [
                {"id": "a1", "upvotes": 5, "comments": 1},
                {"id": "", "upvotes": 2, "comments": 0},
            ],
            [
                {"id": "a1", "upvotes": 10, "comments": 5},
                {"id": "a2", "upvotes": 1, "comments": 0},
            ],
        ],
        total_limit=10,
    )

    # Blank IDs are skipped and duplicates collapsed.
    assert [row["id"] for row in merged] == ["a1", "a2"]


def test_fetch_subreddit_retries_then_succeeds(monkeypatch, settings):
    """Simulate a rate-limit scenario to exercise retry/backoff logic."""

    tool = RedditTool.from_settings(settings)
    attempt_counter = {"count": 0}

    class FlakySubreddit:
        def search(self, *args, **kwargs):
            attempt_counter["count"] += 1
            if attempt_counter["count"] == 1:
                raise Exception("rate limited")
            return [
                DummySubmission(
                    "retry",
                    "Recovered",
                    "",
                    1,
                    0,
                    "http://example.com",
                    "python",
                    1_600_000_000,
                )
            ]

    class FakeClient:
        def subreddit(self, name):
            return FlakySubreddit()

    monkeypatch.setattr(tool, "_client", FakeClient())

    # Avoid real sleeps during the test and capture the delay used.
    sleeps = []
    monkeypatch.setattr("src.tools.reddit_tool.time.sleep", lambda seconds: sleeps.append(seconds))

    results = tool._fetch_subreddit("python", "query", limit=5, time_filter=None, retries=2)

    assert attempt_counter["count"] == 2
    assert sleeps == [0.5]
    assert len(results) == 1
    assert results[0]["title"] == "Recovered"


class RedditDocumentModel(BaseModel):
    """Simple schema to validate the normalised reddit payload."""

    id: str
    title: str
    text: str
    author: str
    subreddit: str
    permalink: str
    url: str
    created_at: str
    upvotes: int
    comments: int
    content_flags: list[str]

    @field_validator("created_at")
    @classmethod
    def ensure_isoformat(cls, value: str) -> str:
        assert value.endswith("+00:00")
        return value


def test_normalized_payload_matches_schema(settings, monkeypatch):
    """Validate the RedditTool output matches the parser's schema contract."""

    items = _load_fixture_submissions()
    client = DummyRedditClient({"test": DummySubreddit(items)})
    monkeypatch.setattr("src.tools.reddit_tool.praw.Reddit", lambda **kw: client)

    tool = RedditTool.from_settings(settings)
    result = tool._run("fixture", subreddits=["test"], limit=2, per_subreddit=2)[0]

    RedditDocumentModel(**result)
