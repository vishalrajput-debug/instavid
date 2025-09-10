#!/usr/bin/env bash
# Exit on first error
set -o errexit

# Install ffmpeg
apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
pip install -r requirements.txt
