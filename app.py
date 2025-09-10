from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app, origins=["https://instaviddownload.com"])  # allow your frontend domain

@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Use yt_dlp to get direct video URL
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get("url")
            title = info.get("title", "video")

        # Stream video directly from YouTube
        def generate():
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

        headers = {
            "Content-Disposition": f'attachment; filename="{title}.mp4"'
        }

        return Response(generate(), headers=headers, mimetype="video/mp4")

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": "Cannot download this video. It may require login or be restricted."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
