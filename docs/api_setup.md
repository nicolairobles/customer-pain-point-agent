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

### Rate Limits and Quota Considerations
- **Daily Quota**: 100 free searches per day (shared across all Google APIs).
- **Rate Limit**: 1 query per second (QPS) per user.
- **Billing**: $5 per 1000 queries after free quota exhaustion.
- **Cost Implications**: Monitor usage to avoid unexpected charges; implement caching to reduce API calls.

### Best Practices
- Use quota-safe queries in testing (e.g., limit to 1-2 results).
- Enable billing alerts in Google Cloud Console.
- Consider upgrading to higher quota plans for production use.
