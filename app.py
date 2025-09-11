import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Use env vars in production
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"

# API hosts
YOUTUBE_API_HOST = "youtube-mp4-mp3-downloader.p.rapidapi.com"
YOUTUBE_API_URL = f"https://{YOUTUBE_API_HOST}/api/v1/progress"

INSTAGRAM_API_HOST = "instagram-reels-downloader-api.p.rapidapi.com"
INSTAGRAM_API_URL = f"https://{INSTAGRAM_API_HOST}/download"

@app.route("/")
def home():
    return "✅ Flask backend is running on Render!"

@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": ""
    }

    try:
        # YouTube handling
        if "youtube.com" in url or "youtu.be" in url:
            headers["x-rapidapi-host"] = YOUTUBE_API_HOST

            # Extract YouTube video ID
            if "v=" in url:
                video_id = url.split("v=")[-1].split("&")[0]
            else:
                video_id = url.split("/")[-1]

            api_url = YOUTUBE_API_URL
            params = {"id": video_id}

            response = requests.get(api_url, headers=headers, params=params, timeout=30)

        # Instagram handling
        elif "instagram.com" in url:
            headers["x-rapidapi-host"] = INSTAGRAM_API_HOST
            api_url = INSTAGRAM_API_URL
            params = {"url": url}

            response = requests.get(api_url, headers=headers, params=params, timeout=30)

        else:
            return jsonify({"error": "Invalid URL. Only YouTube and Instagram are supported."}), 400

        # Handle API response
        response.raise_for_status()
        data = response.json()

        # Extract a valid download link
        download_link = None
        if "url" in data:
            download_link = data["url"]
        elif "download_url" in data:
            download_link = data["download_url"]
        elif "video_url" in data:
            download_link = data["video_url"]

        if not download_link:
            return jsonify({"error": "No valid download link found in API response.", "api_response": data}), 500

        return jsonify({"download_link": download_link}), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "The API request timed out."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API Error: {str(e)}"}), e.response.status_code
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
