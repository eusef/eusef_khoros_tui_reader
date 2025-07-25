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
    def authenticate():
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
                # print("key", new_key)

                # Optionally: update .env here or store in-memory
                os.environ["sessionKey"] = new_key
                os.environ["sessionStartTime"] = str(now)
                os.environ["sessionLastUsed"] = str(now)

        except requests.exceptions.RequestException as e:
            print("HTTP error:", e)

    authenticate()
else:
    os.environ["sessionLastUsed"] = str(now)
