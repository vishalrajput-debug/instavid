from flask import Flask, request, jsonify, send_file, Response, stream_with_context
import requests
import re
from flask_cors import CORS
import json

app = Flask(__name__)
# Allow all origins for development and API access
CORS(app, origins=["*"], supports_credentials=True)

# -----------------
# API Credentials
# -----------------
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238" 

YOUTUBE_RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"
YOUTUBE_API_URL = f"https://{YOUTUBE_RAPIDAPI_HOST}"

INSTAGRAM_RAPIDAPI_HOST = "instagram-reels-stories-downloader-api.p.rapidapi.com"
INSTAGRAM_API_URL = f"https://{INSTAGRAM_RAPIDAPI_HOST}"

# --- Utility Functions (Omitted for brevity) ---
def extract_video_id(url):
    """Extracts YouTube video ID from various URL formats."""
    short_match = re.search(r'shorts/([^\?&]+)', url)
    if short_match:
        return short_match.group(1)

    short_youtu = re.search(r'youtu\.be/([^\?&]+)', url)
    if short_youtu:
        return short_youtu.group(1)

    long_match = re.search(r'v=([^\?&]+)', url)
    if long_match:
        return long_match.group(1)

    return None

def is_youtube_url(url):
    """Checks if the URL is a YouTube domain."""
    return "youtube.com" in url or "youtu.be" in url

def is_instagram_url(url):
    """Checks if the URL is an Instagram domain."""
    return "instagram.com" in url
# -----------------------------------------------


# NEW ROUTE: Proxy to force download with Content-Disposition header
@app.route("/force_download", methods=["GET"])
def force_download():
    """Proxies the final download link and forces the browser to download the file."""
    # The 'file_url' is the direct link to the Instagram media file (the one that was opening in a new tab)
    file_url = request.args.get("file_url")
    filename = request.args.get("filename", "instavid_media.mp4")

    if not file_url:
        return jsonify({"error": "Missing file_url parameter"}), 400

    try:
        # Use requests.get with stream=True to handle large files efficiently
        stream_response = requests.get(file_url, stream=True, timeout=30)
        stream_response.raise_for_status()

        # Extract content type from the source response if available, default to video/mp4
        content_type = stream_response.headers.get("Content-Type", "video/mp4")
        
        # Determine file extension for the download filename
        if 'image' in content_type:
            ext = '.jpg'
        elif 'video' in content_type:
            ext = '.mp4'
        else:
            # Fallback for HEIC/other types, though we default to MP4 for Instagram Reels
            ext = '.bin' 

        # 1. Create a streaming response from Flask
        # 2. Add the crucial Content-Disposition header to force download
        response = Response(
            # Stream the content chunk by chunk
            stream_with_context(stream_response.iter_content(chunk_size=1024 * 1024)), 
            content_type=content_type
        )
        # IMPORTANT: This header tells the browser to download the file
        response.headers["Content-Disposition"] = f"attachment; filename={filename}{ext}"
        
        # Optional: Set Content-Length if the source provided it, helps with download progress
        if 'Content-Length' in stream_response.headers:
            response.headers["Content-Length"] = stream_response.headers["Content-Length"]

        return response

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to stream the file from the source URL", "details": str(e)}), 500


# ✅ YOUTUBE ENDPOINT (UNCHANGED)
@app.route("/download", methods=["POST", "GET"])
def download_youtube():
    """Handles YouTube video downloads."""
    data = request.get_json() if request.method == "POST" else request.args
    url = data.get("url")
    requested_quality = data.get("quality")

    if not url or not is_youtube_url(url):
        return jsonify({"error": "Please provide a valid YouTube URL"}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": YOUTUBE_RAPIDAPI_HOST
    }

    try:
        # 1. Get available qualities
        q_res = requests.get(f"{YOUTUBE_API_URL}/get_available_quality/{video_id}", headers=headers, timeout=20)
        q_res.raise_for_status()
        qualities = q_res.json()
        video_qualities = [q for q in qualities if q.get("type") == "video"]

        if not video_qualities:
             return jsonify({"error": "No video qualities found for this YouTube ID"}), 404

        # 2. Choose quality (default to the first available if requested quality isn't found)
        chosen_quality = next((q["quality"] for q in video_qualities if q["quality"] == requested_quality), video_qualities[0]["quality"])

        # 3. Get download link
        d_res = requests.get(f"{YOUTUBE_API_URL}/download_video/{video_id}?quality={chosen_quality}", headers=headers, timeout=30)
        d_res.raise_for_status()
        dl_data = d_res.json()

        if "file" not in dl_data:
            return jsonify({"error": "Download link not found in API response", "api_response": dl_data}), 404

        # YouTube link is returned directly (it usually has the necessary headers or is temporary)
        return jsonify({"download_link": dl_data["file"]})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to fetch YouTube video", "details": str(e)}), 500

# ✅ INSTAGRAM ENDPOINT (MODIFIED TO RETURN PROXY LINK)
@app.route("/convert", methods=["GET", "POST"])
def convert_instagram():
    """Gets the direct media URL from the API and converts it into a local proxy URL."""
    data = request.get_json() if request.method == "POST" else request.args
    url = data.get("url")

    if not url or not is_instagram_url(url):
        return jsonify({"error": "Please provide a valid Instagram URL"}), 400

    target_url = f"{INSTAGRAM_API_URL}/convert"

    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY,
        "X-Rapidapi-Host": INSTAGRAM_RAPIDAPI_HOST
    }

    try:
        response = requests.get(target_url, headers=headers, params={"url": url}, timeout=20)
        response.raise_for_status()
        api_data = response.json()

        download_link = None
        
        # Correctly parse the download link
        if isinstance(api_data.get("media"), list) and api_data["media"]:
            download_link = api_data["media"][0].get("url")
        elif api_data.get("download_link"):
            download_link = api_data["download_link"]
        elif api_data.get("url"):
            download_link = api_data["url"]
        
        if not download_link:
            error_message = api_data.get("error") or "Failed to extract media link from API response. Check response details."
            return jsonify({
                "error": error_message, 
                "response_details": api_data,
                "note": "The API response was received but the download link could not be found."
            }), 404

        # --- KEY CHANGE: Return the URL to our new Flask proxy route ---
        # The frontend will now call this local proxy route, which forces the download.
        proxied_download_url = f"/force_download?file_url={requests.utils.quote(download_link)}&filename=instavid_media"

        return jsonify({"download_link": proxied_download_url})

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else 500
        return jsonify({
            "error": "Failed to connect to Instagram API", 
            "details": str(e),
            "status_code": status_code,
        }), status_code if status_code >= 400 else 500


if __name__ == "__main__":
    app.run(debug=True)
