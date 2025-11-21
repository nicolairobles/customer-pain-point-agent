#!/usr/bin/env python3
"""Command-line interface to run the RedditTool and output sanitized JSON.

Usage examples:
  python scripts/run_reddit_tool_cli.py --query "decorators" --subreddits python,learnprogramming --limit 10
  python scripts/run_reddit_tool_cli.py -q "asyncio" -s python -l 5 --per-subreddit 5 -o results.json
"""

from __future__ import annotations

import argparse
import json
import sys
import pathlib
from dotenv import load_dotenv

# Ensure repo root is on sys.path when running the script directly
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.settings import settings
from src.tools.reddit_tool import RedditTool


def _sanitize(obj):
    """Sanitize objects to JSON-serializable primitives."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    try:
        return str(obj)
    except Exception:
        return repr(obj)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run RedditTool with requested parameters")
    p.add_argument("--query", "-q", default="python decorators", help="Search query")
    p.add_argument("--subreddits", "-s", default="python,learnprogramming,programming", help="Comma-separated subreddits")
    p.add_argument("--limit", "-l", type=int, default=15, help="Total results to return (1-20)")
    p.add_argument("--per-subreddit", "-p", type=int, default=10, help="Results requested per subreddit")
    p.add_argument("--time-filter", "-t", default="week", help="PRAW time_filter: hour|day|week|month|year|all or 'none'")
    p.add_argument("--out", "-o", help="Write output to file instead of stdout")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    load_dotenv()

    subreddits = [s.strip() for s in args.subreddits.split(",") if s.strip()]
    time_filter = None if str(args.time_filter).lower() in ("none", "null", "") else args.time_filter

    try:
        tool = RedditTool.from_settings(settings)
    except Exception:
        print("Failed to create RedditTool:")
        raise

    results = tool._run(
        args.query,
        subreddits=subreddits,
        limit=max(1, min(int(args.limit), 20)),
        per_subreddit=max(1, int(args.per_subreddit)),
        time_filter=time_filter,
    )

    out = json.dumps(_sanitize(results), indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf8") as fh:
            fh.write(out)
        print(f"Wrote {len(results)} results to {args.out}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
