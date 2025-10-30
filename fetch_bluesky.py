import requests
import json
from datetime import datetime
from onepassword_config import get_config_value

def create_bluesky_session():
    """Create a BlueSky session and return the access token"""
    bluesky_handle = get_config_value("BLUESKY_HANDLE")
    bluesky_password = get_config_value("BLUESKY_APP_PASSWORD")
    
    if not bluesky_handle:
        print("BlueSky credentials not found in configuration")
        print("  BLUESKY_HANDLE is missing")
        print("  Please ensure BLUESKY_HANDLE is set in .env.template with a valid 1Password reference")
        return None
    
    if not bluesky_password:
        print("BlueSky credentials not found in configuration")
        print("  BLUESKY_APP_PASSWORD is missing")
        print("  Please ensure BLUESKY_APP_PASSWORD is set in .env.template with a valid 1Password reference")
        return None
    
    try:
        response = requests.post(
            "https://bsky.social/xrpc/com.atproto.server.createSession",
            json={"identifier": bluesky_handle, "password": bluesky_password},
            timeout=30
        )
        
        if response.status_code == 200:
            session = response.json()
            access_token = session.get("accessJwt")
            print(f"BlueSky authentication successful for {bluesky_handle}")
            return access_token
        else:
            print(f"BlueSky authentication failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error creating BlueSky session: {e}")
        return None

def fetch_bluesky_posts(search_term="1password", post_count=50):
    import os
    debug = os.getenv('FETCH_DEBUG') == '1'
    
    if debug:
        print(f"\n{'='*60}")
        print(f"🦋 BLUESKY FETCH DEBUG")
        print(f"{'='*60}")
        print(f"Starting BlueSky fetch for '{search_term}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Requested post count: {post_count}")
        print("\n[1/3] Authenticating with BlueSky...")

    # Get authentication token
    access_token = create_bluesky_session()
    if not access_token:
        if debug:
            print("❌ Failed to authenticate with BlueSky - skipping BlueSky posts")
            print(f"{'='*60}\n")
        return []
    
    if debug:
        print("✅ Authentication successful")

    url = "https://bsky.social/xrpc/app.bsky.feed.searchPosts"
    params = {
        "q": search_term,
        "limit": post_count
    }
    
    if debug:
        print(f"\n[2/3] Fetching posts from BlueSky API...")
        print(f"URL: {url}")
        print(f"Search term: '{search_term}'")
        print(f"Limit: {post_count}")

    try:
        response = requests.get(url, params=params, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}, timeout=30)
        if debug:
            print(f"Response status code: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        if "posts" in data:
            post_count_actual = len(data['posts'])
            if debug:
                print(f"\n[3/3] ✅ Found {post_count_actual} BlueSky posts for '{search_term}'")
                if post_count_actual > 0:
                    print(f"First post author: {data['posts'][0].get('author', {}).get('handle', 'unknown')}")
                    print(f"First post text (preview): {data['posts'][0].get('record', {}).get('text', '')[:60]}...")
                print(f"{'='*60}\n")
            return data["posts"]
        else:
            if debug:
                print("\n[3/3] ❌ No 'posts' key in BlueSky response")
                print(f"Response keys: {list(data.keys())}")
                print(f"{'='*60}\n")
            return []

    except requests.exceptions.RequestException as e:
        if debug:
            print(f"\n[3/3] ❌ Error fetching BlueSky posts: {e}")
            print(f"{'='*60}\n")
        return []

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Fetch posts from BlueSky')
    parser.add_argument('--search-term', '-s', default='1password',
                       help='Search term for BlueSky posts (default: 1password)')
    parser.add_argument('--count', '-c', type=int, default=50,
                       help='Number of posts to fetch (default: 50)')
    parser.add_argument('--write-output', '-w', action='store_true',
                        help='Write results to an output file')
    parser.add_argument('--output-file', '-o', default='bluesky_data.json',
                        help='Output file path (default: bluesky_data.json)')
    args = parser.parse_args()

    posts = fetch_bluesky_posts(args.search_term, args.count)

    if posts and args.write_output:
        with open(args.output_file, 'w') as f:
            json.dump(posts, f, indent=4)
        print(f"Output written to {args.output_file}")
