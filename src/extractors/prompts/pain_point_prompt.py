"""Utilities for building the pain point extraction prompt.

This module centralizes the prompt text so that every part of the system
produces identical instructions for OpenAI.  The helper functions emit a
documented JSON schema to keep the downstream parsing logic in sync with the
LLM output.
"""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import indent
from typing import Iterable, List, Mapping, Sequence

# Prompt versioning helps with auditability. Increment when intent/schema change.
PAIN_POINT_PROMPT_VERSION = "1.1.0"


def format_documents_for_prompt(documents: Iterable[Mapping[str, str]]) -> str:
    """Convert aggregated tool documents into a bullet list for the prompt.

    Args:
        documents: Each mapping is expected to expose at least ``platform``,
            ``author``, ``timestamp``, ``url`` and ``content`` keys.

    Returns:
        Human-readable bullet list that is easy for the LLM to parse.
    """

    lines: List[str] = []
    for index, doc in enumerate(documents, start=1):
        platform = doc.get("platform", "unknown-platform")
        author = doc.get("author", "unknown-author")
        timestamp = doc.get("timestamp", "unknown-timestamp")
        url = doc.get("url", "unknown-url")
        content = doc.get("content", "").strip()
        summary = doc.get("summary", "").strip()

        bullet = [
            f"{index}. Source: {platform}",
            f"   - Author: {author}",
            f"   - Timestamp: {timestamp}",
            f"   - URL: {url}",
        ]
        if summary:
            bullet.append(f"   - Summary: {summary}")
        if content:
            bullet.append("   - Content:")
            bullet.append(indent(content, prefix="     "))
        lines.append("\n".join(bullet))
    return "\n".join(lines)


@dataclass(frozen=True)
class PainPointPrompt:
    """Builder for the pain point extraction prompt template."""

    response_schema: str = """{
  "pain_points": [
    {
      "name": "string",
      "description": "string",
      "frequency": "high|medium|low",
      "examples": ["string"],
      "sources": [
        {
          "platform": "reddit|google_search",
          "url": "string",
          "timestamp": "ISO-8601 string",
          "author": "string"
        }
      ]
    }
  ],
  "analysis_notes": {
    "common_themes": ["string"],
    "data_coverage": {
      "reddit_posts_considered": 0,
      "google_results_considered": 0
    },
    "confidence": "high|medium|low",
    "content_warnings": ["string"]
  }
}"""

    def build(self, documents: Sequence[Mapping[str, str]]) -> str:
        """Generate the full prompt string given source documents.

        The prompt contains three sections:
        1. A system role that enforces tone and bias mitigation.
        2. Step-by-step instructions, including the frequency rubric.
        3. The payload of source documents followed by the required schema.
        """

        doc_block = format_documents_for_prompt(documents)

        return f"""# SYSTEM ROLE
You are a senior user-research analyst tasked with summarising customer pain points.
Operate with empathy, keep the tone professional and concise, and avoid speculation.
If the data contains sensitive or harmful content, flag it explicitly rather than amplifying it.

# EXTRACTION STEPS
1. Read every source carefully. Capture only pain points that are supported by quotations.
2. Each pain point must cite at least one source URL and author.
3. Frequency rubric:
   - high   : raised independently by 3+ distinct authors or platforms.
   - medium : appears from 2 distinct authors or platforms.
   - low    : mentioned once or inferred from a single platform.
4. Prefer direct quotes in the ``examples`` array. Keep each example under 280 characters.
5. If multiple posts repeat the same issue, merge them into one pain point and aggregate sources.
6. If content appears biased or discriminatory, note it inside ``analysis_notes.content_warnings``.
7. Respond strictly in the JSON schema provided below and do not add commentary outside it.

# SOURCE DOCUMENTS
{doc_block or 'No documents supplied. Return an empty list for pain_points.'}

# RESPONSE SCHEMA (version {PAIN_POINT_PROMPT_VERSION})
{self.response_schema}
"""
