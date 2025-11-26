#!/usr/bin/env python3
"""Smoke test for Google Custom Search API.

Usage: set `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` in your `.env`
and run: `python scripts/test_google_search.py --query "site:reddit.com customer pain points"`
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

try:
    from googleapiclient.discovery import build
except Exception as e:  # pragma: no cover - helpful error message
    print("Missing dependency `google-api-python-client`. Install with `pip install google-api-python-client`.")
    raise


def run_search(api_key: str, cse_id: str, query: str, num: int = 5):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cse_id, num=num).execute()
    return res


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="site:reddit.com customer pain points")
    parser.add_argument("--num", type=int, default=5)
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not cse_id:
        print("ERROR: Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in your .env before running.")
        sys.exit(2)

    print(f"Running Google Custom Search smoke test for query: {args.query!r}\n")
    try:
        res = run_search(api_key, cse_id, args.query, num=args.num)
    except Exception as e:
        print("Search request failed:", e)
        sys.exit(3)

    items = res.get("items", [])
    print(f"Returned {len(items)} items (showing up to {args.num}):\n")
    for i, it in enumerate(items, start=1):
        title = it.get("title")
        link = it.get("link")
        snippet = it.get("snippet")
        print(f"{i}. {title}\n   {link}\n   {snippet}\n")

    # Print a compact JSON summary to stdout for programmatic checks
    summary = {"query": args.query, "count": len(items)}
    print("SUMMARY_JSON:\n" + json.dumps(summary))


if __name__ == "__main__":
    main()
