from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import io

app = Flask(__name__)
CORS(app)

@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        buffer = io.BytesIO()

        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": "-",
            "noplaylist": True,
            "nocheckcertificate": True,
            "progress_hooks": [lambda d: print(d['status'])],
            "postprocessors": [],
            "quiet": True,
            "prefer_ffmpeg": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get("url")

        # Fetch video bytes directly from URL
        import requests
        r = requests.get(video_url, stream=True)
        for chunk in r.iter_content(chunk_size=8192):
            buffer.write(chunk)

        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{info.get('title', 'video')}.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
