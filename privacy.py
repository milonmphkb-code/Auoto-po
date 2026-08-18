import re

# 🛡️ প্রাইভেসি ফিল্টার — প্রতিটা রুল ON/OFF (অ্যাডমিন প্যানেল থেকে)
PRIVACY = {
    "username": {"on": True,  "pattern": r"@[\w\d_]{3,}"},
    "tme_link": {"on": True,  "pattern": r"https?://t\.me/[\w\d_]+"},
    "phone":    {"on": True,  "pattern": r"(?<![\d])(?:\+?88)?01[3-9]\d{8}(?![\d])"},
    "email":    {"on": True,  "pattern": r"[\w.+-]+@[\w-]+\.[\w.]+"},
    "user_id":  {"on": False, "pattern": r"(?<![\d])\d{9,10}(?![\d])"},
}

def clean_personal(text: str) -> str:
    """সব ON রুল প্রয়োগ করে ব্যক্তিগত তথ্য মুছে দেয়"""
    for name, rule in PRIVACY.items():
        if rule["on"]:
            text = re.sub(rule["pattern"], "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
