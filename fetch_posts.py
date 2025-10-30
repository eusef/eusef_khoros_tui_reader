import requests
import json
from datetime import datetime
from auth import get_auth_token, get_hostname

def fetch_posts(community_url, message_count=100):
    import os
    debug = os.getenv('FETCH_DEBUG') == '1'
    
    if debug:
        print(f"Starting fetch at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get authentication token
    auth_token = get_auth_token()
    if not auth_token:
        if debug:
            print("Error: No authentication token available")
        return None
    if debug:
        print("Authentication successful")

    # GraphQL query
    query = """
    query($messageCount: Int!) {
        messages(first: $messageCount) {
            edges {
            node {
                id
                subject
                postTime
                viewHref
                body
                author {
                title
                lastName
                firstName
                }
            }
            }
        }
    }
    """

    # Variables for the query
    variables = {
        "messageCount": message_count
    }

    # Headers including auth token with cache-busting
    headers = {
        "Content-Type": "application/json",
        "li-api-session-key": auth_token,
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    # Make the request
    url = f"https://{community_url}/t5/s/api/2.1/graphql"
    if debug:
        print(f"Fetching messages from: {community_url}")
    
    request_payload = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(
        url,
        json=request_payload,
        headers=headers,
        timeout=30
    )

    if debug:
        print(f"Response status: {response.status_code}")

    # Check if request was successful
    if response.status_code == 200:
        response_dict = response.json()  # Safely parse JSON response

        # Extract the messages data
        messages = response_dict.get('data', {}).get('messages', {}).get('edges', [])
        if debug:
            print(f"Found {len(messages)} messages")

            # Extract the author information for each message
            for i, message in enumerate(messages):
                node = message.get('node', {})
                author = node.get('author', {})
                post_time = node.get('postTime', '')
                subject = node.get('subject', '')
                
                print(f"Message {i+1}:")
                print(f"  ID: {node.get('id')}")
                print(f"  Subject: {subject}")
                print(f"  Post Time: {post_time}")
                print(f"  Author: {author.get('firstName')} {author.get('lastName')}")
                print("  ---")

        return response.json()
    else:
        print(f"Request failed: {response.text}")
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

# Example usage:
if __name__ == "__main__":
    # Get hostname and auth token from auth module
    hostname = get_hostname()
    auth_token = get_auth_token()

    # Add command line argument parsing
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch posts from the community')
    parser.add_argument('--write-output', '-w', action='store_true',
                       help='Write results to output file for testing')
    parser.add_argument('--output-file', '-o', default='current_data.json',
                       help='Output file path (default: current_data.json)')
    parser.add_argument('--count', '-c', type=int, default=100,
                       help='Number of messages to fetch (default: 100)')
    args = parser.parse_args()
    
    try:
        result = fetch_posts(hostname, args.count)
        print(f"Successfully fetched {args.count} messages")
        
        # Write output if requested
        if args.write_output and result:
            with open(args.output_file, 'w') as f:
                json.dump(result, f, indent=4)
            print(f"Output written to {args.output_file}")
    except Exception as e:
        print("Error fetching data:")
        print(f"Technical details: {str(e)}")
        exit(1)
