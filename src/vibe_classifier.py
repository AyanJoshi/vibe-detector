from config import SPOTIFY_PLAYLISTS

class VibeClassifier:
    def __init__(self):
        # Define vibe categories and their characteristics
        self.vibe_categories = {
            "energetic_party": {
                "brightness": ["bright"],
                "color_temp": ["warm"],
                "activity": ["group_activity", "group_hanging_out"],
                "comfort": ["comfortable", "hot"]
            },
            "relaxed_chill": {
                "brightness": ["dim", "dark"],
                "color_temp": ["warm"],
                "activity": ["relaxing", "solo_activity", "watching_tv", "group_watching_tv"],
                "comfort": ["comfortable"]
            },
            "focused_study": {
                "brightness": ["bright", "dim"],
                "color_temp": ["cool"],
                "activity": ["solo_activity"],
                "comfort": ["comfortable", "dry"]
            },
            "cozy_evening": {
                "brightness": ["dim", "dark"],
                "color_temp": ["warm"],
                "activity": ["relaxing", "watching_tv", "group_watching_tv", "pet_alone"],
                "comfort": ["comfortable", "cold"]
            },
            "dinner_time": {
                "brightness": ["bright", "dim"],
                "color_temp": ["warm"],
                "activity": ["dining_alone", "group_dining"],
                "comfort": ["comfortable"]
            },
            "pet_companion": {
                "brightness": ["dim", "bright"],
                "color_temp": ["warm", "cool"],
                "activity": ["pet_alone"],
                "comfort": ["comfortable", "cold", "hot"]
            }
        }
        
        # Spotify playlist mapping (to be filled with your actual playlist URIs)
        self.spotify_playlists = SPOTIFY_PLAYLISTS
    
    def classify(self, brightness, color_temp, activity, comfort):
        """Classify the room vibe based on features"""
        vibe_scores = {}
        
        for vibe, features in self.vibe_categories.items():
            score = 0
            
            # Check brightness match
            if brightness in features["brightness"]:
                score += 1
                
            # Check color temperature match
            if color_temp in features["color_temp"]:
                score += 1
                
            # Check activity match
            if activity in features["activity"]:
                score += 2  # Activity is a stronger indicator
                
            # Check comfort match
            if comfort in features["comfort"]:
                score += 1
                
            vibe_scores[vibe] = score
        
        # Get the vibe with the highest score
        best_vibe = max(vibe_scores, key=vibe_scores.get)
        best_score = vibe_scores[best_vibe]
        
        # If the best score is too low, default to "relaxed_chill"
        if best_score < 2:
            best_vibe = "relaxed_chill"
            
        return best_vibe, self.spotify_playlists[best_vibe], vibe_scores