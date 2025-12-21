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
    assert result.metadata["deduped_items"] == 2
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


def test_parse_timestamp_handles_none_empty_and_zero():
    """Test that None, empty string, and zero return None."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    assert aggregator._parse_timestamp(None) is None
    assert aggregator._parse_timestamp("") is None
    assert aggregator._parse_timestamp(0) is None


def test_parse_timestamp_handles_integer_timestamps():
    """Test parsing of integer Unix timestamps."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # Valid Unix timestamp (2024-01-01 00:00:00 UTC)
    timestamp = 1704067200
    result = aggregator._parse_timestamp(timestamp)
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 1
    assert result.tzinfo == timezone.utc


def test_parse_timestamp_handles_float_timestamps():
    """Test parsing of float Unix timestamps."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # Valid Unix timestamp with fractional seconds
    timestamp = 1704067200.5
    result = aggregator._parse_timestamp(timestamp)
    assert result is not None
    assert result.year == 2024
    assert result.tzinfo == timezone.utc


def test_parse_timestamp_handles_iso_strings():
    """Test parsing of ISO 8601 formatted strings."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # ISO 8601 with Z suffix
    iso_z = "2024-01-01T00:00:00Z"
    result = aggregator._parse_timestamp(iso_z)
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 1
    assert result.tzinfo == timezone.utc

    # ISO 8601 with +00:00 offset
    iso_offset = "2024-01-01T00:00:00+00:00"
    result = aggregator._parse_timestamp(iso_offset)
    assert result is not None
    assert result.year == 2024
    assert result.tzinfo == timezone.utc


def test_parse_timestamp_handles_numeric_strings():
    """Test parsing of numeric strings as Unix timestamps."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # String representation of Unix timestamp
    timestamp_str = "1704067200"
    result = aggregator._parse_timestamp(timestamp_str)
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 1
    assert result.tzinfo == timezone.utc

    # String with fractional seconds
    timestamp_float_str = "1704067200.5"
    result = aggregator._parse_timestamp(timestamp_float_str)
    assert result is not None
    assert result.year == 2024
    assert result.tzinfo == timezone.utc


def test_parse_timestamp_handles_value_error():
    """Test that ValueError is caught and returns None."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # Invalid ISO string
    invalid_iso = "not-a-valid-date"
    result = aggregator._parse_timestamp(invalid_iso)
    assert result is None

    # Invalid numeric string
    invalid_numeric = "invalid123"
    result = aggregator._parse_timestamp(invalid_numeric)
    assert result is None


def test_parse_timestamp_handles_os_error():
    """Test that OSError is caught and returns None."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # Timestamp before epoch on some systems (e.g., Windows)
    # -1 is before Unix epoch and may raise OSError
    negative_timestamp = -1
    result = aggregator._parse_timestamp(negative_timestamp)
    # Should either return None or a valid datetime, depending on platform
    # The important part is it doesn't crash
    assert result is None or isinstance(result, datetime)


def test_parse_timestamp_handles_overflow_error():
    """Test that OverflowError is caught and returns None."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # Extremely large timestamp that causes overflow
    huge_timestamp = 10**15
    result = aggregator._parse_timestamp(huge_timestamp)
    assert result is None

    # Extremely small timestamp
    small_timestamp = -(10**15)
    result = aggregator._parse_timestamp(small_timestamp)
    assert result is None


def test_parse_timestamp_handles_boolean_as_int():
    """Test that booleans are treated as integers (True=1, False=0)."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # In Python, bool is a subclass of int, so True/False are treated as 1/0
    # True should be treated as timestamp 1 (1970-01-01 00:00:01 UTC)
    result = aggregator._parse_timestamp(True)
    assert result is not None
    assert result.year == 1970
    assert result.month == 1
    assert result.day == 1
    assert result.second == 1

    # False should be treated as 0, which returns None (handled as special case)
    result = aggregator._parse_timestamp(False)
    assert result is None


def test_parse_timestamp_handles_unsupported_types():
    """Test that unsupported types return None."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)

    # List, dict, or other unsupported types
    result = aggregator._parse_timestamp([1704067200])
    assert result is None

    result = aggregator._parse_timestamp({"timestamp": 1704067200})
    assert result is None

    result = aggregator._parse_timestamp(complex(1, 2))
    assert result is None
