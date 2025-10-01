from flask import Flask, request, jsonify, send_file
import requests
import re
from flask_cors import CORS
import json
import io

app = Flask(__name__)
# Allow all origins for development and API access
CORS(app, origins=["*"], supports_credentials=True)

# -----------------
# API Credentials
# -----------------
# NOTE: Using the key provided in your previous message.
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238" 

YOUTUBE_RAPIDAPI_HOST = "youtube-video-fast-downloader-24-7.p.rapidapi.com"
YOUTUBE_API_URL = f"https://{YOUTUBE_RAPIDAPI_HOST}"

INSTAGRAM_RAPIDAPI_HOST = "instagram-reels-stories-downloader-api.p.rapidapi.com"
INSTAGRAM_API_URL = f"https://{INSTAGRAM_RAPIDAPI_HOST}"

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
            # The API responded, but didn't provide the expected download link
            return jsonify({"error": "Download link not found in API response", "api_response": dl_data}), 404

        return jsonify({"download_link": dl_data["file"]})

    except requests.exceptions.RequestException as e:
        # General error during request (timeout, connection failure, API HTTP error)
        return jsonify({"error": "Failed to fetch YouTube video", "details": str(e)}), 500

# ✅ INSTAGRAM ENDPOINT (UNCHANGED)
@app.route("/convert", methods=["GET", "POST"])
def convert_instagram():
    """Handles Instagram media downloads by correctly parsing the API response structure."""
    data = request.get_json() if request.method == "POST" else request.args
    url = data.get("url")

    if not url or not is_instagram_url(url):
        return jsonify({"error": "Please provide a valid Instagram URL"}), 400

    # Ensure the API host is used that is defined in the variables
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
        
        # --- FIX: Correctly parse the download link based on the API response structure ---
        if isinstance(api_data.get("media"), list) and api_data["media"]:
            download_link = api_data["media"][0].get("url")
            
        elif api_data.get("download_link"):
            download_link = api_data["download_link"]
        elif api_data.get("url"):
            download_link = api_data["url"]
        # ---------------------------------------------------------------------------------

        if not download_link:
            error_message = api_data.get("error") or "Failed to extract media link from API response. Check response details."
            return jsonify({
                "error": error_message, 
                "response_details": api_data,
                "note": "The API response was received but the download link could not be found in the expected format."
            }), 404

        # Important: Return the direct download link. The frontend will now call 
        # the new /force_download endpoint with this link.
        return jsonify({"download_link": download_link})

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else 500
        return jsonify({
            "error": "Failed to connect to Instagram API", 
            "details": str(e),
            "status_code": status_code,
            "note": "If the status code is 400/404/429/500, the RapidAPI service failed to process the request."
        }), status_code if status_code >= 400 else 500


# ✅ NEW ENDPOINT TO FORCE DOWNLOAD
@app.route("/force_download", methods=["GET"])
def force_download():
    """
    Proxies the download request to force the Content-Disposition header.
    Expects 'link' (the direct media URL) and optional 'filename' as query parameters.
    """
    # The frontend passes the direct media URL as a 'link' query parameter
    download_link = request.args.get("link")
    filename = request.args.get("filename", "instagram_reel.mp4") 

    if not download_link:
        return jsonify({"error": "Missing download link"}), 400
    
    # Simple check to ensure link looks valid before requesting
    if not download_link.startswith("http"):
         return jsonify({"error": "Invalid link format"}), 400

    try:
        # Fetch the content of the video from the direct link (the CDN)
        # Use a reasonable timeout for fetching the video content
        video_response = requests.get(download_link, timeout=60) 
        video_response.raise_for_status()

        # Determine content type (e.g., video/mp4)
        content_type = video_response.headers.get('Content-Type', 'application/octet-stream')
        
        # Read the entire content into an in-memory stream (BytesIO)
        video_data = io.BytesIO(video_response.content)

        # CRITICAL PART: Use send_file with as_attachment=True
        # This function handles setting the Content-Disposition: attachment header 
        # which forces the browser to download the file.
        return send_file(
            video_data,
            mimetype=content_type, 
            as_attachment=True, 
            download_name=filename 
        )

    except requests.exceptions.RequestException as e:
        # Get status code if request failed due to HTTP error (e.g., 404, 500)
        status_code = e.response.status_code if e.response is not None else 500
        return jsonify({
            "error": "Failed to proxy video download (Check CDN link access or timeout)", 
            "details": str(e),
            "status_code": status_code,
        }), status_code if status_code >= 400 else 500


if __name__ == "__main__":
    app.run(debug=True)
