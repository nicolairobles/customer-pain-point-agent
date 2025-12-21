"""Pain point extraction routines powered by OpenAI."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Sequence

from pydantic import BaseModel, Field, ValidationError

from config.settings import settings
from src.extractors.prompts import PainPointPrompt
from src.services import LLMResult, OpenAIService, OpenAIServiceError

LOGGER = logging.getLogger(__name__)


class PainPointSource(BaseModel):
    """Metadata describing where a pain point observation originated."""

    platform: str
    url: str
    timestamp: str
    author: str


class PainPoint(BaseModel):
    """Structured representation of a customer pain point."""

    name: str
    description: str
    frequency: str = Field(default="low", pattern=r"^(high|medium|low)$")
    examples: List[str]
    sources: List[PainPointSource]
    sentiment: str = Field(default="neutral", pattern=r"^(positive|neutral|negative)$")
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def extract_pain_points(
    raw_documents: Sequence[Mapping[str, Any]],
    *,
    service: OpenAIService | None = None,
    batch_size: int = 10,
) -> List[PainPoint]:
    """Transform raw tool outputs into structured pain points.

    Args:
        raw_documents: Normalised documents emitted by the search tools.
        service: Optional OpenAI service instance, primarily for testing.
        batch_size: Maximum number of documents to include per LLM call.

    Returns:
        List of deduplicated :class:`PainPoint` instances.
    """

    if not raw_documents:
        LOGGER.info("No documents supplied; returning empty pain point list.")
        return []

    llm_service = service or OpenAIService.from_settings(settings)
    prompt_builder = PainPointPrompt()

    collected: List[PainPoint] = []
    for batch_index, doc_batch in enumerate(_chunk(raw_documents, batch_size), start=1):
        prompt_text = prompt_builder.build(doc_batch)
        LOGGER.debug("Dispatching LLM request for batch %s with %s documents", batch_index, len(doc_batch))

        try:
            result = llm_service.generate(prompt_text)
        except OpenAIServiceError as exc:  # pragma: no cover - integration safety
            LOGGER.error(
                "OpenAI call failed for batch %s. Partial results will continue. Error: %s",
                batch_index,
                exc,
            )
            continue

        _log_usage(batch_index, result)

        points = _parse_llm_response(result)
        if not points:
            continue

        enriched = [_post_process(point) for point in points]
        collected.extend(enriched)

    deduped = deduplicate_pain_points(collected)
    LOGGER.info("Extracted %s unique pain points", len(deduped))
    return deduped


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _parse_llm_response(result: LLMResult) -> List[PainPoint]:
    """Safely parse the LLM response into :class:`PainPoint` objects."""

    try:
        payload = json.loads(result.text)
    except json.JSONDecodeError as exc:
        LOGGER.warning("Failed to decode LLM response as JSON: %s", exc)
        return []

    raw_points = payload.get("pain_points", []) if isinstance(payload, Mapping) else []
    parsed: List[PainPoint] = []
    for entry in raw_points:
        try:
            parsed.append(PainPoint(**entry))
        except ValidationError as exc:
            LOGGER.warning("Skipping invalid pain point entry: %s", exc)
    return parsed


def _post_process(point: PainPoint) -> PainPoint:
    """Compute sentiment and normalise frequency based on source coverage."""

    combined_text = " ".join(point.examples + [point.description]).lower()
    sentiment = _score_sentiment(combined_text)

    unique_sources = {(src.platform.lower(), src.author.lower(), src.url) for src in point.sources}
    frequency = _calculate_frequency_tag(len(unique_sources))

    # Create updated point with computed frequency for relevance calculation
    updated_point = point.model_copy(update={"frequency": frequency})
    relevance = _calculate_relevance_score(updated_point)

    return updated_point.model_copy(update={"sentiment": sentiment, "relevance": relevance})


def _chunk(iterable: Sequence[Mapping[str, Any]], size: int) -> Iterator[Sequence[Mapping[str, Any]]]:
    """Yield non-overlapping chunks from *iterable* with at most *size* items."""

    if size <= 0:
        raise ValueError("batch_size must be positive")

    start = 0
    total = len(iterable)
    while start < total:
        end = min(start + size, total)
        yield iterable[start:end]
        start = end


def _calculate_frequency_tag(source_count: int) -> str:
    """Map the number of unique sources to the project frequency rubric."""

    if source_count >= 3:
        return "high"
    if source_count == 2:
        return "medium"
    return "low"


def _calculate_relevance_score(point: PainPoint) -> float:
    """Calculate a relevance score based on source diversity, recency, and frequency."""

    # Base score from number of sources (0.0 to 0.4)
    source_count = len(point.sources)
    source_score = min(source_count / 10.0, 0.4)  # Cap at 10 sources for max score

    # Platform diversity bonus (0.0 to 0.3)
    platforms = {src.platform.lower() for src in point.sources}
    platform_score = min(len(platforms) / 3.0, 0.3)  # Max score for 3+ platforms

    # Frequency bonus (0.0 to 0.3)
    frequency_multipliers = {"low": 0.1, "medium": 0.2, "high": 0.3}
    frequency_score = frequency_multipliers.get(point.frequency, 0.0)

    return min(source_score + platform_score + frequency_score, 1.0)


_NEGATIVE_TOKENS = {"error", "fail", "issue", "bug", "hate", "angry", "frustrated"}
_POSITIVE_TOKENS = {"great", "love", "excellent", "helpful", "awesome", "fantastic"}


def _score_sentiment(text: str) -> str:
    """Derive a coarse sentiment label from the provided text."""

    negative_hits = sum(token in text for token in _NEGATIVE_TOKENS)
    positive_hits = sum(token in text for token in _POSITIVE_TOKENS)

    if negative_hits > positive_hits:
        return "negative"
    if positive_hits > negative_hits:
        return "positive"
    return "neutral"


def _log_usage(batch_index: int, result: LLMResult) -> None:
    """Emit structured logging for token usage and estimated cost."""

    usage = result.usage
    LOGGER.info(
        "Batch %s processed in %.2fs | tokens=%s | cost_usd=%s",
        batch_index,
        result.latency_seconds,
        usage.total_tokens,
        usage.cost_usd,
    )


def deduplicate_pain_points(pain_points: Iterable[PainPoint]) -> List[PainPoint]:
    """Remove duplicate pain points while preserving metadata."""

    buckets: Dict[str, PainPoint] = {}
    for point in pain_points:
        key = point.name.strip().lower()
        existing = buckets.get(key)
        if existing is None:
            buckets[key] = point
            continue

        merged_sources = _merge_sources(existing.sources, point.sources)
        merged_examples = _merge_examples(existing.examples, point.examples)
        sentiment = _score_sentiment(" ".join(merged_examples + [existing.description, point.description]).lower())
        frequency = _calculate_frequency_tag(len(merged_sources))

        preferred_description = max([existing.description, point.description], key=len)

        updated_sources = list(merged_sources.values())
        updated_point = existing.model_copy(
            update={
                "description": preferred_description,
                "examples": merged_examples,
                "sources": updated_sources,
                "frequency": frequency,
                "sentiment": sentiment,
            }
        )
        relevance = _calculate_relevance_score(updated_point)
        buckets[key] = updated_point.model_copy(update={"relevance": relevance})

    return list(buckets.values())


def _merge_sources(
    left: Sequence[PainPointSource],
    right: Sequence[PainPointSource],
) -> Dict[tuple[str, str, str], PainPointSource]:
    """Merge sources keeping unique platform/author/url combinations."""

    merged: Dict[tuple[str, str, str], PainPointSource] = {}
    for collection in (left, right):
        for source in collection:
            key = (source.platform.lower(), source.author.lower(), source.url)
            merged[key] = source
    return merged


def _merge_examples(left: Sequence[str], right: Sequence[str]) -> List[str]:
    """Combine example quotes while preserving order and removing duplicates."""

    seen = set()
    merged: List[str] = []
    for example in list(left) + list(right):
        normalised = example.strip()
        if normalised.lower() in seen:
            continue
        seen.add(normalised.lower())
        merged.append(normalised)
    return merged
