"""
Test script for Spotify integration
"""
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parents[1]
sys.path.append(str(project_root))

from src.spotify.controller import SpotifyController

def test_basic_controls():
    """Test basic Spotify controls"""
    controller = SpotifyController()
    
    # Test volume control
    print("Testing volume control...")
    original_volume = controller.get_device_volume()
    print(f"Original volume: {original_volume}")
    
    # Set to 50%
    controller.set_volume(50)
    time.sleep(1)
    print("Volume set to 50%")
    
    # Test playback
    print("\nTesting playback controls...")
    controller.play()
    print("Playback started")
    time.sleep(3)
    
    controller.pause()
    print("Playback paused")
    time.sleep(1)
    
    # Test track navigation
    print("\nTesting track navigation...")
    controller.next_track()
    print("Skipped to next track")
    time.sleep(2)
    
    controller.previous_track()
    print("Returned to previous track")
    time.sleep(2)
    
    # Restore original volume
    controller.set_volume(original_volume)
    print(f"\nRestored volume to {original_volume}%")

if __name__ == "__main__":
    test_basic_controls()