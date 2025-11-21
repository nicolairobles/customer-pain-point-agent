
---

## **Modules**

### `twitter_tool.py`
- Handles **low-level Twitter API calls**.
- Implements:
  - `search_tweets(query, bearer_token, max_results=10)` → fetches recent tweets.
  - `retry_request(url, headers, params)` → handles rate limits and HTTP errors.
- Logs HTTP errors and rate-limiting events.

### `twitter_wrapper.py`
- Provides a **wrapper** around `twitter_tool.py`.
- Normalizes raw tweets into structured objects:
  - `NormalizedTweet`: unified tweet model.
  - `TweetPage`: paginated container.
- Performs **parsing & sanitization**:
  - De-duplicates tweets.
  - Injects metadata (e.g., `platform="twitter"`).
  - Converts timestamps to ISO 8601 UTC.
  - Handles missing fields gracefully.

### `tests/twitter/test_twitter_wrapper.py`
- Unit tests for wrapper parsing logic.
- Validates normalization, empty results, ISO timestamps, and `raw` fields.

### `tests/twitter/test_twitter_tool_unit.py`
- Unit tests for Twitter search tool.
- Covers:
  - Success responses
  - Zero-result queries
  - Rate-limit handling
  - Authentication failures
  - Malformed payloads
  - Wrapper normalization logic
- Fully mocks API calls — no live credentials needed.

---

## **Getting Started**

1. **Clone the repository**

```bash
git clone <repo_url>
cd customer-pain-point-agent
