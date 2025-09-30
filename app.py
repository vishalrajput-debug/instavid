from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)

# -----------------
# API Credentials
# -----------------
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"

YOUTUBE_RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"
YOUTUBE_API_URL = f"https://{YOUTUBE_RAPIDAPI_HOST}"

INSTAGRAM_RAPIDAPI_HOST = "instagram-reels-stories-downloader-api.p.rapidapi.com"
INSTAGRAM_API_URL = f"https://{INSTAGRAM_RAPIDAPI_HOST}"

def extract_video_id(url):
    short_match = re.search(r'shorts/([^\?&]+)', url)
    if short_match:
        return short_match.group(1)

    short_youtu = re.search(r'youtu\.be/([^\?&]+)', url)
    if short_youtu:
        return short_youtu.group(1)

    long_match = re.search(r'v=([^\?&]+)', url)
    if long_match:
        return long_match.group(1)

    return None

def is_youtube_url(url):
    return "youtube.com" in url or "youtu.be" in url

def is_instagram_url(url):
    return "instagram.com" in url

# ✅ YOUTUBE ENDPOINT (UNCHANGED)
@app.route("/download", methods=["POST", "GET"])
def download_youtube():
    data = request.get_json() if request.method == "POST" else request.args
    url = data.get("url")
    requested_quality = data.get("quality")

    if not url or not is_youtube_url(url):
        return jsonify({"error": "Please provide a valid YouTube URL"}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": YOUTUBE_RAPIDAPI_HOST
    }

    try:
        q_res = requests.get(f"{YOUTUBE_API_URL}/get_available_quality/{video_id}", headers=headers, timeout=20)
        q_res.raise_for_status()
        qualities = q_res.json()
        video_qualities = [q for q in qualities if q.get("type") == "video"]

        chosen_quality = next((q["quality"] for q in video_qualities if q["quality"] == requested_quality), video_qualities[0]["quality"])

        d_res = requests.get(f"{YOUTUBE_API_URL}/download_video/{video_id}?quality={chosen_quality}", headers=headers, timeout=30)
        d_res.raise_for_status()
        dl_data = d_res.json()

        if "file" not in dl_data:
            return jsonify({"error": "Download link not found"}), 404

        return jsonify({"download_link": dl_data["file"]})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch YouTube video", "details": str(e)}), 500

# ✅ INSTAGRAM ENDPOINT (NOW SEPARATE)
@app.route("/convert", methods=["GET", "POST"])
def convert_instagram():
    data = request.get_json() if request.method == "POST" else request.args
    url = data.get("url")

    if not url or not is_instagram_url(url):
        return jsonify({"error": "Please provide a valid Instagram URL"}), 400

    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": INSTAGRAM_RAPIDAPI_HOST
    }

    try:
        response = requests.get(f"{INSTAGRAM_API_URL}/convert", headers=headers, params={"url": url}, timeout=20)
        response.raise_for_status()
        data = response.json()

        download_url = data.get("url")
        if not download_url:
            return jsonify({"error": "Failed to get Instagram download link", "response": data}), 404

        return jsonify({"download_link": download_url})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to Instagram API", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
