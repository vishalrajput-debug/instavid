from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for your Netlify frontend
CORS(app, origins=["https://instavid.netlify.app"], supports_credentials=True)

# RapidAPI credentials
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"
RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"

# Function to extract video ID from any YouTube URL
def extract_video_id(url):
    short_match = re.search(r'youtu\.be/([^\?&]+)', url)
    if short_match:
        return short_match.group(1)
    
    long_match = re.search(r'v=([^\?&]+)', url)
    if long_match:
        return long_match.group(1)
    
    return None

def fetch_from_rapidapi(endpoint, video_id, quality):
    url = f"https://{RAPIDAPI_HOST}/{endpoint}/{video_id}?quality={quality}"
    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": RAPIDAPI_HOST
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None, response.text
    return response.json(), None

# Generic route handler for OPTIONS preflight
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return '', 200

@app.route("/download/video", methods=["GET", "OPTIONS"])
def download_video():
    url = request.args.get("url")
    quality = request.args.get("quality", "137")
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    data, error = fetch_from_rapidapi("download_video", video_id, quality)
    if error:
        return jsonify({"error": "Failed to fetch video", "details": error}), 400
    return jsonify(data)

@app.route("/download/audio", methods=["GET", "OPTIONS"])
def download_audio():
    url = request.args.get("url")
    quality = request.args.get("quality", "251")
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    data, error = fetch_from_rapidapi("download_audio", video_id, quality)
    if error:
        return jsonify({"error": "Failed to fetch audio", "details": error}), 400
    return jsonify(data)

@app.route("/download/short", methods=["GET", "OPTIONS"])
def download_short():
    url = request.args.get("url")
    quality = request.args.get("quality", "137")
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    data, error = fetch_from_rapidapi("download_short", video_id, quality)
    if error:
        return jsonify({"error": "Failed to fetch short video", "details": error}), 400
    return jsonify(data)

if __name__ == "__main__":
    # Use host='0.0.0.0' when deploying to Render
    app.run(debug=True, host='0.0.0.0', port=5000)
