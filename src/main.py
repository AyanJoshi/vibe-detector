"""
Main controller for vibe detector system
Coordinates between sensors, vibe analysis, and music control
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from analysis.vibe_analyzer import VibeAnalyzer, VibeCategory
from spotify.controller import SpotifyController
from server.server import app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VibeDetectorController:
    def __init__(self):
        self.vibe_analyzer = VibeAnalyzer()
        self.spotify = SpotifyController()
        self.current_vibe: Optional[VibeCategory] = None
        self.last_change_time = datetime.now()
        
    async def process_sensor_data(self, sensor_data: dict):
        """Process new sensor data and update music if needed"""
        # Add data to analyzer
        self.vibe_analyzer.add_data(sensor_data)
        
        # Determine current vibe
        new_vibe, confidence = self.vibe_analyzer.determine_vibe()
        
        # Check if we should change the music
        if self.vibe_analyzer.should_change_music(new_vibe, confidence, self.current_vibe):
            await self.update_music(new_vibe, confidence)
            self.current_vibe = new_vibe
            self.last_change_time = datetime.now()
            
    async def update_music(self, vibe: VibeCategory, confidence: float):
        """Update music based on detected vibe"""
        try:
            # Get playlist recommendations
            playlists = self.vibe_analyzer.get_playlist_recommendations(vibe, confidence)
            
            if not playlists:
                logger.warning("No playlists found for vibe: %s", vibe)
                return
                
            # Play first recommended playlist
            self.spotify.play_playlist(playlists[0])
            logger.info("Updated music to match vibe: %s (confidence: %.2f)", vibe, confidence)
            
        except Exception as e:
            logger.error("Error updating music: %s", e)
            
    async def start(self):
        """Start the vibe detector system"""
        logger.info("Starting Vibe Detector system...")
        
        # Initialize Spotify
        try:
            # Ensure Spotify is ready
            self.spotify.initialize_spotify()
            logger.info("Spotify controller initialized")
        except Exception as e:
            logger.error("Failed to initialize Spotify: %s", e)
            return

        # Start FastAPI server
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    controller = VibeDetectorController()
    asyncio.run(controller.start())