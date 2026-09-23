import os
import re
import random
import string
import time
import asyncio
import requests
from PIL import Image
from io import BytesIO
import yt_dlp

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1283009799"))

user_requests = {}
user_selected_mode = {}
user_state = {}

DEV_SIGNATURE = "\n\n━━━━━━━━━━━━━\n💻 *Dev: Yahia | المطور يحيى*\n⚠️ _ديربالك على عيونك لأن بس تصبح الصباح ينعمن من نور يحيى_"

def get_main_menu():
    keyboard = [
        [KeyboardButton("📥 تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا، بينترست)")],
        [KeyboardButton("🔍 صيد يوزرات تيليجرام الحقيقي (صاروخي)")],
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
        [InlineKeyboardButton("🎯 صيد صيغة: x1_x1", callback_data="hunt_type_1")],
        [InlineKeyboardButton("🎯 صيد صيغة: x1_1x", callback_data="hunt_type_2")],
        [InlineKeyboardButton("🎯 صيد صيغة: xx_11", callback_data="hunt_type_3")]
    ]
    return InlineKeyboardMarkup(keyboard)

def generate_random_matrix():
    bits = ["".join(random.choices("01", k=8)) for _ in range(4)]
    return " ".join(bits)

def generate_target_username(htype):
    letters = string.ascii_lowercase
    digits = string.digits
    if htype == "1":
        c1, c2 = random.choice(letters), random.choice(letters)
        d1, d2 = random.choice(digits), random.choice(digits)
        return f"{c1}{d1}_{c2}{d2}"
    elif htype == "2":
        c1, c2 = random.choice(letters), random.choice(letters)
        d1, d2 = random.choice(digits), random.choice(digits)
        return f"{c1}{d1}_{d2}{c2}"
    else:
        c1, c2 = random.choice(letters), random.choice(letters)
        d1, d2 = random.choice(digits), random.choice(digits)
        return f"{c1}{c2}_{d1}{d2}"

def check_telegram_username_real(username):
    try:
        url = f"https://t.me/{username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=1.5)
        if res.status_code == 200:
            text = res.text
            if "tgme_page_extra" not in text and "Preview channel" not in text and "Send Message" not in text and "tgme_page_title" not in text:
                return True
    except:
        pass
    return False

async def hunt_username_task(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, htype: str):
    found_username = None
    attempts = 0
    start_time = time.time()
    last_edit_time = 0

    while True:
        attempts += 1
        test_user = generate_target_username(htype)
        current_time = time.time()

        if current_time - last_edit_time > 2.0:
            matrix_code = generate_random_matrix()
            anim_text = (
                f"⚡ *جاري الصيد السريع والصاروخي...*\n\n"
                f"🟢 `{matrix_code}`\n"
                f"🔍 نفحص هسة: `@{test_user}`\n"
                f"📊 عدد المحاولات: `{attempts}`"
                f"{DEV_SIGNATURE}"
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

        await asyncio.sleep(0.01)

    elapsed_time = round(time.time() - start_time, 2)
    final_matrix = generate_random_matrix()
    
    result_text = (
        f"🎉 *تم ايجاد يوزر متاح، ويحيى عمك وعم ولدك!* 👑🔥\n\n"
        f"🟢 `{final_matrix}`\n"
        f"📌 اليوزر الصيد: `@{found_username}`\n"
        f"⏱ الوقت المستغرق: `{elapsed_time}` ثانية\n"
        f"📊 عدد المحاولات: `{attempts}`\n"
        f"🔗 الرابط المباشر: https://t.me/{found_username}"
        f"{DEV_SIGNATURE}"
    )
    try:
        await context.bot.edit_message_text(result_text, chat_id=chat_id, message_id=message_id, reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')
    except:
        await context.bot.send_message(chat_id, result_text, reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')

# دالة التنزيل عبر yt-dlp مع متطلبات التوافق الجدية
def download_media_direct(url, is_audio, quality="best"):
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
    else:
        if quality == "360":
            ydl_opts['format'] = 'b[height<=360]/b/best[height<=360]'
        elif quality == "720":
            ydl_opts['format'] = 'b[height<=720]/b/best[height<=720]'
        elif quality == "1080":
            ydl_opts['format'] = 'b[height<=1080]/b/best[height<=1080]'
        else:
            ydl_opts['format'] = 'b/best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if 'entries' in info and len(info['entries']) > 0:
            info = info['entries'][0]
        filename_actual = ydl.prepare_filename(info)
        
        if not os.path.exists(filename_actual):
            base = os.path.splitext(filename_actual)[0]
            for ext in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.jpg', '.png', '.webp']:
                if os.path.exists(base + ext):
                    return base + ext
        return filename_actual

async def process_media_download(context: ContextTypes.DEFAULT_TYPE, chat_id: int, url: str, is_audio: bool, quality: str = "best"):
    try:
        file_path = await asyncio.to_thread(download_media_direct, url, is_audio, quality)
        if file_path and os.path.exists(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, 'rb') as media_file:
                if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    await context.bot.send_photo(chat_id, media_file, caption=f"📌 *تم تنزيل الصورة بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                elif is_audio or ext in ['.mp3', '.m4a', '.wav', '.ogg']:
                    await context.bot.send_audio(chat_id, media_file, caption=f"🎵 *تم تحميل الصوت بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown', read_timeout=120, write_timeout=120)
                else:
                    await context.bot.send_video(chat_id, media_file, caption=f"🎬 *تم تحميل الفيديو بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown', read_timeout=120, write_timeout=120)
            
            try:
                os.remove(file_path)
            except:
                pass
            return True
    except Exception as e:
        print(f"Download Error Log: {e}")
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
        joined_lines = "\n".join(ascii_lines)
        return "```\n" + joined_lines + "\n```"
    except:
        return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🌟 *أهلاً بك يا غالي في بوت الخدمات الصاروخي* 🚀\n\nاختر الخدمة المطلوبة من الأزرار بالأسفل:{DEV_SIGNATURE}",
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
        await context.bot.send_message(chat_id, f"📥 أرسل الآن الرابط المطلوب للتحميل الفوري:{DEV_SIGNATURE}", parse_mode='Markdown')

    elif data == "type_video":
        await context.bot.edit_message_text(f"🎬 *اختر دقة الفيديو المطلوب:*{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id, reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')

    elif data == "type_audio":
        await context.bot.edit_message_text(f"🎵 *اختر جودة الصوت المطلوب:*{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id, reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')

    elif data.startswith("q_"):
        req = user_requests.get(chat_id)
        quality_code = data.replace("q_", "").replace("audio_", "")
        
        if req:
            url = req.get("url")
            is_audio = req.get("is_audio", False)
            await context.bot.edit_message_text(f"⏳ *جاري التحميل المباشر والسريع...*{DEV_SIGNATURE}", chat_id=chat_id, message_id=query.message.message_id, parse_mode='Markdown')

            success = await process_media_download(context, chat_id, url, is_audio, quality=quality_code)

            if not success:
                await context.bot.send_message(chat_id, f"⚠️ *تعذر التحميل، تأكد من صحة الرابط أو جرب رابطاً آخر.*{DEV_SIGNATURE}", parse_mode='Markdown')
            user_requests.pop(chat_id, None)

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text or ""

    if text.startswith("📥 تنزيل الفيديوهات والصوتيات"):
        await update.message.reply_text(f"📥 *أرسل رابط تيك توك، يوتيوب، انستغرام، أو بينترست مباشرة:*{DEV_SIGNATURE}", reply_markup=get_features_keyboard(), parse_mode='Markdown')
        return
    elif text == "🔍 صيد يوزرات تيليجرام الحقيقي (صاروخي)":
        await update.message.reply_text(f"🔍 *اختر صيغة الصيد والتحقق الحقيقي السريع من سيرفرات تيليجرام:*{DEV_SIGNATURE}", reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')
        return
    elif text == "✨ زخرفة الأسماء الاحترافية":
        user_state[chat_id] = "waiting_name"
        await update.message.reply_text(f"✨ *أرسل الآن الاسم أو الكلمة التي تريد زخرفتها (عربي أو إنجليزي):*{DEV_SIGNATURE}", parse_mode='Markdown')
        return
    elif text == "🎨 تحويل الصورة إلى رسم بالنقاط":
        user_state[chat_id] = "ascii"
        await update.message.reply_text(f"🎨 *أرسل أي صورة الآن لتحويلها إلى رسم فني بالنقاط:*{DEV_SIGNATURE}", reply_markup=get_main_menu(), parse_mode='Markdown')
        return

    if user_state.get(chat_id) == "waiting_name":
        user_state.pop(chat_id, None)
        name = text
        decorations = [
            f"⚡ ⦗ {name} ⦗ ⚡{DEV_SIGNATURE}\n-------------------",
            f"💎 »» {name} »« 💎{DEV_SIGNATURE}\n-------------------",
            f"🔥 ⦇ 𝄠 {name} 𝄠 ⦆ 🔥{DEV_SIGNATURE}\n-------------------",
            f"🌟 ༺ {name} ༻ 🌟{DEV_SIGNATURE}\n-------------------",
            f"🦅 ⫷ {name} ⫸ 🦅{DEV_SIGNATURE}\n-------------------",
            f"👑 𓏺 {name} 𓏺 👑{DEV_SIGNATURE}\n-------------------"
        ]
        final_response = f"✨ *إليك قائمة الزخارف الاحترافية لاسمك:*\n\n" + "\n".join(decorations)
        await update.message.reply_text(final_response, parse_mode='Markdown')
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
                await update.message.reply_text(f"🎵 *اختر جودة الصوت المطلوب:*{DEV_SIGNATURE}", reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')
            else:
                await update.message.reply_text(f"🎬 *اختر دقة الفيديو المطلوب:*{DEV_SIGNATURE}", reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')
        else:
            user_requests[chat_id] = {"url": target_url, "is_audio": False}
            await update.message.reply_text(f"📥 *اختر نوع التحميل المطلوب:*{DEV_SIGNATURE}", reply_markup=get_media_type_keyboard(), parse_mode='Markdown')
        return

    await update.message.reply_text(f"يرجى استخدام الأزرار بالأسفل لتنفيذ الخدمات المتاحة 🚀{DEV_SIGNATURE}", parse_mode='Markdown')

async def handle_photo_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        await update.message.reply_text(f"🎨 *جاري تحويل الصورة إلى رسم بالنقاط...*{DEV_SIGNATURE}", parse_mode='Markdown')
        photo_file = await update.message.photo[-1].get_file()
        downloaded_bytes = await photo_file.download_as_bytearray()
        res = convert_image_to_ascii(bytes(downloaded_bytes))
        if res:
            await update.message.reply_text(f"✨ *النتيجة:*\n\n{res}{DEV_SIGNATURE}", parse_mode='Markdown')
    except:
        await update.message.reply_text(f"⚠️ حدث خطأ بالمعالجة.{DEV_SIGNATURE}", parse_mode='Markdown')

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable is missing!")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_messages))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_messages))

    print("Bot is running perfectly...")
    app.run_polling()
