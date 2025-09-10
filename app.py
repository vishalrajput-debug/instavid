import os
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Use your actual API Key from your RapidAPI account
# IMPORTANT: DO NOT hardcode this in production. Use environment variables.
RAPIDAPI_KEY = "82f0a2c073mshc80b6b4a96395cdp11ed2bjsnae9413302238"

# Define the hosts and base URLs for each API
YOUTUBE_API_HOST = "youtube-media-downloader.p.rapidapi.com"
YOUTUBE_API_URL = f"https://{YOUTUBE_API_HOST}/v2/video" # A more appropriate endpoint for single videos

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
        "x-rapidapi-host": ""  # This will be set dynamically
    }
    
    # Check the URL to determine which API to call
    if "youtube.com" in url or "youtu.be" in url:
        headers["x-rapidapi-host"] = YOUTUBE_API_HOST
        api_url = YOUTUBE_API_URL
        params = {"url": url} # Use 'url' as the parameter key
    elif "instagram.com" in url:
        headers["x-rapidapi-host"] = INSTAGRAM_API_HOST
        api_url = INSTAGRAM_API_URL
        params = {"url": url} # Use 'url' as the parameter key
    else:
        return jsonify({"error": "Invalid URL. Only YouTube and Instagram are supported."}), 400

    try:
        # Make the API request with a timeout
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        
        # Get the JSON response from the API
        data = response.json()
        
        # The API's response structure will vary.
        # You'll need to inspect the JSON to find the actual download link.
        # Example: some APIs return a 'video_url' field.
        if "video_url" in data:
            download_link = data["video_url"]
        elif "download_url" in data:
            download_link = data["download_url"]
        else:
            return jsonify({"error": "API response did not contain a valid download link."}), 500

        # Return the direct download link to the front end
        return jsonify({"download_link": download_link}), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "The API request timed out."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API Error: {str(e)}"}), e.response.status_code
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    # In production, use Gunicorn as defined in your Procfile
    app.run(debug=True)