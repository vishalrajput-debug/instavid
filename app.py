from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)  # allow all origins

# ------------------ RapidAPI Config ------------------
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"

# YouTube API
YOUTUBE_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"

# Instagram API
INSTAGRAM_HOST = "instagram-downloader-scraper-reels-igtv-posts-stories.p.rapidapi.com"

# ------------------ Helper Function ------------------

def extract_video_id(url):
    """Extract YouTube video ID from any URL"""
    short_match = re.search(r'shorts/([^\?&]+)', url)
    if short_match:
        return short_match.group(1), "short"

    short_youtu = re.search(r'youtu\.be/([^\?&]+)', url)
    if short_youtu:
        return short_youtu.group(1), "video"

    long_match = re.search(r'v=([^\?&]+)', url)
    if long_match:
        return long_match.group(1), "video"

    return None, None

# ------------------ Main Download Endpoint ------------------

@app.route("/download", methods=["GET", "POST"])
def download():
    # Handle both POST (JSON) and GET (query params)
    if request.method == "POST":
        data = request.get_json()
        url = data.get("url")
    else:
        url = request.args.get("url")

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    # Auto-detect platform
    if "youtube.com" in url or "youtu.be" in url:
        platform = "youtube"
    elif "instagram.com" in url:
        platform = "instagram"
    else:
        return jsonify({"error": "Unsupported URL"}), 400

    # ------------------ YouTube Handling ------------------
    if platform == "youtube":
        video_id, video_type = extract_video_id(url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400

        quality = "22"  # default 720p
        if video_type == "short":
            endpoint = f"/download_short/{video_id}?quality={quality}"
        else:
            endpoint = f"/download_video/{video_id}?quality={quality}"

        rapidapi_url = f"https://{YOUTUBE_HOST}{endpoint}"
        headers = {
            "X-Rapidapi-Key": RAPIDAPI_KEY,
            "X-Rapidapi-Host": YOUTUBE_HOST
        }

    # ------------------ Instagram Handling ------------------
    elif platform == "instagram":
        rapidapi_url = f"https://{INSTAGRAM_HOST}/?url={url}"
        headers = {
            "X-Rapidapi-Key": RAPIDAPI_KEY,
            "X-Rapidapi-Host": INSTAGRAM_HOST
        }

    # ------------------ API Request ------------------
    try:
        response = requests.get(rapidapi_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Normalize response
        if platform == "youtube" and "file" in data:
            data["download_link"] = data["file"]

        if platform == "instagram":
            # Different APIs may return different keys
            if "media" in data:
                data["download_link"] = data["media"]
            elif "result" in data:
                data["download_link"] = data["result"]
            elif "url" in data:
                data["download_link"] = data["url"]

        return jsonify(data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch from RapidAPI", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Invalid JSON response from RapidAPI", "details": str(e)}), 500

# ------------------ Run App ------------------
if __name__ == "__main__":
    app.run(debug=True)
