"""Helpers for normalising raw Reddit submissions into structured dictionaries.

The RedditTool is responsible for orchestrating the search workflow, but the
story "1.2.3 – Implement Reddit Data Parsing" called out a dedicated parser
with markdown sanitisation, ISO 8601 timestamps, and resilience around missing
data.  Centralising the logic here allows tests to target the parsing rules
directly while keeping `reddit_tool.py` focused on network orchestration.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import logging

LOGGER = logging.getLogger(__name__)


_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_MARKDOWN_BOLD_ITALIC_RE = re.compile(r"(\*\*|\*|__|_)(.*?)\1")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_MULTISPACE_RE = re.compile(r"\s+")
_USER_MENTION_RE = re.compile(r"\bu/([A-Za-z0-9_-]+)")


def sanitize_text(raw_text: Optional[str]) -> str:
    """Return a markdown-lite sanitised text string.

    The sanitiser intentionally stays simple (regex based) to avoid pulling in
    heavier markdown libraries.  It strips link syntax, converts bold/italic to
    plain text, swaps ``u/`` mentions for a friendlier ``@user`` form, and
    collapses whitespace.  This keeps downstream prompt crafting predictable.
    """

    if not raw_text:
        return ""

    # Convert to plain string and unescape common HTML entities emitted by PRAW.
    text = html.unescape(str(raw_text))

    # Replace markdown links "[label](url)" with just "label" whilst preserving
    # the informative part of the text.
    text = _MARKDOWN_LINK_RE.sub(r"\1", text)

    # Strip bold / italic markers but keep the enclosed text.  The regex is
    # intentionally non-greedy to avoid spanning paragraphs.
    text = _MARKDOWN_BOLD_ITALIC_RE.sub(r"\2", text)

    # Inline code blocks get unwrapped – they rarely carry literal formatting
    # value for our summariser.
    text = _INLINE_CODE_RE.sub(r"\1", text)

    # Normalise Reddit user mentions (u/username) into a friendlier @username.
    text = _USER_MENTION_RE.sub(r"@\1", text)

    # Collapse multiple whitespace characters into a single space.
    text = _MULTISPACE_RE.sub(" ", text)

    return text.strip()


def sanitize_url(raw_url: Optional[str]) -> str:
    """Normalise URLs to trimmed strings (empty string for missing values)."""

    if not raw_url:
        return ""
    return str(raw_url).strip()


def to_iso8601(timestamp: Optional[Any]) -> str:
    """Convert a unix timestamp to an ISO 8601 string in UTC.

    Returns an empty string for falsy / unparsable values rather than raising.
    """

    if timestamp in (None, "", 0):
        return ""

    try:
        ts_float = float(timestamp)
    except (TypeError, ValueError):
        LOGGER.debug("Unable to coerce timestamp %r to float", timestamp)
        return ""

    try:
        dt = datetime.fromtimestamp(ts_float, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        LOGGER.debug("Timestamp out of range for conversion: %r", timestamp)
        return ""

    return dt.isoformat()


def extract_subreddit(submission: Any) -> str:
    """Return a human readable subreddit identifier from a submission object."""

    sub_attr = getattr(submission, "subreddit", None)
    if isinstance(sub_attr, str):
        return sub_attr

    pref = getattr(submission, "subreddit_name_prefixed", None)
    if pref:
        return str(pref)

    if sub_attr is not None:
        try:
            return str(sub_attr)
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.debug("Failed to serialise subreddit attribute: %r", sub_attr)

    return ""


def extract_author(submission: Any) -> str:
    """Safely determine the author display string for a submission."""

    author = getattr(submission, "author", None)
    if isinstance(author, str):
        return author

    if author is not None:
        name = getattr(author, "name", None)
        if name:
            return str(name)
        try:
            return str(author)
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.debug("Failed to serialise author attribute: %r", author)

    return "unknown-author"


def build_content_flags(submission: Any) -> List[str]:
    """Return a list of content flags (nsfw, spoiler, removed)."""

    flags: List[str] = []
    if getattr(submission, "over_18", False):
        flags.append("nsfw")
    if getattr(submission, "spoiler", False):
        flags.append("spoiler")
    if getattr(submission, "removed_by_category", None):
        flags.append("removed")
    return flags


def normalize_submission(submission: Any) -> Dict[str, Any]:
    """Convert a PRAW submission-like object into the agent's schema."""

    # All sanitisation helpers purposefully shelter us from missing attributes
    # so the resulting dictionary is safe to serialise downstream.
    return {
        "id": str(getattr(submission, "id", "") or "").strip(),
        "title": sanitize_text(getattr(submission, "title", "")),
        "text": sanitize_text(getattr(submission, "selftext", "")),
        "author": extract_author(submission),
        "subreddit": extract_subreddit(submission),
        "permalink": sanitize_url(getattr(submission, "permalink", "")),
        "url": sanitize_url(getattr(submission, "url", "")),
        "created_at": to_iso8601(getattr(submission, "created_utc", None)),
        "upvotes": int(getattr(submission, "score", 0) or 0),
        "comments": int(getattr(submission, "num_comments", 0) or 0),
        "content_flags": build_content_flags(submission),
    }


