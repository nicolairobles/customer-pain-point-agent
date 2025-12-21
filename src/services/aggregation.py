"""Cross-source aggregation and scoring for tool outputs."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from config.settings import Settings


@dataclass
class AggregationResult:
    """Return type for aggregated tool outputs."""

    items: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class CrossSourceAggregator:
    """Merge, deduplicate, and score results from multiple tools."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        agg_settings = getattr(settings, "aggregation", None)
        self.recency_weight = getattr(agg_settings, "recency_weight", 0.55)
        self.engagement_weight = getattr(agg_settings, "engagement_weight", 0.45)
        self.max_item_age_days = getattr(agg_settings, "max_item_age_days", 365)
        self.near_duplicate_threshold = getattr(agg_settings, "near_duplicate_threshold", 0.82)
        self.reddit_source_weight = getattr(agg_settings, "reddit_source_weight", 1.0)
        self.google_source_weight = getattr(agg_settings, "google_source_weight", 0.9)
        self.default_source_weight = getattr(agg_settings, "default_source_weight", 0.75)

    def aggregate(
        self,
        items: Sequence[Mapping[str, Any]] | None,
        *,
        errors: Sequence[str] | None = None,
    ) -> AggregationResult:
        """Aggregate and score tool outputs.

        Args:
            items: Iterable of tool results.
            errors: Optional list of tool error strings to track provenance failures.
        """

        start_time = time.perf_counter()
        normalized: List[Dict[str, Any]] = []
        for item in items or []:
            if not isinstance(item, Mapping):
                continue
            normalized.append(self._normalize_item(item))

        merged: List[Dict[str, Any]] = []
        url_index: Dict[str, int] = {}
        similarity_merges = 0
        url_merges = 0

        for item in normalized:
            url_key = item.get("_canonical_url", "")
            existing_idx = url_index.get(url_key) if url_key else None
            if existing_idx is not None:
                merged_item = self._merge_items(merged[existing_idx], item, reason="canonical_url")
                merged[existing_idx] = merged_item
                url_merges += 1
                continue

            similar_idx = self._find_similar(merged, item)
            if similar_idx is not None:
                merged_item = self._merge_items(merged[similar_idx], item, reason="similar_text")
                merged[similar_idx] = merged_item
                similarity_merges += 1
                continue

            if url_key:
                url_index[url_key] = len(merged)
            merged.append(item)

        scored = [self._score_item(item) for item in merged]
        scored.sort(key=lambda entry: entry.get("aggregation_score", 0.0), reverse=True)

        processing_time = time.perf_counter() - start_time
        metadata = {
            "input_items": len(items or []),
            "deduped_items": len(scored),
            "deduped_by_url": url_merges,
            "deduped_by_similarity": similarity_merges,
            "errors": list(errors or []),
            "processing_time_seconds": round(processing_time, 4),
            "source_counts": self._count_by_platform(scored),
        }
        return AggregationResult(items=scored, metadata=metadata)

    def _normalize_item(self, item: Mapping[str, Any]) -> Dict[str, Any]:
        source = str(item.get("platform") or item.get("source") or "unknown").strip() or "unknown"
        url = str(item.get("url") or item.get("permalink") or "").strip()
        canonical_url = self._canonical_url(url or str(item.get("permalink", "")))
        title = str(item.get("title") or item.get("summary") or "").strip()
        text = str(item.get("text") or item.get("body") or item.get("content") or "").strip()

        normalized_text = " ".join(part for part in (title, text) if part).strip()
        parsed_created_at = self._parse_timestamp(item.get("created_at") or item.get("timestamp"))

        normalized: Dict[str, Any] = dict(item)
        normalized["platform"] = source
        normalized["source"] = source
        normalized["url"] = url or normalized.get("url") or normalized.get("permalink", "")
        normalized.setdefault("permalink", normalized.get("url", ""))
        normalized["_canonical_url"] = canonical_url
        normalized["_parsed_created_at"] = parsed_created_at
        normalized["_normalized_text"] = normalized_text
        normalized["transformation_notes"] = list(normalized.get("transformation_notes") or [])
        normalized["sources"] = self._merge_source_records(
            list(normalized.get("sources") or []),
            [self._build_source_record(item, source, url)],
        )
        normalized["source_weight"] = self._source_weight(source)
        normalized["engagement_signal"] = self._calculate_engagement(item)
        return normalized

    def _merge_items(self, base: Dict[str, Any], incoming: Dict[str, Any], *, reason: str) -> Dict[str, Any]:
        merged = dict(base)
        merged["sources"] = self._merge_source_records(base.get("sources", []), incoming.get("sources", []))
        merged_text = base.get("_normalized_text", "")
        incoming_text = incoming.get("_normalized_text", "")
        if incoming_text and len(incoming_text) > len(merged_text):
            merged["_normalized_text"] = incoming_text
        merged["_parsed_created_at"] = self._newer_timestamp(
            base.get("_parsed_created_at"), incoming.get("_parsed_created_at")
        )
        merged["engagement_signal"] = max(base.get("engagement_signal", 0.0), incoming.get("engagement_signal", 0.0))
        merged["source_weight"] = max(base.get("source_weight", 0.0), incoming.get("source_weight", 0.0))
        merged["_canonical_url"] = base.get("_canonical_url") or incoming.get("_canonical_url", "")
        if not merged.get("url") and incoming.get("url"):
            merged["url"] = incoming.get("url")
        if not merged.get("permalink") and incoming.get("permalink"):
            merged["permalink"] = incoming.get("permalink")
        merged["transformation_notes"] = list(base.get("transformation_notes") or [])
        merged["transformation_notes"].append(
            f"Merged duplicate entry via {reason.replace('_', ' ')} from {incoming.get('source', 'unknown source')}."
        )
        return merged

    def _score_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        recency_score = self._calculate_recency_score(item.get("_parsed_created_at"))
        engagement_score = self._normalize_engagement(item.get("engagement_signal", 0.0))
        base_weight = float(item.get("source_weight") or 0.0) or self.default_source_weight

        aggregate_score = base_weight * (
            (self.recency_weight * recency_score) + (self.engagement_weight * engagement_score)
        )
        confidence = min(
            1.0,
            0.35 + 0.25 * len(item.get("sources", [])) + 0.4 * recency_score,
        )

        rendered = dict(item)
        rendered["aggregation_score"] = round(aggregate_score, 4)
        rendered["confidence"] = round(confidence, 3)
        # Strip internal helper fields for cleaner downstream consumption
        rendered.pop("_canonical_url", None)
        rendered.pop("_normalized_text", None)
        rendered.pop("_parsed_created_at", None)
        rendered.pop("engagement_signal", None)
        return rendered

    def _find_similar(self, existing: Sequence[Mapping[str, Any]], candidate: Mapping[str, Any]) -> int | None:
        """Return index of a similar item using fuzzy matching."""

        candidate_text = str(candidate.get("_normalized_text", "") or "").lower()
        if not candidate_text:
            return None
        candidate_title = str(candidate.get("title") or candidate.get("summary") or "").lower()
        candidate_len = len(candidate_text)
        candidate_title_len = len(candidate_title) if candidate_title else 0

        for idx, item in enumerate(existing):
            existing_text = str(item.get("_normalized_text", "") or "").lower()
            if not existing_text:
                continue

            # Fast length-based upper bound: the similarity ratio cannot exceed
            # min_len / max_len. If that is already below the threshold, skip
            # computing the more expensive SequenceMatcher ratio.
            existing_len = len(existing_text)
            if existing_len == 0:
                continue
            max_len = max(candidate_len, existing_len)
            min_len = min(candidate_len, existing_len)
            if max_len > 0 and (min_len / max_len) < self.near_duplicate_threshold:
                continue

            ratio = SequenceMatcher(None, candidate_text, existing_text).ratio()
            if ratio >= self.near_duplicate_threshold:
                return idx
            if candidate_title:
                existing_title = str(item.get("title") or item.get("summary") or "").lower()
                if existing_title:
                    existing_title_len = len(existing_title)
                    max_title_len = max(candidate_title_len, existing_title_len)
                    min_title_len = min(candidate_title_len, existing_title_len)
                    title_threshold = max(self.near_duplicate_threshold - 0.1, 0.5)
                    if max_title_len > 0 and (min_title_len / max_title_len) < title_threshold:
                        continue
                    title_ratio = SequenceMatcher(None, candidate_title, existing_title).ratio()
                    if title_ratio >= title_threshold:
                        return idx
        return None

    def _build_source_record(self, item: Mapping[str, Any], platform: str, url: str) -> Dict[str, Any]:
        return {
            "id": str(item.get("id") or item.get("url") or item.get("permalink") or platform or "unknown"),
            "platform": platform,
            "url": url or str(item.get("permalink", "")),
            "ranking_position": item.get("ranking_position"),
        }

    def _merge_source_records(
        self,
        primary: Iterable[Mapping[str, Any]],
        incoming: Iterable[Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def _add(record: Mapping[str, Any]) -> None:
            identifier = (str(record.get("platform", "")), str(record.get("id", "")))
            if identifier in seen:
                return
            seen.add(identifier)
            merged.append(dict(record))

        for record in primary:
            _add(record)
        for record in incoming:
            _add(record)
        return merged

    def _canonical_url(self, url: str) -> str:
        normalized = url.strip().lower()
        if normalized.endswith("/"):
            normalized = normalized[:-1]
        return normalized

    def _parse_timestamp(self, timestamp: Any) -> datetime | None:
        if timestamp in (None, "", 0):
            return None
        if isinstance(timestamp, (int, float)):
            try:
                return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
            except (ValueError, OSError, OverflowError):
                return None

        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                try:
                    return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
                except (ValueError, OSError, OverflowError):
                    return None
        return None

    def _calculate_recency_score(self, timestamp: datetime | None) -> float:
        if timestamp is None:
            return 0.5  # Neutral score when recency is unknown

        now = datetime.now(timezone.utc)
        delta_days = max(0.0, (now - timestamp).total_seconds() / 86400)
        normalized_age = min(1.0, delta_days / float(self.max_item_age_days or 1))
        return max(0.0, 1.0 - normalized_age)

    def _calculate_engagement(self, item: Mapping[str, Any]) -> float:
        votes = float(item.get("upvotes") or item.get("score") or 0.0)
        comments = float(item.get("comments") or 0.0)
        return votes + (comments * 0.5)

    def _normalize_engagement(self, engagement_signal: float) -> float:
        if engagement_signal <= 0:
            return 0.0
        return min(1.0, 1.0 - math.exp(-engagement_signal / 10.0))

    def _source_weight(self, source: str) -> float:
        platform = source.lower()
        extra_weights = getattr(getattr(self.settings, "aggregation", None), "extra_source_weights", {}) or {}
        if platform in extra_weights:
            try:
                return float(extra_weights[platform])
            except (TypeError, ValueError):
                pass
        if "reddit" in platform:
            return self.reddit_source_weight
        if "google" in platform:
            return self.google_source_weight
        return self.default_source_weight

    def _count_by_platform(self, items: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in items:
            platform = str(item.get("platform") or "unknown").strip() or "unknown"
            counts[platform] = counts.get(platform, 0) + 1
        return counts

    def _newer_timestamp(self, first: datetime | None, second: datetime | None) -> datetime | None:
        if first is None:
            return second
        if second is None:
            return first
        return max(first, second)
