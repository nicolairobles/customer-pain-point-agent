# twitter_tool.py
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

BASE_URL = "https://api.twitter.com/2/tweets/search/recent"

def retry_request(url, headers, params, max_retries=3):
    for attempt in range(1, max_retries + 1):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:
            reset = response.headers.get("x-rate-limit-reset")
            retry_in = int(reset) - int(datetime.now().timestamp())
            logging.warning({
                "event": "rate_limited",
                "retry_in_seconds": max(retry_in, 1),
                "attempt": attempt
            })
            time.sleep(max(retry_in, 1))
            continue
        if response.status_code >= 400:
            logging.error({
                "event": "http_error",
                "status_code": response.status_code,
                "response_text": response.text
            })
            response.raise_for_status()
        return response.json()
    raise Exception("Max retries exceeded")

def search_tweets(query, bearer_token, max_results=10):
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": "id,text,author_id,created_at"
    }
    logging.info(f"Search request: query='{query}'")
    raw_response = retry_request(BASE_URL, headers, params)
    if "data" not in raw_response:
        return []
    return [
        {
            "id": t["id"],
            "text": t["text"],
            "author_id": t["author_id"],
            "created_at": t["created_at"]
        }
        for t in raw_response["data"]
    ]
