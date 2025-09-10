from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import yt_dlp
import requests
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

INSTAGRAM_API_KEY = os.getenv("INSTAGRAM_API_KEY")
INSTAGRAM_API_HOST = os.getenv("INSTAGRAM_API_HOST")
INSTAGRAM_API_URL = os.getenv("INSTAGRAM_API_URL")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_HOST = os.getenv("YOUTUBE_API_HOST")
YOUTUBE_API_URL = os.getenv("YOUTUBE_API_URL")

app = Flask(__name__)
CORS(app, origins=["https://instaviddownload.com"])  # allow your frontend domain


def download_youtube(url):
    """Try yt_dlp first, fallback to RapidAPI"""
    try:
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

        return {"status": "ok", "video_url": video_url, "title": title}

    except Exception:
        # fallback to RapidAPI YouTube API
        headers = {
            "x-rapidapi-key": YOUTUBE_API_KEY,
            "x-rapidapi-host": YOUTUBE_API_HOST
        }
        querystring = {"url": url}
        resp = requests.get(YOUTUBE_API_URL, headers=headers, params=querystring)

        if resp.status_code != 200:
            raise Exception("YouTube RapidAPI request failed")

        data = resp.json()
        video_url = data.get("link") or data.get("url")
        title = data.get("title", "youtube_video")

        if not video_url:
            raise Exception("No video found in YouTube API response")

        return {"status": "ok", "video_url": video_url, "title": title}


def download_instagram(url):
    headers = {
        "x-rapidapi-key": INSTAGRAM_API_KEY,
        "x-rapidapi-host": INSTAGRAM_API_HOST
    }
    querystring = {"url": url}
    resp = requests.get(INSTAGRAM_API_URL, headers=headers, params=querystring)

    if resp.status_code != 200:
        raise Exception("Instagram RapidAPI request failed")

    data = resp.json()
    # Some APIs return "links" list, others return "download_url"
    video_url = None
    if "links" in data:
        video_url = data.get("links", [{}])[0].get("url")
    elif "download_url" in data:
        video_url = data.get("download_url")

    if not video_url:
        raise Exception("No video found in Instagram API response")

    return {"status": "ok", "video_url": video_url, "title": "instagram_video"}


@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        if "youtube.com" in url or "youtu.be" in url:
            result = download_youtube(url)
        elif "instagram.com" in url:
            result = download_instagram(url)
        else:
            return jsonify({"error": "Unsupported URL"}), 400

        # Stream video directly
        def generate():
            with requests.get(result["video_url"], stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

        headers = {
            "Content-Disposition": f'attachment; filename="{result["title"]}.mp4"'
        }

        return Response(generate(), headers=headers, mimetype="video/mp4")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
