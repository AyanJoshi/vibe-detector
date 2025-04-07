import cv2
import numpy as np
from collections import deque

class FrameAnalyzer:
    def __init__(self, history_length=10):
        # Store recent analysis results to smooth out fluctuations
        self.brightness_history = deque(maxlen=history_length)
        self.color_temp_history = deque(maxlen=history_length)
        self.activity_history = deque(maxlen=history_length)
        
        # Load model for activity detection (we'll use this later)
        self.activity_detector = None
    
    def analyze_brightness(self, frame):
        """Determine if the room is dark, dim, or bright"""
        # Convert to grayscale and calculate average pixel value
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        
        # Categorize brightness
        if avg_brightness < 50:
            brightness = "dark"
        elif avg_brightness < 150:
            brightness = "dim"
        else:
            brightness = "bright"
            
        self.brightness_history.append(brightness)
        return brightness, avg_brightness
    
    def analyze_color_temperature(self, frame):
        """Analyze if the color palette is warm or cool"""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define warm and cool color ranges in HSV
        # Warm: red to yellow (0-60 in HSV)
        # Cool: green to blue (61-240 in HSV)
        h_channel = hsv[:,:,0]
        
        warm_pixels = np.sum((h_channel <= 30) | (h_channel >= 150))
        cool_pixels = np.sum((h_channel > 30) & (h_channel < 150))
        
        total_pixels = frame.shape[0] * frame.shape[1]
        warm_ratio = warm_pixels / total_pixels
        
        if warm_ratio > 0.6:
            color_temp = "warm"
        else:
            color_temp = "cool"
            
        self.color_temp_history.append(color_temp)
        return color_temp, warm_ratio
    
    def get_dominant_features(self):
        """Return the most common values in our history"""
        if not self.brightness_history:
            return None, None, None
            
        # Get most common brightness
        brightness_counts = {}
        for b in self.brightness_history:
            brightness_counts[b] = brightness_counts.get(b, 0) + 1
        dominant_brightness = max(brightness_counts, key=brightness_counts.get)
        
        # Get most common color temperature
        color_temp_counts = {}
        for c in self.color_temp_history:
            color_temp_counts[c] = color_temp_counts.get(c, 0) + 1
        dominant_color_temp = max(color_temp_counts, key=color_temp_counts.get)
        
        # Get most common activity
        activity_counts = {}
        for a in self.activity_history:
            activity_counts[a] = activity_counts.get(a, 0) + 1
        
        dominant_activity = "unknown"
        if self.activity_history:
            dominant_activity = max(activity_counts, key=activity_counts.get)
            
        return dominant_brightness, dominant_color_temp, dominant_activity