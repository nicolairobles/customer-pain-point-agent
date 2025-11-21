# # test_integration.py
# import asyncio
# from twitter_wrapper import TwitterWrapper


# async def main():
#     wrapper = TwitterWrapper(BEARER_TOKEN)
#     page = await wrapper.search_recent_tweets("OpenAI", max_results=10)

#     print("Fetched tweets:")
#     for tweet in page.tweets:
#         print(f"{tweet.id} | {tweet.author_username} | {tweet.text[:50]}...")

# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
import re
from twitter_wrapper import TwitterWrapper

BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAGAd5gEAAAAAUQ5tKjBdxBns%2B4qXh8D1UdNxqgQ%3DZJzKzr0tY49QwTf9v3TxQWJ8hcV5cnris8fcWEhfkbsnNSbxLu"

URL_REGEX = re.compile(r'https?://\S+')

async def main():
    wrapper = TwitterWrapper(BEARER_TOKEN)
    page = await wrapper.search_recent_tweets("OpenAI", max_results=10)

    seen_ids = set()

    for tweet in page.tweets:
        # Deduplication
        assert tweet.id not in seen_ids, f"Duplicate tweet id: {tweet.id}"
        seen_ids.add(tweet.id)

        # Text checks
        assert tweet.text, f"Empty text for tweet id {tweet.id}"
        assert not URL_REGEX.search(tweet.text), f"URL not removed in tweet id {tweet.id}"
        for char in '*_`':
            assert char not in tweet.text, f"Markdown unsafe char '{char}' in tweet id {tweet.id}"

        # Metadata
        assert tweet.platform == "twitter", f"Platform missing in tweet id {tweet.id}"
        assert tweet.author_username, f"Missing author_username in tweet id {tweet.id}"

        # Timestamp format (ISO 8601 check)
        try:
            from datetime import datetime
            datetime.fromisoformat(tweet.created_at)
        except Exception:
            raise AssertionError(f"Timestamp not ISO 8601: {tweet.created_at} for tweet id {tweet.id}")

    print(f"All {len(page.tweets)} tweets passed parsing verification.\nSample tweets:")
    for tweet in page.tweets[:5]:
        print(f"{tweet.id} | {tweet.author_username} | {tweet.text[:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
