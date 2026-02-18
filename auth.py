"""
One-time OAuth helper.

Run this script locally (not inside Docker) to authorize the bot
with your Google account. It will open a browser for you to sign in,
then save the resulting token to token.json.

Usage:
    pip install google-auth-oauthlib
    python3 auth.py

Prerequisites:
    1. Download your OAuth client_secret.json from Google Cloud Console
    2. Place it in this directory (youtube-stats-bot/)
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

CLIENT_SECRET = os.environ.get("CLIENT_SECRET_PATH", "client_secret.json")
TOKEN_PATH = os.environ.get("TOKEN_PATH", "token.json")


def main():
    if not os.path.exists(CLIENT_SECRET):
        raise SystemExit(
            f"{CLIENT_SECRET} not found.\n"
            "Download it from Google Cloud Console -> APIs & Services -> Credentials\n"
            "and place it in this directory."
        )

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"Authorization successful! Token saved to {TOKEN_PATH}")
    print("You can now start the bot with: docker-compose up -d")


if __name__ == "__main__":
    main()
