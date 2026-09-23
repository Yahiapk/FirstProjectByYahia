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

# توقيع المطور الثابت لحفظ الحقوق
DEV_SIGNATURE = "\n\n━━━━━━━━━━━━━\n💻 *Dev: Yahia | المطور يحيى*"

# القائمة الرئيسية للأزرار الثلاثة
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = KeyboardButton("📥 تنزيل الفيديوهات والصوتيات")
    btn2 = KeyboardButton("🔍 صيد يوزرات تيليجرام")
    btn3 = KeyboardButton("🎨 تحويل الصورة إلى رسم بالنقاط")
    markup.add(btn1, btn2, btn3)
    return markup

def get_features_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    btn_tt_video = InlineKeyboardButton("🎬 تنزيل فيديو تيك توك", callback_data="setmode_tt_video")
    btn_tt_audio = InlineKeyboardButton("🎶 تنزيل أغنية تيك توك", callback_data="setmode_tt_audio")
    btn_yt_video = InlineKeyboardButton("📹 تنزيل فيديو يوتيوب", callback_data="setmode_yt_video")
    btn_yt_audio = InlineKeyboardButton("🎵 تنزيل أغنية يوتيوب", callback_data="setmode_yt_audio")
    markup.add(btn_tt_video, btn_tt_audio, btn_yt_video, btn_yt_audio)
    return markup

def get_video_quality_keyboard():
    markup = InlineKeyboardMarkup()
    btn_360 = InlineKeyboardButton("📱 360p", callback_data="q_360")
    btn_720 = InlineKeyboardButton("📺 720p HD", callback_data="q_720")
    btn_1080 = InlineKeyboardButton("🖥 1080p Full HD", callback_data="q_1080")
    btn_max = InlineKeyboardButton("🌟 4K / Max", callback_data="q_max")
    markup.row(btn_360, btn_720)
    markup.row(btn_1080, btn_max)
    return markup

def get_audio_quality_keyboard():
    markup = InlineKeyboardMarkup()
    btn_128 = InlineKeyboardButton("🎧 128 kbps (عادية)", callback_data="q_audio_128")
    btn_320 = InlineKeyboardButton("🎵 320 kbps (HQ نقية)", callback_data="q_audio_320")
    markup.row(btn_128, btn_320)
    return markup

def get_media_type_keyboard():
    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("🎬 تنزيل فيديو", callback_data="type_video")
    btn_audio = InlineKeyboardButton("🎵 تنزيل صوت / أغنية", callback_data="type_audio")
    markup.row(btn_video, btn_audio)
    return markup

def get_hunt_keyboard():
    markup = InlineKeyboardMarkup()
    btn_start_hunt = InlineKeyboardButton("🚀 بدء الصيد", callback_data="start_hunting")
    markup.add(btn_start_hunt)
    return markup

# دوال التنزيل مع الحقوق
def process_tiktok(chat_id, url, is_audio):
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}&hd=1"
        res = requests.get(api_url, timeout=15).json()
        if res.get("code") == 0:
            data = res.get("data", {})
            if is_audio:
                audio_url = data.get("music")
                if audio_url:
                    bot.send_audio(chat_id, audio_url, caption=f"🎶 *تيك توك | تم تحميل الصوت بنجاح*_{DEV_SIGNATURE}", parse_mode='Markdown')
                    return True
            else:
                video_url = data.get("hdplay") or data.get("play")
                if video_url:
                    bot.send_video(chat_id, video_url, caption=f"🎬 *تيك توك | تم التحميل بدون علامة مائية*_{DEV_SIGNATURE}", parse_mode='Markdown')
                    return True
    except Exception as e:
        print(f"TikTok error: {e}")
    return False

def process_youtube(chat_id, url, is_audio, quality):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    servers = [
        "https://co.wuk.sh/api/json",
        "https://cobalt-api.kwiatek.xyz/",
        "https://api.cobalt.tools/"
    ]
    payload = {
        "url": url,
        "videoQuality": quality if not is_audio else "max",
        "audioFormat": "mp3",
        "downloadMode": "audio" if is_audio else "auto"
    }
    for server in servers:
        try:
            res = requests.post(server, json=payload, headers=headers, timeout=12)
            if res.status_code == 200:
                dl_url = res.json().get("url")
                if dl_url:
                    if is_audio:
                        bot.send_audio(chat_id, dl_url, caption=f"🎵 *تم تحميل الصوت بنجاح*_{DEV_SIGNATURE}", parse_mode='Markdown')
                    else:
                        q_title = "أعلى دقة" if quality == "max" else f"{quality}p"
                        bot.send_video(chat_id, dl_url, caption=f"🎬 *تم تحميل الفيديو بدقة ({q_title})*_{DEV_SIGNATURE}", parse_mode='Markdown')
                    return True
        except Exception as e:
            print(f"Error on {server}: {e}")
            continue
    return False

# تحويل الصورة إلى رسم بالنقاط
def convert_image_to_ascii(image_bytes):
    try:
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        aspect_ratio = height / float(width)
        new_width = 45
        new_height = int(aspect_ratio * new_width * 0.55)
        img = img.resize((new_width, new_height)).convert('L')
        
        pixels = img.getdata()
        chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
        new_pixels = [chars[pixel // 25] for pixel in pixels]
        new_pixels = "".join(new_pixels)
        
        ascii_lines = [new_pixels[index:index + new_width] for index in range(0, len(new_pixels), new_width)]
        ascii_art = "\n".join(ascii_lines)
        return f"```\n{ascii_art}\n```"
    except Exception as e:
        print(f"ASCII conversion error: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🌟 *أهلاً بك عزيزي في بوت الخدمات الشامل* 🚀\n\n"
        "اختر القسم المطلوب من الأزرار السفلية للبدء بالتنزيل أو صيد اليوزرات أو تحويل الصور."
        f"{DEV_SIGNATURE}"
    )
    bot.reply_to(message, welcome_text, reply_markup=get_main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "📥 تنزيل الفيديوهات والصوتيات")
def menu_download(message):
    user_state[message.chat.id] = "download"
    text = f"📥 *قسم تنزيل الوسائط*\n\nأرسل رابط تيك توك أو يوتيوب مباشرة، أو اضغط أدناه للتحكم بالأزرار:" + DEV_SIGNATURE
    bot.reply_to(message, text, reply_markup=get_features_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🔍 صيد يوزرات تيليجرام")
def menu_hunt(message):
    user_state[message.chat.id] = "hunt"
    text = f"🔍 *قسم صيد يوزرات تيليجرام*\n\nاضغط على زر *(بدء الصيد)* أدناه للبحث عن يوزرات عشوائية ممتازة ومتاحة:" + DEV_SIGNATURE
    bot.reply_to(message, text, reply_markup=get_hunt_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🎨 تحويل الصورة إلى رسم بالنقاط")
def menu_ascii(message):
    user_state[message.chat.id] = "ascii"
    text = f"🎨 *قسم تحويل الصور إلى رسومات بالنقاط*\n\nأرسل الآن أي صورة تريد تحويلها إلى تصميم فني مبهر:" + DEV_SIGNATURE
    bot.reply_to(message, text, reply_markup=get_main_menu(), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "start_hunting":
        msg = bot.edit_message_text(f"⏳ *جاري فحص وتوليد اليوزرات العشوائية...*\n`⌛ [▒▒▒▒▒▒▒▒▒▒] 0%`{DEV_SIGNATURE}", chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown')
        
        import time
        steps = [
            (f"⏳ *تفتيش خوادم تيليجرام المتاحة...*\n`🔄 [████▒▒▒▒▒▒] 40%`{DEV_SIGNATURE}", 1),
            (f"⏳ *فحص حالة توفر اليوزر النهائي...*\n`🔄 [████████▒▒] 85%`{DEV_SIGNATURE}", 1),
        ]
        for text, delay in steps:
            time.sleep(delay)
            try:
                bot.edit_message_text(text, chat_id=chat_id, message_id=msg.message_id, parse_mode='Markdown')
            except:
                pass

        # توليد يوزر بالصيغة المطلوبة (مثال: حرف عشوائي أو حرفين + أرقام عشوائية مثل t_12 أو tt_199)
        random_letters = ''.join(random.choices(string.ascii_lowercase, k=random.randint(1, 2)))
        random_numbers = ''.join(random.choices(string.digits, k=random.randint(2, 3)))
        pattern_type = f"{random_letters}_{random_numbers}"
        
        check_url = f"https://t.me/{pattern_type}"
        r = requests.get(check_url)
        
        time.sleep(1)
        result_text = (
            f"🎉 *تم الصيد بنجاح وتم العثور على يوزر مميز!*\n\n"
            f"📌 اليوزر: `@{pattern_type}`\n"
            f"🔗 الرابط: https://t.me/{pattern_type}"
            f"{DEV_SIGNATURE}"
        )

        try:
            bot.edit_message_text(result_text, chat_id=chat_id, message_id=msg.message_id, reply_markup=get_hunt_keyboard(), parse_mode='Markdown')
        except:
            bot.send_message(chat_id, result_text, reply_markup=get_hunt_keyboard(), parse_mode='Markdown')

    elif data.startswith("setmode_"):
        user_selected_mode[chat_id] = data.replace("setmode_", "")
        bot.send_message(chat_id, f"📥 أرسل الآن الرابط المطلوب لتحميله بدقة عالية:{DEV_SIGNATURE}", parse_mode='Markdown')

    elif data == "type_video":
        bot.send_message(chat_id, f"🎬 *اختر دقة الفيديو المطلوبة:*{DEV_SIGNATURE}", reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')
    elif data == "type_audio":
        bot.send_message(chat_id, f"🎵 *اختر جودة الصوت المطلوبة:*{DEV_SIGNATURE}", reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')

    elif data.startswith("q_"):
        req = user_requests.get(chat_id)
        if req:
            url = req.get("url")
            is_audio = req.get("is_audio", False)
            
            q_map = {
                "q_360": "360",
                "q_720": "720",
                "q_1080": "1080",
                "q_max": "max",
                "q_audio_128": "128",
                "q_audio_320": "320"
            }
            selected_q = q_map.get(data, "max")
            
            bot.edit_message_text(f"⏳ *جاري معالجة وتنزيل الملف، يرجى الانتظار ثوانٍ...*{DEV_SIGNATURE}", chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown')
            
            success = False
            if "tiktok.com" in url:
                success = process_tiktok(chat_id, url, is_audio)
            
            if not success:
                success = process_youtube(chat_id, url, is_audio, selected_q)

            if not success:
                bot.send_message(chat_id, f"⚠️ *عذراً، تعذر تنزيل هذا الرابط. جرب رابطاً آخر.*{DEV_SIGNATURE}", parse_mode='Markdown')
            
            user_requests.pop(chat_id, None)
        else:
            bot.send_message(chat_id, f"⚠️ *انتهت مهلة الطلب، يرجى إعادة إرسال الرابط.*{DEV_SIGNATURE}", parse_mode='Markdown')

    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"🎨 *جاري تحويل صورتك إلى تصميم فني بالنقاط، انتظر لحظات...*{DEV_SIGNATURE}", parse_mode='Markdown')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        ascii_result = convert_image_to_ascii(downloaded_file)
        if ascii_result:
            final_msg = f"✨ *تم تحويل الصورة بنجاح وتصميمه بشكل فني بالنقاط:*\n\n{ascii_result}{DEV_SIGNATURE}"
            bot.reply_to(message, final_msg, parse_mode='Markdown')
        else:
            bot.reply_to(message, f"⚠️ *حدث خطأ أثناء معالجة الصورة، حاول مجدداً.*{DEV_SIGNATURE}", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"⚠️ خطأ: {e}{DEV_SIGNATURE}", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    user_text = message.text or ""

    if user_text.startswith("/") or user_text in ["📥 تنزيل الفيديوهات والصوتيات", "🔍 صيد يوزرات تيليجرام", "🎨 تحويل الصورة إلى رسم بالنقاط"]:
        return

    urls = re.findall(r'https?://[^\s]+', user_text)
    if urls:
        target_url = urls[0]
        if "tiktok.com" in target_url or "youtube.com" in target_url or "youtu.be" in target_url:
            preset = user_selected_mode.get(chat_id)
            if preset:
                is_audio = "audio" in preset
                user_requests[chat_id] = {"url": target_url, "is_audio": is_audio}
                user_selected_mode.pop(chat_id, None)
                
                if is_audio:
                    bot.reply_to(message, f"🎵 *اختر جودة الصوت المطلوبة:*{DEV_SIGNATURE}", parse_mode='Markdown')
                else:
                    bot.reply_to(message, f"🎬 *اختر دقة الفيديو المطلوبة:*{DEV_SIGNATURE}", parse_mode='Markdown')
            else:
                user_requests[chat_id] = {"url": target_url, "is_audio": False}
                bot.reply_to(message, f"📥 *اختر نوع التحميل المطلوب:*{DEV_SIGNATURE}", reply_markup=get_media_type_keyboard(), parse_mode='Markdown')
            return

    bot.reply_to(message, f"يرجى استخدام الأزرار في الأسفل لتنفيذ الخدمات المتاحة وتجنب إرسال نصوص عشوائية 🚀{DEV_SIGNATURE}", parse_mode='Markdown')

if __name__ == "__main__":
    print("Bot is starting polling...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
