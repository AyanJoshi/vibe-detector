import cv2
import numpy as np

class ActivityDetector:
    def __init__(self):
        # Load pre-trained MobileNet SSD
        self.net = cv2.dnn.readNetFromCaffe(
            'models/MobileNetSSD_deploy.prototxt',
            'models/MobileNetSSD_deploy.caffemodel'
        )
        
        # Classes that MobileNet was trained on
        self.classes = ["background", "aeroplane", "bicycle", "bird", "boat", 
                        "bottle", "bus", "car", "cat", "chair", "cow", 
                        "diningtable", "dog", "horse", "motorbike", "person", 
                        "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
        
        # Detection confidence threshold
        self.confidence_threshold = 0.5
    
    def detect(self, frame):
        """Detect objects in the frame and return activity context"""
        # Get frame dimensions
        (h, w) = frame.shape[:2]
        
        # Create a blob from the frame
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            0.007843, 
            (300, 300), 
            127.5
        )
        
        # Pass the blob through the network
        self.net.setInput(blob)
        detections = self.net.forward()
        
        # Process detections
        detected_objects = []
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.confidence_threshold:
                class_id = int(detections[0, 0, i, 1])
                detected_objects.append(self.classes[class_id])
        
        # Interpret the detected objects for activity
        activity = self._interpret_activity(detected_objects)
        return activity, detected_objects
    
    def _interpret_activity(self, detected_objects):
        """Interpret detected objects to determine room activity"""
        if not detected_objects:
            return "empty"
            
        # Count people
        person_count = detected_objects.count("person")
        
        # Look for specific objects that give context
        has_diningtable = "diningtable" in detected_objects
        has_sofa = "sofa" in detected_objects
        has_tvmonitor = "tvmonitor" in detected_objects
        has_dog_or_cat = "dog" in detected_objects or "cat" in detected_objects
        
        # Activity interpretation logic
        if person_count == 0 and has_dog_or_cat:
            return "pet_alone"
        elif person_count == 0:
            return "empty"
        elif person_count == 1:
            if has_sofa and has_tvmonitor:
                return "watching_tv"
            elif has_diningtable:
                return "dining_alone"
            elif has_sofa:
                return "relaxing"
            else:
                return "solo_activity"
        elif person_count > 1:
            if has_diningtable:
                return "group_dining"
            elif has_sofa and has_tvmonitor:
                return "group_watching_tv"
            elif has_sofa:
                return "group_hanging_out"
            else:
                return "group_activity"
                
        return "unknown"