import requests
import json
from datetime import datetime
from onepassword_config import get_config_value

def create_bluesky_session():
    """Create a BlueSky session and return the access token"""
    bluesky_handle = get_config_value("BLUESKY_HANDLE")
    bluesky_password = get_config_value("BLUESKY_APP_PASSWORD")
    
    if not bluesky_handle or not bluesky_password:
        print("BlueSky credentials not found in configuration")
        print("Please ensure BLUESKY_HANDLE and BLUESKY_APP_PASSWORD are set in .env.template with valid 1Password references")
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
    print(f"Starting BlueSky fetch for '{search_term}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get authentication token
    access_token = create_bluesky_session()
    if not access_token:
        print("Failed to authenticate with BlueSky - skipping BlueSky posts")
        return []

    url = "https://bsky.social/xrpc/app.bsky.feed.searchPosts"  # Use authenticated endpoint
    params = {
        "q": search_term,
        "limit": post_count
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "posts" in data:
            print(f"Found {len(data['posts'])} BlueSky posts for '{search_term}'")
            return data["posts"]
        else:
            print("No posts found in BlueSky response")
            return []

    except requests.exceptions.RequestException as e:
        print(f"Error fetching BlueSky posts: {e}")
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
