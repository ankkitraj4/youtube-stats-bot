import os
import logging
from datetime import datetime, timedelta

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
YOUTUBE_CHANNEL_ID = os.environ["YOUTUBE_CHANNEL_ID"]
ALLOWED_USER_IDS = {
    int(uid.strip())
    for uid in os.environ.get("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
}

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

TOKEN_PATH = os.environ.get("TOKEN_PATH", "token.json")


def _get_credentials() -> Credentials:
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def _build_data_api():
    return build("youtube", "v3", credentials=_get_credentials())


def _build_analytics_api():
    return build("youtubeAnalytics", "v2", credentials=_get_credentials())


def _format_number(n: int) -> str:
    """Compact format: 1234567 -> 1,234,567"""
    return f"{n:,}"


def _is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS


def get_channel_stats() -> dict:
    yt = _build_data_api()
    resp = yt.channels().list(
        part="statistics,snippet",
        id=YOUTUBE_CHANNEL_ID,
    ).execute()

    if not resp.get("items"):
        raise ValueError("Channel not found. Check YOUTUBE_CHANNEL_ID.")

    item = resp["items"][0]
    stats = item["statistics"]
    return {
        "title": item["snippet"]["title"],
        "views": int(stats.get("viewCount", 0)),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "videos": int(stats.get("videoCount", 0)),
    }


def get_watch_hours(start_date: str, end_date: str) -> float:
    analytics = _build_analytics_api()
    resp = analytics.reports().query(
        ids=f"channel=={YOUTUBE_CHANNEL_ID}",
        startDate=start_date,
        endDate=end_date,
        metrics="estimatedMinutesWatched,views",
    ).execute()

    rows = resp.get("rows", [])
    if not rows:
        return 0.0, 0
    minutes = rows[0][0]
    views = rows[0][1]
    return round(minutes / 60, 1), views


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    await update.message.reply_text(
        "YouTube Stats Bot\n\n"
        "Commands:\n"
        "/stats - Full channel report (lifetime + last 28 days)\n"
        "/today - Today's stats snapshot\n"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    await update.message.reply_text("Fetching stats...")

    try:
        ch = get_channel_stats()

        end = datetime.utcnow().strftime("%Y-%m-%d")
        start_28d = (datetime.utcnow() - timedelta(days=28)).strftime("%Y-%m-%d")
        watch_hours_28d, views_28d = get_watch_hours(start_28d, end)

        start_lifetime = "2005-01-01"
        watch_hours_lifetime, _ = get_watch_hours(start_lifetime, end)

        msg = (
            f"<b>{ch['title']}</b>\n"
            f"{'─' * 28}\n\n"
            f"<b>Lifetime</b>\n"
            f"  Views: {_format_number(ch['views'])}\n"
            f"  Subscribers: {_format_number(ch['subscribers'])}\n"
            f"  Videos: {_format_number(ch['videos'])}\n"
            f"  Watch Hours: {_format_number(int(watch_hours_lifetime))}h\n\n"
            f"<b>Last 28 Days</b>\n"
            f"  Views: {_format_number(views_28d)}\n"
            f"  Watch Hours: {watch_hours_28d}h\n"
        )

        await update.message.reply_text(msg, parse_mode="HTML")

    except Exception as e:
        logger.exception("Failed to fetch stats")
        await update.message.reply_text(f"Error: {e}")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    await update.message.reply_text("Fetching today's stats...")

    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        watch_hours, views = get_watch_hours(today, today)

        msg = (
            f"<b>Today ({today})</b>\n"
            f"{'─' * 28}\n\n"
            f"  Views: {_format_number(views)}\n"
            f"  Watch Hours: {watch_hours}h\n"
        )

        await update.message.reply_text(msg, parse_mode="HTML")

    except Exception as e:
        logger.exception("Failed to fetch today's stats")
        await update.message.reply_text(f"Error: {e}")


def main():
    if not YOUTUBE_CHANNEL_ID:
        raise SystemExit("YOUTUBE_CHANNEL_ID is required in .env")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("today", today_command))

    logger.info("Bot started — polling for updates")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
