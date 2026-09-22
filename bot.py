import os
import telebot
import requests
import time
import re
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# جلب المفاتيح والرموز من متغيرات البيئة (Environment Variables) بـ Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8708302621:AAFAKBSzXgbq7p5fMimAIJuqqVEcIivTFmw")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBi7s4L2yhv6mCBbvC4f8-bY1Lf-gpanBk")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

BOT_ID = int(TELEGRAM_TOKEN.split(':')[0])

GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-2.5-flash",
    "gemini-1.5-flash"
]

user_requests = {}
user_selected_mode = {}

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

def process_tiktok(chat_id, url, is_audio):
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}&hd=1"
        res = requests.get(api_url, timeout=15).json()
        if res.get("code") == 0:
            data = res.get("data", {})
            if is_audio:
                audio_url = data.get("music")
                if audio_url:
                    bot.send_audio(chat_id, audio_url, caption="🎶 **تيك توك | تم تحميل الصوت بنجاح**\n\n\n\n\n\n*Dev:Yahia*", parse_mode='Markdown')
                    return True
            else:
                video_url = data.get("hdplay") or data.get("play")
                if video_url:
                    bot.send_video(chat_id, video_url, caption="🎬 **تيك توك | تم التحميل بدون علامة مائية**\n\n\n\n\n\n*Dev:Yahia*", parse_mode='Markdown')
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
                        bot.send_audio(chat_id, dl_url, caption="🎵 **تم تحميل الصوت بنجاح**\n\n\n\n\n\n*Dev:Yahia*", parse_mode='Markdown')
                    else:
                        q_title = "أعلى دقة" if quality == "max" else f"{quality}p"
                        bot.send_video(chat_id, dl_url, caption=f"🎬 **تم تحميل الفيديو بدقة ({q_title})**\n\n\n\n\n\n*Dev:Yahia*", parse_mode='Markdown')
                    return True
        except Exception as e:
            print(f"Error on {server}: {e}")
            continue
    return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "أهلاً بك! أنا بوت الذكاء الاصطناعي والأدوات الذكية 🚀\n\n"
        "✨ **الخدمات المتاحة:**\n"
        "• تنزيل مقاطع تيك توك ويوتيوب مع إمكانية **اختيار الدقة**.\n"
        "• تحويل المقاطع إلى أغانٍ بصيغة MP3.\n\n"
        "💡 اكتب **(مزايا اخرى)** للتحكم بالأزرار، أو أرسل أي رابط مباشرةً!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text and "مزايا اخرى" in message.text.lower())
def show_extra_features(message):
    bot.reply_to(
        message, 
        "🛠 **قائمة المزايا والأدوات الإضافية:**\nاختر الخدمة المطلوبة ثم أرسل الرابط:", 
        reply_markup=get_features_keyboard(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("setmode_"):
        user_selected_mode[chat_id] = data.replace("setmode_", "")
        bot.send_message(chat_id, "📥 أرسل الآن الرابط للمتابعة وتحديد الدقة المطلوبة:")

    elif data == "type_video":
        bot.send_message(chat_id, "🎬 **اختر دقة الفيديو المطلوبة:**", reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')
    elif data == "type_audio":
        bot.send_message(chat_id, "🎵 **اختر جودة الصوت المطلوبة:**", reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')

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
            
            bot.edit_message_text("⏳ جاري تنزيل المقطع، يرجى الانتظار ثوانٍ...", chat_id=chat_id, message_id=call.message.message_id)
            
            success = False
            if "tiktok.com" in url:
                success = process_tiktok(chat_id, url, is_audio)
            
            if not success:
                success = process_youtube(chat_id, url, is_audio, selected_q)

            if not success:
                bot.send_message(chat_id, "⚠️ تعذر تنزيل هذا المقطع تحديداً. حاول تجربة رابط آخر أو دقة أقل.")
            
            user_requests.pop(chat_id, None)
        else:
            bot.send_message(chat_id, "⚠️ انتهت مهلة الطلب، يرجى إعادة إرسال الرابط.")

    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id

    if message.chat.type in ['group', 'supergroup']:
        if not message.reply_to_message or message.reply_to_message.from_user.id != BOT_ID:
            return

    user_text = message.text or ""
    if not user_text:
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
                    bot.reply_to(message, "🎵 **اختر جودة الصوت المطلوبة:**", reply_markup=get_audio_quality_keyboard(), parse_mode='Markdown')
                else:
                    bot.reply_to(message, "🎬 **اختر دقة الفيديو المطلوبة:**", reply_markup=get_video_quality_keyboard(), parse_mode='Markdown')
            else:
                user_requests[chat_id] = {"url": target_url, "is_audio": False}
                bot.reply_to(message, "📥 **اختر نوع التحميل المطلوب:**", reply_markup=get_media_type_keyboard(), parse_mode='Markdown')
            return

    bot.send_chat_action(chat_id, 'typing')
    
    system_instruction = (
        "أنت مساعد ذكاء اصطناعي محترف، حيادي، ومنطقي للغاية.\n"
        "تلتزم بالقواعد التالية بدقة شديدة:\n"
        "1. الإيجاز الشديد: أجب عن السؤال المطلوب فقط دون أي مقدمات أو خاتمة أو كلام زائد.\n"
        "2. منع الاقتراحات: لا تقترح أسئلة أخرى أو خيارات متابعة إطلاقاً بعد إجابتك.\n"
        "3. المنطقية والتجرد العاطفي: حلل المشاكل ووفّر الحلول بمنطقية وعدل وحياد تام وبدون أي عاطفة أو تعاطف.\n"
        "4. تعدد اللغات: أجب بنفس اللغة التي كتب بها المستخدم (عربي، إنجليزي، روسي، إلخ).\n"
        "5. التنسيق: رتب الإجابة بأسلوب جميل باستخدام Markdown والنقاط أو الجداول إن دعت الحاجة."
    )

    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": user_text}]}],
            "system_instruction": {"parts": [{"text": system_instruction}]}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    ai_reply = data["candidates"][0]["content"]["parts"][0]["text"]
                    formatted_reply = ai_reply + "\n\n\n\n\n\n*Dev:Yahia*"
                    
                    try:
                        bot.reply_to(message, formatted_reply, parse_mode='Markdown')
                    except Exception:
                        bot.reply_to(message, ai_reply + "\n\n\n\n\n\nDev:Yahia")
                    return
            elif response.status_code == 429:
                continue
        except Exception:
            continue

    bot.reply_to(message, "⚠️ السيرفر عليه ضغط حالياً، جرب إعادة الرسالة بعد ثوانٍ.")

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing update: {e}")
    return "!", 200

@app.route("/")
def webhook():
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}"
    else:
        webhook_url = f"https://{request.host}/{TELEGRAM_TOKEN}"
        
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=webhook_url)
        return f"تم تفعيل الـ Webhook بنجاح على Render: {webhook_url}", 200
    except Exception as e:
        return f"حدث خطأ: {e}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
