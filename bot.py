import os
import time
import random
import asyncio
import aiohttp
import requests
from io import BytesIO
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

RAPIDAPI_KEY = "0276121538msh1cbbbeec1cc1582p11753ajsn0b6bf3fabb83"
REMOVEBG_KEY = "842be2PAHbH3Aev5aHhDU9KR"
GEMINI_API_KEY = "AIzaSyBi7s4L2yhv6mCBbvC4f8-bY1Lf-gpanBk"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
alphanumeric = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def generate_5char_username():
    c1 = random.choice(letters)
    c2 = random.choice(alphanumeric)
    c3 = random.choice(alphanumeric)
    c4 = random.choice(alphanumeric)
    c5 = random.choice(alphanumeric)
    return random.choice([
        f"{c1}{c2}_{c3}{c4}",
        f"{c1}_{c2}{c3}{c4}",
        f"{c1}{c2}{c3}_{c4}",
        f"{c1}{c2}{c3}{c4}{c5}"
    ])

async def hunt_usernames_async(count):
    found_users = []
    checked = 0
    max_attempts = count * 400
    sem = asyncio.Semaphore(35)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async def worker():
            nonlocal checked
            while len(found_users) < count and checked < max_attempts:
                u = generate_5char_username()
                if u in found_users:
                    continue
                checked += 1
                async with sem:
                    try:
                        async with session.get(f"https://fragment.com/username/{u}", timeout=4) as r1:
                            if r1.status == 200:
                                t1 = (await r1.text()).lower()
                                if "unavailable" in t1 or "not found" in t1:
                                    async with session.get(f"https://t.me/{u}", timeout=4) as r2:
                                        if r2.status == 200 and "tgme_page_title" not in await r2.text():
                                            if u not in found_users and len(found_users) < count:
                                                found_users.append(u)
                    except:
                        pass

        await asyncio.gather(*[worker() for _ in range(35)])
    return found_users

@app.route("/api/hunt", methods=["GET"])
def api_hunt():
    count = int(request.args.get("count", 5))
    count = min(max(count, 1), 100)
    users = asyncio.run(hunt_usernames_async(count))
    return jsonify({"ok": True, "users": users})

@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.json or {}
    url = data.get("url", "").strip()
    is_audio = bool(data.get("is_audio", False))
    quality = data.get("quality", "best")

    if not url:
        return jsonify({"ok": False, "error": "الرابط فارغ"}), 400

    uid = f"yf_{int(time.time())}_{random.randint(1000,9999)}"
    out_template = os.path.join(DOWNLOAD_DIR, f"{uid}.%(ext)s")

    if is_audio:
        ydl_opts = {
            "outtmpl": out_template,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        fmt = "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"
        if quality == "360":
            fmt = "best[height<=360][ext=mp4]/best[height<=360]/best"
        elif quality == "720":
            fmt = "best[height<=720][ext=mp4]/best[height<=720]/best"
        ydl_opts = {
            "outtmpl": out_template,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "format": fmt,
            "merge_output_format": "mp4",
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info and len(info["entries"]) > 0:
                info = info["entries"][0]
            title = info.get("title", "YahiaFadhelTools_Media")
            actual = ydl.prepare_filename(info)
            base = os.path.splitext(actual)[0]
            final_file = None
            for ext in [".mp3", ".mp4", ".m4a", ".mkv", ".webm"]:
                if os.path.exists(base + ext):
                    final_file = base + ext
                    break
            if not final_file and os.path.exists(actual):
                final_file = actual

            if final_file and os.path.exists(final_file):
                fname = os.path.basename(final_file)
                return jsonify({
                    "ok": True,
                    "title": title,
                    "filename": fname,
                    "is_audio": is_audio,
                    "file_url": f"/files/{fname}"
                })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({"ok": False, "error": "تعذر استخراج الملف"}), 500

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Not found", 404

@app.route("/api/prayer", methods=["GET"])
def api_prayer():
    city = request.args.get("city", "Baghdad")
    try:
        r = requests.get(f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Iraq&method=0", timeout=10)
        js = r.json()
        if js.get("code") == 200:
            return jsonify({"ok": True, "timings": js["data"]["timings"]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": False, "error": "فشل جلب المواقيت"}), 500

@app.route("/api/song", methods=["POST"])
def api_song():
    query = (request.json or {}).get("query", "").strip()
    if not query:
        return jsonify({"ok": False, "error": "اكتب وصف أو مقطع الأغنية"}), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True}) as ydl:
            res = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = res.get("entries", [])
            if entries:
                top = entries[0]
                return jsonify({
                    "ok": True,
                    "result": f"اسم الأغنية: {top.get('title')}\nالقناة / الفنان: {top.get('uploader')}\nالرابط: {top.get('webpage_url')}"
                })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": False, "error": "لم يتم العثور على الأغنية"}), 404

@app.route("/api/removebg", methods=["POST"])
def api_removebg():
    if "image" not in request.files:
        return jsonify({"ok": False, "error": "لم يتم إرسال صورة"}), 400
    img_bytes = request.files["image"].read()
    try:
        r = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": img_bytes},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVEBG_KEY},
            timeout=25
        )
        if r.status_code == 200:
            return send_file(BytesIO(r.content), mimetype="image/png", as_attachment=True, download_name="nobg.png")
        return jsonify({"ok": False, "error": f"Remove.bg error: {r.status_code}"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
