"""
Configuration file for Vibe Detector system
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ZeroMQ connection settings
RASPBERRY_PI_IP = os.getenv("RASPBERRY_PI_IP", "192.168.1.210")  
ZEROMQ_SENSOR_PORT = int(os.getenv("ZEROMQ_SENSOR_PORT", "5555"))
ZEROMQ_VIDEO_PORT = int(os.getenv("ZEROMQ_VIDEO_PORT", "5556"))
ZEROMQ_TOPIC = os.getenv("ZEROMQ_TOPIC", "")

# Spotify API settings
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

# Playlist URIs for different vibes
SPOTIFY_PLAYLISTS = {
    "energetic_party": os.getenv("PLAYLIST_ENERGETIC_PARTY"),
    "relaxed_chill": os.getenv("PLAYLIST_RELAXED_CHILL"),
    "focused_study": os.getenv("PLAYLIST_FOCUSED_STUDY"),
    "cozy_evening": os.getenv("PLAYLIST_COZY_EVENING"),
    "dinner_time": os.getenv("PLAYLIST_DINNER_TIME"),
    "pet_companion": os.getenv("PLAYLIST_PET_COMPANION")
}

# Paths to model files
MODEL_DIR = os.getenv("MODEL_DIR", "models")
MOBILENET_PROTOTXT = os.getenv("MOBILENET_PROTOTXT", f"{MODEL_DIR}/MobileNetSSD_deploy.prototxt")
MOBILENET_MODEL = os.getenv("MOBILENET_MODEL", f"{MODEL_DIR}/MobileNetSSD_deploy.caffemodel")

# Analysis parameters
FRAME_HISTORY_LENGTH = int(os.getenv("FRAME_HISTORY_LENGTH", "10"))
SENSOR_HISTORY_LENGTH = int(os.getenv("SENSOR_HISTORY_LENGTH", "20"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

# Visualization settings
ENABLE_VISUALIZATION = os.getenv("ENABLE_VISUALIZATION", "True").lower() == "true"
DASHBOARD_DATA_POINTS = int(os.getenv("DASHBOARD_DATA_POINTS", "100"))

# Output directory
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")