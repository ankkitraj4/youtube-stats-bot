# YouTube Stats Telegram Bot

A Telegram bot that reports your YouTube channel statistics including views, subscribers, video count, and watch hours.

## What It Does

Send a command in Telegram, get your channel stats back:

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with usage info |
| `/stats` | Full report: lifetime views, subscribers, videos, watch hours + last 28 days |
| `/today` | Today's views and watch hours |

**Sample `/stats` output:**

```
My Channel Name
────────────────────────────

Lifetime
  Views: 1,234,567
  Subscribers: 12,345
  Videos: 200
  Watch Hours: 56,789h

Last 28 Days
  Views: 45,678
  Watch Hours: 1,234.5h
```

## Prerequisites

- Python 3.10+ (or Docker)
- A Google account that owns the YouTube channel
- A Telegram account

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Save the **bot token** you receive

### 2. Set Up Google Cloud Credentials

The bot needs OAuth access to your YouTube account to fetch watch hours (the Analytics API requires channel owner authentication).

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable these two APIs:
   - **YouTube Data API v3** — [Enable here](https://console.cloud.google.com/apis/library/youtube.googleapis.com)
   - **YouTube Analytics API** — [Enable here](https://console.cloud.google.com/apis/library/youtubeanalytics.googleapis.com)
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth client ID**
6. Choose **Desktop app** as the application type
7. Download the JSON file and rename it to `client_secret.json`
8. Place `client_secret.json` in this project directory

### 3. Find Your YouTube Channel ID

1. Go to [YouTube Studio](https://studio.youtube.com/)
2. Click your profile icon > **Settings** > **Advanced settings**
3. Copy your **Channel ID** (starts with `UC`)

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxxxxxx
ALLOWED_USER_IDS=123456789
```

`ALLOWED_USER_IDS` is optional. Leave it empty to allow anyone, or set comma-separated Telegram user IDs to restrict access. To find your Telegram user ID, message [@userinfobot](https://t.me/userinfobot).

### 5. Authorize with Google (One-Time)

This step generates a `token.json` that the bot uses to access your YouTube Analytics data.

```bash
pip install google-auth-oauthlib
python3 auth.py
```

A browser window will open. Sign in with the Google account that owns the YouTube channel and grant access. The token is saved locally to `token.json`.

> **Headless server?** Run `auth.py` on a machine with a browser first, then copy `token.json` to the server.

### 6. Run the Bot

**With Docker (recommended):**

```bash
docker compose up -d --build
```

**Without Docker:**

```bash
pip install -r requirements.txt
python3 bot.py
```

## Project Structure

```
youtube-stats-bot/
├── bot.py               # Main bot: Telegram handlers + YouTube API calls
├── auth.py              # One-time OAuth helper to generate token.json
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container image
├── docker-compose.yml   # Docker deployment config
├── .env.example         # Environment variable template
├── .env                 # Your secrets (git-ignored)
├── client_secret.json   # Google OAuth credentials (git-ignored)
└── token.json           # Google OAuth token (git-ignored, created by auth.py)
```

## Troubleshooting

**"Channel not found" error**
- Double-check your `YOUTUBE_CHANNEL_ID` in `.env`. It should start with `UC`.

**"token.json not found" error**
- Run `python3 auth.py` to complete the OAuth flow first.

**"You are not authorized" in Telegram**
- Your Telegram user ID isn't in `ALLOWED_USER_IDS`. Remove the value to allow everyone, or add your ID.

**Watch hours showing 0**
- The YouTube Analytics API can have a 48-72 hour delay for recent data. Lifetime stats should appear immediately.

## License

MIT
