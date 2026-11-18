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

OXFORD_PDF_URL = "https://drive.google.com/uc?export=download&id=1GqE_PbV4GMUMo6B99sF3v4KtDlErCq7I"

user_selected_mode = {}
user_quality = {}
user_state = {}
banned_users = set()
user_activity_logs = {}  # حفظ النشاط بصمت وبدون نصوص أو روابط للحفاظ على الخصوصية

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
        [KeyboardButton("زخرفة الأسماء الاحترافية")],
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
# دالة إرسال اللوغز الفورية للبوت الثاني (بدون إظهار محتوى الرسالة للحفاظ على الخصوصية)
# =============================================================================
def send_live_log(user, action_type):
    if not ALERT_BOT_TOKEN or not ADMIN_ID:
        return
    
    user_id = user.id
    first_name = user.first_name or "بدون اسم"
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{user.username}" if user.username else "لا يوجد معرف"
    profile_link = f"tg://user?id={user_id}"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_text = (
        f"📊 [سجل نشاط / Log]\n\n"
        f"👤 الاسم: {full_name}\n"
        f"🆔 الآي دي: `{user_id}`\n"
        f"🔗 المعرف: {username}\n"
        f"📌 الرابط: {profile_link}\n"
        f"⚡ الحدث: {action_type}\n"
        f"⏰ الوقت: {timestamp}"
    )
    
    url = f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": log_text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Log error: {e}")

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
# دوال التنزيل الشاملة والمضمونة
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

def download_pinterest_scraping(url):
    filename = f"dl_{int(time.time())}_{random.randint(1000,9999)}.mp4"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        if "pin.it" in url:
            res_redir = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            url = res_redir.url

        res = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        html_content = res.text

        video_urls = re.findall(r'https?://[^\s<>"]+?\.(?:mp4)', html_content)
        if not video_urls:
            video_urls = re.findall(r'"url"\s*:\s*"(https?://[^"]+?\.(?:mp4)[^"]*)"', html_content)
        if not video_urls:
            video_urls = re.findall(r'<meta property="og:video" content="(https?://[^"]+?)">', html_content)

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
        bitrate = '320' if quality == '320' else '192'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate,
        }]
    else:
        if quality == '360':
            ydl_opts['format'] = 'best[height<=360]/best'
        elif quality == '720':
            ydl_opts['format'] = 'best[height<=720]/best'
        elif quality == '1080':
            ydl_opts['format'] = 'best[height<=1080]/best'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best/best'

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
        data = {'api_token': 'test', 'return': 'apple_music,spotify'}
        files = {'file': audio_bytes}
        res = requests.post('https://api.audd.io/', data=data, files=files, timeout=10)
        if res.status_code == 200:
            result = res.json()
            if result.get('status') == 'success' and result.get('result'):
                title = result['result'].get('title')
                artist = result['result'].get('artist')
                return f"اسم الأغنية: {title}\nالفنان: {artist}"
    except:
        pass
    return None

# =============================================================================
# دالة زخرفة الخطوط
# =============================================================================
def decorate_text_fonts(text):
    bold_map = str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
                             "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝑗𝑘𝑙𝐦𝐧𝑜𝑝𝐪𝑟𝐬𝑡𝑢𝑣𝑤𝑥𝑦𝑧𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗")
    sans_map = str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
                             "𝗮𝗯𝗰𝗱𝚎𝗳𝗴𝙝𝗶𝗷𝗸𝗹𝗺𝚗𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝲲𝗳𝴁𝴂")
    script_map = str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                               "𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜ℬ𝒞𝒟ℰ𝒢ℋℐ𝒥𝒦𝒧𝒨𝒩𝒪𝒫𝒬𝒭𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵")
    mono_map = str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
                             "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠🇽𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿")
    bubble_map = str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
                               "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ⓪①②③④⑤⑥⑦⑧⑨")

    ar_fancy = text.replace("ا", "آ").replace("ب", "بّ").replace("د", "دّ").replace("ر", "رّ").replace("س", "سۦ").replace("م", "مُ")
    ar_spaced = " ".join(list(text))

    res_bold = text.translate(bold_map)
    res_sans = text.translate(sans_map)
    res_script = text.translate(script_map)
    res_mono = text.translate(mono_map)
    res_bubble = text.translate(bubble_map)

    output = (
        f"✒️ أنواع الخطوط وزخرفة الاسم لـ ({text}):\n\n"
        f"1️⃣ خط عريض (Bold):\n{res_bold}\n\n"
        f"2️⃣ خط حديث (Sans):\n{res_sans}\n\n"
        f"3️⃣ خط مائل فخم (Script):\n{res_script}\n\n"
        f"4️⃣ خط الآلة الكاتبة (Mono):\n{res_mono}\n\n"
        f"5️⃣ خط الدوائر (Bubble):\n{res_bubble}\n\n"
        f"6️⃣ زخرفة مميزة:\n{ar_fancy}\n\n"
        f"7️⃣ حروف مباعدة:\n{ar_spaced}\n\n"
        f"{DEV_SIGNATURE}"
    )
    return output

# =============================================================================
# أوامر الإدارة (أمر /view يكتب في البوت الثاني فقط)
# =============================================================================
async def alert_bot_view_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("يرجى كتابة الآي دي بعد الأمر هكذا:\n`/view 123456789`", parse_mode="Markdown")
        return
    try:
        target_id = int(context.args[0])
        logs = user_activity_logs.get(target_id, [])
        if not logs:
            await update.message.reply_text(f"لا توجد نشاطات مسجلة لهذا المستخدم (`{target_id}`).", parse_mode="Markdown")
            return
        
        log_text = f"📊 سجل نشاط المستخدم (`{target_id}`):\n\n" + "\n".join(logs[-40:])
        await update.message.reply_text(log_text, parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("الآي دي يجب أن يكون أرقاماً صحيحة.")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("يرجى كتابة الآي دي بعد الأمر هكذا:\n`/ban 123456789`", parse_mode="Markdown")
        return
    try:
        target_id = int(context.args[0])
        banned_users.add(target_id)
        await update.message.reply_text(f"تم حظر المستخدم صاحب الآي دي: `{target_id}` بنجاح 🚫", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("الآي دي يجب أن يكون أرقاماً صحيحة.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("يرجى كتابة الآي دي بعد الأمر هكذا:\n`/unban 123456789`", parse_mode="Markdown")
        return
    try:
        target_id = int(context.args[0])
        if target_id in banned_users:
            banned_users.remove(target_id)
            await update.message.reply_text(f"تم رفع الحظر عن المستخدم صاحب الآي دي: `{target_id}` بنجاح ✅", parse_mode="Markdown")
        else:
            await update.message.reply_text("هذا المستخدم ليس في قائمة المحظورين.")
    except ValueError:
        await update.message.reply_text("الآي دي يجب أن يكون أرقاماً صحيحة.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id in banned_users:
        await update.message.reply_text("عذراً، أنت محظور من استخدام هذا البوت ❌")
        return

    # إرسال إشعار الدخول للبوت الثاني مع تفاصيل المستخدم الأساسية
    send_live_log(user, "دخل إلى البوت لأول مرة (/start)")

    await update.message.reply_text(
        f"أهلاً بك يا عزيزي في بوت الخدمات الشامل 🚀\n\nاختر الخدمة المطلوبة من الأزرار بالأسفل:\n\n{DEV_SIGNATURE}",
        reply_markup=get_main_menu()
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id in banned_users:
        await query.answer("أنت محظور من استخدام البوت ❌", show_alert=True)
        return

    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    if data.startswith("hunt_count_") or data.startswith("get_"):
        count = int(data.split("_")[-1])
        status_msg = await context.bot.send_message(chat_id, "🚀 جاري بدء صيد اليوزرات الحقيقية المتاحة...")
        
        found = await check_real_available_usernames(count)
        
        if found:
            res_text = f"🔥 تم صيد اليوزرات بنجاح ({len(found)}):\n\n"
            for u in found:
                res_text += f"@{u}\n"
            res_text += f"\n{DEV_SIGNATURE}"
            await context.bot.edit_message_text(res_text, chat_id=chat_id, message_id=status_msg.message_id)
        else:
            await context.bot.edit_message_text("عذراً، لم يتم العثور على يوزرات متاحة في هذه المحاولة. حاول مرة أخرى.", chat_id=chat_id, message_id=status_msg.message_id)

    elif data.startswith("pray_"):
        parts = data.split("_")
        en_city = parts[1]
        ar_city = parts[2]
        
        timings = get_prayer_times_jaafari(en_city)
        if timings:
            fajr = format_time_12h(timings.get('Fajr'))
            sunrise = format_time_12h(timings.get('Sunrise'))
            dhuhr = format_time_12h(timings.get('Dhuhr'))
            asr = format_time_12h(timings.get('Asr'))
            maghrib = format_time_12h(timings.get('Maghrib'))
            isha = format_time_12h(timings.get('Isha'))
            
            msg = (
                f"🕌 مواقيت الصلاة (التقويم الجعفري) في مدينة **{ar_city}**:\n\n"
                f"🔹 الفجر: `{fajr}`\n"
                f"🔹 الشروق: `{sunrise}`\n"
                f"🔹 الظهر: `{dhuhr}`\n"
                f"🔹 العصر: `{asr}`\n"
                f"🔹 المغرب: `{maghrib}`\n"
                f"🔹 العشاء: `{isha}`\n\n"
                f"{DEV_SIGNATURE}"
            )
            await query.message.reply_text(msg, parse_mode="Markdown")
        else:
            await query.message.reply_text("عذراً، حدث خطأ في جلب مواقيت الصلاة. حاول لاحقاً.")

    elif data.startswith("setmode_"):
        mode = data.replace("setmode_", "")
        user_selected_mode[user_id] = mode
        
        mode_names = {
            "tt_video": "تنزيل فيديو تيك توك",
            "tt_audio": "تنزيل أغنية تيك توك",
            "yt_video": "تنزيل فيديو يوتيوب",
            "yt_audio": "تنزيل أغنية يوتيوب",
            "insta_video": "تنزيل فيديو/صورة انستغرام",
            "pin": "تنزيل فيديو بينترست"
        }
        
        if mode == "pin":
            user_quality[user_id] = "best"
            await query.message.reply_text(f"تم اختيار وضع: **{mode_names.get(mode, mode)}**\n\nأرسل الرابط الآن للتحميل:", parse_mode="Markdown")
        elif "audio" in mode or mode == "tt_audio" or mode == "yt_audio":
            await query.message.reply_text(f"تم اختيار وضع: **{mode_names.get(mode, mode)}**\n\nاختر جودة الصوت المطلوبة:", reply_markup=get_audio_quality_keyboard(), parse_mode="Markdown")
        else:
            await query.message.reply_text(f"تم اختيار وضع: **{mode_names.get(mode, mode)}**\n\nاختر جودة الفيديو المطلوبة:", reply_markup=get_video_quality_keyboard(), parse_mode="Markdown")

    elif data.startswith("q_"):
        quality = data.replace("q_", "")
        if quality.startswith("audio_"):
            quality = quality.replace("audio_", "")
        
        user_quality[user_id] = quality
        await query.message.reply_text(f"✅ تم تثبيت الجودة بنجاح.\n\nأرسل الرابط الآن للتحميل:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if user_id in banned_users:
        return

    text = update.message.text
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if user_id not in user_activity_logs:
        user_activity_logs[user_id] = []

    # حفظ الحدث بصمت وبدون تدوين محتوى رسالة المستخدم للحفاظ على الخصوصية الكاملة
    if text:
        user_activity_logs[user_id].append(f"[{timestamp}] كتب نصاً (محتوى مخفي للخصوصية)")
        send_live_log(user, "كتب نصاً (محتوى مخفي)")
    elif update.message.photo:
        user_activity_logs[user_id].append(f"[{timestamp}] أرسل صورة")
        send_live_log(user, "أرسل صورة")
    elif update.message.audio or update.message.voice:
        user_activity_logs[user_id].append(f"[{timestamp}] أرسل بصمة أو ملف صوتي")
        send_live_log(user, "أرسل بصمة أو ملف صوتي")

    if not text:
        if update.message.photo:
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            file_bytes = await file.download_as_bytearray()
            
            current_state = user_state.get(user_id)
            if current_state == "remove_bg":
                msg = await update.message.reply_text("⏳ جاري إزالة الخلفية وتفريغ الصورة...")
                result_bytes = remove_background_api(file_bytes)
                if result_bytes:
                    await update.message.reply_photo(BytesIO(result_bytes), caption=f"تم إزالة الخلفية بنجاح ✅\n\n{DEV_SIGNATURE}")
                else:
                    await update.message.reply_text("عذراً، فشل تفريغ الصورة. تأكد من مفتاح Remove.bg أو جرب صورة أخرى.")
                user_state[user_id] = None
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
                
            elif current_state == "ascii_art":
                msg = await update.message.reply_text("⏳ جاري تحويل الصورة إلى رسم بالنقاط والحروف...")
                ascii_result = convert_image_to_ascii(file_bytes)
                if ascii_result:
                    await update.message.reply_text(f"```\n{ascii_result}\n```\n\n{DEV_SIGNATURE}", parse_mode="Markdown")
                else:
                    await update.message.reply_text("عذراً، حدث خطأ أثناء تحويل الصورة.")
                user_state[user_id] = None
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
            else:
                await update.message.reply_text("يرجى اختيار الخدمة المطلوبة من القائمة أولاً.")
            return

        elif update.message.audio or update.message.voice:
            audio = update.message.audio or update.message.voice
            file = await context.bot.get_file(audio.file_id)
            file_bytes = await file.download_as_bytearray()
            
            msg = await update.message.reply_text("⏳ جاري التعرف على الأغنية من البصمة الصوتية...")
            song_result = recognize_song_audd(file_bytes)
            if song_result:
                await update.message.reply_text(f"🎵 {song_result}\n\n{DEV_SIGNATURE}")
            else:
                await update.message.reply_text("عذراً، لم أتمكن من معرفة الأغنية. تأكد من وضوح الصوت.")
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
            return

        return

    welcome_keywords = ["فتح", "بوت", "خدمات", "استخدام", "عرض", "تنزيل", "افتح", "شون"]
    if text in welcome_keywords:
        await update.message.reply_text(
            f"أهلاً بك يا عزيزي في بوت الخدمات الشامل 🚀\n\nاختر الخدمة المطلوبة من الأزرار بالأسفل:\n\n{DEV_SIGNATURE}",
            reply_markup=get_main_menu()
        )
        return

    if text == "تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا، بينترست)":
        await update.message.reply_text("اختر منصة التحميل المطلوبة:", reply_markup=get_features_keyboard())

    elif text == "معرفة اسم الأغنية (من البصمة/الصوت)":
        await update.message.reply_text("أرسل بصمة صوتية أو ملف صوتي للأغنية لكي أتعرف عليها وأجلب لك اسمها والفنان 🎶")

    elif text == "إزالة خلفية الصورة (تفريغ)":
        user_state[user_id] = "remove_bg"
        await update.message.reply_text("أرسل الصورة الآن لكي أقوم بإزالة خلفيتها بدقة عالية 🖼️")

    elif text == "مواقيت الصلاة والأذكار (جعفري)":
        await update.message.reply_text("اختر مدينتك لعرض مواقيت الصلاة (التقويم الجعفري):", reply_markup=get_prayer_cities_keyboard())

    elif text == "صيد يوزرات تيليجرام الحقيقي (صاروخي)":
        await update.message.reply_text("اختر عدد اليوزرات التي تريد سحبها:", reply_markup=get_hunt_count_keyboard())

    elif text == "ملف أوكسفورد":
        await update.message.reply_text(f"📖 يمكنك تحميل ملف أوكسفورد عبر الرابط التالي:\n{OXFORD_PDF_URL}\n\n{DEV_SIGNATURE}")

    elif text == "زخرفة الأسماء الاحترافية":
        user_state[user_id] = "font_decoration"
        await update.message.reply_text("✍️ أرسل الاسم أو الكلمة الآن لكي أعطيك إياها بأنواع مختلفة من الخطوط العربية والإنجليزية:")

    elif text == "تحويل الصورة إلى رسم بالنقاط":
        user_state[user_id] = "ascii_art"
        await update.message.reply_text("أرسل الصورة الآن لكي أحولها إلى رسم بالحروف والنقاط (ASCII Art) 🎨")

    else:
        if text.startswith("http://") or text.startswith("https://"):
            mode = user_selected_mode.get(user_id, "yt_video")
            quality = user_quality.get(user_id, "best")
            is_audio = "audio" in mode or mode == "tt_audio" or mode == "yt_audio"
            
            if mode == "pin":
                is_audio = False

            msg = await update.message.reply_text("⏳ جاري تحميل الملف المطلوب، انتظر قليلاً...")
            success = await process_media_download(context, update.effective_chat.id, text, is_audio, quality)
            if not success:
                await update.message.reply_text("عذراً، فشل التحميل. تأكد من صحة الرابط أو جرب رابطاً آخر.")
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
            except:
                pass
        else:
            if user_state.get(user_id) == "font_decoration":
                res = decorate_text_fonts(text)
                await update.message.reply_text(res)
                user_state[user_id] = None
            else:
                res = decorate_text_fonts(text)
                await update.message.reply_text(res)

async def main_async():
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN is missing!")
        return

    # تشغيل البوت الأساسي وبوت التنبيهات معاً
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    alert_app = ApplicationBuilder().token(ALERT_BOT_TOKEN).build()

    # معالجات البوت الأصلي
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.AUDIO | filters.VOICE, handle_message))

    # معالجات بوت التنبيهات الثاني (أمر /view يكتب هنا حصراً)
    alert_app.add_handler(CommandHandler("view", alert_bot_view_command))

    await app.initialize()
    await alert_app.initialize()
    await app.start()
    await alert_app.start()

    await app.updater.start_polling()
    await alert_app.updater.start_polling()

    print("Both bots are running successfully...")

    stop_signal = asyncio.Event()
    await stop_signal.wait()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
