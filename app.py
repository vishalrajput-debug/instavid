from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)  # allow all origins

# ------------------ RapidAPI Config ------------------
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"
RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"

# ------------------ Helper Function ------------------


def extract_video_id(url):
    """
    Extract YouTube video ID from any URL
    """
    # Shorts URL: youtube.com/shorts/VIDEO_ID
    short_match = re.search(r'shorts/([^\?&]+)', url)
    if short_match:
        return short_match.group(1), "short"

    # Short youtu.be URL
    short_youtu = re.search(r'youtu\.be/([^\?&]+)', url)
    if short_youtu:
        return short_youtu.group(1), "video"

    # Standard URL: youtube.com/watch?v=VIDEO_ID
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
        quality = data.get("quality")
        download_type = data.get("type")
    else:
        url = request.args.get("url")
        quality = request.args.get("quality")
        download_type = request.args.get("type")

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    video_id, video_type = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # Default quality values
    quality = "18"

    # Determine endpoint
    if video_type == "short":
        endpoint = f"/download_short/{video_id}?quality={quality}"
    else:
        endpoint = f"/download_video/{video_id}?quality={quality}"

    rapidapi_url = f"https://{RAPIDAPI_HOST}{endpoint}"
    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": RAPIDAPI_HOST
    }

    try:
        response = requests.get(rapidapi_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "file" in data:
            data["download_link"] = data["file"]
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch from RapidAPI", "details": str(e)}), 500
    except Exception:
        return jsonify({"error": "Invalid JSON response from RapidAPI"}), 500

# ------------------ Run App ------------------
if __name__ == "__main__":
    app.run(debug=True)
