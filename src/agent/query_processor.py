"""Agent responsible for preprocessing and analyzing user queries."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from config.settings import Settings


@dataclass
class QueryAnalysis:
    """Structured output from the query processor."""
    
    refined_query: str
    search_terms: List[str]
    subreddits: List[str]
    context_notes: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class QueryProcessor:
    """Analyzes user queries to determine search strategy and constraints."""

    def __init__(self, settings: Settings, llm: Optional[Any] = None) -> None:
        self.settings = settings
        if llm:
            self.llm = llm
        else:
            try:
                from langchain_openai import ChatOpenAI  # type: ignore
            except Exception as exc:  # pragma: no cover - environment specific
                raise ImportError(
                    "ChatOpenAI is not available. Install the `langchain-openai` package to enable query processing."
                ) from exc

            self.llm = ChatOpenAI(
                api_key=settings.api.openai_api_key,
                model=settings.llm.model,
                temperature=0.0,  # Deterministic for JSON extraction
                max_tokens=settings.llm.max_output_tokens,
                timeout=settings.llm.request_timeout_seconds,
            )

    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze the user query and extract search parameters."""

        try:
            from langchain_core.messages import SystemMessage, HumanMessage  # type: ignore
        except Exception as exc:  # pragma: no cover - environment specific
            raise ImportError(
                "LangChain message classes are not available. Install `langchain` to enable query processing."
            ) from exc
        
        system_prompt = """You are an expert researcher planning a search strategy for customer pain points.
        
Your goal is to analyze the User's Query and output a JSON object with the following fields:

1. "refined_query": A clean, specific version of the user's topic that will be used for searching (e.g., "ecommerce checkout bugs", "software subscription pricing issues").
   - This should be specific and search-friendly
   - Include key terms that would appear in relevant posts
2. "search_terms": A list of 3-5 keywords or short phrases that describe what to look for (e.g., ["checkout", "payment", "cart abandoned"]).
   - These help identify relevant content
3. "subreddits": A list of 4-8 relevant subreddits where this topic is likely discussed.
   - CRITICAL: Choose subreddits where the SPECIFIC topic is discussed, not just general business subreddits
   - For tech/SaaS topics: include "SaaS", "webdev", "startups", "Entrepreneur"
   - For ecommerce: include "ecommerce", "shopify", "smallbusiness", "Entrepreneur"
   - For general business: "smallbusiness", "Entrepreneur", "startups", "BusinessTips"
   - Always include at least one topic-specific subreddit and fallback to broader ones
4. "context_notes": Brief instructions emphasizing what makes a post relevant (e.g., "Only posts discussing actual checkout problems, not general ecommerce advice").

Output ONLY valid JSON.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ]

        # In a real production scenario, we might use function calling / tool binding for structured output.
        # For this MVP, extracting JSON from the content is sufficient.
        response = self.llm.invoke(messages)
        content = response.content.strip()
        
        # Strip markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            data = json.loads(content)
            return QueryAnalysis(
                refined_query=data.get("refined_query", query),
                search_terms=data.get("search_terms", []),
                subreddits=data.get("subreddits", []),
                context_notes=data.get("context_notes", ""),
            )
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return QueryAnalysis(
                refined_query=query,
                search_terms=[query],
                subreddits=["smallbusiness", "Entrepreneur", "startups", "BusinessTips"],  # Default fallback with more options
                context_notes="Could not parse specific requirements. Focus on posts directly related to the query.",
            )
