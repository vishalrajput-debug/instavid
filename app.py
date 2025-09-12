from flask import Flask, request, jsonify
import requests
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)

# ------------------ RapidAPI Config ------------------
# This new API is more reliable for combined video and audio streams.
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"
RAPIDAPI_HOST = "ytstream-download-youtube-videos.p.rapidapi.com"

# ------------------ Helper Function ------------------
def extract_video_id(url):
    """
    Extract YouTube video ID from any URL
    """
    # ... (Your existing function remains the same)
    short_match = re.search(r'shorts/([^\?&]+)', url)
    if short_match:
        return short_match.group(1), "short"

    short_youtu = re.search(r'youtu\.be/([^\?&]+)', url)
    if short_youtu:
        return short_youtu.group(1), "video"

    long_match = re.search(r'v=([^\?&]+)', url)
    if long_match:
        return long_match.group(1), "video"

    return None, None

# ------------------ Main Download Endpoint ------------------
@app.route("/download", methods=["GET", "POST"])
def download():
    if request.method == "POST":
        data = request.get_json()
        url = data.get("url")
    else:
        url = request.args.get("url")

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    video_id, video_type = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # Step 1: Get all available streams for the video
    rapidapi_info_url = f"https://{RAPIDAPI_HOST}/stream"
    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": RAPIDAPI_HOST
    }
    querystring = {"url": f"https://www.youtube.com/watch?v={video_id}"}
    
    try:
        response_info = requests.get(rapidapi_info_url, headers=headers, params=querystring, timeout=30)
        response_info.raise_for_status()
        data_info = response_info.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch video streams from RapidAPI", "details": str(e)}), 500

    # Step 2: Find a high-quality stream with both video and audio
    try:
        # Filter for streams that have both video and audio (progressive streams) and are in MP4 format
        download_stream = next((
            item for item in data_info.get("data", {}).get("adaptive_formats", [])
            if "progressive" in item.get("mime_type", "") and "mp4" in item.get("mime_type", "")
        ), None)

        if not download_stream:
             # If a progressive stream isn't available, try to find the best resolution adaptive stream.
             # Note: This might still be video-only. A more advanced solution would merge audio and video.
             download_stream = next((
                 item for item in data_info.get("data", {}).get("adaptive_formats", [])
                 if "video" in item.get("mime_type", "") and "mp4" in item.get("mime_type", "")
             ), None)
            
        if not download_stream:
            return jsonify({"error": "Could not find a suitable video stream to download."}), 404
        
        # The download URL is within the stream data
        download_link = download_stream.get("url")
        if not download_link:
            return jsonify({"error": "Download link not found in the stream data."}), 404

        return jsonify({"download_link": download_link})

    except Exception as e:
        return jsonify({"error": "Failed to process API response", "details": str(e)}), 500

# ------------------ Run App ------------------
if __name__ == "__main__":
    app.run(debug=True)