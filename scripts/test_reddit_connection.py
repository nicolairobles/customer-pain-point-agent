#!/usr/bin/env python3
"""Diagnostic script to test Reddit API connection and credentials.

Run this to verify your Reddit API credentials are valid:
    python scripts/test_reddit_connection.py
"""

import os
import sys
import socket
import urllib.request

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_network_connectivity():
    """Test basic network connectivity to Reddit."""
    
    print("\n0. Testing network connectivity...")
    
    # Test DNS resolution
    try:
        ip = socket.gethostbyname("www.reddit.com")
        print(f"   ✓ DNS resolution: www.reddit.com -> {ip}")
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        print("   Your machine cannot resolve www.reddit.com")
        print("   Check your DNS settings or network connection")
        return False
    
    # Test basic HTTPS connection
    try:
        req = urllib.request.Request(
            "https://www.reddit.com/",
            headers={"User-Agent": "Mozilla/5.0 (connection test)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            print(f"   ✓ HTTPS connection: status {status}")
    except urllib.error.URLError as e:
        print(f"   ❌ HTTPS connection failed: {e}")
        print("\n   Possible causes:")
        print("   - VPN or firewall blocking Reddit")
        print("   - Corporate network restrictions")
        print("   - ISP blocking Reddit")
        print("   - Network proxy not configured")
        return False
    except Exception as e:
        print(f"   ❌ HTTPS connection failed: {e}")
        return False
    
    # Test OAuth endpoint specifically
    try:
        req = urllib.request.Request(
            "https://www.reddit.com/api/v1/access_token",
            headers={"User-Agent": "Mozilla/5.0 (connection test)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            # We expect 401 Unauthorized without credentials, but connection should work
            pass
    except urllib.error.HTTPError as e:
        if e.code in (401, 400):
            print(f"   ✓ OAuth endpoint reachable (got expected {e.code})")
        else:
            print(f"   ⚠ OAuth endpoint returned {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"   ❌ OAuth endpoint unreachable: {e}")
        print("   Reddit's OAuth endpoint is blocked")
        return False
    except Exception as e:
        print(f"   ❌ OAuth endpoint test failed: {e}")
        return False
    
    return True


def test_reddit_credentials():
    """Test Reddit API credentials and connection."""
    
    print("=" * 60)
    print("Reddit API Connection Diagnostic")
    print("=" * 60)
    
    # 0. Test network connectivity first
    if not test_network_connectivity():
        print("\n" + "=" * 60)
        print("❌ NETWORK CONNECTIVITY ISSUE DETECTED")
        print("=" * 60)
        print("\nYour machine cannot connect to Reddit's servers.")
        print("This is NOT a credentials issue - it's a network problem.")
        print("\nTry these fixes:")
        print("1. Disconnect from VPN (if using one)")
        print("2. Try a different network (e.g., mobile hotspot)")
        print("3. Check if Reddit is blocked on your network")
        print("4. Try: curl -I https://www.reddit.com/")
        return False
    
    # 1. Check environment variables
    print("\n1. Checking environment variables...")
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = os.getenv("REDDIT_USER_AGENT", "customer-pain-point-agent/0.1")
    
    if not client_id:
        print("   ❌ REDDIT_CLIENT_ID is not set!")
        return False
    else:
        print(f"   ✓ REDDIT_CLIENT_ID is set ({client_id[:8]}...)")
    
    if not client_secret:
        print("   ❌ REDDIT_CLIENT_SECRET is not set!")
        return False
    else:
        print(f"   ✓ REDDIT_CLIENT_SECRET is set ({client_secret[:4]}...)")
    
    print(f"   ✓ User Agent: {user_agent}")
    
    # 2. Test PRAW initialization
    print("\n2. Testing PRAW initialization...")
    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            check_for_async=False,
        )
        print("   ✓ PRAW Reddit client created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create Reddit client: {e}")
        return False
    
    # 3. Test read-only access (no authentication required)
    print("\n3. Testing basic Reddit access...")
    try:
        # Try to access Reddit's front page (read-only, no auth needed)
        subreddit = reddit.subreddit("test")
        print(f"   ✓ Subreddit object created: r/{subreddit.display_name}")
    except Exception as e:
        print(f"   ❌ Failed to access subreddit: {e}")
        return False
    
    # 4. Test OAuth authentication
    print("\n4. Testing OAuth authentication...")
    try:
        # This forces an OAuth token request
        reddit.auth.scopes()
        print("   ✓ OAuth authentication successful")
    except Exception as e:
        print(f"   ❌ OAuth authentication failed: {e}")
        print("\n   This usually means:")
        print("   - Your REDDIT_CLIENT_ID is invalid")
        print("   - Your REDDIT_CLIENT_SECRET is invalid")
        print("   - Your Reddit app has been revoked")
        print("\n   To fix:")
        print("   1. Go to https://www.reddit.com/prefs/apps")
        print("   2. Check your app is still active")
        print("   3. Regenerate the secret if needed")
        print("   4. Update your .env file")
        return False
    
    # 5. Test search functionality
    print("\n5. Testing search functionality...")
    try:
        subreddit = reddit.subreddit("python")
        results = list(subreddit.search("hello world", limit=3, time_filter="week"))
        print(f"   ✓ Search returned {len(results)} results from r/python")
        if results:
            print(f"   ✓ First result: '{results[0].title[:50]}...'")
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        print(f"\n   Error type: {type(e).__name__}")
        
        if "RemoteDisconnected" in str(e) or "Connection aborted" in str(e):
            print("\n   This error suggests:")
            print("   - Reddit may be rate-limiting your IP/credentials")
            print("   - Your credentials may be invalid or expired")
            print("   - There may be a network/proxy issue")
            print("\n   To fix:")
            print("   1. Wait 10-15 minutes and try again (rate limit cooldown)")
            print("   2. Verify credentials at https://www.reddit.com/prefs/apps")
            print("   3. Try regenerating your app secret")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Reddit API is working correctly.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_reddit_credentials()
    sys.exit(0 if success else 1)
