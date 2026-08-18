import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}
API_ID = int(os.getenv("TELEGRAM_API_ID") or "0")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION = os.getenv("TELEGRAM_SESSION", "session_name")
PHONE = os.getenv("TELEGRAM_PHONE")
SOURCE_CHANNELS = [s.strip() for s in os.getenv("SOURCE_CHANNELS", "").split(",") if s.strip()]
DEST_CHANNEL_ID = int(os.getenv("DEST_CHANNEL_ID") or "0")
DELAY_MINUTES = int(os.getenv("DELAY_MINUTES") or "0")
TEMPLATE_HEADER = os.getenv("TEMPLATE_HEADER", "")
TEMPLATE_FOOTER = os.getenv("TEMPLATE_FOOTER", "")
