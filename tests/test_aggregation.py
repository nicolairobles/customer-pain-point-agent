from datetime import datetime, timedelta, timezone

from config.settings import AggregationSettings, Settings
from src.services.aggregation import CrossSourceAggregator


def make_settings(**overrides):
    agg_settings = AggregationSettings(
        recency_weight=overrides.get("recency_weight", 0.6),
        engagement_weight=overrides.get("engagement_weight", 0.4),
        max_item_age_days=overrides.get("max_item_age_days", 365),
        near_duplicate_threshold=overrides.get("near_duplicate_threshold", 0.8),
        comment_weight=overrides.get("comment_weight", 0.5),
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


def test_configurable_comment_weight():
    """Test that comment_weight configuration affects engagement calculation."""
    now = datetime.now(timezone.utc)
    
    # Item with 10 upvotes and 10 comments
    item = {
        "id": "test-1",
        "title": "Test item",
        "text": "Test content",
        "url": "https://example.com/test",
        "platform": "reddit_search",
        "created_at": now.isoformat(),
        "upvotes": 10,
        "comments": 10,
    }
    
    # Test with default comment_weight (0.5)
    settings_default = make_settings(comment_weight=0.5)
    aggregator_default = CrossSourceAggregator(settings_default)
    engagement_default = aggregator_default._calculate_engagement(item)
    # Should be: 10 + (10 * 0.5) = 15.0
    assert engagement_default == 15.0
    
    # Test with higher comment_weight (1.0) - comments valued equally to votes
    settings_high = make_settings(comment_weight=1.0)
    aggregator_high = CrossSourceAggregator(settings_high)
    engagement_high = aggregator_high._calculate_engagement(item)
    # Should be: 10 + (10 * 1.0) = 20.0
    assert engagement_high == 20.0
    
    # Test with lower comment_weight (0.25) - comments valued less
    settings_low = make_settings(comment_weight=0.25)
    aggregator_low = CrossSourceAggregator(settings_low)
    engagement_low = aggregator_low._calculate_engagement(item)
    # Should be: 10 + (10 * 0.25) = 12.5
    assert engagement_low == 12.5
    
    # Test that higher comment weight results in higher aggregation score
    # when all else is equal
    result_default = aggregator_default.aggregate([item])
    result_high = aggregator_high.aggregate([item])
    # With higher comment weight, same item should get higher score
    assert result_high.items[0]["aggregation_score"] > result_default.items[0]["aggregation_score"]


def test_parse_timestamp_with_none_and_empty():
    """Test _parse_timestamp handles None and empty values."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)
    
    assert aggregator._parse_timestamp(None) is None
    assert aggregator._parse_timestamp("") is None
    assert aggregator._parse_timestamp(0) is None


def test_parse_timestamp_with_unix_timestamps():
    """Test _parse_timestamp handles Unix timestamps (int and float)."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)
    
    # Valid Unix timestamp (2024-01-01 00:00:00 UTC)
    timestamp_int = 1704067200
    result_int = aggregator._parse_timestamp(timestamp_int)
    assert result_int is not None
    assert result_int.year == 2024
    assert result_int.month == 1
    assert result_int.day == 1
    
    # Valid Unix timestamp as float
    timestamp_float = 1704067200.5
    result_float = aggregator._parse_timestamp(timestamp_float)
    assert result_float is not None
    assert result_float.year == 2024
    
    # Test with very large timestamp (overflow - year 5138+)
    result_overflow = aggregator._parse_timestamp(99999999999)
    assert result_overflow is not None  # Modern systems handle this
    
    # Test with extremely large timestamp that causes actual overflow
    result_extreme = aggregator._parse_timestamp(999999999999999)
    # This may return None or a valid date depending on platform


def test_parse_timestamp_with_iso_strings():
    """Test _parse_timestamp handles ISO format strings."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)
    
    # ISO format with Z suffix
    iso_with_z = "2024-01-15T10:30:00Z"
    result_z = aggregator._parse_timestamp(iso_with_z)
    assert result_z is not None
    assert result_z.year == 2024
    assert result_z.month == 1
    assert result_z.day == 15
    
    # ISO format with timezone offset
    iso_with_offset = "2024-01-15T10:30:00+00:00"
    result_offset = aggregator._parse_timestamp(iso_with_offset)
    assert result_offset is not None
    assert result_offset.year == 2024
    
    # ISO format without timezone (should still parse)
    iso_no_tz = "2024-01-15T10:30:00"
    result_no_tz = aggregator._parse_timestamp(iso_no_tz)
    assert result_no_tz is not None


def test_parse_timestamp_with_numeric_strings():
    """Test _parse_timestamp handles numeric strings as Unix timestamps."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)
    
    # Valid numeric string
    numeric_str = "1704067200"
    result = aggregator._parse_timestamp(numeric_str)
    assert result is not None
    assert result.year == 2024
    
    # Invalid numeric string
    invalid_str = "not-a-number"
    result_invalid = aggregator._parse_timestamp(invalid_str)
    assert result_invalid is None
    
    # Overflow numeric string
    overflow_str = "999999999999"
    result_overflow = aggregator._parse_timestamp(overflow_str)
    assert result_overflow is None


def test_parse_timestamp_error_handling():
    """Test _parse_timestamp handles various error cases gracefully."""
    settings = make_settings()
    aggregator = CrossSourceAggregator(settings)
    
    # Test ValueError cases
    assert aggregator._parse_timestamp("invalid-date") is None
    assert aggregator._parse_timestamp("2024-99-99") is None
    
    # Test with non-string, non-numeric types (should return None)
    assert aggregator._parse_timestamp([]) is None
    assert aggregator._parse_timestamp({}) is None


def test_source_weight_platform_matching():
    """Test _source_weight correctly identifies platforms and applies weights."""
    settings = make_settings(
        reddit_source_weight=1.0,
        google_source_weight=0.85,
        default_source_weight=0.7
    )
    aggregator = CrossSourceAggregator(settings)
    
    # Test Reddit platform matching
    assert aggregator._source_weight("reddit") == 1.0
    assert aggregator._source_weight("reddit_search") == 1.0
    assert aggregator._source_weight("Reddit") == 1.0
    assert aggregator._source_weight("REDDIT_API") == 1.0
    
    # Test Google platform matching
    assert aggregator._source_weight("google") == 0.85
    assert aggregator._source_weight("google_search") == 0.85
    assert aggregator._source_weight("Google") == 0.85
    assert aggregator._source_weight("GOOGLE_CUSTOM") == 0.85
    
    # Test default fallback
    assert aggregator._source_weight("twitter") == 0.7
    assert aggregator._source_weight("unknown") == 0.7
    assert aggregator._source_weight("") == 0.7


def test_source_weight_extra_weights_configuration():
    """Test _source_weight uses extra_source_weights from configuration."""
    agg_settings = AggregationSettings(
        recency_weight=0.6,
        engagement_weight=0.4,
        extra_source_weights={
            "twitter": 0.95,
            "stackoverflow": 0.88
        }
    )
    settings = Settings(aggregation=agg_settings)
    aggregator = CrossSourceAggregator(settings)
    
    # Test extra weights are used
    assert aggregator._source_weight("twitter") == 0.95
    assert aggregator._source_weight("stackoverflow") == 0.88
    
    # Test fallback still works for non-configured platforms
    # Reddit and Google should use their configured weights
    assert aggregator._source_weight("reddit") == aggregator.reddit_source_weight
    assert aggregator._source_weight("google") == aggregator.google_source_weight
    assert aggregator._source_weight("unknown") == aggregator.default_source_weight


def test_source_weight_error_handling():
    """Test _source_weight handles invalid extra_source_weights gracefully."""
    # Invalid weight value that can't be converted to float
    agg_settings = AggregationSettings(
        recency_weight=0.6,
        engagement_weight=0.4,
        extra_source_weights={
            "twitter": "not-a-number"  # type: ignore
        }
    )
    settings = Settings(aggregation=agg_settings)
    aggregator = CrossSourceAggregator(settings)
    
    # Should fall back to default weight when conversion fails
    weight = aggregator._source_weight("twitter")
    assert weight == aggregator.default_source_weight

