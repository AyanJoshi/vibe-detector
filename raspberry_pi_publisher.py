#!/usr/bin/env python3
import zmq
import time
import cv2
import json
import numpy as np
import logging
import board
import adafruit_dht
import signal
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - vibe_detector - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vibe_detector')

# Define constants
SERVER_IP = "192.168.1.X"  # Replace with your laptop's IP address
SENSOR_PORT = 5555
VIDEO_PORT = 5556
DHT_PIN = board.D4  # Adjust if your DHT22 is connected to a different pin

class VibeDetectorPublisher:
    def __init__(self):
        self.running = True
        self.frame_count = 0
        self.start_time = None
        
        # Setup signal handler for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Initialize ZeroMQ context
        self.context = zmq.Context()
        
        # Socket for sending sensor data
        self.sensor_socket = self.context.socket(zmq.PUB)
        self.sensor_socket.bind(f"tcp://*:{SENSOR_PORT}")
        
        # Socket for sending video frames
        self.video_socket = self.context.socket(zmq.PUB)
        self.video_socket.bind(f"tcp://*:{VIDEO_PORT}")
        
        # Initialize DHT22 sensor
        try:
            self.dht = adafruit_dht.DHT22(DHT_PIN)
            logger.info("DHT22 initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DHT22: {e}")
            self.dht = None
        
        # Initialize webcam
        try:
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            if not self.camera.isOpened():
                raise Exception("Could not open webcam")
            logger.info("Webcam initialized")
        except Exception as e:
            logger.error(f"Failed to initialize webcam: {e}")
            self.camera = None
    
    def read_dht22(self):
        """Read temperature and humidity from DHT22 sensor"""
        if not self.dht:
            return {"temperature": None, "humidity": None}
        
        try:
            temperature = self.dht.temperature
            humidity = self.dht.humidity
            return {"temperature": temperature, "humidity": humidity}
        except Exception as e:
            logger.error(f"Error reading DHT22: {e}")
            return {"temperature": None, "humidity": None}
    
    def capture_frame(self):
        """Capture a frame from the webcam"""
        if not self.camera:
            return None
        
        ret, frame = self.camera.read()
        if ret:
            self.frame_count += 1
            if self.frame_count % 10 == 0:
                logger.info(f"Frame #{self.frame_count} captured")
            return frame
        return None
    
    def send_sensor_data(self, data):
        """Send sensor data over ZeroMQ"""
        try:
            # Add timestamp to data
            data["timestamp"] = datetime.now().isoformat()
            
            # Convert dict to JSON string and send
            json_data = json.dumps(data)
            self.sensor_socket.send_string(json_data)
            logger.debug(f"Sent sensor data: {json_data}")
        except Exception as e:
            logger.error(f"Error sending sensor data: {e}")
    
    def send_frame(self, frame):
        """Send video frame over ZeroMQ"""
        try:
            if frame is None:
                return
                
            # Compress frame to JPEG to reduce data size
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            
            # Create metadata with timestamp and frame dimensions
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "frame_id": self.frame_count,
                "height": frame.shape[0],
                "width": frame.shape[1],
                "channels": frame.shape[2] if len(frame.shape) > 2 else 1
            }
            
            # Send metadata as a JSON string
            self.video_socket.send_string(json.dumps(metadata), zmq.SNDMORE)
            
            # Send the actual frame data
            self.video_socket.send(buffer.tobytes())
            logger.debug(f"Sent frame #{self.frame_count}")
        except Exception as e:
            logger.error(f"Error sending frame: {e}")
    
    def cleanup(self):
        """Release resources and close connections"""
        if self.camera:
            self.camera.release()
            logger.info("Webcam released")
            
        if self.dht:
            self.dht.exit()
            logger.info("DHT22 cleaned up")
            
        # Close ZeroMQ sockets
        self.sensor_socket.close()
        self.video_socket.close()
        self.context.term()
        logger.info("ZeroMQ connections closed")
        
        # Display runtime statistics
        if self.start_time:
            elapsed = time.time() - self.start_time
            logger.info(f"Ran for {elapsed:.1f} seconds")
            logger.info(f"Captured {self.frame_count} frames")
            logger.info(f"Average FPS: {self.frame_count / elapsed:.1f}")
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C to shut down cleanly"""
        print("\nreceived SIGINT")
        print("Shutting down...")
        self.running = False
    
    def run(self):
        """Main loop for capturing and sending data"""
        self.start_time = time.time()
        last_dht_read = 0
        dht_read_interval = 2  # seconds
        skip_count = 0

        print("Vibe Detector - ZeroMQ Publisher")
        print("-----------------------------------")
        print(f"Publishing sensor data on port {SENSOR_PORT}")
        print(f"Publishing video frames on port {VIDEO_PORT}")
        print("Press Ctrl+C to exit\n")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Read and send DHT22 data at specified interval
                if current_time - last_dht_read >= dht_read_interval:
                    sensor_data = self.read_dht22()
                    if sensor_data["temperature"] is not None:
                        print(f"Temperature: {sensor_data['temperature']:.1f}°C, Humidity: {sensor_data['humidity']:.1f}%")
                    self.send_sensor_data(sensor_data)
                    last_dht_read = current_time
                
                # Capture and send video frame
                skip_count += 1
                if skip_count % 10 == 0:  # Change the '3' to adjust skipping rate
                    # Capture and send video frame
                    frame = self.capture_frame()
                    if frame is not None:
                        self.send_frame(frame)
                
                # Brief sleep to avoid maxing out the CPU
                time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    publisher = VibeDetectorPublisher()
    publisher.run()
