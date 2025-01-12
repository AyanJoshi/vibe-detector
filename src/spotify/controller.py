"""
Spotify controller for managing playback and playlists
"""
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from pathlib import Path
import sys
import os

# Add project root to path to allow imports from config
project_root = Path(__file__).parents[2]
sys.path.append(str(project_root))

from config.spotify_credentials import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES

class SpotifyController:
    def __init__(self):
        """Initialize Spotify controller with authentication"""
        self.sp = None
        self.current_device_id = None
        self.initialize_spotify()
        
    def initialize_spotify(self):
        """Initialize Spotify client with proper authentication"""
        try:
            auth_manager = SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=SCOPES,
                cache_path='.spotify_cache'
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            self._get_active_device()
        except Exception as e:
            print(f"Error initializing Spotify: {e}")
            raise
            
    def _get_active_device(self):
        """Get the active Spotify device ID"""
        devices = self.sp.devices()
        if not devices['devices']:
            print("No active devices found. Please open Spotify on your device.")
            return None
            
        # Prefer active device, otherwise take the first available
        active_devices = [d for d in devices['devices'] if d['is_active']]
        self.current_device_id = active_devices[0]['id'] if active_devices else devices['devices'][0]['id']
        
    def play(self, context_uri=None):
        """Start or resume playback"""
        try:
            if context_uri:
                self.sp.start_playback(device_id=self.current_device_id, context_uri=context_uri)
            else:
                self.sp.start_playback(device_id=self.current_device_id)
        except Exception as e:
            print(f"Error during playback: {e}")
            
    def pause(self):
        """Pause playback"""
        try:
            self.sp.pause_playback(device_id=self.current_device_id)
        except Exception as e:
            print(f"Error pausing playback: {e}")
            
    def next_track(self):
        """Skip to next track"""
        try:
            self.sp.next_track(device_id=self.current_device_id)
        except Exception as e:
            print(f"Error skipping track: {e}")
            
    def previous_track(self):
        """Go back to previous track"""
        try:
            self.sp.previous_track(device_id=self.current_device_id)
        except Exception as e:
            print(f"Error returning to previous track: {e}")
            
    def set_volume(self, volume_percent):
        """Set volume (0-100)"""
        try:
            self.sp.volume(volume_percent, device_id=self.current_device_id)
        except Exception as e:
            print(f"Error setting volume: {e}")
            
    def get_current_playback(self):
        """Get current playback state"""
        try:
            return self.sp.current_playback()
        except Exception as e:
            print(f"Error getting playback state: {e}")
            return None
            
    def play_playlist(self, playlist_uri):
        """Play a specific playlist"""
        try:
            self.sp.start_playback(device_id=self.current_device_id, context_uri=playlist_uri)
        except Exception as e:
            print(f"Error playing playlist: {e}")
            
    def get_device_volume(self):
        """Get current device volume"""
        playback = self.get_current_playback()
        if playback and 'device' in playback:
            return playback['device'].get('volume_percent', 0)
        return 0