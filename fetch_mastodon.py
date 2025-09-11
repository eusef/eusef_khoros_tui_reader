import requests
import json
import os
from datetime import datetime

def create_mastodon_session():
    """Get Mastodon bearer token from environment variables"""
    mastodon_server = os.getenv("MASTODON_SERVER")
    mastodon_token = os.getenv("MASTODON_ACCESS_TOKEN")
    
    if not mastodon_server or not mastodon_token:
        print("Mastodon credentials not found in environment variables")
        print("Please set MASTODON_SERVER and MASTODON_ACCESS_TOKEN")
        return None, None
    
    # Ensure server URL has proper format
    if not mastodon_server.startswith('http'):
        mastodon_server = f"https://{mastodon_server}"
    
    print(f"Mastodon authentication configured for {mastodon_server}")
    return mastodon_server, mastodon_token

def fetch_mastodon_posts(search_term="1password", post_count=50):
    """Fetch posts from Mastodon using the search API"""
    print(f"Starting Mastodon fetch for '{search_term}' at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get authentication credentials
    server_url, access_token = create_mastodon_session()
    if not server_url or not access_token:
        print("Failed to get Mastodon credentials - skipping Mastodon posts")
        return []
    
    # Use Mastodon v2 search API
    url = f"{server_url}/api/v2/search"
    params = {
        "q": search_term,
        "type": "statuses",  # Only search for statuses/posts
        "limit": min(post_count, 40),  # API max is 40 per request
        "resolve": "false"  # Don't resolve remote URLs for better performance
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "statuses" in data and data["statuses"]:
            statuses = data["statuses"]
            print(f"Found {len(statuses)} Mastodon posts for '{search_term}'")
            return statuses
        else:
            print("No posts found in Mastodon response")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Mastodon posts: {e}")
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
