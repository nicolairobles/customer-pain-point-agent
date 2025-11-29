"""Tests for external source tools."""

from __future__ import annotations

import os
import pytest
from unittest.mock import Mock
from typing import List, Dict, Any
from pydantic import BaseModel, field_validator

from config.settings import settings
from src.tools.google_parser import normalize_google_result, sanitize_text, parse_google_date, extract_publication_date
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


def test_google_search_tool_normalization() -> None:
    """Test that Google search results are properly normalized."""
    from unittest.mock import patch, MagicMock
    
    # Mock the Google API client
    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()
    
    mock_response = {
        "items": [
            {
                "title": "Test Result 1",
                "snippet": "This is a test snippet",
                "link": "https://example.com/1",
                "displayLink": "example.com",
                "pagemap": {
                    "metatags": [{"article:published_time": "2023-01-01"}]
                }
            },
            {
                "title": "Test Result 2", 
                "snippet": "Another test snippet",
                "link": "https://example.com/2",
                "displayLink": "example.com"
            }
        ]
    }
    
    mock_execute.return_value = mock_response
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse
    
    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(settings)
        results = tool._run("test query")
        
        assert len(results) == 2
        assert results[0]["title"] == "Test Result 1"
        assert results[0]["text"] == "This is a test snippet"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["display_url"] == "example.com"
        assert results[0]["created_at"] == "2023-01-01"
        assert results[0]["ranking_position"] == 1
        
        assert results[1]["ranking_position"] == 2
        assert results[1]["created_at"] == ""  # No date available


def test_google_search_tool_zero_results() -> None:
    """Test handling of zero search results."""
    from unittest.mock import patch, MagicMock
    
    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()
    
    mock_execute.return_value = {"items": []}
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse
    
    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(settings)
        results = tool._run("test query")
        
        assert results == []


def test_google_search_tool_quota_error_retry() -> None:
    """Test quota error handling with retry logic."""
    from unittest.mock import patch, MagicMock
    from googleapiclient.errors import HttpError
    
    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()
    
    # Create a mock HttpError for quota exceeded
    quota_error = HttpError(Mock(status=403), b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}')
    quota_error.error_details = [{"reason": "quotaExceeded"}]
    
    # Mock successful response after retry
    mock_response = {
        "items": [{
            "title": "Success Result",
            "snippet": "Success snippet",
            "link": "https://example.com",
            "displayLink": "example.com"
        }]
    }
    
    # First call raises quota error, second returns success response
    mock_execute.side_effect = [quota_error, mock_response]
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse
    
    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(settings)
        results = tool._run("test query")
        
        assert len(results) == 1
        assert results[0]["title"] == "Success Result"
        # Verify execute was called twice (initial + retry)
        assert mock_execute.call_count == 2


def test_google_search_tool_parameters() -> None:
    """Test that query parameters are properly passed to the API."""
    from unittest.mock import patch, MagicMock
    
    mock_client = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_execute = MagicMock()
    
    mock_execute.return_value = {"items": []}
    mock_list.return_value.execute = mock_execute
    mock_cse.return_value.list = mock_list
    mock_client.cse = mock_cse
    
    with patch('src.tools.google_search_tool.build', return_value=mock_client):
        tool = GoogleSearchTool.from_settings(settings)
        
        # Test with various parameters
        tool._run("test query", num=5, lang="en", site="example.com")
        
        # Verify the call was made with correct parameters
        call_args = mock_list.call_args
        assert call_args[1]["q"] == "test query"
        assert call_args[1]["num"] == 5
        assert call_args[1]["lr"] == "lang_en"
        assert call_args[1]["siteSearch"] == "example.com"


@pytest.mark.skipif(
    not (os.getenv("GOOGLE_SEARCH_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID") and 
         not os.getenv("GOOGLE_SEARCH_API_KEY", "").startswith("dummy") and
         not os.getenv("GOOGLE_SEARCH_ENGINE_ID", "").startswith("dummy")),
    reason="Requires valid Google Custom Search API credentials (not dummy values)"
)
def test_google_search_tool_integration() -> None:
    """Integration test that executes a live query and verifies results."""
    import time
    
    tool = GoogleSearchTool.from_settings(settings)
    
    start_time = time.time()
    results = tool._run("python programming", num=5)
    duration = time.time() - start_time
    
    # Should return at least 5 results (or fewer if API returns less)
    assert isinstance(results, list)
    assert len(results) >= 1  # At least some results
    
    # Verify result structure
    for result in results:
        assert "title" in result
        assert "snippet" in result
        assert "url" in result
        assert "display_url" in result
        assert "ranking_position" in result
        assert isinstance(result["ranking_position"], int)
        assert result["ranking_position"] >= 1
    
    # Should complete within reasonable time
    assert duration < 30.0  # 30 seconds max for integration test


@pytest.mark.skipif(
    not (os.getenv("GOOGLE_SEARCH_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID") and 
         not os.getenv("GOOGLE_SEARCH_API_KEY", "").startswith("dummy") and
         not os.getenv("GOOGLE_SEARCH_ENGINE_ID", "").startswith("dummy")),
    reason="Requires valid Google Custom Search API credentials (not dummy values)"
)
def test_google_search_tool_performance() -> None:
    """Performance test: benchmark execution time for multiple queries."""
    import time
    import statistics
    
    tool = GoogleSearchTool.from_settings(settings)
    
    # Test queries that should return results
    queries = [
        "python programming",
        "machine learning",
        "data science",
        "artificial intelligence",
        "web development"
    ]
    
    durations = []
    
    for query in queries:
        start_time = time.time()
        results = tool._run(query, num=3)  # Small result set for speed
        duration = time.time() - start_time
        durations.append(duration)
        
        # Basic validation that we got some results
        assert isinstance(results, list)
        assert len(results) >= 1
    
    # Calculate 95th percentile (sort and take 95th percentile)
    durations.sort()
    percentile_95 = durations[int(0.95 * len(durations))]
    
    # 95th percentile should be under 10 seconds
    assert percentile_95 < 10.0, f"95th percentile latency {percentile_95:.2f}s exceeds 10s limit"
    
    # Log performance metrics
    print(f"Performance test results:")
    print(f"Mean latency: {statistics.mean(durations):.2f}s")
    print(f"95th percentile: {percentile_95:.2f}s")
    print(f"Min/Max: {min(durations):.2f}s / {max(durations):.2f}s")


class GoogleDocumentModel(BaseModel):
    """Schema to validate normalized Google search result payloads."""

    id: str
    title: str
    text: str
    author: str
    subreddit: str
    permalink: str
    url: str
    display_url: str
    created_at: str
    upvotes: int
    comments: int
    content_flags: List[str]
    platform: str
    ranking_position: int
    search_metadata: Dict[str, Any]

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: str) -> str:
        # Allow empty string for missing dates, otherwise expect ISO format
        if value == "":
            return value
        # Should be ISO format (may or may not have timezone)
        from datetime import datetime
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        except ValueError:
            raise ValueError(f"Invalid ISO format: {value}")


def test_google_parser_sanitize_text() -> None:
    """Test HTML sanitization in Google parser."""
    # Basic HTML stripping
    assert sanitize_text("<b>Bold text</b>") == "Bold text"
    assert sanitize_text("Normal text") == "Normal text"
    
    # HTML entities
    assert sanitize_text("Price: &pound;10 &amp; &lt;more&gt;") == "Price: £10 & <more>"
    
    # Multiple whitespace
    assert sanitize_text("Text   with    spaces") == "Text with spaces"
    
    # Empty/None handling
    assert sanitize_text("") == ""
    assert sanitize_text(None) == ""


def test_google_parser_parse_date() -> None:
    """Test date parsing for various Google date formats."""
    # ISO format (should pass through)
    assert parse_google_date("2023-01-01") == "2023-01-01"
    assert parse_google_date("2023-01-01T12:00:00Z") == "2023-01-01T12:00:00Z"
    
    # Common formats
    assert parse_google_date("Jan 1, 2023").startswith("2023-01-01")
    assert parse_google_date("January 15, 2023").startswith("2023-01-15")
    
    # Unix timestamp
    result = parse_google_date("1672531200")  # 2023-01-01 00:00:00 UTC
    assert result.startswith("2023-01-01")
    
    # Invalid dates
    assert parse_google_date("") == ""
    assert parse_google_date("invalid") == ""
    assert parse_google_date(None) == ""


def test_google_parser_extract_publication_date() -> None:
    """Test extraction of publication dates from Google result items."""
    # Test with article:published_time
    item_with_published = {
        "pagemap": {
            "metatags": [{"article:published_time": "2023-01-01"}]
        }
    }
    assert extract_publication_date(item_with_published).startswith("2023-01-01")
    
    # Test with date field
    item_with_date = {
        "pagemap": {
            "metatags": [{"date": "Jan 15, 2023"}]
        }
    }
    assert extract_publication_date(item_with_date).startswith("2023-01-15")
    
    # Test with no date
    item_no_date = {"pagemap": {"metatags": [{}]}}
    assert extract_publication_date(item_no_date) == ""
    
    # Test with no pagemap
    item_no_pagemap = {}
    assert extract_publication_date(item_no_pagemap) == ""


def test_google_parser_normalize_standard_result() -> None:
    """Test normalization of standard Google search result."""
    item = {
        "title": "<b>Sample</b> Title &amp; More",
        "snippet": "This is a <em>sample</em> snippet with   extra   spaces",
        "link": "https://example.com/page",
        "displayLink": "example.com",
        "cacheId": "abc123",
        "pagemap": {
            "metatags": [{"article:published_time": "2023-01-01"}]
        }
    }
    
    result = normalize_google_result(item, 1)
    
    assert result is not None
    assert result["id"] == "abc123"
    assert result["title"] == "Sample Title & More"
    assert result["text"] == "This is a sample snippet with extra spaces"
    assert result["url"] == "https://example.com/page"
    assert result["display_url"] == "example.com"
    assert result["created_at"].startswith("2023-01-01")
    assert result["platform"] == "google_search"
    assert result["ranking_position"] == 1
    assert "search_metadata" in result


def test_google_parser_normalize_news_result() -> None:
    """Test normalization of news result with different date format."""
    item = {
        "title": "Breaking News Story",
        "snippet": "Important news content here",
        "link": "https://news.example.com/story",
        "displayLink": "news.example.com",
        "pagemap": {
            "metatags": [{"date": "Jan 15, 2023"}]
        }
    }
    
    result = normalize_google_result(item, 2)
    
    assert result is not None
    assert result["title"] == "Breaking News Story"
    assert result["created_at"].startswith("2023-01-15")
    assert result["ranking_position"] == 2


def test_google_parser_normalize_missing_fields() -> None:
    """Test normalization when optional fields are missing."""
    item = {
        "title": "Minimal Result",
        "link": "https://example.com"
    }
    
    result = normalize_google_result(item, 3)
    
    assert result is not None
    assert result["title"] == "Minimal Result"
    assert result["text"] == ""  # Missing snippet
    assert result["display_url"] == ""  # Missing displayLink
    assert result["created_at"] == ""  # No date info
    assert result["ranking_position"] == 3


def test_google_parser_skip_non_web_results() -> None:
    """Test that non-web results are skipped."""
    # Image result
    image_item = {
        "kind": "customsearch#result",
        "title": "Sample Image",
        "link": "https://example.com/image.jpg"
    }
    
    result = normalize_google_result(image_item, 1)
    assert result is None  # Should be filtered out


def test_google_parser_malformed_payload() -> None:
    """Test handling of malformed or unexpected payload structures."""
    # Completely empty item
    result = normalize_google_result({}, 1)
    assert result is not None
    assert result["title"] == ""
    assert result["text"] == ""
    
    # Malformed pagemap
    malformed_item = {
        "title": "Test",
        "pagemap": "not_a_dict"
    }
    result = normalize_google_result(malformed_item, 1)
    assert result is not None
    assert result["created_at"] == ""  # Should handle gracefully


def test_google_parser_normalize_validates_against_schema():
    """Test that normalized Google results validate against the document schema."""
    item = {
        "title": "Sample Title",
        "snippet": "Sample snippet text",
        "link": "https://example.com",
        "displayLink": "example.com",
        "cacheId": "abc123",
        "pagemap": {
            "metatags": [{"article:published_time": "2023-01-01T12:00:00Z"}]
        }
    }
    
    result = normalize_google_result(item, 1)
    assert result is not None
    
    # Validate against Pydantic model
    doc = GoogleDocumentModel(**result)
    assert doc.id == "abc123"
    assert doc.title == "Sample Title"
    assert doc.platform == "google_search"
    assert doc.ranking_position == 1
    assert isinstance(doc.search_metadata, dict)
