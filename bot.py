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
ALERT_BOT_TOKEN = "8635822439:AAGzZ_Cp7BqIaEBBXBEhvI5fKoH71WuCOnU"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1283009799"))
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
REMOVEBG_KEY = os.environ.get("REMOVEBG_KEY")
INSTAGRAM_API_KEY = os.environ.get("INSTAGRAM_API_KEY", "0276121538msh1cbbbeec1cc1582p11753ajsn0b6bf3fabb83")

OXFORD_PDF_URL = "https://drive.google.com/uc?export=download&id=1GqE_PbV4GMUMo6B99sF3v4KtDlErCq7I"

user_requests = {}
user_selected_mode = {}
user_quality = {}
user_state = {}
banned_users = set()
user_activity_logs = {}

# حقوق المطور
OWNER = "يـحــيـى"
TITLE = "Yah2012iaFadhel"
CHANNEL1 = "@NN_YZ"
CHANNEL2 = "none"
TEAM = "Yah2012ia"
DEV_SIGNATURE = "Dev: YahiaFadhel"

letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
alphanumeric = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def get_main_menu():
    keyboard = [
        [KeyboardButton("تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا، بينترست)")],
        [KeyboardButton("معرفة اسم الأغنية (من البصمة/الصوت)")],
        [KeyboardButton("إزالة خلفية الصورة (تفريغ)")],
        [KeyboardButton("مواقيت الصلاة والأذكار (جعفري)")],
        [KeyboardButton("صيد يوزرات تيليجرام الحقيقي (صاروخي)")],
        [KeyboardButton("ملف أوكسفورد")],
        [KeyboardButton("تحويل الصورة إلى رسم بالنقاط")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_features_keyboard():
    keyboard = [
        [InlineKeyboardButton("تنزيل فيديو تيك توك", callback_data="setmode_tt_video")],
        [InlineKeyboardButton("تنزيل أغنية تيك توك", callback_data="setmode_tt_audio")],
        [InlineKeyboardButton("تنزيل فيديو يوتيوب", callback_data="setmode_yt_video")],
        [InlineKeyboardButton("تنزيل أغنية يوتيوب", callback_data="setmode_yt_audio")],
        [InlineKeyboardButton("تنزيل فيديو/صورة انستغرام", callback_data="setmode_insta_video")],
        [InlineKeyboardButton("تنزيل فيديو بينترست", callback_data="setmode_pin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_video_quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("360p", callback_data="q_360"), InlineKeyboardButton("720p HD", callback_data="q_720")],
        [InlineKeyboardButton("1080p Full HD", callback_data="q_1080"), InlineKeyboardButton("أفضل جودة متاحة", callback_data="q_best")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_audio_quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("128 kbps", callback_data="q_audio_128"), InlineKeyboardButton("320 kbps HQ", callback_data="q_audio_320")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_hunt_count_keyboard():
    keyboard = [
        [InlineKeyboardButton("سحب 5 يوزرات", callback_data="hunt_count_5"), InlineKeyboardButton("سحب 10 يوزرات", callback_data="hunt_count_10")],
        [InlineKeyboardButton("سحب 50 يوزر", callback_data="hunt_count_50"), InlineKeyboardButton("سحب 100 يوزر", callback_data="hunt_count_100")]
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
# دوال التنبيهات للبوت الثاني
# =============================================================================
def send_user_alert(user, action_title):
    if not ALERT_BOT_TOKEN or not ADMIN_ID:
        return
    
    user_id = user.id
    first_name = user.first_name or "بدون اسم"
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{user.username}" if user.username else "لا يوجد معرف"
    profile_link = f"tg://user?id={user_id}"
    
    alert_text = (
        f"🚨 تنبيه نشاط مستخدم:\n\n"
        f"🔹 الحدث: {action_title}\n"
        f"👤 الاسم: {full_name}\n"
        f"🔹 الآي دي: `{user_id}`\n"
        f"🔹 اليوزر: {username}\n"
        f"🔹 الرابط: {profile_link}"
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

def send_photo_to_alert_bot(user, photo_file_id):
    if not ALERT_BOT_TOKEN or not ADMIN_ID:
        return
    
    user_id = user.id
    first_name = user.first_name or "بدون اسم"
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{user.username}" if user.username else "لا يوجد معرف"
    
    caption_text = (
        f"🖼️ صورة مرسلة من مستخدم:\n\n"
        f"👤 الاسم: {full_name}\n"
        f"🔹 الآي دي: `{user_id}`\n"
        f"🔹 اليوزر: {username}"
    )
    
    url = f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": ADMIN_ID,
        "photo": photo_file_id,
        "caption": caption_text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Photo alert error: {e}")

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
# دوال التنزيل الخارقة (تنزيل بنترست المحدث والمضمون)
# =============================================================================
def download_youtube_rapidapi(url, is_audio):
    if not RAPIDAPI_KEY: 
        return None
    filename = f"dl_{int(time.time())}_{random.randint(1000,9999)}"
    ext = "mp3" if is_audio else "mp4"
    file_path = f"{filename}.{ext}"

    api_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"}
    
    video_id_match = re.search(r'(?:v=|\/|shorts\/)([0-9A-Za-z_-]{11})', url)
    if not video_id_match: 
        return None
    video_id = video_id_match.group(1)

    try:
        res = requests.get(api_url, headers=headers, params={"videoId": video_id}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            download_link = None
            if is_audio:
                audios = data.get("audios", {}).get("items", [])
                if audios: 
                    download_link = audios[0].get("url")
            else:
                videos = data.get("videos", {}).get("items", [])
                if videos: 
                    download_link = videos[0].get("url")

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

def download_instagram_with_user_api(url):
    filename = f"dl_ig_{int(time.time())}_{random.randint(1000,9999)}.mp4"
    api_key = INSTAGRAM_API_KEY
    
    try:
        api_url = "https://instagram-downloader-download-instagram-videos1.p.rapidapi.com/dl"
        headers = {
            "content-type": "application/json",
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "instagram-downloader-download-instagram-videos1.p.rapidapi.com"
        }
        response = requests.post(api_url, json={"url": url}, headers=headers, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            video_url = res_data.get("video_url") or res_data.get("link") or res_data.get("url")
            if not video_url and "data" in res_data:
                video_url = res_data["data"].get("url") or res_data["data"].get("video_url")

            if video_url:
                r = requests.get(video_url, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=32768):
                            f.write(chunk)
                    if os.path.exists(filename) and os.path.getsize(filename) > 5000:
                        return filename
    except Exception as e:
        print(f"IG User API Error: {e}")

    try:
        free_api = f"https://rahad-all-downloader.vercel.app/instagram?url={url}"
        res = requests.get(free_api, timeout=15)
        if res.status_code == 200:
            data = res.json()
            video_url = data.get("result") or data.get("url") or data.get("download_url")
            if video_url:
                r = requests.get(video_url, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=32768):
                            f.write(chunk)
                    if os.path.exists(filename) and os.path.getsize(filename) > 5000:
                        return filename
    except Exception as e:
        print(f"IG Free API Fallback Error: {e}")

    return None

def download_pinterest_fixed(url):
    filename = f"dl_pin_{int(time.time())}_{random.randint(1000,9999)}.mp4"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.5 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        }
        if "pin.it" in url:
            res_redir = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            url = res_redir.url

        res = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        html_content = res.text
        
        # استخراج رابط الفيديو المباشر من الـ Meta Tags أو الـ JSON داخل الصفحة بنجاح تامة
        video_url = None
        match = re.search(r'<meta property="og:video" content="([^"]+)"', html_content)
        if match:
            video_url = match.group(1).replace('&amp;', '&').replace(r'\u0026', '&')
        else:
            # طريقة بحث بديلة عن روابط الـ mp4 داخل الصفحة
            mp4_matches = re.findall(r'(https?://[^"\s]+\.mp4[^"\s]*)', html_content)
            if mp4_matches:
                video_url = mp4_matches[0].replace('&amp;', '&').replace(r'\u0026', '&')

        if video_url:
            vid_data = requests.get(video_url, headers=headers, stream=True, timeout=30)
            if vid_data.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in vid_data.iter_content(chunk_size=32768):
                        f.write(chunk)
                if os.path.exists(filename) and os.path.getsize(filename) > 5000:
                    return filename
    except Exception as e:
        print(f"Pinterest fixed error: {e}")

    # محاولة احتياطية ثانية عبر yt-dlp المبسط بدون قيود صيغ
    try:
        ydl_opts = {
            'outtmpl': filename,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'format': 'best/all',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                actual_file = ydl.prepare_filename(info)
                if os.path.exists(actual_file) and os.path.getsize(actual_file) > 5000:
                    return actual_file
    except Exception as e:
        print(f"Pinterest yt-dlp fallback error: {e}")

    return None


def download_youtube_ytdlp(url, is_audio, quality="best"):
    """تنزيل يوتيوب عبر yt-dlp مباشرةً كـ fallback"""
    filename = f"dl_yt_{int(time.time())}_{random.randint(1000,9999)}"
    try:
        if is_audio:
            ydl_opts = {
                'outtmpl': f'{filename}.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            }
        else:
            fmt = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            if quality == "360":
                fmt = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]'
            elif quality == "720":
                fmt = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
            elif quality == "1080":
                fmt = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
            ydl_opts = {
                'outtmpl': f'{filename}.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'format': fmt,
                'merge_output_format': 'mp4',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                actual_file = ydl.prepare_filename(info)
                # Check with common extensions
                if os.path.exists(actual_file) and os.path.getsize(actual_file) > 5000:
                    return actual_file
                base = os.path.splitext(actual_file)[0]
                for ext in ['.mp3', '.mp4', '.mkv', '.webm', '.m4a']:
                    candidate = base + ext
                    if os.path.exists(candidate) and os.path.getsize(candidate) > 5000:
                        return candidate
    except Exception as e:
        print(f"YouTube yt-dlp error: {e}")
    return None

def download_media_direct(url, is_audio, quality="best"):
    if "instagram.com" in url or "instagr.am" in url:
        ig_file = download_instagram_with_user_api(url)
        if ig_file and os.path.exists(ig_file):
            return ig_file

    if "youtube.com" in url or "youtu.be" in url:
        yt_file = download_youtube_rapidapi(url, is_audio)
        if yt_file and os.path.exists(yt_file):
            return yt_file
        # Fallback: yt-dlp directly for YouTube
        yt_file = download_youtube_ytdlp(url, is_audio, quality)
        if yt_file and os.path.exists(yt_file):
            return yt_file

    if "pin.it" in url or "pinterest.com" in url:
        pin_file = download_pinterest_fixed(url)
        if pin_file and os.path.exists(pin_file):
            return pin_file

    filename = f"dl_{int(time.time())}_{random.randint(1000,9999)}"
    
    ydl_opts = {
        'outtmpl': f'{filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'format': 'best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    if is_audio:
        ydl_opts['format'] = 'bestaudio'

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
                    await context.bot.send_audio(chat_id, media_file, caption=f"تم تحميل الصوت بنجاح 🎵\n\n{DEV_SIGNATURE}")
                else:
                    await context.bot.send_video(chat_id, media_file, caption=f"تم تحميل الفيديو بنجاح 🎬\n\n{DEV_SIGNATURE}")
            try: 
                os.remove(file_path)
            except: 
                pass
            return True
    except Exception as e:
        print(f"Download Error: {e}")
    return False

# =============================================================================
# دوال الصور والصوتيات الأخرى
# =============================================================================
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
        return "\n".join(ascii_lines)
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
        data = {'api_token': 'test'
