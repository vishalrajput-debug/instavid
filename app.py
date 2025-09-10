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

    buffer = io.BytesIO()

    # yt-dlp options
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": "-",  # '-' means write to stdout
        "noplaylist": True,
        "quiet": True,
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download video into memory
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get("title", "video")

        # yt-dlp writes directly to stdout; here we simulate with a temp file
        # Since we can't truly stream to BytesIO without custom extractor,
        # simpler approach: download to temp file and then serve it
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts["outtmpl"] = f"{tmpdir}/%(title)s.%(ext)s"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info_dict)

            return send_file(
                downloaded_file,
                as_attachment=True,
                download_name=f"{video_title}.mp4",
                mimetype="video/mp4"
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
