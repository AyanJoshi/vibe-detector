#!/usr/bin/env python3
import zmq
import time
import cv2
import json
import numpy as np
import logging
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
PI_IP = "192.168.1.210"  # Raspberry Pi's IP address
SENSOR_PORT = 5555
VIDEO_PORT = 5556

class VibeDetectorSubscriber:
    def __init__(self):
        self.running = True
        self.frame_count = 0
        self.start_time = None
        
        # Setup signal handler for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Initialize ZeroMQ context
        self.context = zmq.Context()
        
        # Socket for receiving sensor data
        self.sensor_socket = self.context.socket(zmq.SUB)
        self.sensor_socket.connect(f"tcp://{PI_IP}:{SENSOR_PORT}")
        self.sensor_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Socket for receiving video frames
        self.video_socket = self.context.socket(zmq.SUB)
        #self.video_socket.setsockopt(zmq.CONFLATE, 1)  # Only keep latest message (this will result in frame skipping but reduce latency)
        self.video_socket.connect(f"tcp://{PI_IP}:{VIDEO_PORT}")
        self.video_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # For storing received sensor data
        self.latest_sensor_data = {
            "temperature": None,
            "humidity": None,
            "timestamp": None
        }
    
    def receive_sensor_data(self, timeout=100):
        """
        Receive sensor data from ZeroMQ socket with timeout
        Returns True if data was received, False if timeout
        """
        try:
            # Set socket to non-blocking mode with timeout
            self.sensor_socket.setsockopt(zmq.RCVTIMEO, timeout)
            
            # Receive data
            json_data = self.sensor_socket.recv_string()
            data = json.loads(json_data)
            
            # Update latest sensor data
            self.latest_sensor_data = data
            
            logger.debug(f"Received sensor data: {data}")
            return True
        except zmq.Again:
            # Timeout occurred, no data received
            return False
        except Exception as e:
            logger.error(f"Error receiving sensor data: {e}")
            return False
    
    def receive_frame(self, timeout=100):
        """
        Receive video frame from ZeroMQ socket with timeout
        Returns (metadata, frame) tuple if successful, (None, None) if timeout
        """
        try:
            # Set socket to non-blocking mode with timeout
            self.video_socket.setsockopt(zmq.RCVTIMEO, timeout)
            
            # First receive the metadata
            metadata_json = self.video_socket.recv_string()
            metadata = json.loads(metadata_json)
            
            # Then receive the frame data
            frame_data = self.video_socket.recv()
            
            # Decode the frame from JPEG to numpy array
            buffer = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
            
            self.frame_count += 1
            logger.debug(f"Received frame #{metadata.get('frame_id')}")
            
            return metadata, frame
        except zmq.Again:
            # Timeout occurred, no data received
            return None, None
        except Exception as e:
            logger.error(f"Error receiving frame: {e}")
            return None, None
    
    def process_data(self, sensor_data, frame):
        """
        Process received data (implement your vibe detection logic here)
        This is a placeholder for your actual processing logic
        """
        # Just print the data for now
        if sensor_data:
            temp = sensor_data.get("temperature")
            humidity = sensor_data.get("humidity")
            if temp is not None and humidity is not None:
                print(f"Temperature: {temp:.1f}°C, Humidity: {humidity:.1f}%")
        
        # Display the frame if available
        if frame is not None:
            cv2.imshow("Vibe Detector - Received Frame", frame)
            cv2.waitKey(1)
    
    def cleanup(self):
        """Release resources and close connections"""
        # Close OpenCV windows
        cv2.destroyAllWindows()
        
        # Close ZeroMQ sockets
        self.sensor_socket.close()
        self.video_socket.close()
        self.context.term()
        logger.info("ZeroMQ connections closed")
        
        # Display runtime statistics
        if self.start_time:
            elapsed = time.time() - self.start_time
            logger.info(f"Ran for {elapsed:.1f} seconds")
            logger.info(f"Received {self.frame_count} frames")
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
        
        print("Vibe Detector - ZeroMQ Subscriber")
        print("-----------------------------------")
        print(f"Receiving sensor data from {PI_IP}:{SENSOR_PORT}")
        print(f"Receiving video frames from {PI_IP}:{VIDEO_PORT}")
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

if __name__ == "__main__":
    subscriber = VibeDetectorSubscriber()
    subscriber.run()