"""Unit tests for the pain point extractor pipeline."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from src.extractors.pain_point_extractor import (
    PainPoint,
    PainPointSource,
    deduplicate_pain_points,
    extract_pain_points,
)
from src.services.openai_llm import LLMResult, LLMUsage, OpenAIServiceError


class FakeService:
    """Minimal OpenAI service double returning pre-seeded results."""

    def __init__(self, responses: List[Any]) -> None:
        self._responses = responses
        self.calls: int = 0

    def generate(self, _: str) -> LLMResult:
        response = self._responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


def _make_usage() -> LLMUsage:
    return LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, cost_usd=0.01)


def test_extract_pain_points_returns_expected_models() -> None:
    documents = [
        {
            "platform": "reddit",
            "author": "user-a",
            "timestamp": "2025-11-18T10:00:00Z",
            "url": "https://reddit.com/r/example/1",
            "content": "The dashboard crashes whenever I filter by date.",
        },
        {
            "platform": "twitter",
            "author": "user-b",
            "timestamp": "2025-11-18T11:00:00Z",
            "url": "https://twitter.com/example/status/1",
            "content": "Filtering by date produces 500 errors repeatedly.",
        },
    ]

    response_payload = {
        "pain_points": [
            {
                "name": "Dashboard filtering failures",
                "description": "Users cannot filter dashboards by date without encountering application errors.",
                "frequency": "high",
                "examples": [
                    "The dashboard crashes whenever I filter by date.",
                    "Filtering by date produces 500 errors repeatedly.",
                ],
                "sources": [
                    {
                        "platform": "reddit",
                        "url": "https://reddit.com/r/example/1",
                        "timestamp": "2025-11-18T10:00:00Z",
                        "author": "user-a",
                    },
                    {
                        "platform": "twitter",
                        "url": "https://twitter.com/example/status/1",
                        "timestamp": "2025-11-18T11:00:00Z",
                        "author": "user-b",
                    },
                ],
            }
        ]
    }

    fake_service = FakeService(
        [
            LLMResult(
                text=json.dumps(response_payload),
                usage=_make_usage(),
                model="gpt-4o-mini",
                response_id="resp-1",
                latency_seconds=0.25,
                raw_response=response_payload,
            )
        ]
    )

    points = extract_pain_points(documents, service=fake_service, batch_size=2)

    assert len(points) == 1
    point = points[0]
    assert isinstance(point, PainPoint)
    assert point.frequency == "medium"
    assert point.sentiment == "negative"
    assert point.relevance == 0.7
    assert len(point.sources) == 2


def test_extract_pain_points_handles_invalid_json() -> None:
    documents: List[Dict[str, Any]] = [
        {"platform": "reddit", "author": "user", "timestamp": "", "url": "", "content": "Sample"}
    ]
    fake_service = FakeService(
        [
            LLMResult(
                text="not json",
                usage=_make_usage(),
                model="gpt-4o-mini",
                response_id="resp-2",
                latency_seconds=0.1,
                raw_response="not json",
            )
        ]
    )

    points = extract_pain_points(documents, service=fake_service)
    assert points == []


def test_extract_pain_points_continues_after_service_error() -> None:
    documents = [
        {"platform": "reddit", "author": "user1", "timestamp": "", "url": "", "content": "foo"},
        {"platform": "reddit", "author": "user2", "timestamp": "", "url": "", "content": "bar"},
    ]

    response_payload = {
        "pain_points": [
            {
                "name": "Example pain point",
                "description": "Example description.",
                "frequency": "low",
                "examples": ["foo"],
                "sources": [
                    {"platform": "reddit", "url": "url", "timestamp": "2024-01-01T00:00:00Z", "author": "user1"}
                ],
            }
        ]
    }

    fake_service = FakeService(
        [
            OpenAIServiceError("temporary failure"),
            LLMResult(
                text=json.dumps(response_payload),
                usage=_make_usage(),
                model="gpt-4o-mini",
                response_id="resp-3",
                latency_seconds=0.2,
                raw_response=response_payload,
            ),
        ]
    )

    points = extract_pain_points(documents, service=fake_service, batch_size=1)
    assert len(points) == 1


def test_deduplicate_pain_points_merges_and_updates_frequency() -> None:
    base_sources = [
        PainPointSource(platform="reddit", url="url1", timestamp="2024-01-01T00:00:00Z", author="user-a"),
        PainPointSource(platform="twitter", url="url2", timestamp="2024-01-02T00:00:00Z", author="user-b"),
    ]

    point_a = PainPoint(
        name="Slow checkout flow",
        description="Users abandon the flow because checkout is slow.",
        frequency="low",
        examples=["Checkout takes ages."],
        sources=base_sources[:1],
        sentiment="negative",
    )
    point_b = PainPoint(
        name="Slow checkout flow",
        description="Multiple mentions of sluggish checkout, especially on mobile.",
        frequency="medium",
        examples=["Mobile checkout loads forever."],
        sources=base_sources,
        sentiment="negative",
    )

    deduped = deduplicate_pain_points([point_a, point_b])
    assert len(deduped) == 1
    merged = deduped[0]
    assert merged.frequency == "medium"
    assert len(merged.examples) == 2
    assert len(merged.sources) == 2


def test_extract_pain_points_batches_large_dataset() -> None:
    documents: List[Dict[str, Any]] = [
        {
            "platform": "reddit",
            "author": f"user-{i}",
            "timestamp": "2025-11-18T00:00:00Z",
            "url": f"https://example.com/{i}",
            "content": "Checkout issue",
        }
        for i in range(30)
    ]

    response_payload = {
        "pain_points": [
            {
                "name": "Checkout latency",
                "description": "Users see slow checkout behaviour.",
                "frequency": "low",
                "examples": ["Checkout issue"],
                "sources": [
                    {
                        "platform": "reddit",
                        "url": "https://example.com/0",
                        "timestamp": "2025-11-18T00:00:00Z",
                        "author": "user-0",
                    }
                ],
            }
        ]
    }

    batches_needed = 3  # 30 documents with batch_size=10
    fake_service = FakeService(
        [
            LLMResult(
                text=json.dumps(response_payload),
                usage=_make_usage(),
                model="gpt-4o-mini",
                response_id=f"resp-{i}",
                latency_seconds=0.1,
                raw_response=response_payload,
            )
            for i in range(batches_needed)
        ]
    )

    extract_pain_points(documents, service=fake_service, batch_size=10)
    assert fake_service.calls == batches_needed


