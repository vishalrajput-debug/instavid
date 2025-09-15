from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow all origins, adjust if needed

# Ensure downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    try:
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        output_template = f"downloads/{unique_id}.%(ext)s"

        # yt-dlp options (no cookies.txt, 720p max, mp4 output)
        ydl_opts = {
            "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/mp4",
            "merge_output_format": "mp4",
            "outtmpl": output_template,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info)
            if not final_filename.endswith(".mp4"):
                final_filename = final_filename.rsplit(".", 1)[0] + ".mp4"

        return send_file(final_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "YouTube Downloader API is running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
