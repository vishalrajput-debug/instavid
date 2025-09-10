from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app)  # Allow all origins for now

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return "✅ Flask backend is running on Render!"

@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Create a temporary file path
        temp_filepath = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4()}")
        
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": f"{temp_filepath}.%(ext)s",  # Use a template to include the original extension
            "noplaylist": True,
            "nocheckcertificate": True,
            "progress_hooks": [lambda d: print(d['status'])] # Add a progress hook for debugging
        }

        # Use a list to store the filename extracted by yt-dlp
        filename_storage = []

        def get_filename_hook(d):
            if d['status'] == 'finished':
                # Store the actual file path after the download is complete
                filename_storage.append(d['filename'])

        ydl_opts['progress_hooks'].append(get_filename_hook)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Get the actual filename after the download
        if not filename_storage:
            return jsonify({"error": "yt-dlp failed to download the video."}), 500

        filepath = filename_storage[0]
        # Extract the original filename from the full path
        original_filename = os.path.basename(filepath)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=original_filename # Pass the filename to the user's browser
        )

    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)