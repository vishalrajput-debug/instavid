from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)

RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"
RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"


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


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    requested_quality = data.get("quality")  # from frontend

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": RAPIDAPI_HOST
    }

    try:
        # Step 1: Get available qualities
        q_res = requests.get(f"https://{RAPIDAPI_HOST}/get_available_quality/{video_id}", headers=headers, timeout=20)
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
            # Try exact match first
            for q in video_qualities:
                if q.get("quality") == requested_quality:
                    chosen_quality = q["quality"]
                    break
        # If 'best' or exact match not found, pick highest quality
        if not chosen_quality:
            chosen_quality = video_qualities[0]["quality"]

        # Step 3: Fetch download link
        d_res = requests.get(f"https://{RAPIDAPI_HOST}/download_video/{video_id}?quality={chosen_quality}", headers=headers, timeout=30)
        d_res.raise_for_status()
        dl_data = d_res.json()

        if "file" not in dl_data:
            return jsonify({"error": "Download link not found"}), 404

        dl_data["download_link"] = dl_data["file"]
        return jsonify(dl_data)

    except Exception as e:
        return jsonify({"error": "Failed to fetch video", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
