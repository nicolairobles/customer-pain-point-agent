"""Helpers for normalising raw Google Custom Search results into structured dictionaries.

The GoogleSearchTool is responsible for orchestrating the search workflow, but the
story "2.2.3 – Implement Google Data Parsing" called out a dedicated parser
with HTML sanitisation, ISO 8601 timestamps, and resilience around missing
data. Centralising the logic here allows tests to target the parsing rules
directly while keeping `google_search_tool.py` focused on network orchestration.
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)

# Regex patterns for HTML tag removal and text cleaning
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MULTISPACE_RE = re.compile(r"\s+")


def sanitize_text(raw_text: Optional[str]) -> str:
    """Return HTML-sanitised text string from Google search results.

    Strips HTML tags, unescapes entities, and collapses whitespace to present
    clean text suitable for downstream processing.
    """
    if not raw_text:
        return ""

    # Convert to string first
    text = str(raw_text)

    # Remove HTML tags first
    text = _HTML_TAG_RE.sub("", text)

    # Then unescape HTML entities
    text = html.unescape(text)

    # Collapse multiple whitespace characters into a single space
    text = _MULTISPACE_RE.sub(" ", text)

    return text.strip()


def sanitize_url(raw_url: Optional[str]) -> str:
    """Normalise URLs to trimmed strings (empty string for missing values)."""
    if not raw_url:
        return ""
    return str(raw_url).strip()


def parse_google_date(date_str: Optional[str]) -> str:
    """Parse various Google date formats and return ISO 8601 string.

    Handles common Google date formats like:
    - "2023-01-01" (already ISO)
    - "Jan 1, 2023"
    - Unix timestamps
    - Empty/missing values

    Returns empty string for unparseable dates.
    """
    if not date_str or date_str.strip() == "":
        return ""

    date_str = date_str.strip()

    # Try ISO format first (already what we want)
    try:
        # Validate it's a proper ISO date
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_str
    except (ValueError, AttributeError):
        pass

    # Try common date formats
    date_formats = [
        "%b %d, %Y",  # "Jan 1, 2023"
        "%B %d, %Y",  # "January 1, 2023"
        "%Y-%m-%d",   # "2023-01-01"
        "%m/%d/%Y",   # "1/1/2023"
        "%d/%m/%Y",   # "1/1/2023"
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Assume dates without timezone are UTC
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue

    # Try unix timestamp
    try:
        ts_float = float(date_str)
        dt = datetime.fromtimestamp(ts_float, tz=timezone.utc)
        return dt.isoformat()
    except (ValueError, TypeError, OverflowError, OSError):
        pass

    LOGGER.debug("Unable to parse date: %r", date_str)
    return ""


def extract_publication_date(item: Dict[str, Any]) -> str:
    """Extract publication date from Google search result item.

    Checks multiple possible locations where Google might store dates:
    - pagemap.metatags[].article:published_time
    - pagemap.metatags[].date
    - pagemap.metatags[].publish-date
    - pagemap.metatags[].pubdate
    """
    pagemap = item.get("pagemap", {})
    if not isinstance(pagemap, dict):
        return ""
        
    metatags = pagemap.get("metatags", [])
    if not isinstance(metatags, list) or not metatags:
        return ""

    # Check first metatags object for various date fields
    meta = metatags[0] if metatags else {}
    if not isinstance(meta, dict):
        return ""

    date_candidates = [
        meta.get("article:published_time"),
        meta.get("date"),
        meta.get("publish-date"),
        meta.get("pubdate"),
        meta.get("article:modified_time"),
    ]

    for date_str in date_candidates:
        if date_str:
            parsed = parse_google_date(date_str)
            if parsed:
                return parsed

    return ""


def normalize_google_result(item: Dict[str, Any], position: int) -> Optional[Dict[str, Any]]:
    """Convert a Google Custom Search result item into the agent's cross-source schema.

    Extracts core fields, sanitizes text, normalizes dates, and tags with platform
    information for consistent downstream processing.
    """
    # Skip non-web results (images, videos, etc.) - focus on web pages
    kind = item.get("kind", "")
    if kind and not kind.endswith("#searchResult"):
        LOGGER.debug("Skipping non-web result: %s", kind)
        return None  # Filtered out by caller

    return {
        "id": str(item.get("cacheId", item.get("link", "")) or "").strip(),
        "title": sanitize_text(item.get("title", "")),
        "text": sanitize_text(item.get("snippet", "")),
        "author": "",  # Google doesn't provide author info
        "subreddit": "",  # Not applicable for Google search
        "permalink": sanitize_url(item.get("link", "")),
        "url": sanitize_url(item.get("link", "")),
        "display_url": sanitize_url(item.get("displayLink", "")),
        "created_at": extract_publication_date(item),
        "upvotes": 0,  # Not applicable for Google search
        "comments": 0,  # Not applicable for Google search
        "content_flags": [],  # No content flags for Google search
        "platform": "google_search",
        "ranking_position": position,
        "search_metadata": {
            "kind": item.get("kind", ""),
            "html_title": item.get("htmlTitle", ""),
            "html_snippet": item.get("htmlSnippet", ""),
        }
    }
