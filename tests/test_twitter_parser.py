# tests/test_twitter_parser.py
from src.twitter_parser import parse_tweets

def test_parse_tweets_removes_duplicates_and_empty(sample_tweets, caplog):
    caplog.set_level("INFO")
    parsed = parse_tweets(sample_tweets)

    assert len(parsed) == 1
    tweet = parsed[0]
    assert tweet["text"] == "Hello world! Visit"
    assert tweet["platform"] == "twitter"
    assert "timestamp" in tweet
    assert "author_handle" in tweet
    assert "url" in tweet

    assert any("Duplicate tweet skipped" in r.message for r in caplog.records)
    assert any("Skipping tweet with missing text" in r.message for r in caplog.records)
