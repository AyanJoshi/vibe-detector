from collections import deque

class SensorAnalyzer:
    def __init__(self, history_length=20):
        self.temp_history = deque(maxlen=history_length)
        self.humidity_history = deque(maxlen=history_length)
    
    def analyze(self, temperature, humidity):
        """Analyze temperature and humidity data"""
        self.temp_history.append(temperature)
        self.humidity_history.append(humidity)
        
        # Get averages to smooth out readings
        avg_temp = sum(self.temp_history) / len(self.temp_history)
        avg_humidity = sum(self.humidity_history) / len(self.humidity_history)
        
        # Analyze comfort level
        comfort = self._determine_comfort(avg_temp, avg_humidity)
        
        return {
            "temperature": avg_temp,
            "humidity": avg_humidity,
            "comfort": comfort
        }
    
    def _determine_comfort(self, temp, humidity):
        """Determine comfort level based on temp and humidity"""
        # Based on general comfort guidelines
        if 20 <= temp <= 25:  # Comfortable temperature range (in °C)
            if 30 <= humidity <= 60:  # Comfortable humidity range
                return "comfortable"
            elif humidity < 30:
                return "dry"
            else:
                return "humid"
        elif temp < 20:
            return "cold"
        else:
            if humidity > 60:
                return "hot_and_humid"
            else:
                return "hot"