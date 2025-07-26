# This is based on the discussion on the Khoros boards and have been adjusted to Python for our purposes.
# src. https://community.khoros.com/discussions/studio/can-someone-walk-me-through-authenticating-and-using-postman-with-aurora/765348

import os
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
session_key = os.getenv("sessionKey", "")
hostname = os.getenv("hostname")
tapestry = os.getenv("tapestry")
username = os.getenv("username")
password = os.getenv("password")
session_start_time = int(os.getenv("sessionStartTime") or "0")
session_last_used = int(os.getenv("sessionLastUsed") or "0")

def get_auth_token():
    """Get the authentication token, re-authenticating if necessary."""
    global session_key, session_start_time, session_last_used
    
    # Time calculations
    now = int(time.time() * 1000)
    thirty_mins_ago = now - (1000 * 60 * 30)
    two_hours_ago = now - (1000 * 60 * 60 * 2)

    # Determine if re-authentication is needed
    if (
        session_last_used == 0
        or session_start_time == 0
        or session_last_used < thirty_mins_ago
        or session_start_time < two_hours_ago
        or session_key == ""
    ):
        print("authenticating")
        authenticate()
    
    # Update last used time
    os.environ["sessionLastUsed"] = str(now)
    session_last_used = now
    
    return session_key

def get_hostname():
    """Get the hostname from environment variables."""
    return hostname

def authenticate():
    """Authenticate and get a new session key."""
    global session_key, session_start_time
    
    url = (
        f"https://{hostname}/{tapestry}/s/restapi/vc/authentication/sessions/login"
        f"?user.login={username}&user.password={password}&restapi.response_format=json"
    )

    try:
        response = requests.post(url)
        response.raise_for_status()
        data = response.json()

        if "error" in data.get("response", {}):
            print(data["response"]["error"]["message"])
            raise Exception("Authentication failed")
        else:
            new_key = data["response"]["value"]["$"]
            print("key", new_key)

            # Update environment variables
            os.environ["sessionKey"] = new_key
            os.environ["sessionStartTime"] = str(int(time.time() * 1000))
            
            # Update global variables
            session_key = new_key
            session_start_time = int(time.time() * 1000)

    except requests.exceptions.RequestException as e:
        print("HTTP error:", e)
        raise

# Initialize authentication if needed when module is imported
if __name__ == "__main__":
    get_auth_token()
