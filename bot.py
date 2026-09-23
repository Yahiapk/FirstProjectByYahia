import os
import telebot
import requests
import re
import random
import string
import time
from PIL import Image
from io import BytesIO
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TELEGRAM_TOKEN = "8708302621:AAFAKBSzXgbq7p5fMimAIJuqqVEcIivTFmw"
ADMIN_ID = 1283009799

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
BOT_ID = int(TELEGRAM_TOKEN.split(':')[0])

user_requests = {}
user_selected_mode = {}
user_state = {}

DEV_SIGNATURE = "\n\n━━━━━━━━━━━━━\n💻 *Dev: Yahia | المطور يحيى*\n⚠️ _ديربالك على عيونك لأن بس تصبح الصباح ينعمن من نور يحيى_"

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = KeyboardButton("📥 تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا)")
    btn2 = KeyboardButton("🔍 صيد يوزرات تيليجرام الحقيقي (صاروخي)")
    btn3 = KeyboardButton("✨ زخرفة الأسماء الاحترافية")
    btn4 = KeyboardButton("🎨 تحويل الصورة إلى رسم بالنقاط")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def get_features_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🎬 تنزيل فيديو تيك توك", callback_data="setmode_tt_video"),
        InlineKeyboardButton("🎶 تنزيل أغنية تيك توك", callback_data="setmode_tt_audio"),
        InlineKeyboardButton("📹 تنزيل فيديو يوتيوب", callback_data="setmode_yt_video"),
        InlineKeyboardButton("🎵 تنزيل أغنية يوتيوب", callback_data="setmode_yt_audio"),
        InlineKeyboardButton("📸 تنزيل فيديو انستغرام", callback_data="setmode_insta_video"),
        InlineKeyboardButton("🎵 تنزيل صوت/أغنية انستغرام", callback_data="setmode_insta_audio")
    )
    return markup

def get_video_quality_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 360p", callback_data="q_360"), InlineKeyboardButton("📺 720p HD", callback_data="q_720"))
    markup.row(InlineKeyboardButton("🖥 1080p Full HD", callback_data="q_1080"), InlineKeyboardButton("🌟 4K / Max", callback_data="q_max"))
    return markup

def get_audio_quality_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎧 128 kbps", callback_data="q_audio_128"), InlineKeyboardButton("🎵 320 kbps HQ", callback_data="q_audio_320"))
    return markup

def get_media_type_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎬 تنزيل فيديو", callback_data="type_video"), InlineKeyboardButton("🎵 تنزيل صوت", callback_data="type_audio"))
    return markup

def get_hunt_types_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("⚡ صيد سريع حقيقي: (x_x1)", callback_data="hunt_type_1"),
        InlineKeyboardButton("⚡ صيد شبه ثلاثي/رباعي: (x1_x1)", callback_data="hunt_type_2"),
        InlineKeyboardButton("⚡ صيد مميز: (x_1x1)", callback_data="hunt_type_3")
    )
    return markup

def generate_random_matrix():
    bits = ["".join(random.choices("01", k=8)) for _ in range(4)]
    return " ".join(bits)

def generate_target_username(htype):
    letters = string.ascii_lowercase
    digits = string.digits
    
    if htype == "1":
        # نمط مثل x_x1 أو x_1x
        c1, c2 = random.choice(letters), random.choice(letters)
        d1 = random.choice(digits)
        return f"{c1}_{c2}{d1}"
    elif htype == "2":
        # نمط مثل x1_x1
        c1, c2 = random.choice(letters), random.choice(letters)
        d1, d2 = random.choice(digits), random.choice(digits)
        return f"{c1}{d1}_{c2}{d2}"
    else:
        # نمط مميز مثل x_1x1
        c1, c2 = random.choice(letters), random.choice(letters)
        d1, d2 = random.choice(digits), random.choice(digits)
        return f"{c1}_{d1}{c2}{d2}"

def check_telegram_username_real(username):
    """فحص حقيقي 100% عبر سيرفرات تيليجرام"""
    try:
        url = f"https://t.me/{username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            # إذا ظهر زر "If you have Telegram, you can contact..." واليوزر غير مستخدم تكون الصفحة خالية من أزرار التواصل
            text = res.text
            if "tgme_page_extra" not in text and "Preview channel" not in text and "Send Message" not in text:
                return True
    except:
        pass
    return False

def process_tiktok(chat_id, url, is_audio):
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}&hd=1"
        res = requests.get(api_url, timeout=15).json()
        if res.get("code") == 0:
            data = res.get("data", {})
            if is_audio:
                bot.send_audio(chat_id, data.get("music"), caption=f"🎶 *تيك توك | تم تحميل الصوت بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                return True
            else:
                bot.send_video(chat_id, data.get("hdplay") or data.get("play"), caption=f"🎬 *تيك توك | تم تحميل الفيديو بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                return True
    except:
        pass
    return False

def process_instagram(chat_id, url, is_audio):
    try:
        payload = {"url": url, "videoQuality": "max", "downloadMode": "audio" if is_audio else "auto"}
        res = requests.post("https://co.wuk.sh/api/json", json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=12)
        if res.status_code == 200:
            dl_url = res.json().get("url")
            if dl_url:
                if is_audio:
                    bot.send_audio(chat_id, dl_url, caption=f"🎵 *انستغرام | تم تحميل الصوت/الأغنية بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                else:
                    bot.send_video(chat_id, dl_url, caption=f"📸 *انستغرام | تم تحميل الفيديو بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                return True
    except:
        pass
    return False

def process_youtube(chat_id, url, is_audio, quality):
    servers = ["https://co.wuk.sh/api/json", "https://api.cobalt.tools/"]
    payload = {"url": url, "videoQuality": quality if not is_audio else "max", "audioFormat": "mp3", "downloadMode": "audio" if is_audio else "auto"}
    for server in servers:
        try:
            res = requests.post(server, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=12)
            if res.status_code == 200:
                dl_url = res.json().get("url")
                if dl_url:
                    if is_audio:
                        bot.send_audio(chat_id, dl_url, caption=f"🎵 *يوتيوب | تم تحميل الصوت بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                    else:
                        bot.send_video(chat_id, dl_url, caption=f"🎬 *يوتيوب | تم تحميل الفيديو بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                    return True
        except:
            continue
    return False

def convert_image_to_ascii(image_bytes):
    try:
        img = Image.open(BytesIO(image_bytes))
        w, h = img.size
        new_w = 45
        new_h = int((h / float(w)) * new_w * 0.55)
        img = img.resize((new_w, new_h)).convert('L')
        chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
        pixels = [chars[p // 25] for p in img.getdata()]
        pixel_str = "".join(pixels)
        ascii_lines = [pixel_str[i:i + new_w] for i in range(0, len(pixel_str), new_w)]
        return f"```\n" + "\n".join(ascii_lines) + "\n
