from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

# RapidAPI credentials
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"
RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"

# Function to extract video ID from any YouTube URL
def extract_video_id(url):
    # Short URL: youtu.be/VIDEO_ID
    short_match = re.search(r'youtu\.be/([^\?&]+)', url)
    if short_match:
        return short_match.group(1)
    
    # Standard URL: youtube.com/watch?v=VIDEO_ID
    long_match = re.search(r'v=([^\?&]+)', url)
    if long_match:
        return long_match.group(1)
    
    return None

@app.route("/download/video", methods=["GET"])
def download_video():
    url = request.args.get("url")
    quality = request.args.get("quality", "137")  # default 137
    
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    rapidapi_url = f"https://{RAPIDAPI_HOST}/download_video/{video_id}?quality={quality}"
    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": RAPIDAPI_HOST
    }
    
    response = requests.get(rapidapi_url, headers=headers)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch video", "details": response.text}), 400
    
    return jsonify(response.json())

@app.route("/download/audio", methods=["GET"])
def download_audio():
    url = request.args.get("url")
    quality = request.args.get("quality", "251")  # default 251
    
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    rapidapi_url = f"https://{RAPIDAPI_HOST}/download_audio/{video_id}?quality={quality}"
    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": RAPIDAPI_HOST
    }
    
    response = requests.get(rapidapi_url, headers=headers)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch audio", "details": response.text}), 400
    
    return jsonify(response.json())

@app.route("/download/short", methods=["GET"])
def download_short():
    url = request.args.get("url")
    quality = request.args.get("quality", "137")  # default 137
    
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    rapidapi_url = f"https://{RAPIDAPI_HOST}/download_short/{video_id}?quality={quality}"
    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": RAPIDAPI_HOST
    }
    
    response = requests.get(rapidapi_url, headers=headers)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch short video", "details": response.text}), 400
    
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(debug=True)
