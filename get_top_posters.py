import requests
import json
from auth import get_auth_token, get_hostname

def fetch_top_posters(community_url, num_users):
    # Get authentication token
    auth_token = get_auth_token()

    # GraphQL query
    query = """
    {
        messages(first: 10) {
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
    }

    # Headers including auth token
    headers = {
        # "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "li-api-session-key": auth_token
    }

    # Make the request
    response = requests.post(
        f"https://{community_url}/t5/s/api/2.1/graphql",
        json={
            "query": query,
            "variables": variables
        },
        headers=headers
    )

    # Check if request was successful
    if response.status_code == 200:

        response_dict = response.json()  # Safely parse JSON response

        # Extract the messages data
        messages = response_dict.get('data', {}).get('messages', {}).get('edges', [])

        # Extract the author information for each message
        for message in messages:
            author = message.get('node', {}).get('author', {})
            print(f"Message ID: {message.get('node', {}).get('id')}")
            print(f"Author: {author.get('firstName')} {author.get('lastName')}")
            print(f"Message: {message.get('node', {}).get('body')}")
            print(f"Subject: {message.get('node', {}).get('subject')}")
            print(f"Post Time: {message.get('node', {}).get('postTime')}")
            print(f"View Href: {message.get('node', {}).get('viewHref')}")
            print("--------------------------------")

        return response.json()
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

# Example usage:
if __name__ == "__main__":
    # Get hostname and auth token from auth module
    hostname = get_hostname()
    auth_token = get_auth_token()
    
    try:
        result = fetch_top_posters(hostname, 10)
    except Exception as e:
        print("Error fetching data:")
        print(f"Technical details: {str(e)}")
        exit(1)
    print(result)
