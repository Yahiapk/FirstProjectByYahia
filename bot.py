import os
import telebot
import requests
import re
import random
import string
import time
import threading
from PIL import Image
from io import BytesIO
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TELEGRAM_TOKEN = "8708302621:AAFAKBSzXgbq7p5fMimAIJuqqVEcIivTFmw"
ADMIN_ID = 1283009799

# زيادة عدد الألياف (Threads) لضمان السرعة المطلقة
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True, num_threads=20)
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
        InlineKeyboardButton("🎯 صيد صيغة: x1_x1", callback_data="hunt_type_1"),
        InlineKeyboardButton("🎯 صيد صيغة: x1_1x", callback_data="hunt_type_2"),
        InlineKeyboardButton("🎯 صيد صيغة: xx_11", callback_data="hunt_type_3")
    )
    return markup

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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=2.0)
        if res.status_code == 200:
            text = res.text
            if "tgme_page_extra" not in text and "Preview channel" not in text and "Send Message" not in text:
                return True
    except:
        pass
    return False

def hunt_username_thread(chat_id, message_id, htype):
    found_username = None
    attempts = 0
    start_time = time.time()
    last_edit_time = 0
    
    while True:
        attempts += 1
        test_user = generate_target_username(htype)
        current_time = time.time()
        
        if current_time - last_edit_time > 3.0:
            matrix_code = generate_random_matrix()
            anim_text = (
                f"⚡ *جاري الصيد والتحقق الحقيقي...*\n\n"
                f"🟢 `{matrix_code}`\n"
                f"🔍 فحص اليوزر: `@{test_user}`\n"
                f"📊 المحاولات: `{attempts}`"
                f"{DEV_SIGNATURE}"
            )
            try:
                bot.edit_message_text(anim_text, chat_id=chat_id, message_id=message_id, parse_mode='Markdown')
                last_edit_time = time.time()
            except:
                pass

        if check_telegram_username_real(test_user):
            found_username = test_user
            break
            
        time.sleep(0.01)

    elapsed_time = round(time.time() - start_time, 2)
    final_matrix = generate_random_matrix()
    result_text = (
        f"🎉 *تم صيد يوزر متاح حقيقي 100%!* ✨\n\n"
        f"🟢 `{final_matrix}`\n"
        f"📌 اليوزر المتاح: `@{found_username}`\n"
        f"⏱ المستغرق: `{elapsed_time}` ثانية\n"
        f"📊 المحاولات: `{attempts}`\n"
        f"🔗 الرابط المباشر: https://t.me/{found_username}"
        f"{DEV_SIGNATURE}"
    )
    try:
        bot.edit_message_text(result_text, chat_id=chat_id, message_id=message_id, reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')
    except:
        bot.send_message(chat_id, result_text, reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')

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
        res = requests.post("https://co.wuk.sh/api/json", json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=15)
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
            res = requests.post(server, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=15)
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
        joined_lines = "\n".join(ascii_lines)
        return "```\n" + joined_lines + "\n```"
    except:
        return None

# المعالجة المستقلة للـ Callback لحل مشكلة التأخير
def process_callback_async(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("hunt_type_"):
        htype = data.split("_")[-1]
        hunt_username_thread(chat_id, call.message.message_id, htype)

    elif data.startswith("setmode_"):
        mode = data.replace("setmode_", "")
        user_selected_mode[chat_id] = mode
        try:
            bot.send_message(chat_id, f"📥 أرسل الآن الرابط المطلوب للتحميل الفوري:{DEV_SIGNATURE}", parse_mode='Markdown')
        except:
            pass

    elif data == "type_video":
        try:
            bot.edit_message_text(f"🎬 *اختر دقة الفيديو:*{DEV_SIGNATURE}", chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')
        except:
            pass
            
    elif data == "type_audio":
        try:
            bot.edit_message_text(f"🎵 *اختر جودة الصوت:*{DEV_SIGNATURE}", chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')
        except:
            pass

    elif data.startswith("q_"):
        req = user_requests.get(chat_id)
        if req:
            url, is_audio = req.get("url"), req.get("is_audio", False)
            q_map = {"q_360": "360", "q_720": "720", "q_1080": "1080", "q_max": "max", "q_audio_128": "128", "q_audio_320": "320"}
            selected_q = q_map.get(data, "max")
            
            try:
                bot.edit_message_text(f"⏳ *جاري التحميل ومعالجة الرابط...*{DEV_SIGNATURE}", chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown')
            except:
                pass
            
            success = False
            if "instagram.com" in url:
                success = process_instagram(chat_id, url, is_audio)
            elif "tiktok.com" in url:
                success = process_tiktok(chat_id, url, is_audio)
            else:
                success = process_youtube(chat_id, url, is_audio, selected_q)

            if not success:
                try:
                    bot.send_message(chat_id, f"⚠️ *تعذر التحميل، تأكد من صحة الرابط.*{DEV_SIGNATURE}", parse_mode='Markdown')
                except:
                    pass
            user_requests.pop(chat_id, None)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    # إجابة فورية وحاسمة تلغي الـ Loading بنفس اللحظة
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    # تشغيل منطق العملية بخيط فرعي مستقل تماماً
    threading.Thread(target=process_callback_async, args=(call,)).start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(message, f"🌟 *أهلاً بك يا غالي في بوت الخدمات الصاروخي* 🚀\n\nاختر الخدمة المطلوبة من الأزرار بالأسفل:{DEV_SIGNATURE}", reply_markup=get_main_menu(), parse_mode='Markdown')
    except:
        pass

@bot.message_handler(func=lambda message: message.text == "📥 تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا)")
def menu_download(message):
    bot.reply_to(message, f"📥 *أرسل رابط تيك توك، يوتيوب، أو انستغرام مباشرة، أو اختر الخدمة:*{DEV_SIGNATURE}", reply_markup=get_features_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🔍 صيد يوزرات تيليجرام الحقيقي (صاروخي)")
def menu_hunt(message):
    bot.reply_to(message, f"🔍 *اختر صيغة الصيد والتحقق الحقيقي السريع من سيرفرات تيليجرام:*{DEV_SIGNATURE}", reply_markup=get_hunt_types_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "✨ زخرفة الأسماء الاحترافية")
def menu_decorate(message):
    user_state[message.chat.id] = "waiting_name"
    bot.reply_to(message, f"✨ *أرسل الآن الاسم أو الكلمة التي تريد زخرفتها (عربي أو إنجليزي):*{DEV_SIGNATURE}", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🎨 تحويل الصورة إلى رسم بالنقاط")
def menu_ascii(message):
    user_state[message.chat.id] = "ascii"
    bot.reply_to(message, f"🎨 *أرسل أي صورة الآن لتحويلها إلى رسم فني بالنقاط:*{DEV_SIGNATURE}", reply_markup=get_main_menu(), parse_mode='Markdown')

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    try:
        bot.send_message(chat_id, f"🎨 *جاري تحويل الصورة إلى رسم بالنقاط...*{DEV_SIGNATURE}", parse_mode='Markdown')
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

    if text.startswith("/") or text in ["📥 تنزيل الفيديوهات والصوتيات (يوتيوب، تيكتوك، انستا)", "🔍 صيد يوزرات تيليجرام الحقيقي (صاروخي)", "✨ زخرفة الأسماء الاحترافية", "🎨 تحويل الصورة إلى رسم بالنقاط"]:
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
        try:
            bot.reply_to(message, final_response, parse_mode='Markdown')
        except:
            pass
        return

    urls = re.findall(r'https?://[^\s]+', text)
    if urls:
        target_url = urls[0]
        if "instagram.com" in target_url:
            preset = user_selected_mode.get(chat_id)
            is_audio = preset == "insta_audio"
            user_selected_mode.pop(chat_id, None)
            try:
                bot.reply_to(message, f"⏳ *جاري جلب المحتوى من انستغرام...*{DEV_SIGNATURE}", parse_mode='Markdown')
            except:
                pass
            threading.Thread(target=process_instagram, args=(chat_id, target_url, is_audio)).start()
            return
        elif "tiktok.com" in target_url or "youtube.com" in target_url or "youtu.be" in target_url:
            preset = user_selected_mode.get(chat_id)
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

    try:
        bot.reply_to(message, f"يرجى استخدام الأزرار بالأسفل لتنفيذ الخدمات المتاحة 🚀{DEV_SIGNATURE}", parse_mode='Markdown')
    except:
        pass

if __name__ == "__main__":
    while True:
        try:
            print("Bot is running seamlessly...")
            bot.remove_webhook()
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            time.sleep(2)
