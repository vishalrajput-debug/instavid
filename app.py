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

# YouTube API Details
YOUTUBE_RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"
YOUTUBE_API_URL = f"https://{YOUTUBE_RAPIDAPI_HOST}"

# Instagram API Details (from the provided screenshot)
INSTAGRAM_RAPIDAPI_HOST = "instagram-downloader-download-instagram-stories-videos4.p.rapidapi.com"
INSTAGRAM_API_URL = f"https://{INSTAGRAM_RAPIDAPI_HOST}"


def extract_video_id(url):
    """Extract YouTube video ID from any URL"""
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
    """Check if the URL is from YouTube."""
    return "youtube.com" in url or "youtu.be" in url

def is_instagram_url(url):
    """Check if the URL is from Instagram."""
    return "instagram.com" in url

@app.route("/download", methods=["POST", "GET"])
def download():
    """Unified endpoint to download videos from YouTube and Instagram."""
    
    # Check the request method and get data accordingly
    if request.method == "POST":
        data = request.get_json()
    else:  # Assumes GET request
        data = request.args

    url = data.get("url")
    requested_quality = data.get("quality")

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    # -----------------
    # Logic for YouTube
    # -----------------
    if is_youtube_url(url):
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400

        headers = {
            "X-Rapidapi-Key": RAPIDAPI_KEY,
            "X-Rapidapi-Host": YOUTUBE_RAPIDAPI_HOST
        }

        try:
            # Step 1: Get available qualities
            q_res = requests.get(f"{YOUTUBE_API_URL}/get_available_quality/{video_id}", headers=headers, timeout=20)
            q_res.raise_for_status()
            qualities = q_res.json()

            if not qualities:
                return jsonify({"error": "No qualities found"}), 404

            # Filter only video types
            video_qualities = [q for q in qualities if q.get("type") == "video"]
            if not video_qualities:
                return jsonify({"error": "No video formats available"}), 404

            # Step 2: Choose quality
            chosen_quality = None
            if requested_quality and requested_quality != "best":
                for q in video_qualities:
                    if q.get("quality") == requested_quality:
                        chosen_quality = q["quality"]
                        break
            if not chosen_quality:
                chosen_quality = video_qualities[0]["quality"]

            # Step 3: Fetch download link
            d_res = requests.get(f"{YOUTUBE_API_URL}/download_video/{video_id}?quality={chosen_quality}", headers=headers, timeout=30)
            d_res.raise_for_status()
            dl_data = d_res.json()

            if "file" not in dl_data:
                return jsonify({"error": "Download link not found"}), 404

            dl_data["download_link"] = dl_data["file"]
            return jsonify(dl_data)

        except requests.exceptions.RequestException as e:
            return jsonify({"error": "Failed to fetch YouTube video", "details": str(e)}), 500

    # -----------------
    # Logic for Instagram
    # -----------------
    elif is_instagram_url(url):
        headers = {
            "X-Rapidapi-Key": RAPIDAPI_KEY,
            "X-Rapidapi-Host": INSTAGRAM_RAPIDAPI_HOST
        }
        
        # NOTE: Instagram API uses a GET request with query parameters.
        params = {
            "downloadUrl": url
        }

        try:
            response = requests.get(f"{INSTAGRAM_API_URL}/downloadReel", headers=headers, params=params, timeout=20)
            response.raise_for_status()
            reel_data = response.json()

            if not reel_data.get("url"):
                return jsonify({"error": "Failed to get Instagram download link"}), 404

            download_url = reel_data["url"]
            return jsonify({"download_link": download_url, "title": reel_data.get("title", "Instagram Reel")})

        except requests.exceptions.RequestException as e:
            return jsonify({"error": "Failed to fetch Instagram Reel", "details": str(e)}), 500

    else:
        return jsonify({"error": "Unsupported URL format. Please provide a YouTube or Instagram URL."}), 400

if __name__ == "__main__":
    app.run(debug=True)