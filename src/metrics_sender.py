from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

logger = logging.getLogger('vibe_detector')

class MetricsSender:
    def __init__(self, url="http://localhost:8086", token="jRfHu8tbIv8_rlh8JuYiyiCdjVuo-cWG2iLP1wdoEQQ9b36WXdYaVYV_C92jFG0kPSNgg3EGHDW7F9t8dKgUVw==", 
                 org="VibeDetector", bucket="vibe_detector"):
        """Initialize InfluxDB client connection"""
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
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
            if brightness:
                point = point.field("brightness", brightness)
            if color_temp:
                point = point.field("color_temp", color_temp)
            if activity:
                point = point.field("activity", activity)
            if vibe:
                point = point.field("vibe", vibe)
            
            # Write the point
            self.write_api.write(bucket=self.bucket, record=point)
        except Exception as e:
            logger.error(f"Error sending metrics: {e}")
    
    def close(self):
        """Close InfluxDB client connection"""
        if self.client:
            self.client.close()