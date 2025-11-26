import sys
import os
import asyncio
import json
from datetime import datetime, timedelta
from src.twitter_wrapper import TwitterWrapper

async def run_tests():
    wrapper = TwitterWrapper()  # Uses bearer token from config.settings

    # ----------------------------
    # Design Review: Representative queries
    # ----------------------------
    print("=== Design Review: Representative Queries ===")

    # 1. Single keyword
    single_keyword_page = await wrapper.search_recent_tweets(query="python", max_results=3)
    print("\nSingle keyword search results:")
    for t in single_keyword_page.tweets:
        print(f"- {t.text} (by {t.author_username})")

    # 2. Hashtag search
    hashtag_page = await wrapper.search_recent_tweets(query="#AI", hashtags=["AI"], max_results=3)
    print("\nHashtag search results:")
    for t in hashtag_page.tweets:
        print(f"- {t.text} (by {t.author_username})")

    # 3. Time-bound search: last 24 hours
    now = datetime.utcnow()
    start_time = (now - timedelta(days=1)).isoformat() + "Z"
    end_time = now.isoformat() + "Z"
    time_bound_page = await wrapper.search_recent_tweets(
        query="chatbot",
        start_time=start_time,
        end_time=end_time,
        max_results=3
    )
    print("\nTime-bound search results:")
    for t in time_bound_page.tweets:
        print(f"- {t.text} (by {t.author_username})")

    # ----------------------------
    # Schema Validation: Serialize first tweet to JSON
    # ----------------------------
    print("\n=== Schema Validation: Sample Normalized Payload ===")
    if single_keyword_page.tweets:
        sample_tweet = single_keyword_page.tweets[0]
        tweet_json = json.dumps(sample_tweet.__dict__, indent=2)
        print(tweet_json)
    else:
        print("No tweets returned for schema validation.")

# Run the tests
asyncio.run(run_tests())
