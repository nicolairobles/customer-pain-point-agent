#!/usr/bin/env python3
"""
Run a debug call to the TwitterTool and show full output/traceback.
"""

import json
import logging
import pathlib
import sys
import traceback

from dotenv import load_dotenv

# Set up logging for the script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.settings import settings
from src.tools.twitter_tool import TwitterTool, TwitterAPIError

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

    # Fallback: stringify non-serializable objects (e.g., Tweepy models)
    try:
        return str(obj)
    except Exception:
        return repr(obj)

def main():
    load_dotenv()
    try:
        tool = TwitterTool.from_settings(settings)
        print("TwitterTool created successfully")
    except TwitterAPIError as e:
        print(f"Failed to create TwitterTool: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print("Failed to create TwitterTool:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(2)

    try:
        # Test with a simple, non-sensitive query
        results = tool._run(
            "customer service",  # Simple keyword search
            max_results=15,      # Between 10-20 as specified
            lang="en"            # English language filter
        )
        print(f"Search returned {len(results)} tweets")
        print(json.dumps(_sanitize(results), indent=2))
    except TwitterAPIError as e:
        print(f"TwitterTool._run raised TwitterAPIError: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as exc:
        print("TwitterTool._run raised an exception:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()