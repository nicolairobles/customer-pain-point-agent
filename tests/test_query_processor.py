"""Unit tests for the QueryProcessor agent."""

import json
from unittest.mock import MagicMock, Mock

import pytest
from langchain_core.messages import AIMessage

from config.settings import Settings
from src.agent.query_processor import QueryProcessor, QueryAnalysis


@pytest.fixture
def mock_settings():
    settings = Mock(spec=Settings)
    settings.api = Mock()
    settings.api.openai_api_key = "fake_key"
    settings.llm = Mock()
    settings.llm.model = "gpt-3.5-turbo"
    settings.llm.max_output_tokens = 1000
    settings.llm.request_timeout_seconds = 30
    return settings


@pytest.fixture
def mock_llm():
    return Mock()


def test_analyze_success(mock_settings, mock_llm):
    """Test successful JSON parsing from LLM response."""
    processor = QueryProcessor(mock_settings, llm=mock_llm)
    
    mock_response_content = json.dumps({
        "refined_query": "billing issues",
        "search_terms": ["invoice fail", "chargeback"],
        "subreddits": ["saas", "hacker_news"],
        "context_notes": "Look for recent posts."
    })
    mock_llm.invoke.return_value = AIMessage(content=mock_response_content)

    result = processor.analyze("issues with billing")

    assert isinstance(result, QueryAnalysis)
    assert result.refined_query == "billing issues"
    assert "invoice fail" in result.search_terms
    assert "saas" in result.subreddits
    assert result.context_notes == "Look for recent posts."


def test_analyze_json_markdown_handling(mock_settings, mock_llm):
    """Test handling of markdown code blocks in LLM response."""
    processor = QueryProcessor(mock_settings, llm=mock_llm)
    
    mock_response_content = """```json
    {
        "refined_query": "clean",
        "search_terms": [],
        "subreddits": [],
        "context_notes": ""
    }
    ```"""
    mock_llm.invoke.return_value = AIMessage(content=mock_response_content)

    result = processor.analyze("anything")
    assert result.refined_query == "clean"


def test_analyze_fallback(mock_settings, mock_llm):
    """Test fallback when JSON parsing fails."""
    processor = QueryProcessor(mock_settings, llm=mock_llm)
    
    mock_llm.invoke.return_value = AIMessage(content="Not valid JSON")

    result = processor.analyze("original query")
    
    assert result.refined_query == "original query"
    assert result.search_terms == ["original query"]
    # Fallback defaults
    assert "smallbusiness" in result.subreddits
