# test_integration.py
import asyncio
from twitter_wrapper import TwitterWrapper

BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAGAd5gEAAAAAUQ5tKjBdxBns%2B4qXh8D1UdNxqgQ%3DZJzKzr0tY49QwTf9v3TxQWJ8hcV5cnris8fcWEhfkbsnNSbxLu"

async def main():
    wrapper = TwitterWrapper(BEARER_TOKEN)
    page = await wrapper.search_recent_tweets("OpenAI", max_results=10)

    print("Fetched tweets:")
    for tweet in page.tweets:
        print(f"{tweet.id} | {tweet.author_username} | {tweet.text[:50]}...")

if __name__ == "__main__":
    asyncio.run(main())