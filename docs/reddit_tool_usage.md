# RedditTool Usage

This document describes the `RedditTool` implemented in `src/tools/reddit_tool.py`.

Summary
- Searches multiple subreddits concurrently using PRAW and returns normalized post dictionaries.
- Each post dict contains: `id`, `title`, `body`, `score`, `comments`, `url`, `author`, `subreddit`, `timestamp`.

Basic usage

```python
from config.settings import settings
from src.tools.reddit_tool import RedditTool

tool = RedditTool.from_settings(settings)
results = tool._run(
    "search query",
    subreddits=["python", "learnprogramming", "programming"],
    limit=15,
    per_subreddit=10,
    time_filter="week",  # optional: 'day', 'week', 'month', 'year', 'all'
)
```

Notes
- `limit` is the total number of posts returned (capped between 1 and 20).
- `per_subreddit` controls how many results are requested from each subreddit.
- The tool uses a simple relevance heuristic (upvotes + comments) to rank results.
- The implementation includes retries/backoff for transient errors and logs per-request durations for diagnostics.

Testing
- Unit tests live in `tests/test_reddit_tool.py` and mock PRAW clients — they do not require network access.

Production considerations
- For CI/deploy, provide credentials via environment variables (do not commit `.env`).
- Consider caching, adaptive backoff based on headers, and more advanced ranking for production workloads.
