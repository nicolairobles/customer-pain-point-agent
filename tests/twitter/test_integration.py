import sys
from pathlib import Path
import asyncio

# ----------------------------
# Fix imports: add tests/ folder to sys.path
# ----------------------------
project_root = Path(__file__).resolve().parents[1]  # Goes up from tests/twitter/ to tests/
sys.path.insert(0, str(project_root))

# ----------------------------
# Imports
# ----------------------------
from twitter_wrapper import TwitterWrapper

# ----------------------------
# Use your real Bearer token here
# ----------------------------
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAGAd5gEAAAAAUQ5tKjBdxBns%2B4qXh8D1UdNxqgQ%3DZJzKzr0tY49QwTf9v3TxQWJ8hcV5cnris8fcWEhfkbsnNSbxLu"

# ----------------------------
# Integration test: fetch real tweets
# ----------------------------
async def main():
    wrapper = TwitterWrapper(BEARER_TOKEN)
    page = await wrapper.search_recent_tweets("OpenAI", max_results=10)

    print("Fetched tweets:")
    for tweet in page.tweets:
        print(f"{tweet.id} | {tweet.author_username} | {tweet.text[:50]}...")


if __name__ == "__main__":
    asyncio.run(main())
