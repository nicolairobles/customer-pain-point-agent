"""Unit tests for the Reddit parsing helpers introduced in story 1.2.3."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

from pydantic import BaseModel, field_validator

from src.tools import reddit_parser


def _make_submission(**kwargs):
    """Helper to stand up a submission-like object with sensible defaults."""

    defaults = {
        "id": "abc123",
        "title": "**Bold** title with [link](http://example.com)",
        "selftext": "Body `code` and u/name mention",
        "score": 1,
        "num_comments": 0,
        "url": " https://example.com/post ",
        "permalink": " /r/test/comments/abc123/post/ ",
        "subreddit": "test",
        "created_utc": 1_700_000_000,
        "author": SimpleNamespace(name="author_one"),
        "over_18": True,
        "spoiler": False,
        "removed_by_category": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_sanitize_text_strips_markdown():
    raw = "**Hello** [world](http://example.com) `code` u/test"
    cleaned = reddit_parser.sanitize_text(raw)
    assert cleaned == "Hello world code @test"


def test_to_iso8601_handles_invalid_values():
    assert reddit_parser.to_iso8601(None) == ""
    assert reddit_parser.to_iso8601("not-a-number") == ""


def test_normalize_submission_includes_expected_fields():
    submission = _make_submission()
    parsed = reddit_parser.normalize_submission(submission)

    assert parsed["id"] == "abc123"
    assert parsed["title"] == "Bold title with link"
    assert parsed["text"] == "Body code and @name mention"
    assert parsed["author"] == "author_one"
    assert parsed["subreddit"] == "test"
    assert parsed["permalink"] == "/r/test/comments/abc123/post/"
    assert parsed["url"] == "https://example.com/post"
    assert parsed["created_at"].endswith("+00:00")
    assert parsed["upvotes"] == 1
    assert parsed["comments"] == 0
    assert parsed["content_flags"] == ["nsfw"]


def test_normalize_submission_handles_missing_author_and_subreddit_object():
    class FakeAuthor:
        def __str__(self):
            return "stringified-author"

    class FakeSub:
        def __str__(self):
            return "r/mock"

    submission = _make_submission(
        author=FakeAuthor(),
        subreddit=FakeSub(),
        over_18=False,
        spoiler=True,
        removed_by_category="moderator",
    )

    parsed = reddit_parser.normalize_submission(submission)

    assert parsed["author"] == "stringified-author"
    assert parsed["subreddit"] == "r/mock"
    assert sorted(parsed["content_flags"]) == ["removed", "spoiler"]


class RedditDocumentModel(BaseModel):
    """Minimal schema to validate normalised payloads."""

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
    content_flags: List[str]

    @field_validator("created_at")
    @classmethod
    def validate_isoformat(cls, value: str) -> str:
        assert value.endswith("+00:00")
        return value


def test_normalize_submission_validates_against_pydantic_model():
    submission = _make_submission()
    parsed = reddit_parser.normalize_submission(submission)

    # Ensure our normalised output satisfies the schema expectations.
    RedditDocumentModel(**parsed)


def test_sanitize_text_handles_large_bodies():
    huge_body = "word " * 3000  # >10k characters
    submission = _make_submission(selftext=huge_body)
    parsed = reddit_parser.normalize_submission(submission)

    # The sanitiser should keep the text intact and the function should not
    # raise errors for large payloads.
    assert len(parsed["text"]) == len(huge_body.strip())


