from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    requested_quality = data.get("quality", "720p")

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    try:
        # Download options
        ydl_opts = {
            "format": f"bestvideo[height<={requested_quality}]+bestaudio/best[height<={requested_quality}]",
            "merge_output_format": "mp4",
            "outtmpl": "downloads/%(id)s.%(ext)s"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace(".webm", ".mp4").replace(".m4a", ".mp4")

        return jsonify({
            "title": info.get("title"),
            "id": info.get("id"),
            "download_link": f"/static/{os.path.basename(file_path)}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
