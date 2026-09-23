import os
import re
import random
import string
import time
import asyncio
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO
import yt_dlp

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1283009799"))
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
REMOVEBG_KEY = os.environ.get("REMOVEBG_KEY")

OXFORD_PDF_URL = "https://drive.google.com/uc?export=download&id=1GqE_PbV4GMUMo6B99sF3v4KtDlErCq7I"

user_requests = {}
user_selected_mode = {}
user_state = {}

DEV_SIGNATURE = "💻 Dev: YahiaFadhel"

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
        [InlineKeyboardButton("📌 تنزيل صور/فيديو بينترست", callback_data="setmode_pin")]
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

def get_hunt_types_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎯 صيغة: x1_1x", callback_data="hunt_type_1"), InlineKeyboardButton("🎯 صيغة: xx_11", callback_data="hunt_type_2")],
        [InlineKeyboardButton("🎯 صيغة: x1x1x", callback_data="hunt_type_3"), InlineKeyboardButton("🎯 صيغة: xx11x", callback_data="hunt_type_4")],
        [InlineKeyboardButton("🎯 صيغة: x_1x1", callback_data="hunt_type_5"), InlineKeyboardButton("🎯 صيغة: x_x11", callback_data="hunt_type_6")],
        [InlineKeyboardButton("🎯 صيغة: x_xxx", callback_data="hunt_type_7")]
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

def generate_random_matrix():
    bits = ["".join(random.choices("01", k=8)) for _ in range(4)]
    return " ".join(bits)

def generate_target_username(htype):
    letters = string.ascii_lowercase
    digits = string.digits
    x1, x2, x3, x4 = random.choice(letters), random.choice(letters), random.choice(letters), random.choice(letters)
    d1, d2 = random.choice(digits), random.choice(digits)

    if htype == "1": return f"{x1}{d1}_{d2}{x2}"
    elif htype == "2": return f"{x1}{x2}_{d1}{d2}"
    elif htype == "3": return f"{x1}{d1}{x2}{d2}{x3}"
    elif htype == "4": return f"{x1}{x2}{d1}{d2}{x3}"
    elif htype == "5": return f"{x1}_{d1}{x2}{d2}"
    elif htype == "6": return f"{x1}_{x2}{d1}{d2}"
    elif htype == "7": return f"{x1}_{x2}{x3}{x4}"
    return f"{x1}{d1}_{d2}{x2}"

def check_telegram_username_real(username):
    try:
        url = f"https://t.me/{username}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=1.5)
        if res.status_code == 200:
            text = res.text
            if "tgme_page_extra" not in text and "Preview channel" not in text and "Send Message" not in text and "tgme_page_title" not in text:
                return True
    except:
        pass
    return False

def build_sword_with_info(username, attempts, elapsed_time):
    user_str = f"@{username}".center(22)
    att_str = f"Attempts: {attempts}".center(22)
    time_str = f"Time: {elapsed_time}s".center(22)
    dev_str = f"{DEV_SIGNATURE}".center(22)

    return f"""```
                  /\\
                 /  \\
                / /\\ \\
               / /  \\ \\
              / /    \\ \\
             / /  /\\  \\ \\
            / /  /    \\  \\ \\
           / /  /      \\  \\ \\
          | |  |        |  | |
          | |  |        |  | |
          | | [SUCCESS] |  | |
          | |           |  | |
          | |{user_str}| |
          | |           |  | |
          | |{att_str}| |
          | |           |  | |
          | |{time_str}| |
          | |           |  | |
          | |{dev_str}| |
          | |           |  | |
          | |___________|  | |
         /                   \\
        /____   _______   ____\\
             | |       | |
             | |       | |
            [___________]
                 |   |
                 |   |
                (_____)
```"""

async def hunt_username_task(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, htype: str):
    found_username = None
    attempts = 0
    start_time = time.time()
    last_edit_time = 0

    while True:
        attempts += 1
        test_user = generate_target_username(htype)
        current_time = time.time()

        if current_time - last_edit_time > 1.8:
            matrix_code = generate_random_matrix()
            anim_text = (
                f"⚡ *جاري الصيد السريع والصاروخي...*\n\n"
                f"🟢 `{matrix_code}`\n"
                f"🔍 نفحص هسة: `@{test_user}`\n"
                f"📊 عدد المحاولات: `{attempts}`\n\n"
                f"━━━━━━━━━━━━━\n{DEV_SIGNATURE}"
            )
            try:
                await context.bot.edit_message_text(anim_text, chat_id=chat_id, message_id=message_id, parse_mode='Markdown')
                last_edit_time = time.time()
            except:
                pass

        is_available = await asyncio.to_thread(check_telegram_username_real, test_user)
        if is_available:
            found_username = test_user
            break

        await asyncio.sleep(0.02)

    elapsed_time = round(time.time() - start_time, 2)
    sword_final = build_sword_with_info(found_username, attempts, elapsed_time)
    
    caption_text = (
        f"👑 *تم صيد يوزر متاح بنجاح!*\n"
        f"🔗 الرابط المباشر: https://t.me/{found_username}\n\n"
        f"{sword_final}"
    )

    await context.bot.send_message(chat_id=chat_id, text=caption_text, reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')

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

def download_media_direct(url, is_audio, quality="best"):
    if "youtube.com" in url or "youtu.be" in url:
        yt_file = download_youtube_rapidapi(url, is_audio)
        if yt_file and os.path.exists(yt_file): return yt_file

    filename = f"dl_{int(time.time())}_{random.randint(1000,9999)}"
    ydl_opts = {
        'outtmpl': f'{filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    if is_audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
    else:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info and len(info['entries']) > 0: info = info['entries'][0]
            filename_actual = ydl.prepare_filename(info)
            if os.path.exists(filename_actual): return filename_actual

            base = os.path.splitext(filename_actual)[0]
            for ext in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.jpg', '.png', '.webp']:
                if os.path.exists(base + ext): return base + ext
    except Exception as e:
        print(f"yt-dlp error: {e}")
    return None

async def process_media_download(context: ContextTypes.DEFAULT_TYPE, chat_id: int, url: str, is_audio: bool, quality: str = "best"):
    try:
        file_path = await asyncio.to_thread(download_media_direct, url, is_audio, quality)
        if file_path and os.path.exists(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, 'rb') as media_file:
                if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    await context.bot.send_photo(chat_id, media_file, caption=f"📌 *تم تنزيل الصورة بنجاح*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
                elif is_audio or ext in ['.mp3', '.m4a', '.wav', '.ogg']:
                    await context.bot.send_audio(chat_id, media_file, caption=f"🎵 *تم تحميل الصوت بنجاح*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
                else:
                    await context.bot.send_video(chat_id, media_file, caption=f"🎬 *تم تحميل الفيديو بنجاح*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
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
                return f"🎵 *اسم الأغنية:* {title}\n👤 *الفنان:* {artist}"
    except:
        pass
    return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🌟 *أهلاً بك يا غالي في بوت الخدمات الصاروخي* 🚀\n\nاختر الخدمة المطلوبة من الأزرار بالأسفل:\n\n{DEV_SIGNATURE}",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    if data.startswith("hunt_type_"):
        htype = data.split("_")[-1]
        asyncio.create_task(hunt_username_task(context, chat_id, query.message.message_id, htype))

    elif data.startswith("setmode_"):
        mode = data.replace("setmode_", "")
        user_selected_mode[chat_id] = mode
        await context.bot.send_message(chat_id, f"📥 أرسل الآن الرابط المطلوب للتحميل الفوري:\n\n{DEV_SIGNATURE}", parse_mode='Markdown')

    elif data == "type_video":
        await context.bot.edit_message_text(f"🎬 *اختر دقة الفيديو المطلوب:*\n\n{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id, reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')

    elif data == "type_audio":
        await context.bot.edit_message_text(f"🎵 *اختر جودة الصوت المطلوب:*\n\n{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id, parse_mode='Markdown')

    elif data.startswith("q_"):
        req = user_requests.get(chat_id)
        quality_code = data.replace("q_", "").replace("audio_", "")
        if req:
            url = req.get("url")
            is_audio = req.get("is_audio", False)
            await context.bot.edit_message_text(f"⏳ *جاري التحميل المباشر والسريع...*\n\n{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id, parse_mode='Markdown')
            success = await process_media_download(context, chat_id, url, is_audio, quality=quality_code)
            if not success:
                await context.bot.send_message(chat_id, f"⚠️ *تعذر التحميل، تأكد من صحة الرابط أو جرب رابطاً آخر.*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
            user_requests.pop(chat_id, None)

    elif data.startswith("pray_"):
        parts = data.split("_")
        city_en = parts[1]
        city_ar = parts[2]
        
        timings = get_prayer_times_jaafari(city_en)
        if timings:
            text = (
                f"🕌 *مواقيت الصلاة الشرعية (المذهب الجعفري) - {city_ar}:*\n\n"
                f"🌅 *أذان الفجر:* `{format_time_12h(timings['Fajr'])}`\n"
                f"☀️ *الشروق:* `{format_time_12h(timings['Sunrise'])}`\n"
                f"☀️ *أذان الظهر:* `{format_time_12h(timings['Dhuhr'])}`\n"
                f"🌤 *أذان العصر:* `{format_time_12h(timings['Asr'])}`\n"
                f"🌆 *أذان المغرب الشرعي:* `{format_time_12h(timings['Maghrib'])}`\n"
                f"🌌 *أذان العشاء:* `{format_time_12h(timings['Isha'])}`\n"
                f"🌙 *منتصف الليل الشرعي:* `{format_time_12h(timings['Midnight'])}`\n\n"
                f"🤲 *من الأذكار:* (اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وآلِ مُحَمَّدٍ)\n\n"
                f"{DEV_SIGNATURE}"
            )
            await context.bot.send_message(chat_id, text, parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id, "⚠️ تعذر جلب مواقيت الصلاة حالياً، حاول مجدداً.", parse_mode='Markdown')

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text or ""

    if text.startswith("📥 تنزيل الفيديوهات والصوتيات"):
        await update.message.reply_text(f"📥 *أرسل رابط تيك توك، يوتيوب، انستغرام، أو بينترست مباشرة:*\n\n{DEV_SIGNATURE}", reply_markup=get_features_keyboard(), parse_mode='Markdown')
        return
    elif text == "🔍 صيد يوزرات تيليجرام الحقيقي (صاروخي)":
        await update.message.reply_text(f"🔍 *اختر صيغة الصيد المطلوبة:*\n\n{DEV_SIGNATURE}", reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')
        return
    elif text == "📚 ملف أوكسفورد":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📥 اضغط هنا لتنزيل ملف أوكسفورد", url=OXFORD_PDF_URL)]])
        await update.message.reply_text(f"📚 *تفضل رابط تحميل ملف أوكسفورد المباشر:*\n\n{DEV_SIGNATURE}", reply_markup=kb, parse_mode='Markdown')
        return
    elif text == "✨ زخرفة الأسماء الاحترافية":
        user_state[chat_id] = "waiting_name"
        await update.message.reply_text(f"✨ *أرسل الآن الاسم أو الكلمة التي تريد زخرفتها (عربي أو إنجليزي):*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
        return
    elif text == "🎨 تحويل الصورة إلى رسم بالنقاط":
        user_state[chat_id] = "ascii"
        await update.message.reply_text(f"🎨 *أرسل أي صورة الآن لتحويلها إلى رسم فني بالنقاط:*\n\n{DEV_SIGNATURE}", reply_markup=get_main_menu(), parse_mode='Markdown')
        return
    elif text == "🎵 معرفة اسم الأغنية (من البصمة/الصوت)":
        user_state[chat_id] = "shazam"
        await update.message.reply_text(f"🎵 *أرسل البصمة الصوتية أو الملف الصوتي الآن لمعرفة اسمه:* \n\n{DEV_SIGNATURE}", parse_mode='Markdown')
        return
    elif text == "🖼 إزالة خلفية الصورة (تفريغ)":
        user_state[chat_id] = "remove_bg"
        await update.message.reply_text(f"🖼 *أرسل الصورة المراد إزالة خلفيتها الآن:*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
        return
    elif text.startswith("⏰ مواقيت الصلاة والأذكار"):
        await update.message.reply_text(f"🕌 *اختر محافظتك لمشاهدة مواقيت الصلاة اليومية (حسب التوقيت الشرعي الجعفري):*\n\n{DEV_SIGNATURE}", reply_markup=get_prayer_cities_keyboard(), parse_mode='Markdown')
        return

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
        await update.message.reply_text(f"✨ *إليك قائمة الزخارف الاحترافية لاسمك:*\n\n" + "\n".join(decorations) + f"\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
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
                await update.message.reply_text(f"🎵 *اختر جودة الصوت المطلوب:*\n\n{DEV_SIGNATURE}", reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')
            else:
                await update.message.reply_text(f"🎬 *اختر دقة الفيديو المطلوب:*\n\n{DEV_SIGNATURE}", reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')
        else:
            user_requests[chat_id] = {"url": target_url, "is_audio": False}
            await update.message.reply_text(f"📥 *اختر نوع التحميل المطلوب:*\n\n{DEV_SIGNATURE}", reply_markup=get_media_type_keyboard(), parse_mode='Markdown')
        return

    await update.message.reply_text(f"يرجى استخدام الأزرار بالأسفل لتنفيذ الخدمات المتاحة 🚀\n\n{DEV_SIGNATURE}", parse_mode='Markdown')

async def handle_photo_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mode = user_state.get(chat_id)

    if mode == "remove_bg":
        user_state.pop(chat_id, None)
        await update.message.reply_text(f"⏳ *جاري تفريغ وإزالة خلفية الصورة...*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
        try:
            photo_file = await update.message.photo[-1].get_file()
            downloaded_bytes = await photo_file.download_as_bytearray()
            out_bytes = remove_background_api(bytes(downloaded_bytes))
            if out_bytes:
                await context.bot.send_document(chat_id, document=BytesIO(out_bytes), filename="no_bg.png", caption=f"🖼 *تم تفريغ الصورة بنجاح!*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
            else:
                await update.message.reply_text("⚠️ تعذر إزالة الخلفية، يرجى إضافة REMOVEBG_KEY بـ Railway لتفعيل الخدمة.")
        except:
            await update.message.reply_text("⚠️ حدث خطأ في معالجة الصورة.")
        return

    try:
        await update.message.reply_text(f"🎨 *جاري تحويل الصورة إلى رسم بالنقاط...*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
        photo_file = await update.message.photo[-1].get_file()
        downloaded_bytes = await photo_file.download_as_bytearray()
        res = convert_image_to_ascii(bytes(downloaded_bytes))
        if res:
            await update.message.reply_text(f"✨ *النتيجة:*\n\n{res}\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
    except:
        await update.message.reply_text("⚠️ حدث خطأ بالمعالجة.")

async def handle_audio_voice_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🔍 *جاري البحث عن اسم الأغنية...*\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
    try:
        audio_obj = update.message.voice or update.message.audio
        if audio_obj:
            file = await audio_obj.get_file()
            audio_bytes = await file.download_as_bytearray()
            res = recognize_song_audd(bytes(audio_bytes))
            if res:
                yt_query = res.replace("🎵 *اسم الأغنية:* ", "").replace("\n👤 *الفنان:* ", " ")
                search_url = f"https://www.youtube.com/results?search_query={yt_query.replace(' ', '+')}"
                await update.message.reply_text(f"{res}\n\n🔗 [ابحث عنها في يوتيوب]({search_url})\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"⚠️ لم أستطع التعرف على الأغنية، تأكد من وضوح الصوت.\n\n{DEV_SIGNATURE}", parse_mode='Markdown')
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
