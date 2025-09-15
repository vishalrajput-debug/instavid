from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import re
import os

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)

# ------------------ Helper Function ------------------

def extract_video_id(url):
    """
    Extract YouTube video ID from any URL
    """
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

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    video_id, video_type = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # ---------------- yt-dlp Options ----------------
    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
"merge_output_format": "mp4",
        "outtmpl": f"downloads/{video_id}.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp4")

        return jsonify({
            "title": info.get("title"),
            "id": info.get("id"),
            "download_link": f"/{filename}"
        })

    except Exception as e:
        return jsonify({"error": "Download failed", "details": str(e)}), 500

# ------------------ Run App ------------------

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    app.run(debug=True)
