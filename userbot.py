# userbot.py — সোর্স → প্রাইভেসি → টেমপ্লেট → ডিলে → পাবলিশ
import asyncio
from telethon import TelegramClient, events
from telegram.ext import Application

from config import (BOT_TOKEN, API_ID, API_HASH, SESSION, PHONE,
                    SOURCE_CHANNELS, DEST_CHANNEL_ID,
                    DELAY_MINUTES, TEMPLATE_HEADER, TEMPLATE_FOOTER)
from privacy import clean_personal

bot_app = Application.builder().token(BOT_TOKEN).build()
user_client = TelegramClient(SESSION, API_ID, API_HASH)

def autopost_enabled() -> bool:
    try:
        with open("autopost.txt") as f:
            return f.read().strip() == "on"
    except FileNotFoundError:
        return True

def log_post(status: str):
    with open("posts.log", "a") as f:
        f.write(status + "\n")

def apply_template(text: str) -> str:
    parts = []
    if TEMPLATE_HEADER: parts.append(TEMPLATE_HEADER)
    parts.append(text)
    if TEMPLATE_FOOTER: parts.append(TEMPLATE_FOOTER)
    return "\n\n".join(parts)

@user_client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def on_new_post(event):
    if not autopost_enabled():
        print("⏸️ অটো পোস্ট বন্ধ — স্কিপ"); return

    msg = event.message
    text = msg.text or msg.message or ""
    if not text.strip():
        print("📎 মিডিয়া পোস্ট — এই ধাপে স্কিপ"); log_post("skipped"); return

    safe = clean_personal(text)              # 🛡️ ধাপ ১: প্রাইভেসি ফিল্টার
    if not safe:
        print("⏭️ ফিল্টারে সব মুছে গেছে — স্কিপ"); log_post("skipped"); return

    final = apply_template(safe)             # 📝 ধাপ ২: টেমপ্লেট

    if DELAY_MINUTES > 0:                    # ⏱️ ধাপ ৩: ডিলে
        print(f"⏱️ {DELAY_MINUTES} মিনিট পর পোস্ট হবে...")
        await asyncio.sleep(DELAY_MINUTES * 60)

    await bot_app.bot.send_message(DEST_CHANNEL_ID, final)   # 🚀 ধাপ ৪: পাবলিশ
    log_post("published")
    print(f"✅ পোস্ট হয়েছে → {final[:50]}...")

async def main():
    await bot_app.initialize()
    await bot_app.start()
    await user_client.start(phone=PHONE)     # প্রথমবার OTP চাইবে
    print(f"👀 {len(SOURCE_CHANNELS)}টা সোর্স চ্যানেল দেখা হচ্ছে...")
    await user_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
