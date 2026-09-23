import os
import telebot
import requests
import re
import random
import string
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

DEV_SIGNATURE = "\n\n━━━━━━━━━━━━━\n💻 *Dev: Yahia | المطور يحيى*"

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = KeyboardButton("📥 تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا)")
    btn2 = KeyboardButton("🔍 صيد يوزرات تيليجرام المتطورة")
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
        InlineKeyboardButton("📸 تنزيل فيديو/صورة انستغرام", callback_data="setmode_insta")
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
        InlineKeyboardButton("🔹 صيغة 1: (tt_11)", callback_data="hunt_type_1"),
        InlineKeyboardButton("🔹 صيغة 2: (t1_t1)", callback_data="hunt_type_2"),
        InlineKeyboardButton("🔹 صيغة 3: (t1_1t)", callback_data="hunt_type_3")
    )
    return markup

def process_tiktok(chat_id, url, is_audio):
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}&hd=1"
        res = requests.get(api_url, timeout=15).json()
        if res.get("code") == 0:
            data = res.get("data", {})
            if is_audio:
                bot.send_audio(chat_id, data.get("music"), caption=f"🎶 *تيك توك | تم تحميل الصوت*{DEV_SIGNATURE}", parse_mode='Markdown')
                return True
            else:
                bot.send_video(chat_id, data.get("hdplay") or data.get("play"), caption=f"🎬 *تيك توك | تم التحميل بدون علامة مائية*{DEV_SIGNATURE}", parse_mode='Markdown')
                return True
    except:
        pass
    return False

def process_instagram(chat_id, url):
    try:
        api_url = f"https://cobalt.tools/api/json"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = {"url": url, "videoQuality": "max"}
        res = requests.post("https://co.wuk.sh/api/json", json=payload, headers=headers, timeout=12)
        if res.status_code == 200:
            dl_url = res.json().get("url")
            if dl_url:
                bot.send_video(chat_id, dl_url, caption=f"📸 *انستغرام | تم تحميل المحتوى بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                return True
    except:
        pass
    return False

def process_youtube(chat_id, url, is_audio, quality):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    servers = ["https://co.wuk.sh/api/json", "https://api.cobalt.tools/"]
    payload = {"url": url, "videoQuality": quality if not is_audio else "max", "audioFormat": "mp3", "downloadMode": "audio" if is_audio else "auto"}
    for server in servers:
        try:
            res = requests.post(server, json=payload, headers=headers, timeout=12)
            if res.status_code == 200:
                dl_url = res.json().get("url")
                if dl_url:
                    if is_audio:
                        bot.send_audio(chat_id, dl_url, caption=f"🎵 *تم تحميل الصوت بنجاح*{DEV_SIGNATURE}", parse_mode='Markdown')
                    else:
                        bot.send_video(chat_id, dl_url, caption=f"🎬 *تم تحميل الفيديو*{DEV_SIGNATURE}", parse_mode='Markdown')
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
        return f"```\n" + "\n".join(ascii_lines) + "\n```"
    except:
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"🌟 *أهلاً بك يا بطل في بوت الخدمات الاحترافي* 🚀\n\nاختر الخدمة من الأزرار بالأسفل:{DEV_SIGNATURE}", reply_markup=get_main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "📥 تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا)")
def menu_download(message):
    bot.reply_to(message, f"📥 *أرسل رابط تيك توك، يوتيوب، أو انستغرام مباشرة، أو اختر الخدمة:*{DEV_SIGNATURE}", reply_markup=get_features_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🔍 صيد يوزرات تيليجرام المتطورة")
def menu_hunt(message):
    bot.reply_to(message, f"🔍 *اختر صيغة اليوزرات التي تريد صيدها:*{DEV_SIGNATURE}", reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "✨ زخرفة الأسماء الاحترافية")
def menu_decorate(message):
    user_state[message.chat.id] = "waiting_name"
    bot.reply_to(message, f"✨ *أرسل الآن الاسم أو الكلمة التي تريد زخرفتها (عربي أو إنجليزي):*{DEV_SIGNATURE}", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🎨 تحويل الصورة إلى رسم بالنقاط")
def menu_ascii(message):
    user_state[message.chat.id] = "ascii"
    bot.reply_to(message, f"🎨 *أرسل أي صورة الآن لتحويلها إلى رسم فني بالنقاط:*{DEV_SIGNATURE}", reply_markup=get_main_menu(), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("hunt_type_"):
        htype = data.split("_")[-1]
        
        # تأثير الودينغ الهكري بالأرقام الخضراء 0101
        matrix_msg = f"🟢 `01001001 01010011 01010011 01010011`\n⏳ *جاري اختراق فحص الخوادم وبدء الصيد...*\n`🟢 [██████████] 100%`{DEV_SIGNATURE}"
        msg = bot.edit_message_text(matrix_msg, chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown')
        
        import time
        time.sleep(1.5)

        # توليد حسب الصيغة المطلوبة
        if htype == "1": # tt_11
            l = ''.join(random.choices(string.ascii_lowercase, k=2))
            n = ''.join(random.choices(string.digits, k=2))
            username = f"{l}_{n}"
        elif htype == "2": # t1_t1
            l1, l2 = random.choice(string.ascii_lowercase), random.choice(string.ascii_lowercase)
            d1, d2 = random.choice(string.digits), random.choice(string.digits)
            username = f"{l1}{d1}_{l2}{d2}"
        else: # t1_1t
            l1, l2 = random.choice(string.ascii_lowercase), random.choice(string.ascii_lowercase)
            d1, d2 = random.choice(string.digits), random.choice(string.digits)
            username = f"{l1}{d1}_{d2}{l2}"

        result_text = (
            f"🎉 *تم صيد يوزر مميز بنجاح!* ✨\n\n"
            f"🟢 `01001111 01010011 01010011`\n"
            f"📌 اليوزر: `@{username}`\n"
            f"🔗 الرابط: https://t.me/{username}"
            f"{DEV_SIGNATURE}"
        )
        try:
            bot.edit_message_text(result_text, chat_id=chat_id, message_id=msg.message_id, reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')
        except:
            bot.send_message(chat_id, result_text, reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')

    elif data.startswith("setmode_"):
        mode = data.replace("setmode_", "")
        user_selected_mode[chat_id] = mode
        if mode == "insta":
            bot.send_message(chat_id, f"📸 أرسل الآن رابط انستغرام للتحميل:{DEV_SIGNATURE}", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, f"📥 أرسل الآن الرابط للمتابعة:{DEV_SIGNATURE}", parse_mode='Markdown')

    elif data == "type_video":
        bot.send_message(chat_id, f"🎬 *اختر دقة الفيديو:*{DEV_SIGNATURE}", reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')
    elif data == "type_audio":
        bot.send_message(chat_id, f"🎵 *اختر جودة الصوت:*{DEV_SIGNATURE}", reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')

    elif data.startswith("q_"):
        req = user_requests.get(chat_id)
        if req:
            url, is_audio = req.get("url"), req.get("is_audio", False)
            q_map = {"q_360": "360", "q_720": "720", "q_1080": "1080", "q_max": "max", "q_audio_128": "128", "q_audio_320": "320"}
            selected_q = q_map.get(data, "max")
            
            bot.edit_message_text(f"⏳ *جاري التحميل...*{DEV_SIGNATURE}", chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown')
            
            success = False
            if "instagram.com" in url:
                success = process_instagram(chat_id, url)
            elif "tiktok.com" in url:
                success = process_tiktok(chat_id, url, is_audio)
            else:
                success = process_youtube(chat_id, url, is_audio, selected_q)

            if not success:
                bot.send_message(chat_id, f"⚠️ *تعذر التحميل، تأكد من صحة الرابط.*{DEV_SIGNATURE}", parse_mode='Markdown')
            user_requests.pop(chat_id, None)

    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"🎨 *جاري تحويل الصورة إلى رسم بالنقاط...*{DEV_SIGNATURE}", parse_mode='Markdown')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        res = convert_image_to_ascii(downloaded)
        if res:
            bot.reply_to(message, f"✨ *النتيجة:*\n\n{res}{DEV_SIGNATURE}", parse_mode='Markdown')
    except:
        bot.reply_to(message, f"⚠️ حدث خطأ بالمعالجة.{DEV_SIGNATURE}", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    text = message.text or ""

    if text.startswith("/") or text in ["📥 تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا)", "🔍 صيد يوزرات تيليجرام المتطورة", "✨ زخرفة الأسماء الاحترافية", "🎨 تحويل الصورة إلى رسم بالنقاط"]:
        return

    # معالجة قسم الزخرفة
    if user_state.get(chat_id) == "waiting_name":
        user_state.pop(chat_id, None)
        name = text
        # توليد زخارف متنوعة ومرتبة مع خطوط وحقوقك تفصل بينها
        decorations = [
            f"⚡ ⦗ {name} ⦗ ⚡{DEV_SIGNATURE}\n-------------------",
            f"💎 »» {name} «« 💎{DEV_SIGNATURE}\n-------------------",
            f"🔥 ⦇ 𝄠 {name} 𝄠 ⦆ 🔥{DEV_SIGNATURE}\n-------------------",
            f"🌟 ༺ {name} ༻ 🌟{DEV_SIGNATURE}\n-------------------",
            f"🦅 ⫷ {name} ⫸ 🦅{DEV_SIGNATURE}\n-------------------",
            f"👑 𓏺 {name} 𓏺 👑{DEV_SIGNATURE}\n-------------------"
        ]
        final_response = f"✨ *إليك قائمة الزخارف الاحترافية لاسمك:*\n\n" + "\n".join(decorations)
        bot.reply_to(message, final_response, parse_mode='Markdown')
        return

    # معالجة الروابط
    urls = re.findall(r'https?://[^\s]+', text)
    if urls:
        target_url = urls[0]
        if "instagram.com" in target_url:
            bot.reply_to(message, f"⏳ *جاري جلب محتوى انستغرام...*{DEV_SIGNATURE}", parse_mode='Markdown')
            process_instagram(chat_id, target_url)
            return
        elif "tiktok.com" in target_url or "youtube.com" in target_url or "youtu.be" in target_url:
            preset = user_selected_mode.get(chat_id)
            if preset == "insta":
                process_instagram(chat_id, target_url)
                return
            if preset:
                is_audio = "audio" in preset
                user_requests[chat_id] = {"url": target_url, "is_audio": is_audio}
                user_selected_mode.pop(chat_id, None)
                if is_audio:
                    bot.reply_to(message, f"🎵 *اختر جودة الصوت:*{DEV_SIGNATURE}", reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')
                else:
                    bot.reply_to(message, f"🎬 *اختر دقة الفيديو:*{DEV_SIGNATURE}", reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')
            else:
                user_requests[chat_id] = {"url": target_url, "is_audio": False}
                bot.reply_to(message, f"📥 *اختر نوع التحميل:*{DEV_SIGNATURE}", reply_markup=get_media_type_keyboard(), parse_mode='Markdown')
            return

    bot.reply_to(message, f"يرجى استخدام الأزرار بالأسفل لتنفيذ الخدمات المتاحة 🚀{DEV_SIGNATURE}", parse_mode='Markdown')

if __name__ == "__main__":
    print("Bot is starting polling...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
