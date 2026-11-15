import os
import re
import random
import string
import time
import asyncio
import aiohttp
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO
import yt_dlp

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ALERT_BOT_TOKEN = os.environ.get("ALERT_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1283009799"))
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
REMOVEBG_KEY = os.environ.get("REMOVEBG_KEY")

OXFORD_PDF_URL = "https://drive.google.com/uc?export=download&id=1GqE_PbV4GMUMo6B99sF3v4KtDlErCq7I"

user_requests = {}
user_selected_mode = {}
user_state = {}

# حقوق المطور
OWNER = "يـحــيـى"
TITLE = "Yah2012iaFadhel"
CHANNEL1 = "@NN_YZ"
CHANNEL2 = "none"
TEAM = "Yah2012ia"
DEV_SIGNATURE = "💻 Dev: YahiaFadhel"

letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
alphanumeric = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def get_main_menu():
    keyboard = [
        [KeyboardButton("📥 تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا، بينترست)")],
        [KeyboardButton("🎵 معرفة اسم الأغنية (من البصمة/الصوت)")],
        [KeyboardButton("🖼 إزالة خلفية الصورة (تفريغ)")],
        [KeyboardButton("⏰ مواقيت الصلاة والأذكار (جعفري)")],
        [KeyboardButton("🔍 صيد يوزرات تيليجرام الحقيقي (صاروخي)")],
        [KeyboardButton("📚 ملف أوكسفورد")],
        [KeyboardButton("✨ زخرفة الأسماء الاحترافية")],
        [KeyboardButton("🎨 تحويل الصورة إلى رسم بالنقاط")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_features_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 تنزيل فيديو تيك توك", callback_data="setmode_tt_video")],
        [InlineKeyboardButton("🎶 تنزيل أغنية تيك توك", callback_data="setmode_tt_audio")],
        [InlineKeyboardButton("📹 تنزيل فيديو يوتيوب", callback_data="setmode_yt_video")],
        [InlineKeyboardButton("🎵 تنزيل أغنية يوتيوب", callback_data="setmode_yt_audio")],
        [InlineKeyboardButton("📸 تنزيل فيديو/صورة انستغرام", callback_data="setmode_insta_video")],
        [InlineKeyboardButton("📌 تنزيل فيديو بينترست", callback_data="setmode_pin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_video_quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 360p", callback_data="q_360"), InlineKeyboardButton("📺 720p HD", callback_data="q_720")],
        [InlineKeyboardButton("🖥 1080p Full HD", callback_data="q_1080"), InlineKeyboardButton("🌟 أفضل جودة متاحة", callback_data="q_best")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_audio_quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎧 128 kbps", callback_data="q_audio_128"), InlineKeyboardButton("🎵 320 kbps HQ", callback_data="q_audio_320")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_media_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 تنزيل فيديو", callback_data="type_video"), InlineKeyboardButton("🎵 تنزيل صوت", callback_data="type_audio")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_hunt_count_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔍 سحب 5 يوزرات", callback_data="hunt_count_5"), InlineKeyboardButton("🔍 سحب 10 يوزرات", callback_data="hunt_count_10")],
        [InlineKeyboardButton("🔍 سحب 50 يوزر", callback_data="hunt_count_50"), InlineKeyboardButton("🔍 سحب 100 يوزر", callback_data="hunt_count_100")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_prayer_cities_keyboard():
    cities = [
        ("بغداد", "Baghdad"), ("النجف", "Najaf"), ("كربلاء", "Karbala"), 
        ("البصرة", "Basrah"), ("أربيل", "Erbil"), ("الموصل", "Mosul"), 
        ("الحلة", "Hillah"), ("الناصرية", "Nasiriyah"), ("العمارة", "Amarah"), 
        ("الديوانية", "Diwaniyah"), ("الكوت", "Kut"), ("السماوة", "Samawah"), 
        ("كركوك", "Kirkuk"), ("ديالى", "Diyala"), ("الأنبار", "Anbar"), 
        ("دهوك", "Duhok"), ("السليمانية", "Sulaymaniyah")
    ]
    keyboard = []
    row = []
    for ar_name, en_name in cities:
        row.append(InlineKeyboardButton(ar_name, callback_data=f"pray_{en_name}_{ar_name}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def format_time_12h(time_str):
    try:
        clean_time = time_str.split(" ")[0]
        t = datetime.strptime(clean_time, "%H:%M")
        formatted = t.strftime("%I:%M").lstrip('0')
        period = "ص" if t.hour < 12 else "م"
        return f"{formatted} {period}"
    except:
        return time_str

# =============================================================================
# دالة إرسال التنبيه للبوت الثاني
# =============================================================================
async def send_alert_to_admin_bot(user, action_type="دخل إلى البوت"):
    if not ALERT_BOT_TOKEN or not ADMIN_ID:
        return
    
    user_id = user.id
    first_name = user.first_name or "بدون اسم"
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{user.username}" if user.username else "لا يوجد معرف"
    profile_link = f"tg://user?id={user_id}"
    
    alert_text = (
        f"🚨 *تنبيه دخول جديد للبوت!*\n\n"
        f"👤 الاسم: {full_name}\n"
        f"🆔 الآي دي: `{user_id}`\n"
        f"🌐 المعرف: {username}\n"
        f"🔗 الرابط المباشر للحساب: [اضغط هنا للدخول للحساب]({profile_link})\n"
        f"⚡ الحدث: {action_type}\n"
        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    url = f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": alert_text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Alert error: {e}")

# =============================================================================
# أدوات صيد اليوزرات الحقيقية
# =============================================================================
def generate_5char_username():
    c1 = random.choice(letters)
    c2 = random.choice(alphanumeric)
    c3 = random.choice(alphanumeric)
    c4 = random.choice(alphanumeric)
    c5 = random.choice(alphanumeric)
    
    patterns = [
        f"{c1}{c2}_{c3}{c4}",
        f"{c1}_{c2}{c3}{c4}",
        f"{c1}{c2}{c3}_{c4}",
        f"{c1}{c2}{c3}{c4}{c5}"
    ]
    return random.choice(patterns)

async def check_real_available_usernames(count):
    found_users = []
    checked = 0
    max_attempts = count * 500  

    CONCURRENCY_LIMIT = 40
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async def check_single():
            nonlocal checked
            while len(found_users) < count and checked < max_attempts:
                user = generate_5char_username()
                if user in found_users:
                    continue
                
                checked += 1
                async with semaphore:
                    try:
                        frag_url = f"https://fragment.com/username/{user}"
                        async with session.get(frag_url, timeout=3) as frag_resp:
                            if frag_resp.status == 200:
                                frag_text = await frag_resp.text()
                                if "unavailable" in frag_text.lower() or "not found" in frag_text.lower():
                                    tg_url = f"https://t.me/{user}"
                                    async with session.get(tg_url, timeout=3) as tg_resp:
                                        if tg_resp.status == 200:
                                            tg_text = await tg_resp.text()
                                            if "tgme_page_title" not in tg_text:
                                                if user not in found_users and len(found_users) < count:
                                                    found_users.append(user)
                    except:
                        pass

        workers = [check_single() for _ in range(CONCURRENCY_LIMIT)]
        await asyncio.gather(*workers)

    return found_users

# =============================================================================
# دوال تحميل الوسائط والخدمات الأخرى
# =============================================================================
def download_youtube_rapidapi(url, is_audio):
    if not RAPIDAPI_KEY: return None
    filename = f"dl_{int(time.time())}_{random.randint(1000,9999)}"
    ext = "mp3" if is_audio else "mp4"
    file_path = f"{filename}.{ext}"

    api_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"}
    
    video_id_match = re.search(r'(?:v=|\/|shorts\/)([0-9A-Za-z_-]{11})', url)
    if not video_id_match: return None
    video_id = video_id_match.group(1)

    try:
        res = requests.get(api_url, headers=headers, params={"videoId": video_id}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            download_link = None
            if is_audio:
                audios = data.get("audios", {}).get("items", [])
                if audios: download_link = audios[0].get("url")
            else:
                videos = data.get("videos", {}).get("items", [])
                if videos: download_link = videos[0].get("url")

            if download_link:
                r = requests.get(download_link, stream=True, timeout=120)
                if r.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=32768):
                            f.write(chunk)
                    return file_path
    except Exception as e:
        print(f"API Download Error: {e}")
    return None

def download_pinterest_scraping(url):
    filename = f"dl_{int(time.time())}_{random.randint(1000,9999)}.mp4"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        res = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        html_content = res.text

        video_urls = re.findall(r'https?://[^\s<>"]+?\.(?:mp4)', html_content)
        if not video_urls:
            video_urls = re.findall(r'"url"\s*:\s*"(https?://[^"]+?\.(?:mp4)[^"]*)"', html_content)

        if video_urls:
            direct_video_url = video_urls[0].replace(r'\u0026', '&')
            vid_data = requests.get(direct_video_url, headers=headers, stream=True, timeout=30)
            if vid_data.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in vid_data.iter_content(chunk_size=32768):
                        f.write(chunk)
                return filename
    except Exception as e:
        print(f"Pinterest scraping error: {e}")
    return None

def download_media_direct(url, is_audio, quality="best"):
    if "youtube.com" in url or "youtu.be" in url:
        yt_file = download_youtube_rapidapi(url, is_audio)
        if yt_file and os.path.exists(yt_file): 
            return yt_file

    if "pin.it" in url or "pinterest.com" in url:
        pin_file = download_pinterest_scraping(url)
        if pin_file and os.path.exists(pin_file):
            return pin_file

    filename = f"dl_{int(time.time())}_{random.randint(1000,9999)}"
    ydl_opts = {
        'outtmpl': f'{filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    if is_audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info and len(info['entries']) > 0: 
                info = info['entries'][0]
            filename_actual = ydl.prepare_filename(info)
            if os.path.exists(filename_actual): 
                return filename_actual

            base = os.path.splitext(filename_actual)[0]
            for ext in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a']:
                if os.path.exists(base + ext): 
                    return base + ext
    except Exception as e:
        print(f"yt-dlp error: {e}")
    return None

async def process_media_download(context: ContextTypes.DEFAULT_TYPE, chat_id: int, url: str, is_audio: bool, quality: str = "best"):
    try:
        file_path = await asyncio.to_thread(download_media_direct, url, is_audio, quality)
        if file_path and os.path.exists(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, 'rb') as media_file:
                if is_audio or ext in ['.mp3', '.m4a', '.wav', '.ogg']:
                    await context.bot.send_audio(chat_id, media_file, caption=f"🎵 تم تحميل الصوت بنجاح\n\n{DEV_SIGNATURE}")
                else:
                    await context.bot.send_video(chat_id, media_file, caption=f"🎬 تم تحميل الفيديو بنجاح\n\n{DEV_SIGNATURE}")
            try: os.remove(file_path)
            except: pass
            return True
    except Exception as e:
        print(f"Download Error: {e}")
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
        return "```\n" + "\n".join(ascii_lines) + "\n```"
    except:
        return None

def remove_background_api(image_bytes):
    key = REMOVEBG_KEY or "free_demo"
    try:
        res = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={'image_file': image_bytes},
            data={'size': 'auto'},
            headers={'X-Api-Key': key},
            timeout=20
        )
        if res.status_code == 200:
            return res.content
    except Exception as e:
        print(f"Remove bg error: {e}")
    return None

def get_prayer_times_jaafari(city_en):
    try:
        url = f"http://api.aladhan.com/v1/timingsByCity?city={city_en}&country=Iraq&method=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get('code') == 200:
                return data['data']['timings']
    except Exception as e:
        print(f"Prayer API Error: {e}")
    return None

def recognize_song_audd(audio_bytes):
    try:
        data = {'api_token': 'test', 'return': 'apple_music,spotify'}
        files = {'file': audio_bytes}
        res = requests.post('https://api.audd.io/', data=data, files=files, timeout=10)
        if res.status_code == 200:
            result = res.json()
            if result.get('status') == 'success' and result.get('result'):
                title = result['result'].get('title')
                artist = result['result'].get('artist')
                return f"🎵 اسم الأغنية: {title}\n👤 الفنان: {artist}"
    except:
        pass
    return None

# =============================================================================
# أوامر ومعالجات البوت
# =============================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await send_alert_to_admin_bot(user, action_type="ضغط على /start ودخل للبوت")

    await update.message.reply_text(
        f"🌟 أهلاً بك يا عزيزي في بوت الخدمات الشامل 🚀\n\nاختر الخدمة المطلوبة من الأزرار بالأسفل:\n\n{DEV_SIGNATURE}",
        reply_markup=get_main_menu()
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    if data.startswith("hunt_count_") or data.startswith("get_"):
        count = int(data.split("_")[-1])

        status_msg = await query.message.reply_text(
            f"🚀 جاري الفحص الدقيق واستبعاد المحجوزة لصيد ({count}) يوزر متاح حقيقي...\n"
            f"⏳ انتظر ثواني معدودة لتجهيز اليوزرات الخالية 100%."
        )
        
        found_usernames = await check_real_available_usernames(count)
        
        if found_usernames:
            try:
                await status_msg.delete()
            except:
                pass
            
            result_text = f"╔══════════════════════════════════════╗\n"
            result_text += f"       🎯 دفعة اليوزرات المتاحة فعلياً\n"
            result_text += f"╚══════════════════════════════════════╝\n\n"
            
            for idx, u in enumerate(found_usernames, 1):
                result_text += f"{idx}. @{u}\n"
                
                if idx % 5 == 0 and idx < len(found_usernames):
                    result_text += f"\n─────────── 👑 {OWNER} ───────────\n\n"
            
            result_text += f"\n╔══════════════════════════════════════╗\n"
            result_text += f"  👤 المطور: {OWNER} | {TITLE}\n"
            result_text += f"  📢 القناة: {CHANNEL1}\n"
            result_text += f"  ⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result_text += f"╚══════════════════════════════════════╝"
            
            await query.message.reply_text(result_text)
        else:
            await status_msg.edit_text("❌ تأخرت المحاولات بسبب ندرة اليوزرات المجانية المتاحة، اضغط على زر الصيد وجرب مرة ثانية.")

    elif data.startswith("setmode_"):
        mode = data.replace("setmode_", "")
        user_selected_mode[chat_id] = mode
        await context.bot.send_message(chat_id, f"📥 أرسل الآن الرابط المطلوب للتحميل الفوري:\n\n{DEV_SIGNATURE}")

    elif data == "type_video":
        await context.bot.edit_message_text(f"🎬 اختر دقة الفيديو المطلوب:\n\n{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id, reply_markup=get_video_quality_keyboard())

    elif data == "type_audio":
        await context.bot.edit_message_text(f"🎵 اختر جودة الصوت المطلوب:\n\n{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id, reply_markup=get_audio_quality_keyboard())

    elif data.startswith("q_"):
        req = user_requests.get(chat_id)
        quality_code = data.replace("q_", "").replace("audio_", "")
        if req:
            url = req.get("url")
            is_audio = req.get("is_audio", False)
            await context.bot.edit_message_text(f"⏳ جاري التحميل المباشر والسريع...\n\n{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id)
            success = await process_media_download(context, chat_id, url, is_audio, quality=quality_code)
            if not success:
                await context.bot.send_message(chat_id, f"⚠️ تعذر التحميل، تأكد من صحة الرابط أو جرب رابطاً آخر.\n\n{DEV_SIGNATURE}")
            user_requests.pop(chat_id, None)

    elif data.startswith("pray_"):
        parts = data.split("_")
        city_en = parts[1]
        city_ar = parts[2]
        
        timings = get_prayer_times_jaafari(city_en)
        if timings:
            text = (
                f"🕌 مواقيت الصلاة الشرعية (المذهب الجعفري) - {city_ar}:\n\n"
                f"🌅 أذان الفجر: {format_time_12h(timings['Fajr'])}\n"
                f"☀️ الشروق: {format_time_12h(timings['Sunrise'])}\n"
                f"☀️ أذان الظهر: {format_time_12h(timings['Dhuhr'])}\n"
                f"🌤 أذان العصر: {format_time_12h(timings['Asr'])}\n"
                f"🌆 أذان المغرب الشرعي: {format_time_12h(timings['Maghrib'])}\n"
                f"🌌 أذان العشاء: {format_time_12h(timings['Isha'])}\n"
                f"🌙 منتصف الليل الشرعي: {format_time_12h(timings['Midnight'])}\n\n"
                f"🤲 من الأذكار: (اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وآلِ مُحَمَّدٍ)\n\n"
                f"{DEV_SIGNATURE}"
            )
            await context.bot.send_message(chat_id, text)
        else:
            await context.bot.send_message(chat_id, "⚠️ تعذر جلب مواقيت الصلاة حالياً، حاول مجدداً.")

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text or ""

    if text.strip() == "عرض":
        keyboard = [
            [
                InlineKeyboardButton("🔍 سحب 5 يوزرات", callback_data="get_5"),
                InlineKeyboardButton("🔍 سحب 10 يوزرات", callback_data="get_10")
            ],
            [
                InlineKeyboardButton("🔍 سحب 50 يوزر", callback_data="get_50"),
                InlineKeyboardButton("🔍 سحب 100 يوزر", callback_data="get_100")
            ]
        ]
        await update.message.reply_text(
            f"╔═════════════════════════╗\n"
            f"   🔥 قائمة الصيد النظيف والحر\n"
            f"╚═════════════════════════╝\n\n"
            f"اختر العدد المطلوب يا عزيزي وتجيك الدفعة الحقيقية المتاحة للتسجيل الفوري:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if text.startswith("📥 تنزيل الفيديوهات والصوتيات"):
        await update.message.reply_text(f"📥 أرسل رابط تيك توك، يوتيوب، انستغرام، أو بينترست مباشرة:\n\n{DEV_SIGNATURE}", reply_markup=get_features_keyboard())
        return
    elif text == "🔍 صيد يوزرات تيليجرام الحقيقي (صاروخي)":
        await update.message.reply_text(f"🔍 اختر العدد المطلوب سحبه من اليوزرات المتاحة فعلياً:\n\n{DEV_SIGNATURE}", reply_markup=get_hunt_count_keyboard())
        return
    elif text == "📚 ملف أوكسفورد":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📥 اضغط هنا لتنزيل ملف أوكسفورد", url=OXFORD_PDF_URL)]])
        await update.message.reply_text(f"📚 تفضل رابط تحميل ملف أوكسفورد المباشر:\n\n{DEV_SIGNATURE}", reply_markup=kb)
        return
    elif text == "✨ زخرفة الأسماء الاحترافية":
        user_state[chat_id] = "waiting_name"
        await update.message.reply_text(f"✨ أرسل الآن الاسم أو الكلمة التي تريد زخرفتها (عربي أو إنجليزي):\n\n{DEV_SIGNATURE}")
        return
    elif text == "🎨 تحويل الصورة إلى رسم بالنقاط":
        user_state[chat_id] = "ascii"
        await update.message.reply_text(f"🎨 أرسل أي صورة الآن لتحويلها إلى رسم فني بالنقاط:\n\n{DEV_SIGNATURE}", reply_markup=get_main_menu())
        return
    elif text == "🎵 معرفة اسم الأغنية (من البصمة/الصوت)":
        user_state[chat_id] = "shazam"
        await update.message.reply_text(f"🎵 أرسل البصمة الصوتية أو الملف الصوتي الآن لمعرفة اسمه:\n\n{DEV_SIGNATURE}")
        return
    elif text == "🖼 إزالة خلفية الصورة (تفريغ)":
        user_state[chat_id] = "remove_bg"
        await update.message.reply_text(f"🖼 أرسل الصورة المراد إزالة خلفيتها الآن:\n\n{DEV_SIGNATURE}")
        return
    elif text.startswith("⏰ مواقيت الصلاة والأذكار"):
        await update.message.reply_text(f"🕌 اختر محافظتك لمشاهدة مواقيت الصلاة اليومية (حسب التوقيت الشرعي الجعفري):\n\n{DEV_SIGNATURE}", reply_markup=get_prayer_cities_keyboard())
        return

    await send_alert_to_admin_bot(user, action_type=f"كتب رسالة: {text}")

    if user_state.get(chat_id) == "waiting_name":
        user_state.pop(chat_id, None)
        decorations = [
            f"⚡ ⦗ {text} ⦗ ⚡",
            f"💎 »» {text} »« 💎",
            f"🔥 ⦇ 𝄠 {text} 𝄠 ⦆ 🔥",
            f"🌟 ༺ {text} ༻ 🌟",
            f"🦅 ⫷ {text} ⫸ 🦅",
            f"👑 𓏺 {text} 𓏺 👑"
        ]
        await update.message.reply_text(f"✨ إليك قائمة الزخارف الاحترافية لاسمك:\n\n" + "\n".join(decorations) + f"\n\n{DEV_SIGNATURE}")
        return

    urls = re.findall(r'https?://[^\s]+', text)
    if urls:
        target_url = urls[0]
        preset = user_selected_mode.get(chat_id)
        if preset:
            is_audio = "audio" in preset
            user_requests[chat_id] = {"url": target_url, "is_audio": is_audio}
            user_selected_mode.pop(chat_id, None)
            if is_audio:
                await update.message.reply_text(f"🎵 اختر جودة الصوت المطلوب:\n\n{DEV_SIGNATURE}", reply_markup=get_audio_quality_keyboard())
            else:
                await update.message.reply_text(f"🎬 اختر دقة الفيديو المطلوب:\n\n{DEV_SIGNATURE}", reply_markup=get_video_quality_keyboard())
        else:
            user_requests[chat_id] = {"url": target_url, "is_audio": False}
            await update.message.reply_text(f"📥 اختر نوع التحميل المطلوب:\n\n{DEV_SIGNATURE}", reply_markup=get_media_type_keyboard())
        return

    await update.message.reply_text(f"يرجى استخدام الأزرار بالأسفل لتنفيذ الخدمات المتاحة 🚀\n\n{DEV_SIGNATURE}")

async def handle_photo_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    mode = user_state.get(chat_id)

    await send_alert_to_admin_bot(user, action_type="أرسل صورة للبوت")

    if mode == "remove_bg":
        user_state.pop(chat_id, None)
        await update.message.reply_text(f"⏳ جاري تفريغ وإزالة خلفية الصورة...\n\n{DEV_SIGNATURE}")
        try:
            photo_file = await update.message.photo[-1].get_file()
            downloaded_bytes = await photo_file.download_as_bytearray()
            out_bytes = remove_background_api(bytes(downloaded_bytes))
            if out_bytes:
                await context.bot.send_document(chat_id, document=BytesIO(out_bytes), filename="no_bg.png", caption=f"🖼 تم تفريغ الصورة بنجاح!\n\n{DEV_SIGNATURE}")
            else:
                await update.message.reply_text("⚠️ تعذر إزالة الخلفية، يرجى إضافة REMOVEBG_KEY بـ Railway لتفعيل الخدمة.")
        except:
            await update.message.reply_text("⚠️ حدث خطأ في معالجة الصورة.")
        return

    try:
        await update.message.reply_text(f"🎨 جاري تحويل الصورة إلى رسم بالنقاط...\n\n{DEV_SIGNATURE}")
        photo_file = await update.message.photo[-1].get_file()
        downloaded_bytes = await photo_file.download_as_bytearray()
        res = convert_image_to_ascii(bytes(downloaded_bytes))
        if res:
            await update.message.reply_text(f"✨ النتيجة:\n\n{res}\n\n{DEV_SIGNATURE}")
    except:
        await update.message.reply_text(f"⚠️ حدث خطأ بالمعالجة.\n\n{DEV_SIGNATURE}")

async def handle_audio_voice_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    await send_alert_to_admin_bot(user, action_type="أرسل بصمة صوتية أو ملف صوتي")

    await update.message.reply_text(f"🔍 جاري البحث عن اسم الأغنية...\n\n{DEV_SIGNATURE}")
    try:
        audio_obj = update.message.voice or update.message.audio
        if audio_obj:
            file = await audio_obj.get_file()
            audio_bytes = await file.download_as_bytearray()
            res = recognize_song_audd(bytes(audio_bytes))
            if res:
                yt_query = res.replace("🎵 اسم الأغنية: ", "").replace("\n👤 الفنان: ", " ")
                search_url = f"https://www.youtube.com/results?search_query={yt_query.replace(' ', '+')}"
                await update.message.reply_text(f"{res}\n\n🔗 [ابحث عنها في يوتيوب]({search_url})\n\n{DEV_SIGNATURE}")
            else:
                await update.message.reply_text(f"⚠️ لم أستطع التعرف على الأغنية، تأكد من وضوح الصوت.\n\n{DEV_SIGNATURE}")
    except:
        await update.message.reply_text("⚠️ حدث خطأ أثناء المعالجة.")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable is missing!")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_messages))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio_voice_messages))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_messages))

    print("Bot is running perfectly...")
    app.run_polling()
