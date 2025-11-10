Activity ID: 1.2.1
Activity: Design Reddit API wrapper interface
Description: Define function signatures and return data structure
Work Package: 2.2.1 Reddit API Wrapper Development
Duration: 1 hour

"""
Acceptance Criteria:
- Class must search at least 3 subreddits simultaneously
- Return 10-20 posts per query
- Each post must include: title, text, upvotes, comments, url, subreddit, timestamp
- Must handle API errors gracefully (return empty list, log error)
- Response time < 5 seconds for 10 posts
- Results sorted by relevance (upvotes + comments)

Test Criteria:
- Test that search returns correct data structure
- Test that it handles empty/no results
- Test that it filters by time period
- Test error handling when API fails
- Test that results are sorted correctly
- Mock Reddit API responses (no real API calls in tests)

Constraints:
- Use PRAW library
- Python 3.9+ with type hints
- Compatible with pytest

Implement the complete Reddit search wrapper class with full test suite.
"""

from typing import List, Dict, Optional
import praw
import pytest


# Implementation here
