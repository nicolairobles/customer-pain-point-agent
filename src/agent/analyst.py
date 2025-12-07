"""Analyst component that reviews and filters research results for relevance.

This module implements a post-processing step that ensures search results
are actually relevant to the user's query before they are included in the
final analysis.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Sequence

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from config.settings import Settings

LOGGER = logging.getLogger(__name__)

# Minimum length for a keyword to be considered an "entity keyword" (e.g., "grok api", "stripe")
# Shorter keywords like "api", "sdk" are too generic and could match irrelevant content
MIN_ENTITY_KEYWORD_LENGTH = 6


class Analyst:
    """Reviews research output and filters results for relevance to the query."""

    def __init__(self, settings: Settings, llm: Any | None = None) -> None:
        self.settings = settings
        if llm:
            self.llm = llm
        else:
            self.llm = ChatOpenAI(
                api_key=settings.api.openai_api_key,
                model=settings.llm.model,
                temperature=0.0,  # Deterministic for filtering
                max_tokens=2000,
                timeout=settings.llm.request_timeout_seconds,
            )

    def review_and_filter_results(
        self, 
        query: str, 
        documents: Sequence[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Review research results and filter for relevance to the query.
        
        Args:
            query: The original user query
            documents: List of documents from search tools
            
        Returns:
            Filtered list of documents that are relevant to the query
        """
        if not documents:
            LOGGER.info("No documents to review")
            return []

        LOGGER.info(f"Analyst running review on research output of length {sum(len(str(d)) for d in documents)}")
        
        # First, do a fast keyword-based filter to remove obviously irrelevant results
        query_keywords = self._extract_keywords(query)
        potentially_relevant = self._keyword_filter(documents, query_keywords)
        
        if not potentially_relevant:
            LOGGER.warning(f"Keyword filter removed all {len(documents)} documents - none mentioned query terms")
            return []
        
        if len(potentially_relevant) < len(documents):
            LOGGER.info(
                f"Keyword filter: {len(documents)} documents -> {len(potentially_relevant)} potentially relevant"
            )
        
        # For queries about specific APIs or products, use LLM for deeper relevance check
        if self._is_specific_entity_query(query):
            relevant = self._llm_relevance_filter(query, potentially_relevant)
            LOGGER.info(
                f"LLM filter: {len(potentially_relevant)} documents -> {len(relevant)} relevant"
            )
            return relevant
        
        # For general queries, keyword filtering is sufficient
        return potentially_relevant

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract key terms from the query for relevance checking."""
        # Remove common words and extract meaningful terms
        stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'when', 'what', 'where', 'why', 'how',
            'about', 'pain', 'points', 'issues', 'problems', 'report', 'developers',
            'calling', 'using', 'users', 'customers'
        }
        
        # Extract words, convert to lowercase, remove stopwords
        words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        # Also extract multi-word phrases that look like API names (CamelCase or "X API")
        api_pattern = r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b|(\w+\s+API)\b'
        api_matches = re.findall(api_pattern, query)
        for match in api_matches:
            api_name = match[0] or match[1]
            if api_name:
                keywords.append(api_name.lower())
        
        return keywords

    def _keyword_filter(
        self, 
        documents: Sequence[Dict[str, Any]], 
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Fast filter that removes documents that don't mention query keywords.
        
        For specific entity queries (e.g., "Grok API"), requires the entity name
        to be present. For general queries, requires at least one keyword.
        """
        if not keywords:
            # If no keywords extracted, return all documents
            return list(documents)
        
        # Find the most specific keywords (multi-word phrases, or unique entity names)
        # These should be present for the document to be relevant
        entity_keywords = [k for k in keywords if ' ' in k or len(k) > MIN_ENTITY_KEYWORD_LENGTH]
        
        # If we have entity keywords, use strict matching (require entity name)
        # Otherwise use lenient matching (require any keyword)
        use_strict_matching = len(entity_keywords) > 0
        
        filtered = []
        for doc in documents:
            # Check title, body/content, and summary
            text_fields = []
            if 'title' in doc:
                text_fields.append(str(doc['title']))
            if 'body' in doc:
                text_fields.append(str(doc['body']))
            if 'content' in doc:
                text_fields.append(str(doc['content']))
            if 'summary' in doc:
                text_fields.append(str(doc['summary']))
            
            combined_text = ' '.join(text_fields).lower()
            
            if use_strict_matching:
                # For specific entities, require the entity name to be mentioned
                if any(entity_kw in combined_text for entity_kw in entity_keywords):
                    filtered.append(doc)
            else:
                # For general queries, any keyword match is sufficient
                if any(keyword in combined_text for keyword in keywords):
                    filtered.append(doc)
        
        return filtered

    def _is_specific_entity_query(self, query: str) -> bool:
        """Check if query is about a specific product/API vs general topic."""
        # Queries about specific APIs, products, or services need deeper validation
        # Look for patterns that indicate a specific named entity
        
        # Check for API/SDK/library mentions (case insensitive)
        if re.search(r'\bapi\b', query, re.IGNORECASE):
            return True
        if re.search(r'\bsdk\b', query, re.IGNORECASE):
            return True
        
        # Check for CamelCase names (product names like "StripeAPI", "TensorFlow")
        # Must have at least 2 capital letters to avoid matching common words
        if re.search(r'\b[A-Z][a-z]*[A-Z][a-zA-Z]*\b', query):
            return True
        
        # Check for version numbers
        if re.search(r'\bversion\b|\bv\d+\b', query, re.IGNORECASE):
            return True
        
        return False

    def _llm_relevance_filter(
        self, 
        query: str, 
        documents: Sequence[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use LLM to check if documents are actually about the query topic."""
        if len(documents) > 20:
            # Don't process too many at once - take top scoring ones
            documents = documents[:20]
        
        # Build a concise summary of each document for LLM review
        doc_summaries = []
        for i, doc in enumerate(documents):
            title = doc.get('title', '')
            body = doc.get('body', doc.get('content', ''))
            # Limit body length
            body_preview = body[:500] if body else ''
            doc_summaries.append(f"{i}. Title: {title}\n   Content preview: {body_preview}")
        
        docs_text = '\n\n'.join(doc_summaries)
        
        system_prompt = f"""You are a relevance filter for search results.

User Query: "{query}"

Your task: Review each document and determine if it is ACTUALLY about the specific topic in the query.

IMPORTANT: 
- If the query mentions a specific API, product, or service by name (like "Grok API"), 
  the document MUST explicitly mention that specific name.
- General discussions about APIs or similar topics are NOT relevant if they don't mention 
  the specific entity from the query.
- Be strict: only mark as relevant if the document is clearly about the query topic.

Output format: Return ONLY a comma-separated list of relevant document numbers (e.g., "0,2,5").
If no documents are relevant, return "NONE".
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Documents to review:\n\n{docs_text}"),
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            if content == "NONE" or not content:
                return []
            
            # Parse comma-separated indices
            try:
                relevant_indices = [int(idx.strip()) for idx in content.split(',')]
                filtered = [documents[i] for i in relevant_indices if 0 <= i < len(documents)]
                return filtered
            except (ValueError, IndexError) as e:
                LOGGER.warning(f"Failed to parse LLM relevance response: {content}. Error: {e}")
                # On parse error, be conservative and return all documents
                return list(documents)
                
        except Exception as e:
            LOGGER.error(f"LLM relevance check failed: {e}")
            # On error, return all documents (fail open)
            return list(documents)
