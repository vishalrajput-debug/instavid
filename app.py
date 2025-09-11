import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load API key (use env var in production)
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238")

YOUTUBE_API_HOST = "youtube-video-and-shorts-downloader.p.rapidapi.com"

@app.route("/")
def home():
    return "✅ Flask backend with RapidAPI is running!"

@app.route("/download", methods=["POST"])
def download_video():
    url = None

    # Handle both JSON and form-urlencoded
    if request.is_json:
        data = request.get_json()
        url = data.get("url")
    else:
        url = request.form.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": YOUTUBE_API_HOST
    }

    try:
        # API endpoint: Resolve URL → Get download links
        api_url = f"https://{YOUTUBE_API_HOST}/resolveUrl.php"
        params = {"url": url}
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract download link
        download_link = None
        if isinstance(data, dict):
            if "url" in data:
                download_link = data["url"]
            elif "download_url" in data:
                download_link = data["download_url"]
            elif "video" in data and isinstance(data["video"], list):
                download_link = data["video"][0].get("url")

        if not download_link:
            return jsonify({
                "error": "No valid download link found in API response",
                "api_response": data
            }), 500

        return jsonify({
            "message": "Download link fetched successfully",
            "download_link": download_link
        }), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "API request timed out"}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API Error: {str(e)}"}), e.response.status_code
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
