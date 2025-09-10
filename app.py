from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import tempfile

app = Flask(__name__)

# Path to your cookies file (add cookies.txt to your repo)
YOUTUBE_COOKIES = "cookies.txt"

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_path,
    }

    # Use cookies only for YouTube URLs
    if "youtube.com" in url or "youtu.be" in url:
        ydl_opts["cookies"] = YOUTUBE_COOKIES

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return jsonify({"error": "Download failed"}), 500

@app.route("/")
def index():
    return "Server is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
