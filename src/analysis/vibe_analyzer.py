"""
Vibe analysis module
Processes sensor data to determine room vibe and appropriate music
"""
from typing import Dict, List, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum, auto

class VibeCategory(Enum):
    PARTY = auto()
    CHILL = auto()
    FOCUS = auto()
    SOCIAL = auto()
    NEUTRAL = auto()

@dataclass
class VibeThresholds:
    """Thresholds for different vibe categories"""
    sound_level: Tuple[float, float]  # min, max in dB
    motion_level: Tuple[float, float]  # min, max (normalized 0-1)
    temperature: Tuple[float, float]  # min, max in Celsius
    light_level: Tuple[float, float]  # min, max (normalized 0-1)

# Define thresholds for each vibe category
VIBE_THRESHOLDS = {
    VibeCategory.PARTY: VibeThresholds(
        sound_level=(70, 100),
        motion_level=(0.7, 1.0),
        temperature=(22, 28),
        light_level=(0.4, 1.0)
    ),
    VibeCategory.CHILL: VibeThresholds(
        sound_level=(0, 30),
        motion_level=(0, 0.3),
        temperature=(20, 24),
        light_level=(0, 0.4)
    ),
    VibeCategory.FOCUS: VibeThresholds(
        sound_level=(30, 50),
        motion_level=(0.3, 0.5),
        temperature=(21, 25),
        light_level=(0.5, 0.8)
    ),
    VibeCategory.SOCIAL: VibeThresholds(
        sound_level=(50, 70),
        motion_level=(0.5, 0.7),
        temperature=(21, 26),
        light_level=(0.4, 0.8)
    )
}

# Spotify playlist mappings
PLAYLIST_MAPPING = {
    VibeCategory.PARTY: [
        # High energy, upbeat playlists
        "spotify:playlist:37i9dQZF1DXaXB8fQg7xCW",  # Dance Party
        "spotify:playlist:37i9dQZF1DX7ZUug1ANKRP"   # Party Hits
    ],
    VibeCategory.CHILL: [
        # Relaxing, calm playlists
        "spotify:playlist:37i9dQZF1DX8Uebhn9wzrS",  # Chill Hits
        "spotify:playlist:37i9dQZF1DX6VdMW310YC7"   # Atmospheric Calm
    ],
    VibeCategory.FOCUS: [
        # Concentration and productivity playlists
        "spotify:playlist:37i9dQZF1DX8NTLI2TtZa6",  # Focus Flow
        "spotify:playlist:37i9dQZF1DWZeKCadgRdKQ"   # Deep Focus
    ],
    VibeCategory.SOCIAL: [
        # Medium energy, social playlists
        "spotify:playlist:37i9dQZF1DX7gIoKXt0gmx",  # Feel Good Mix
        "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"   # Today's Top Hits
    ],
    VibeCategory.NEUTRAL: [
        # General purpose playlists
        "spotify:playlist:37i9dQZF1DX4JAvHpjipBk",  # New Music Mix
        "spotify:playlist:37i9dQZF1DXcF6B6QPhFDv"   # All-Purpose Mix
    ]
}

class VibeAnalyzer:
    def __init__(self, buffer_size: int = 30):
        self.buffer_size = buffer_size
        self.data_buffer: List[Dict] = []
        
    def add_data(self, sensor_data: Dict):
        """Add new sensor data to buffer"""
        self.data_buffer.append(sensor_data)
        if len(self.data_buffer) > self.buffer_size:
            self.data_buffer.pop(0)
            
    def get_averages(self) -> Dict[str, float]:
        """Calculate average values from buffer"""
        if not self.data_buffer:
            return {}
            
        averages = {}
        for key in ['sound_level', 'motion', 'temperature', 'light_level']:
            values = [d[key] for d in self.data_buffer if key in d and d[key] is not None]
            if values:
                averages[key] = sum(values) / len(values)
            else:
                averages[key] = 0
        return averages
        
    def calculate_vibe_scores(self, averages: Dict[str, float]) -> Dict[VibeCategory, float]:
        """Calculate how well current conditions match each vibe category"""
        scores = {}
        
        for category, thresholds in VIBE_THRESHOLDS.items():
            score = 0
            total_factors = 0
            
            # Check each factor if data is available
            if 'sound_level' in averages:
                score += self._calculate_factor_score(
                    averages['sound_level'],
                    thresholds.sound_level[0],
                    thresholds.sound_level[1]
                )
                total_factors += 1
                
            if 'motion' in averages:
                score += self._calculate_factor_score(
                    averages['motion'],
                    thresholds.motion_level[0],
                    thresholds.motion_level[1]
                )
                total_factors += 1
                
            if 'temperature' in averages:
                score += self._calculate_factor_score(
                    averages['temperature'],
                    thresholds.temperature[0],
                    thresholds.temperature[1]
                )
                total_factors += 1
                
            if 'light_level' in averages:
                score += self._calculate_factor_score(
                    averages['light_level'],
                    thresholds.light_level[0],
                    thresholds.light_level[1]
                )
                total_factors += 1
                
            scores[category] = score / total_factors if total_factors > 0 else 0
            
        return scores
        
    def _calculate_factor_score(self, value: float, min_threshold: float, max_threshold: float) -> float:
        """Calculate how well a value fits within thresholds"""
        if value < min_threshold:
            return 1 - (min_threshold - value) / min_threshold
        elif value > max_threshold:
            return 1 - (value - max_threshold) / max_threshold
        else:
            return 1.0
            
    def determine_vibe(self) -> Tuple[VibeCategory, float]:
        """Determine the current vibe category and confidence score"""
        averages = self.get_averages()
        if not averages:
            return VibeCategory.NEUTRAL, 0.0
            
        scores = self.calculate_vibe_scores(averages)
        best_category = max(scores.items(), key=lambda x: x[1])
        
        return best_category[0], best_category[1]
        
    def get_playlist_recommendations(self, vibe: VibeCategory, confidence: float) -> List[str]:
        """
        Get playlist recommendations based on vibe and confidence score
        Returns list of Spotify playlist URIs
        """
        # If confidence is low, return neutral playlists
        if confidence < 0.5:
            return PLAYLIST_MAPPING[VibeCategory.NEUTRAL]
            
        return PLAYLIST_MAPPING.get(vibe, PLAYLIST_MAPPING[VibeCategory.NEUTRAL])
        
    def should_change_music(self, new_vibe: VibeCategory, new_confidence: float, 
                          current_vibe: VibeCategory, min_confidence: float = 0.6,
                          min_duration: int = 300) -> bool:
        """
        Determine if music should be changed based on new vibe detection
        
        Args:
            new_vibe: Newly detected vibe
            new_confidence: Confidence in new vibe detection
            current_vibe: Currently playing vibe
            min_confidence: Minimum confidence threshold for change
            min_duration: Minimum duration (seconds) between changes
            
        Returns:
            bool: True if music should be changed
        """
        # Check if we have enough confidence in the new vibe
        if new_confidence < min_confidence:
            return False
            
        # Check if vibe has actually changed
        if new_vibe == current_vibe:
            return False
            
        # Additional logic could be added here:
        # - Time-based rules (don't change too frequently)
        # - Transition rules (some vibes can transition directly, others need intermediate steps)
        # - User preference rules
        
        return True