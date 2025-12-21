#!/usr/bin/env python3
"""Smoke test for verifying Google Custom Search API connectivity using project credentials."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from time import perf_counter

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def mask_secret(value: str) -> str:
    """Return a partially masked representation of a secret for safe logging."""

    if not value:
        return "<empty>"
    visible = value[:4]
    return f"{visible}{'*' * max(0, len(value) - 4)}"


def configure_logging(verbose: bool) -> None:
    """Configure the root logger with a friendly format and log level."""

    level = logging.DEBUG if verbose else logging.INFO
    # Timestamped logs make it easier to share results in project tracking tools.
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the smoke test."""

    parser = argparse.ArgumentParser(
        description="Verify connectivity to the Google Custom Search API using project credentials.",
    )
    parser.add_argument(
        "--query",
        default="test query",
        help="Search query for the smoke test (default: %(default)s)",
    )
    parser.add_argument(
        "--num",
        type=int,
        default=1,
        help="Number of results to request (keep low to respect quota, default: %(default)s)",
    )
    # Timeout can save cost by preventing hung requests from running indefinitely.
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Request timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging for troubleshooting.",
    )
    return parser.parse_args()


def load_configuration() -> tuple[str, str]:
    """Load environment variables and return the Google API credentials."""

    load_dotenv()
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
    logging.debug("Loaded GOOGLE_SEARCH_API_KEY=%s", mask_secret(api_key))
    logging.debug("Loaded GOOGLE_SEARCH_ENGINE_ID=%s", mask_secret(engine_id))
    if not api_key:
        logging.error(
            "GOOGLE_SEARCH_API_KEY is missing. Ensure it is defined in your .env file before running the smoke test."
        )
        sys.exit(1)
    if not engine_id:
        logging.error(
            "GOOGLE_SEARCH_ENGINE_ID is missing. Ensure it is defined in your .env file before running the smoke test."
        )
        sys.exit(1)
    return api_key, engine_id


def perform_smoke_test(api_key: str, engine_id: str, query: str, num: int, timeout: float) -> None:
    """Issue a lightweight search request to confirm API reachability."""

    service = build("customsearch", "v1", developerKey=api_key)
    # Keep the query simple and limit results to respect quota.
    logging.info("Requesting search results for query='%s' (num=%d)", query, num)
    start = perf_counter()

    try:
        response = service.cse().list(
            q=query,
            cx=engine_id,
            num=num,
        ).execute()
    except HttpError as exc:
        logging.exception("Google Custom Search API call failed: %s", exc)
        logging.error(
            "Double-check your network connectivity, API key permissions, and custom search engine configuration."
        )
        sys.exit(1)

    duration = perf_counter() - start
    logging.info("Received response in %.2f seconds", duration)
    items = response.get("items", [])
    logging.info("Response status: %s", response.get("searchInformation", {}).get("searchTime", "unknown"))
    logging.info("Result count: %d", len(items))
    if items:
        logging.info("First result title: %s", items[0].get("title", "<no title>"))
    logging.debug("Raw response payload: %s", response)
    logging.info("Smoke test succeeded.")


def main() -> None:
    """Entry point for the script."""

    args = parse_args()
    configure_logging(args.verbose)
    api_key, engine_id = load_configuration()
    perform_smoke_test(api_key, engine_id, args.query, args.num, args.timeout)


if __name__ == "__main__":
    main()