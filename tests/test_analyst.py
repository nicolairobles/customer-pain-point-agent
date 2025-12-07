"""Tests for the Analyst relevance filtering component."""

from unittest.mock import Mock, MagicMock
import pytest

from src.agent.analyst import Analyst
from config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.api = Mock()
    settings.api.openai_api_key = "test-key"
    settings.llm = Mock()
    settings.llm.model = "gpt-4"
    settings.llm.request_timeout_seconds = 30
    return settings


@pytest.fixture
def mock_llm():
    """Create mock LLM for testing."""
    llm = Mock()
    return llm


@pytest.fixture
def analyst(mock_settings, mock_llm):
    """Create Analyst instance with mocked dependencies."""
    return Analyst(mock_settings, mock_llm)


def test_analyst_keyword_filter_removes_irrelevant(mock_settings, mock_llm):
    """Test that keyword filter removes documents without query keywords."""
    analyst = Analyst(mock_settings, mock_llm)
    
    query = "Grok API issues"
    documents = [
        {
            "title": "Problems with Grok API authentication",
            "body": "I'm having trouble with the Grok API",
            "platform": "reddit"
        },
        {
            "title": "General developer problems",
            "body": "My code doesn't work",
            "platform": "reddit"
        },
        {
            "title": "How to use Grok API",
            "body": "Tutorial for beginners",
            "platform": "reddit"
        }
    ]
    
    # Should filter out the middle document as it doesn't mention Grok or API
    filtered = analyst.review_and_filter_results(query, documents)
    
    # Should keep documents that mention Grok or API
    assert len(filtered) <= len(documents)
    assert any("grok" in doc.get("title", "").lower() or "grok" in doc.get("body", "").lower() for doc in filtered)


def test_analyst_empty_documents(mock_settings, mock_llm):
    """Test analyst handles empty document list."""
    analyst = Analyst(mock_settings, mock_llm)
    
    result = analyst.review_and_filter_results("test query", [])
    assert result == []


def test_analyst_extract_keywords(mock_settings, mock_llm):
    """Test keyword extraction from query."""
    analyst = Analyst(mock_settings, mock_llm)
    
    # Test basic keyword extraction
    keywords = analyst._extract_keywords("Pain points with Grok API")
    assert "grok" in keywords or "api" in keywords
    
    # Test stopword removal
    keywords = analyst._extract_keywords("What are the issues with billing")
    assert "the" not in keywords
    assert "billing" in keywords


def test_analyst_is_specific_entity_query(mock_settings, mock_llm):
    """Test detection of specific entity queries."""
    analyst = Analyst(mock_settings, mock_llm)
    
    # Should detect API queries
    assert analyst._is_specific_entity_query("Grok API issues")
    assert analyst._is_specific_entity_query("Problems with StripeAPI")
    
    # Should detect SDK queries
    assert analyst._is_specific_entity_query("TensorFlow SDK problems")
    
    # General queries should not be detected as specific
    assert not analyst._is_specific_entity_query("general coding problems")


def test_analyst_keyword_filter_all_documents_relevant(mock_settings, mock_llm):
    """Test that all documents pass when they mention keywords."""
    analyst = Analyst(mock_settings, mock_llm)
    
    query = "coding problems"
    documents = [
        {"title": "My coding issue", "body": "Problems with code", "platform": "reddit"},
        {"title": "Coding bug", "body": "Found a problem", "platform": "reddit"},
    ]
    
    filtered = analyst.review_and_filter_results(query, documents)
    
    # All documents mention either "coding" or "problems" so should be kept
    assert len(filtered) == len(documents)


def test_analyst_llm_filter_integration(mock_settings):
    """Test LLM-based filtering for specific entities."""
    # Mock LLM to return relevant document indices
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = "0,2"  # Keep documents 0 and 2
    mock_llm.invoke.return_value = mock_response
    
    analyst = Analyst(mock_settings, mock_llm)
    
    query = "Grok API issues"
    documents = [
        {"title": "Grok API auth problems", "body": "Grok API doesn't work", "platform": "reddit"},
        {"title": "General API stuff", "body": "APIs are hard", "platform": "reddit"},
        {"title": "Grok API rate limits", "body": "Hit Grok API limits", "platform": "reddit"},
    ]
    
    # This should trigger LLM filtering because query mentions specific API
    filtered = analyst._llm_relevance_filter(query, documents)
    
    # Should have called LLM
    assert mock_llm.invoke.called
    
    # Should return documents 0 and 2 as specified by mock
    assert len(filtered) == 2
    assert filtered[0] == documents[0]
    assert filtered[1] == documents[2]


def test_analyst_llm_filter_handles_none_response(mock_settings):
    """Test LLM filter handles NONE response."""
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = "NONE"
    mock_llm.invoke.return_value = mock_response
    
    analyst = Analyst(mock_settings, mock_llm)
    
    documents = [{"title": "Test", "body": "Content", "platform": "reddit"}]
    filtered = analyst._llm_relevance_filter("test query", documents)
    
    # Should return empty list when LLM says NONE are relevant
    assert filtered == []


def test_analyst_llm_filter_handles_error(mock_settings):
    """Test LLM filter fails open on error."""
    mock_llm = Mock()
    mock_llm.invoke.side_effect = Exception("API error")
    
    analyst = Analyst(mock_settings, mock_llm)
    
    documents = [{"title": "Test", "body": "Content", "platform": "reddit"}]
    filtered = analyst._llm_relevance_filter("test query", documents)
    
    # Should return all documents on error (fail open)
    assert filtered == documents
