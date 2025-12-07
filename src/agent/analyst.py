"""Agent responsible for reviewing and synthesizing research findings."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from config.settings import Settings
from src.agent.query_processor import QueryAnalysis

_LOG = logging.getLogger(__name__)


class Analyst:
    """Reviews and synthesizes raw research findings into a final report."""

    def __init__(self, settings: Settings, llm: Optional[Any] = None) -> None:
        self.settings = settings
        if llm:
            self.llm = llm
        else:
            self.llm = ChatOpenAI(
                api_key=settings.api.openai_api_key,
                model=settings.llm.model,
                temperature=0.3,  # Slight creativity for synthesis
                max_tokens=settings.llm.max_output_tokens,
                timeout=settings.llm.request_timeout_seconds,
            )

    def review(self, analysis: QueryAnalysis, research_output: str) -> str:
        """Review research findings and generate a final answer.
        
        Args:
            analysis: The original search plan and refined query.
            research_output: The raw output from the Research Agent (likely a list of posts).
            
        Returns:
            A synthesized markdown response.
        """
        
        system_prompt = f"""You are a Senior Data Analyst reviewing raw search results to identify customer pain points.

YOUR GOAL:
Synthesize the provided raw research findings into a clear, actionable report answering the User's Original Query.

CONTEXT:
- User Query: "{analysis.refined_query}"
- What we looked for: {analysis.context_notes}
- The Raw Findings below were collected by a junior researcher.

INSTRUCTIONS:
1. Filter out irrelevant posts (spam, off-topic, or low quality).
2. Group similar pain points together.
3. Highlight specific examples from the findings (cite them if possible).
4. Provide a direct answer to the user's query.
5. If the findings are empty or irrelevant, honestly state that no strong evidence was found.

FORMAT:
Return the final answer in clean Markdown. Use bullet points and sections.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"--- RAW RESEARCH FINDINGS ---\n\n{research_output}"),
        ]

        _LOG.info("Analyst running review on research output of length %d", len(research_output))
        response = self.llm.invoke(messages)
        return response.content
