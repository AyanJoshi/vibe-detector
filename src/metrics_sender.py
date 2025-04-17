from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger('vibe_detector')

class MetricsSender:    
    def __init__(self):
        """Initialize InfluxDB client connection"""
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_API_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG", "VibeDetector")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "vibe_detector")
        self.client = None
        self.write_api = None
        
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            logger.info("Connected to InfluxDB")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            self.client = None
    
    def send_metrics(self, temperature, humidity, brightness, color_temp, activity, vibe):
        """Send basic metrics to InfluxDB"""
        if not self.write_api:
            return
            
        try:
            # Create a point with all metrics
            point = Point("room_metrics")
            
            # Add metrics if they're not None
            if temperature is not None:
                point = point.field("temperature", float(temperature))
            if humidity is not None:
                point = point.field("humidity", float(humidity))
            if brightness is not None:
                point = point.field("brightness", brightness)
            if color_temp is not None:
                point = point.field("color_temp", color_temp)
            if activity is not None:
                point = point.field("activity", activity)
            if vibe is not None:
                point = point.field("vibe", vibe)
            
            # Write the point
            self.write_api.write(bucket=self.bucket, record=point)
        except Exception as e:
            logger.error(f"Error sending metrics: {e}")
    
    def close(self):
        """Close InfluxDB client connection"""
        if self.client:
            self.client.close()