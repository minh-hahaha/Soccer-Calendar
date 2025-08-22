import base64
import hashlib
import os
import re
import secrets
import uuid

from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = "bfcbaf69-aade-4c1b-8f00-c1cb8a193030"
URLS = {
    "auth": "https://account.premierleague.com/as/authorize",
    "start": "https://account.premierleague.com/davinci/policy/262ce4b01d19dd9d385d26bddb4297b6/start",
    "login": "https://account.premierleague.com/davinci/connections/{}/capabilities/customHTMLTemplate",
    "resume": "https://account.premierleague.com/as/resume",
    "token": "https://account.premierleague.com/as/token",
    "me": "https://fantasy.premierleague.com/api/me/",
}
STANDARD_CONNECTION_ID = "0d8c928e4970386733ce110b9dda8412"


def generate_code_verifier():
    return secrets.token_urlsafe(64)[:128]


def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


code_verifier = generate_code_verifier()  # code_verifier for PKCE
code_challenge = generate_code_challenge(code_verifier)  # code_challenge from the code_verifier
initial_state = uuid.uuid4().hex  # random initial state for the OAuth flow

session = requests.Session(impersonate="chrome124")

# Step 1: Request authorization page
params = {
    "client_id": "bfcbaf69-aade-4c1b-8f00-c1cb8a193030",
    "redirect_uri": "https://fantasy.premierleague.com/",
    "response_type": "code",
    "scope": "openid profile email offline_access",
    "state": initial_state,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
}
auth_response = session.get(URLS["auth"], params=params)
login_html = auth_response.text

access_token = re.search(r'"accessToken":"([^"]+)"', login_html).group(1)
# need to read state here for when we resume the OAuth flow later on
new_state = re.search(r'<input[^>]+name="state"[^>]+value="([^"]+)"', login_html).group(1)


# Step 2: Use accessToken to get interaction id and token
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}
response = session.post(URLS["start"], headers=headers).json()
interaction_id = response["interactionId"]
interaction_token = response["interactionToken"]

# Step 3: log in with interaction tokens (requires 3 post requests)
response = session.post(
    URLS["login"].format(STANDARD_CONNECTION_ID),
    headers={
        "interactionId": interaction_id,
        "interactionToken": interaction_token,
    },
    json={
        "id": response["id"],
        "eventName": "continue",
        "parameters": {"eventType": "polling"},
        "pollProps": {"status": "continue", "delayInMs": 10, "retriesAllowed": 1, "pollChallengeStatus": False},
    },
)

response = session.post(
    URLS["login"].format(STANDARD_CONNECTION_ID),
    headers={
        "interactionId": interaction_id,
        "interactionToken": interaction_token,
    },
    json={
        "id": response.json()["id"],
        "nextEvent": {
            "constructType": "skEvent",
            "eventName": "continue",
            "params": [],
            "eventType": "post",
            "postProcess": {},
        },
        "parameters": {
            "buttonType": "form-submit",
            "buttonValue": "SIGNON",
            "username": os.getenv("EMAIL"),
            "password": os.getenv("PASSWORD"),
        },
        "eventName": "continue",
    },
).json()

response = session.post(
    URLS["login"].format(response["connectionId"]),  # need to use new connectionId from prev response
    headers=headers,
    json={
        "id": response["id"],
        "nextEvent": {
            "constructType": "skEvent",
            "eventName": "continue",
            "params": [],
            "eventType": "post",
            "postProcess": {},
        },
        "parameters": {
            "buttonType": "form-submit",
            "buttonValue": "SIGNON",
        },
        "eventName": "continue",
    },
)

# Step 4: Resume the login using the dv_response and handle redirect
response = session.post(
    URLS["resume"],
    data={
        "dvResponse": response.json()["dvResponse"],
        "state": new_state,
    },
    allow_redirects=False,
)

location = response.headers["Location"]
auth_code = re.search(r"[?&]code=([^&]+)", location).group(1)

# Step 5: Exchange auth code for access token
response = session.post(
    URLS["token"],
    data={
        "grant_type": "authorization_code",
        "redirect_uri": "https://fantasy.premierleague.com/",
        "code": auth_code,  # from the parsed redirect URL
        "code_verifier": code_verifier,  # the original code_verifier generated at the start
        "client_id": "bfcbaf69-aade-4c1b-8f00-c1cb8a193030",
    },
)

access_token = response.json()["access_token"]
response = session.get(URLS["me"], headers={"X-API-Authorization": f"Bearer {access_token}"})

print (access_token)
print(response.json())


