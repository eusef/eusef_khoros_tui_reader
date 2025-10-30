import requests
import json
from datetime import datetime
from onepassword_config import get_config_value

def create_mastodon_session():
    """Get Mastodon bearer token from 1Password configuration"""
    mastodon_server = get_config_value("MASTODON_SERVER")
    mastodon_token = get_config_value("MASTODON_ACCESS_TOKEN")
    
    if not mastodon_server:
        print("Mastodon credentials not found in configuration")
        print("  MASTODON_SERVER is missing")
        print("  Please ensure MASTODON_SERVER is set in .env.template with a valid 1Password reference")
        return None, None
    
    if not mastodon_token:
        print("Mastodon credentials not found in configuration")
        print("  MASTODON_ACCESS_TOKEN is missing")
        print("  Please ensure MASTODON_ACCESS_TOKEN is set in .env.template with a valid 1Password reference")
        return None, None
    
    # Ensure server URL has proper format
    if not mastodon_server.startswith('http'):
        mastodon_server = f"https://{mastodon_server}"
    
    print(f"Mastodon authentication configured for {mastodon_server}")
    return mastodon_server, mastodon_token

def fetch_mastodon_posts(search_term="1password", post_count=50):
    """Fetch posts from Mastodon using the search API"""
    import os
    debug = os.getenv('FETCH_DEBUG') == '1'
    
    if debug:
        print(f"\n{'='*60}")
        print(f"🐘 MASTODON FETCH DEBUG")
        print(f"{'='*60}")
        print(f"Starting Mastodon fetch for '{search_term}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Requested post count: {post_count}")
        print("\n[1/3] Getting Mastodon credentials...")
    
    # Get authentication credentials
    server_url, access_token = create_mastodon_session()
    if not server_url or not access_token:
        if debug:
            print("❌ Failed to get Mastodon credentials - skipping Mastodon posts")
            print(f"  Server URL: {server_url or 'NOT SET'}")
            print(f"  Access token: {'SET' if access_token else 'NOT SET'}")
            print(f"{'='*60}\n")
        return []
    
    if debug:
        print(f"✅ Credentials loaded")
        print(f"  Server: {server_url}")
    
    # Use Mastodon v2 search API
    url = f"{server_url}/api/v2/search"
    actual_limit = min(post_count, 40)  # API max is 40 per request
    params = {
        "q": search_term,
        "type": "statuses",  # Only search for statuses/posts
        "limit": actual_limit,
        "resolve": "false"  # Don't resolve remote URLs for better performance
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    if debug:
        print(f"\n[2/3] Fetching posts from Mastodon API...")
        print(f"URL: {url}")
        print(f"Search term: '{search_term}'")
        print(f"Limit: {actual_limit}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if debug:
            print(f"Response status code: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        
        if "statuses" in data and data["statuses"]:
            statuses = data["statuses"]
            if debug:
                print(f"\n[3/3] ✅ Found {len(statuses)} Mastodon posts for '{search_term}'")
                if len(statuses) > 0:
                    print(f"First post author: @{statuses[0].get('account', {}).get('username', 'unknown')}")
                    content_preview = statuses[0].get('content', '')[:60].replace('<', '').replace('>', '')
                    print(f"First post content (preview): {content_preview}...")
                print(f"{'='*60}\n")
            return statuses
        else:
            if debug:
                print(f"\n[3/3] ⚠️  No statuses found in Mastodon response")
                print(f"Response keys: {list(data.keys())}")
                if "statuses" in data:
                    print(f"Statuses list length: {len(data['statuses'])}")
                print(f"{'='*60}\n")
            return []
            
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"\n[3/3] ❌ Error fetching Mastodon posts: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response text: {e.response.text[:200]}")
            print(f"{'='*60}\n")
        return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch posts from Mastodon')
    parser.add_argument('--search-term', '-s', default='1password',
                       help='Search term for Mastodon posts (default: 1password)')
    parser.add_argument('--count', '-c', type=int, default=50,
                       help='Number of posts to fetch (default: 50)')
    parser.add_argument('--write-output', '-w', action='store_true',
                        help='Write results to an output file')
    parser.add_argument('--output-file', '-o', default='mastodon_data.json',
                        help='Output file path (default: mastodon_data.json)')
    args = parser.parse_args()
    
    posts = fetch_mastodon_posts(args.search_term, args.count)
    
    if posts and args.write_output:
        with open(args.output_file, 'w') as f:
            json.dump(posts, f, indent=4)
        print(f"Output written to {args.output_file}")
