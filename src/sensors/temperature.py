"""
Temperature and humidity sensor module using DHT22
"""
import time
import Adafruit_DHT

class TemperatureSensor:
    def __init__(self, pin=4):
        self.sensor = Adafruit_DHT.DHT22
        self.pin = pin
        
    def read(self):
        """
        Read temperature and humidity data
        Returns:
            tuple: (temperature, humidity) or (None, None) if reading fails
        """
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        return temperature, humidity if humidity is not None else (None, None)
    
    def get_formatted_data(self):
        """
        Get formatted temperature and humidity data
        Returns:
            dict: Formatted sensor data
        """
        temp, humidity = self.read()
        return {
            'timestamp': time.time(),
            'temperature': round(temp, 2) if temp is not None else None,
            'humidity': round(humidity, 2) if humidity is not None else None,
            'status': 'ok' if None not in (temp, humidity) else 'error'
        }