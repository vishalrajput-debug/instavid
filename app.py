from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pytube import YouTube
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/download", methods=["POST"])
def download_video():
    try:
        data = request.get_json()
        video_url = data.get("url")

        if not video_url:
            return jsonify({"error": "No URL provided"}), 400

        # Initialize YouTube object
        yt = YouTube(video_url)

        # Get highest resolution stream
        stream = yt.streams.get_highest_resolution()

        # Create safe filename
        filename = "".join(c for c in yt.title if c.isalnum() or c in (" ", "_", "-")).rstrip() + ".mp4"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        # Download video
        stream.download(output_path=DOWNLOAD_FOLDER, filename=filename)

        return send_file(filepath, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "YouTube Downloader API running with pytube"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
