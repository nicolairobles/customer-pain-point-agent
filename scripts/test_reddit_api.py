#!/usr/bin/env python3
"""Smoke test for verifying Reddit API connectivity using PRAW."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from time import perf_counter

from dotenv import load_dotenv
import praw
from praw.exceptions import PRAWException


def mask_secret(value: str) -> str:
    """Return a partially masked version of a secret for log output."""

    if not value:
        return "<empty>"
    return f"{value[:4]}{'*' * max(0, len(value) - 4)}"


def configure_logging(verbose: bool) -> None:
    """Configure logging with timestamped messages."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the Reddit smoke test."""

    parser = argparse.ArgumentParser(
        description="Verify Reddit API connectivity by fetching sample submissions.",
    )
    parser.add_argument(
        "--subreddit",
        default="python",
        help="Subreddit to probe during the smoke test (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="How many submissions to fetch for the test (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Timeout for the Reddit client in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging for troubleshooting.",
    )
    return parser.parse_args()


def load_configuration() -> dict[str, str]:
    """Load and validate Reddit credentials from the .env file."""

    load_dotenv()
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = os.getenv("REDDIT_USER_AGENT", "single-agent-smoke-test/0.1")

    logging.debug("REDDIT_CLIENT_ID=%s", mask_secret(client_id))
    logging.debug("REDDIT_CLIENT_SECRET=%s", mask_secret(client_secret))
    logging.debug("REDDIT_USER_AGENT=%s", user_agent)

    if not client_id or not client_secret:
        logging.error(
            "Reddit credentials are missing. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in your .env file."
        )
        sys.exit(1)

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "user_agent": user_agent,
    }


def perform_smoke_test(subreddit_name: str, limit: int, timeout: float) -> None:
    """Fetch a few submission titles from a subreddit to confirm connectivity."""

    creds = load_configuration()
    # `request_timeout` ensures we fail fast instead of hanging indefinitely.
    reddit = praw.Reddit(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        user_agent=creds["user_agent"],
        request_timeout=timeout,
    )

    logging.info(
        "Fetching %s submission(s) from r/%s to verify Reddit API access",
        limit,
        subreddit_name,
    )
    start = perf_counter()

    try:
        subreddit = reddit.subreddit(subreddit_name)
        submissions = subreddit.hot(limit=limit)
        titles = [submission.title for submission in submissions]
    except PRAWException as exc:
        logging.exception("Reddit API call failed: %s", exc)
        logging.error(
            "Confirm your Reddit credentials and network access. If rate-limited, retry later or lower --limit."
        )
        sys.exit(1)

    duration = perf_counter() - start
    logging.info("Received %d submissions in %.2f seconds", len(titles), duration)
    for idx, title in enumerate(titles, start=1):
        logging.info("%d. %s", idx, title)
    logging.info("Smoke test succeeded.")


def main() -> None:
    """Entry point for the Reddit smoke test script."""

    args = parse_args()
    configure_logging(args.verbose)
    perform_smoke_test(args.subreddit, args.limit, args.timeout)


if __name__ == "__main__":
    main()
