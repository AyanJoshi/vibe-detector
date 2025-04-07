#!/usr/bin/env python3
import zmq
import time
import cv2
import json
import numpy as np
import logging
import signal
import sys
import os
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Import analyzers and config
from frame_analyzer import FrameAnalyzer
from activity_detector import ActivityDetector
from sensor_analyzer import SensorAnalyzer
from vibe_classifier import VibeClassifier
from metrics_sender import MetricsSender

from config import (
    RASPBERRY_PI_IP, ZEROMQ_SENSOR_PORT, ZEROMQ_VIDEO_PORT, ZEROMQ_TOPIC,
    SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI,
    SPOTIFY_PLAYLISTS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - vibe_detector - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vibe_detector')

class VibeDetectorProcessor:
    def __init__(self):
        self.running = True
        self.frame_count = 0
        self.start_time = None
        self.last_detected_objects = []
        
        # Setup signal handler for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Initialize ZeroMQ context and sockets
        self.context = zmq.Context()
        
        # Socket for receiving sensor data
        self.sensor_socket = self.context.socket(zmq.SUB)
        self.sensor_socket.connect(f"tcp://{RASPBERRY_PI_IP}:{ZEROMQ_SENSOR_PORT}")
        self.sensor_socket.setsockopt_string(zmq.SUBSCRIBE, ZEROMQ_TOPIC)
        
        # Socket for receiving video frames
        self.video_socket = self.context.socket(zmq.SUB)
        self.video_socket.connect(f"tcp://{RASPBERRY_PI_IP}:{ZEROMQ_VIDEO_PORT}")
        self.video_socket.setsockopt_string(zmq.SUBSCRIBE, ZEROMQ_TOPIC)
        
        # For storing received sensor data
        self.latest_sensor_data = {
            "temperature": None,
            "humidity": None,
            "timestamp": None
        }
        
        # Initialize analyzers
        self.frame_analyzer = FrameAnalyzer()
        self.activity_detector = ActivityDetector()
        self.sensor_analyzer = SensorAnalyzer()
        self.vibe_classifier = VibeClassifier()
        self.metrics_sender = MetricsSender()

        # For Spotify API
        if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
            try:
                self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                    client_id=SPOTIFY_CLIENT_ID,
                    client_secret=SPOTIFY_CLIENT_SECRET,
                    redirect_uri=SPOTIFY_REDIRECT_URI,
                    scope="user-read-playback-state,user-modify-playback-state"
                ))
                logger.info("Spotify API initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify API: {e}")
                self.sp = None
        else:
            logger.warning("Spotify credentials not found. Music playback disabled.")
            self.sp = None
        
        # Current vibe and playlist
        self.current_vibe = None
        self.current_playlist = None
        self.last_vibe_change = time.time()
        self.min_vibe_duration = 10  # seconds (minimum time between vibe changes)
        
        # Create a resizable window
        cv2.namedWindow("Vibe Detector", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Vibe Detector", 800, 600)
    
    def receive_sensor_data(self, timeout=100):
        """Receive sensor data from ZeroMQ socket with timeout"""
        try:
            self.sensor_socket.setsockopt(zmq.RCVTIMEO, timeout)
            json_data = self.sensor_socket.recv_string()
            data = json.loads(json_data)
            self.latest_sensor_data = data
            return True
        except zmq.Again:
            return False
        except Exception as e:
            logger.error(f"Error receiving sensor data: {e}")
            return False
    
    def receive_frame(self, timeout=100):
        """Receive video frame from ZeroMQ socket with timeout"""
        try:
            self.video_socket.setsockopt(zmq.RCVTIMEO, timeout)
            metadata_json = self.video_socket.recv_string()
            metadata = json.loads(metadata_json)
            frame_data = self.video_socket.recv()
            
            buffer = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
            
            self.frame_count += 1
            return metadata, frame
        except zmq.Again:
            return None, None
        except Exception as e:
            logger.error(f"Error receiving frame: {e}")
            return None, None
    
    def process_data(self, sensor_data, frame):
        """Process received data for vibe detection"""
        if frame is None:
            return
        
        # Extract sensor values
        temperature = sensor_data.get("temperature")
        humidity = sensor_data.get("humidity")
        
        if temperature is None or humidity is None:
            return
        
        # Analyze frame for brightness and color temperature
        brightness, _ = self.frame_analyzer.analyze_brightness(frame)
        color_temp, _ = self.frame_analyzer.analyze_color_temperature(frame)
        
        # Detect activity
        activity, detected_objects = self.activity_detector.detect(frame)
        self.last_detected_objects = detected_objects
        self.frame_analyzer.activity_history.append(activity)
        
        # Get dominant features over time
        dom_brightness, dom_color_temp, dom_activity = self.frame_analyzer.get_dominant_features()
        
        # Analyze sensor data
        sensor_analysis = self.sensor_analyzer.analyze(temperature, humidity)
        comfort = sensor_analysis["comfort"]
        
        # Classify vibe
        vibe, playlist_uri, _ = self.vibe_classifier.classify(
            dom_brightness, dom_color_temp, dom_activity, comfort
        )
        
        self.metrics_sender.send_metrics(
            temperature=temperature,
            humidity=humidity,
            brightness=dom_brightness,
            color_temp=dom_color_temp,
            activity=dom_activity,
            vibe=vibe
        )

        # Update current vibe and playlist if changed
        current_time = time.time()
        if (self.current_vibe != vibe and 
            current_time - self.last_vibe_change > self.min_vibe_duration):
            logger.info(f"Vibe changed from {self.current_vibe} to {vibe}")
            self.current_vibe = vibe
            self.current_playlist = playlist_uri
            
            # Play the playlist on Spotify
            if self.sp:
                self._play_playlist(playlist_uri)
        
        # Display simple visualization with just the vibe
        self._display_simple_visualization(frame, vibe)
        
        # Log current state periodically
        if self.frame_count % 100 == 0:
            print(f"Current vibe: {vibe} - Temp: {temperature:.1f}°C, Humidity: {humidity:.1f}%")
    
    def _play_playlist(self, playlist_uri):
        """Play the selected playlist on Spotify with shuffle"""
        if not self.sp or not playlist_uri:
            return
            
        try:
            # Check if there are active devices
            devices = self.sp.devices()
            if not devices or not devices['devices']:
                logger.warning("No active Spotify devices found")
                return
                
            # Use the first available device
            device_id = devices['devices'][0]['id']
            
            # Get playlist tracks to determine a random starting point
            playlist_id = playlist_uri.split(":")[-1].split("?")[0]  # Extract ID from URI
            playlist_tracks = self.sp.playlist_tracks(playlist_id)
            
            if playlist_tracks and playlist_tracks['items']:
                # Get total number of tracks
                total_tracks = len(playlist_tracks['items'])
                
                # Generate random offset
                import random
                random_offset = random.randint(0, total_tracks - 1)
                
                # Start playback from random position
                self.sp.start_playback(
                    device_id=device_id, 
                    context_uri=playlist_uri,
                    offset={"position": random_offset}
                )
                logger.info(f"Playing playlist: {playlist_uri} (starting at track {random_offset+1})")
            else:
                # Fallback to regular playback if we can't get track info
                self.sp.start_playback(device_id=device_id, context_uri=playlist_uri)
                logger.info(f"Playing playlist: {playlist_uri}")
                
        except Exception as e:
            logger.error(f"Error playing playlist: {e}")
    
    def _display_simple_visualization(self, frame, vibe):
        """Display a simple visualization with just the current vibe"""
        # Create a copy of the frame for display
        display = frame.copy()
        
        # Add a semi-transparent overlay at the top for the vibe text
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (display.shape[1], 60), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, display, 0.3, 0, display)
        
        # Add the vibe text in large, clear font - with smaller font size and centered
        vibe_text = f"CURRENT VIBE: {vibe}"
        
        # Get text size to center it
        text_size = cv2.getTextSize(vibe_text, cv2.FONT_HERSHEY_TRIPLEX, 0.6, 1)[0]
        text_x = (display.shape[1] - text_size[0]) // 2  # Center horizontally
        
        # Draw the text
        cv2.putText(
            display, 
            vibe_text, 
            (text_x, 30),  # Centered x position
            cv2.FONT_HERSHEY_TRIPLEX, 
            0.6,  # Smaller font size
            (0, 220, 120), 
            1
        )
        
        # Display the frame
        cv2.imshow("Vibe Detector", display)
        cv2.waitKey(1)
    
    def cleanup(self):
        """Release resources and close connections"""
        cv2.destroyAllWindows()
        self.sensor_socket.close()
        self.video_socket.close()
        self.context.term()
        logger.info("ZeroMQ connections closed")
        
        if hasattr(self, 'metrics_sender'):
            self.metrics_sender.close()
        if self.start_time:
            elapsed = time.time() - self.start_time
            logger.info(f"Ran for {elapsed:.1f} seconds")
            logger.info(f"Processed {self.frame_count} frames")
            if elapsed > 0:
                logger.info(f"Average FPS: {self.frame_count / elapsed:.1f}")
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C to shut down cleanly"""
        print("\nreceived SIGINT")
        print("Shutting down...")
        self.running = False
    
    def run(self):
        """Main loop for receiving and processing data"""
        self.start_time = time.time()
        
        print("Vibe Detector - Main Processor")
        print("-----------------------------------")
        print(f"Receiving sensor data from {RASPBERRY_PI_IP}:{ZEROMQ_SENSOR_PORT}")
        print(f"Receiving video frames from {RASPBERRY_PI_IP}:{ZEROMQ_VIDEO_PORT}")
        if self.sp:
            print("Spotify integration enabled")
        else:
            print("Spotify integration disabled")
        print("Press Ctrl+C to exit\n")
        
        try:
            while self.running:
                # Try to receive sensor data (non-blocking)
                sensor_received = self.receive_sensor_data()
                
                # Try to receive frame (non-blocking)
                metadata, frame = self.receive_frame()
                
                # Process the received data
                if sensor_received or frame is not None:
                    self.process_data(self.latest_sensor_data, frame)
                else:
                    # If no data was received, sleep to avoid maxing CPU
                    time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()

# Run the program
if __name__ == "__main__":
    processor = VibeDetectorProcessor()
    processor.run()