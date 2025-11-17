#!/usr/bin/env python3
"""
Run a debug call to the RedditTool and show full output/traceback.
"""

from dotenv import load_dotenv
import json
import traceback
import sys, pathlib
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from config.settings import settings
from src.tools.reddit_tool import RedditTool

def _sanitize(obj):
    """Recursively convert objects to JSON-serializable types.

    - dict/list/tuple: sanitized recursively
    - primitives: returned as-is
    - other objects: converted to str(obj)
    """
    # Primitive types
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Mappings
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}

    # Iterables
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]

    # Fallback: stringify non-serializable objects (e.g., PRAW models)
    try:
        return str(obj)
    except Exception:
        return repr(obj)

def main():
    load_dotenv()
    try:
        tool = RedditTool.from_settings(settings)
    except Exception as e:
        print("Failed to create RedditTool:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(2)

    try:
        results = tool._run(
            "python decorators",
            subreddits=["python", "learnprogramming", "programming"],
            limit=15,
            per_subreddit=10,
            time_filter="week"  # try changing to None or 'day' if this errors
        )
        print(json.dumps(_sanitize(results), indent=2))
    except Exception as exc:
        print("RedditTool._run raised an exception:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()