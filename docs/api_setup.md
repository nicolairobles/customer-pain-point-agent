# API Setup Instructions

## OpenAI
1. Create an account at [OpenAI](https://platform.openai.com/).
2. Generate an API key and store it in the `.env` file under `OPENAI_API_KEY`.

## Reddit
1. Visit [Reddit Apps](https://www.reddit.com/prefs/apps).
2. Create a new script application and record the client ID and client secret.
3. Populate `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in the `.env` file.

## Twitter
1. Apply for a developer account at [developer.twitter.com](https://developer.twitter.com/).
2. Create a project/app and generate API credentials.
3. Populate `TWITTER_API_KEY` and `TWITTER_API_SECRET` in the `.env` file.

## Google Custom Search
1. Create an API key via the [Google Cloud Console](https://console.cloud.google.com/).
2. Configure a Custom Search Engine and capture its ID.
3. Populate `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` in the `.env` file.

### Quotas and Cost Notes

- Google Custom Search enforces quotas and may require billing for higher usage. Check `APIs & Services -> Quotas` in your Cloud Console for exact per-minute and daily limits for your project.
- For development and smoke tests: keep requests small (`num <= 10`) and add local caching to avoid repeated queries.
- Restrict API keys to the Custom Search API and, if possible, to specific IPs or referrers to reduce risk of abuse.

