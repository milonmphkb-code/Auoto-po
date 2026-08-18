# main.py — অটো পোস্ট বটের অ্যাডমিন প্যানেল (সম্পূর্ণ বাংলা UI)
from dotenv import load_dotenv
load_dotenv()

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          filters, ContextTypes)

from config import BOT_TOKEN, ADMIN_IDS, SOURCE_CHANNELS
from privacy import PRIVACY

# ═══ স্টেট ও ডেটা ═══
settings = {"autopost": True, "delay_minutes": 0,
            "template": {"header": "", "footer": ""}}
my_channels = {}
user_state = {}   # {user_id: {"step": ..., "type": ...}}

# ═══ ফাইল-ভিত্তিক স্টেট ও স্ট্যাটস (আসল, কাজ করে) ═══
def set_autopost(on: bool):
    with open("autopost.txt", "w") as f:
        f.write("on" if on else "off")

def read_stats():
    pub = skip = 0
    try:
        with open("posts.log") as f:
            for line in f:
                if line.strip() == "published": pub += 1
                elif line.strip() == "skipped": skip += 1
    except FileNotFoundError:
        pass
    return pub, skip

# ═══ UI: মেনুগুলো ═══
def main_kb():
    return ReplyKeyboardMarkup([
        ["📡 চ্যানেল সেটিংস"],
        ["🛡️ প্রাইভেসি ফিল্টার"],
        ["📝 অটো পোস্ট", "📊 পরিসংখ্যান"],
        ["⚙️ সেটিংস", "❓ সাহায্য"],
    ], resize_keyboard=True)

def channel_kb():
    return ReplyKeyboardMarkup([
        ["🏠 আমার চ্যানেল", "📡 সোর্স চ্যানেল"],
        ["⬅️ ফিরে যান"],
    ], resize_keyboard=True)

def privacy_kb():
    return ReplyKeyboardMarkup([
        ["👤 @username", "📞 ফোন"],
        ["✉️ ইমেইল", "🔗 t.me লিংক"],
        ["⬅️ ফিরে যান"],
    ], resize_keyboard=True)

def autopost_kb():
    return ReplyKeyboardMarkup([
        ["🟢 চালু করুন", "🔴 বন্ধ করুন"],
        ["⬅️ ফিরে যান"],
    ], resize_keyboard=True)

def settings_kb():
    return ReplyKeyboardMarkup([
        ["⏱️ ডিলে সেট", "📝 টেমপ্লেট"],
        ["⬅️ ফিরে যান"],
    ], resize_keyboard=True)

def is_admin(uid): return uid in ADMIN_IDS

# ═══ হ্যান্ডলার ═══
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ অনুমতি নেই。"); return
    await update.message.reply_text(
        "👋 স্বাগতম! এটা আপনার **অটো পোস্ট বট**।\n\n"
        "নিচের বাটন থেকে যেকোনো মেনু খুলুন — সব ধাপে ধাপে পরিচালিত হবে।",
        reply_markup=main_kb())

async def handle_forward(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    fwd = update.message.forward_from_chat
    state = user_state.get(update.effective_user.id, {})
    if not fwd or state.get("step") != "await_channel_url" or state.get("type") != "my":
        await update.message.reply_text("💡 প্রথমে '🏠 আমার চ্যানেল' চাপুন, তারপর চ্যানেল থেকে পোস্ট ফরোয়ার্ড করুন。")
        return
    name = fwd.username or str(fwd.id)
    my_channels[name] = {"id": fwd.id, "title": fwd.title or name}
    user_state[update.effective_user.id].pop("step", None)
    await update.message.reply_text(
        f"✅ চ্যানেল যোগ হয়েছে!\n\n📛 নাম: {fwd.title}\n🆔 ID: {fwd.id}",
        reply_markup=channel_kb())

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ অনুমতি নেই。"); return

    # ── ধাপ: চ্যানেল URL ──
    if uid in user_state and user_state[uid]["step"] == "await_channel_url":
        username = t.replace("https://t.me/", "").replace("@", "").split("/")[0]
        try:
            chat = await ctx.bot.get_chat(f"@{username}")
            my_channels[username] = {"id": chat.id, "title": chat.title or username}
            user_state.pop(uid)
            await update.message.reply_text(
                f"✅ ধাপ ২ সম্পন্ন! চ্যানেল যোগ হয়েছে。\n\n"
                f"📛 নাম: {chat.title}\n🆔 ID: {chat.id}", reply_markup=channel_kb())
        except Exception:
            await update.message.reply_text(
                "❌ চ্যানেল পাওয়া যায়নি。\n\n"
                "💡 ধাপ ১: বটকে ওই চ্যানেলে অ্যাডমিন বানান\n"
                "💡 ধাপ ২: আবার URL পাঠান", reply_markup=channel_kb())
        return

    # ── ধাপ: ডিলে ──
    if uid in user_state and user_state[uid]["step"] == "await_delay":
        if not t.strip().isdigit():
            await update.message.reply_text("⚠️ শুধু মিনিট সংখ্যা লিখুন (যেমন: 5)"); return
        settings["delay_minutes"] = int(t.strip())
        user_state.pop(uid)
        await update.message.reply_text(
            f"✅ ডিলে সেট হয়েছে: **{settings['delay_minutes']} মিনিট**。", reply_markup=settings_kb())
        return

    # ── ধাপ: টেমপ্লেট ──
    if uid in user_state and user_state[uid]["step"] in ("await_tmpl_header", "await_tmpl_footer"):
        step = user_state[uid]["step"]
        if step == "await_tmpl_header":
            settings["template"]["header"] = t
            user_state[uid]["step"] = "await_tmpl_footer"
            await update.message.reply_text("✅ হেডার সেভ হয়েছে!\n\n📝 এখন **ফুটার** লিখুন (না চাইলে 'না' লিখুন):")
        else:
            if t.lower() != "না":
                settings["template"]["footer"] = t
            user_state.pop(uid)
            await update.message.reply_text(
                f"✅ টেমপ্লেট সেভ হয়েছে!\n\n"
                f"📌 হেডার: {settings['template']['header'] or '(খালি)'}\n"
                f"📌 ফুটার: {settings['template']['footer'] or '(খালি)'}",
                reply_markup=settings_kb())
        return

    # ── মূল মেনু ──
    if t == "📡 চ্যানেল সেটিংস":
        await update.message.reply_text("📡 চ্যানেল সেটিংস\n\nকোন ধরনের চ্যানেল?", reply_markup=channel_kb())

    elif t == "🏠 আমার চ্যানেল":
        user_state[uid] = {"step": "await_channel_url", "type": "my"}
        lst = "\n".join(f"🟢 {c['title']} ({name})" for name, c in my_channels.items()) or "খালি"
        await update.message.reply_text(
            f"🏠 আমার চ্যানেল:\n{lst}\n\n"
            f"➕ **ধাপ ১:** চ্যানেলের URL পাঠান (t.me/...) বা পোস্ট ফরোয়ার্ড করুন\n"
            f"**ধাপ ২:** ✅ নিশ্চিত মেসেজ পাবেন", reply_markup=channel_kb())

    elif t == "📡 সোর্স চ্যানেল":
        lst = "\n".join(f"📡 {s}" for s in SOURCE_CHANNELS) or "খালি — .env-এ SOURCE_CHANNELS বসান"
        await update.message.reply_text(
            f"📡 সোর্স চ্যানেল (userbot যেগুলো দেখবে):\n{lst}\n\n"
            f"💡 সোর্স চ্যানেল .env-এ বসানো হয় — এখানে অ্যাডমিন লাগে না।", reply_markup=channel_kb())

    elif t == "🛡️ প্রাইভেসি ফিল্টার":
        await update.message.reply_text(
            "🛡️ প্রাইভেসি ফিল্টার\n\nযে তথ্য পোস্ট থেকে মুছে যাবে — চাপ দিয়ে ON/OFF করুন:",
            reply_markup=privacy_kb())

    elif t in ("👤 @username", "📞 ফোন", "✉️ ইমেইল", "🔗 t.me লিংক"):
        key = {"👤 @username": "username", "📞 ফোন": "phone",
               "✉️ ইমেইল": "email", "🔗 t.me লিংক": "tme_link"}[t]
        PRIVACY[key]["on"] = not PRIVACY[key]["on"]
        st = "🟢 চালু" if PRIVACY[key]["on"] else "🔴 বন্ধ"
        await update.message.reply_text(
            f"✅ ফিল্টার আপডেট!\n\n🔍 {t}: {st}\n\n"
            f"⚠️ এই নিয়ম এখন থেকে সোর্স পোস্টে প্রযোজ্য।", reply_markup=privacy_kb())

    elif t == "📝 অটো পোস্ট":
        st = "🟢 চালু" if settings["autopost"] else "🔴 বন্ধ"
        await update.message.reply_text(
            f"📝 অটো পোস্ট\n\n📊 অবস্থা: {st}\n"
            f"📡 সোর্স: {len(SOURCE_CHANNELS)}টা\n\n"
            f"চালু/বন্ধ করতে নিচের বাটন ব্যবহার করুন:", reply_markup=autopost_kb())

    elif t == "🟢 চালু করুন":
        settings["autopost"] = True
        set_autopost(True)
        await update.message.reply_text("✅ অটো পোস্ট চালু হয়েছে!", reply_markup=autopost_kb())

    elif t == "🔴 বন্ধ করুন":
        settings["autopost"] = False
        set_autopost(False)
        await update.message.reply_text("⏸️ অটো পোস্ট বন্ধ করা হয়েছে!", reply_markup=autopost_kb())

    elif t == "📊 পরিসংখ্যান":
        pub, skip = read_stats()
        await update.message.reply_text(
            f"📊 পরিসংখ্যান\n\n"
            f"✅ পাবলিশ: {pub}\n"
            f"⏭️ স্কিপ: {skip}\n"
            f"📡 সোর্স: {len(SOURCE_CHANNELS)}\n"
            f"🏠 চ্যানেল: {len(my_channels)}", reply_markup=main_kb())

    elif t == "⚙️ সেটিংস":
        await update.message.reply_text(
            f"⚙️ সেটিংস\n\n"
            f"⏱️ ডিলে: {settings['delay_minutes']} মিনিট\n"
            f"📌 হেডার: {settings['template']['header'] or '(খালি)'}\n"
            f"📌 ফুটার: {settings['template']['footer'] or '(খালি)'}",
            reply_markup=settings_kb())

    elif t == "⏱️ ডিলে সেট":
        user_state[uid] = {"step": "await_delay"}
        await update.message.reply_text(
            "⏱️ ডিলে সেট\n\n"
            "**ধাপ ১:** কত মিনিট পরে পোস্ট হবে, সংখ্যায় লিখুন (যেমন: 5)\n"
            "**ধাপ ২:** ✅ নিশ্চিত মেসেজ পাবেন")

    elif t == "📝 টেমপ্লেট":
        user_state[uid] = {"step": "await_tmpl_header"}
        await update.message.reply_text(
            "📝 টেমপ্লেট\n\n"
            "**ধাপ ১:** হেডার লিখুন (যেমন: 📢 নতুন আপডেট)\n"
            "**ধাপ ২:** ফুটার লিখুন\n"
            "**ধাপ ৩:** ✅ সেভ হয়ে যাবে")

    elif t == "❓ সাহায্য":
        await update.message.reply_text(
            "❓ সাহায্য\n\n"
            "🤖 এই বট সোর্স চ্যানেলের পোস্ট নিয়ে আপনার চ্যানেলে পোস্ট করে।\n\n"
            "📌 প্রথমে:\n"
            "১. 📡 চ্যানেল সেটিংস → আপনার চ্যানেল যোগ করুন\n"
            "২. .env-এ সোর্স চ্যানেল বসান\n"
            "৩. 📝 অটো পোস্ট চালু রাখুন\n\n"
            "🛡️ প্রাইভেসি ফিল্টার থেকে ব্যক্তিগত তথ্য সরানোর নিয়ম ON/OFF করুন。",
            reply_markup=main_kb())

    elif t == "⬅️ ফিরে যান":
        await update.message.reply_text("🏠 মূল মেনুতে ফিরে এলাম।", reply_markup=main_kb())

    else:
        await update.message.reply_text("❌ চিনতে পারিনি। নিচের বাটন ব্যবহার করুন。", reply_markup=main_kb())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, handle_forward))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle))
    print("🤖 অ্যাডমিন বট চালু হয়েছে")
    app.run_polling()

if __name__ == "__main__":
    main()
