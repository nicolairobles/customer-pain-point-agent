from datetime import datetime, timedelta, timezone

from config.settings import AggregationSettings, Settings
from src.services.aggregation import CrossSourceAggregator


def make_settings(**overrides):
    agg_settings = AggregationSettings(
        recency_weight=overrides.get("recency_weight", 0.6),
        engagement_weight=overrides.get("engagement_weight", 0.4),
        max_item_age_days=overrides.get("max_item_age_days", 365),
        near_duplicate_threshold=overrides.get("near_duplicate_threshold", 0.8),
        reddit_source_weight=overrides.get("reddit_source_weight", 1.0),
        google_source_weight=overrides.get("google_source_weight", 0.85),
        default_source_weight=overrides.get("default_source_weight", 0.7),
    )
    return Settings(aggregation=agg_settings)


def test_aggregate_merges_duplicates_and_scores():
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)
    now = datetime.now(timezone.utc)

    items = [
        {
            "id": "reddit-1",
            "title": "Checkout keeps failing",
            "text": "Users cannot pay because the checkout gateway times out.",
            "url": "https://example.com/posts/checkout",
            "platform": "reddit_search",
            "created_at": now.isoformat(),
            "upvotes": 25,
            "comments": 3,
        },
        {
            "id": "google-1",
            "title": "Checkout keeps failing for users",
            "text": "Payment gateway timeout during checkout experience.",
            "url": "https://example.com/posts/checkout/",
            "platform": "google_search",
            "created_at": (now - timedelta(days=10)).isoformat(),
            "comments": 0,
        },
        {
            "id": "google-2",
            "title": "Subscription billing errors spike",
            "text": "Recurring billing produces duplicate invoices.",
            "url": "https://example.com/posts/billing",
            "platform": "google_search",
            "created_at": (now - timedelta(days=5)).isoformat(),
            "comments": 1,
        },
    ]

    result = aggregator.aggregate(items)
    assert result.metadata["deduped_items"] >= 1
    assert result.metadata["deduped_by_url"] == 1

    top_item = result.items[0]
    assert top_item["aggregation_score"] >= result.items[1]["aggregation_score"]
    assert len(top_item["sources"]) == 2
    assert any("Merged duplicate entry" in note for note in top_item["transformation_notes"])
    assert top_item["confidence"] >= 0.35


def test_aggregate_handles_near_duplicates_by_similarity():
    settings = make_settings(near_duplicate_threshold=0.65)
    aggregator = CrossSourceAggregator(settings)
    now = datetime.now(timezone.utc)

    items = [
        {
            "id": "reddit-2",
            "title": "Payment page crashes on submit",
            "text": "users report the payment page crashes during checkout process",
            "platform": "reddit_search",
            "created_at": (now - timedelta(days=3)).isoformat(),
        },
        {
            "id": "google-3",
            "title": "Payment page crash during checkout submission",
            "text": "Customers see a crash on the payment step.",
            "platform": "google_search",
            "created_at": (now - timedelta(days=2)).isoformat(),
        },
    ]

    result = aggregator.aggregate(items)
    assert result.metadata["deduped_by_similarity"] == 1
    assert result.metadata["deduped_items"] == 1
    merged_item = result.items[0]
    assert len(merged_item["sources"]) == 2
    assert merged_item["aggregation_score"] > 0


def test_aggregate_captures_errors_without_interrupting_results():
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)
    now = datetime.now(timezone.utc)

    items = [
        {
            "id": "reddit-3",
            "title": "Checkout slow after new deployment",
            "text": "pages take more than 10s to load",
            "platform": "reddit_search",
            "created_at": now.isoformat(),
        },
        "not-a-dict",
    ]

    errors = ["google_search failed due to quota"]
    result = aggregator.aggregate(items, errors=errors)
    assert result.metadata["errors"] == errors
    assert result.metadata["deduped_items"] == 1
    assert result.items[0]["platform"] == "reddit_search"


def test_aggregation_performance_for_large_input():
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)
    base_time = datetime.now(timezone.utc)

    items = []
    for i in range(100):
        items.append(
            {
                "id": f"item-{i}",
                "title": f"Pain point {i}",
                "text": "customers describe a repeatable failure scenario",
                "url": f"https://example.com/{i}",
                "platform": "reddit_search" if i % 2 == 0 else "google_search",
                "created_at": (base_time - timedelta(minutes=i)).isoformat(),
                "upvotes": i % 7,
                "comments": i % 3,
            }
        )

    result = aggregator.aggregate(items)
    assert 0 < result.metadata["deduped_items"] <= 100
    assert result.metadata["processing_time_seconds"] < 2.0
