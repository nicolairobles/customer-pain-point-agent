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
        self.comment_weight = getattr(agg_settings, "comment_weight", 0.5)
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
            items: Sequence of tool results.
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
        source_weight = item.get("source_weight")
        if source_weight is None:
            base_weight = self.default_source_weight
        else:
            try:
                base_weight = float(source_weight)
            except (TypeError, ValueError):
                base_weight = self.default_source_weight

        aggregate_score = base_weight * (
            (self.recency_weight * recency_score) + (self.engagement_weight * engagement_score)
        )
        # Confidence calculation combines base confidence, multi-source validation, and recency:
        # - 0.35: Base confidence for any item (establishes minimum confidence floor)
        # - 0.25 * source_count: Each additional source adds validation (up to +0.25 for multi-source)
        # - 0.4 * recency_score: Recent items get confidence boost (up to +0.4 for very recent)
        # This ensures confidence grows with cross-source validation and recency, capped at 1.0
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
                    # Title similarity uses a more lenient threshold than full text:
                    # - Subtract 0.1 from main threshold to allow minor title variations
                    # - Floor at 0.5 to prevent matching completely different titles
                    # Rationale: Titles are shorter and more formulaic, so small word changes
                    # (e.g., "Payment fails" vs "Payment failure") should still match
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
        """Canonicalize URL for deduplication purposes.
        
        Normalizes common URL variations to detect duplicates:
        - Removes trailing slashes
        - Converts to lowercase
        - Normalizes http/https protocols to https
        - Removes www. prefix
        - Strips fragment identifiers (#)
        - Sorts query parameters alphabetically
        
        Note: This is intentionally a simple normalization focused on common
        variations. More sophisticated URL parsing (e.g., domain equivalence,
        URL shortener expansion) is not performed to keep processing fast.
        """
        from urllib.parse import urlparse, parse_qs, urlencode
        
        normalized = url.strip().lower()
        if not normalized:
            return ""
        
        try:
            parsed = urlparse(normalized)
            
            # Normalize scheme (http -> https)
            scheme = "https" if parsed.scheme in ("http", "https") else parsed.scheme
            
            # Remove www. prefix from netloc
            netloc = parsed.netloc
            if netloc.startswith("www."):
                netloc = netloc[4:]
            
            # Remove fragment
            fragment = ""
            
            # Sort query parameters for consistent ordering
            query = ""
            if parsed.query:
                params = parse_qs(parsed.query, keep_blank_values=True)
                sorted_params = sorted(params.items())
                query = urlencode(sorted_params, doseq=True)
            
            # Remove trailing slash from path
            path = parsed.path.rstrip("/") if parsed.path else ""
            
            # Reconstruct URL
            if netloc:
                canonical = f"{scheme}://{netloc}{path}"
                if query:
                    canonical += f"?{query}"
                return canonical
            else:
                # Fallback for malformed URLs
                return normalized.rstrip("/")
        except Exception:
            # If URL parsing fails, fall back to simple normalization
            return normalized.rstrip("/")

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
        """Calculate engagement signal from votes and comments.
        
        Combines upvotes/score with comments using a configurable weight.
        The comment_weight reflects that comments typically indicate deeper
        engagement than votes, but may be valued differently across platforms.
        For example, on Reddit a comment often signals strong interest, while
        on other platforms voting might be the primary engagement mechanism.
        
        Default weight of 0.5 means: engagement = votes + (comments * 0.5)
        This implies 2 comments ≈ 1 upvote in terms of engagement value.
        """
        votes = float(item.get("upvotes") or item.get("score") or 0.0)
        comments = float(item.get("comments") or 0.0)
        return votes + (comments * self.comment_weight)

    def _normalize_engagement(self, engagement_signal: float) -> float:
        """Normalize engagement signal to [0, 1] range using exponential decay.
        
        The scaling factor of 10.0 controls the rate of saturation:
        - engagement=10 → ~0.63 normalized score
        - engagement=23 → ~0.90 normalized score
        - engagement=46 → ~0.99 normalized score
        
        This logarithmic curve prevents extremely high engagement from dominating
        scores while still rewarding popular content. Adjust the factor (10.0) to
        control sensitivity: smaller values saturate faster, larger values allow
        higher engagement items to differentiate more.
        """
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
