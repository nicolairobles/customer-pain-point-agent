"""Agent responsible for reviewing and synthesizing research findings."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config.settings import Settings
from src.agent.query_processor import QueryAnalysis

_LOG = logging.getLogger(__name__)


class Analyst:
    """Reviews and synthesizes raw research findings into a final report."""

    def __init__(self, settings: Settings, llm: Optional[Any] = None) -> None:
        self.settings = settings
        self._init_error: Exception | None = None
        if llm:
            self.llm = llm
        else:
            try:
                from langchain_openai import ChatOpenAI  # type: ignore
            except Exception as exc:  # pragma: no cover - environment specific
                # Defer failure until `review()` is called so unit tests can stub
                # the analyst without requiring langchain-openai to import cleanly.
                self.llm = None
                self._init_error = exc
                return

            self.llm = ChatOpenAI(
                api_key=settings.api.openai_api_key,
                model=settings.llm.model,
                temperature=0.3,  # Slight creativity for synthesis
                timeout=60,  # Longer timeout for detailed responses
                model_kwargs={"max_tokens": 8192},  # Force max_tokens via kwargs
            )

    def review(self, analysis: QueryAnalysis, research_output: str) -> str:
        """Review research findings and generate a final answer.
        
        Args:
            analysis: The original search plan and refined query.
            research_output: The raw output from the Research Agent (likely a list of posts).
            
        Returns:
            A synthesized markdown response.
        """

        if getattr(self, "llm", None) is None:
            raise ImportError(
                "Analyst LLM is unavailable (langchain-openai import failed)."
            ) from self._init_error

        try:
            from langchain_core.messages import SystemMessage, HumanMessage  # type: ignore
        except Exception as exc:  # pragma: no cover - environment specific
            raise ImportError(
                "LangChain message classes are not available. Install `langchain` to enable analyst synthesis."
            ) from exc
        
        system_prompt = f"""You are a Senior Data Analyst reviewing raw search results to identify customer pain points.

YOUR GOAL:
Synthesize the provided raw research findings into a clear, actionable report answering the User's Original Query.

CONTEXT:
- User Query: "{analysis.refined_query}"
- What we looked for: {analysis.context_notes}
- The Raw Findings below were collected by a junior researcher.

CRITICAL FILTERING RULES:
1. ONLY use posts that DIRECTLY mention "{analysis.refined_query.split()[0] if analysis.refined_query else 'the topic'}".
2. DISCARD posts that discuss generic topics (e.g., "API issues" when we asked about "OpenAI API").
3. If a post doesn't explicitly reference the specific product/service in the query, DO NOT cite it.
4. Be STRICT - it's better to report fewer, highly relevant findings than many vague ones.

SYNTHESIS INSTRUCTIONS:
1. Group similar pain points together.
2. Highlight specific examples from the findings (cite post titles).
3. Provide a direct answer to the user's query.
4. If most findings are off-topic, honestly state: "Limited relevant data found. The following insights are based on [X] directly relevant posts out of [Y] total."

FORMAT:
- Return the final answer in clean Markdown.
- Be CONCISE: aim for 3-5 key pain points maximum.
- Use bullet points, not long paragraphs.
- ALWAYS end with a brief "Conclusion" section to ensure the report is complete.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"--- RAW RESEARCH FINDINGS ---\n\n{research_output}"),
        ]

        _LOG.info("Analyst running review on research output of length %d", len(research_output))
        response = self.llm.invoke(messages)
        
        # Log response metadata to diagnose truncation
        if hasattr(response, 'response_metadata'):
            metadata = response.response_metadata
            finish_reason = metadata.get('finish_reason', 'unknown')
            usage = metadata.get('usage', {}) or metadata.get('token_usage', {})
            _LOG.info(
                "Analyst LLM response: finish_reason=%s, completion_tokens=%s, total_tokens=%s",
                finish_reason,
                usage.get('completion_tokens', 'N/A'),
                usage.get('total_tokens', 'N/A')
            )
            if finish_reason == 'length':
                _LOG.warning("Response was truncated due to max_tokens limit!")
        
        return response.content
