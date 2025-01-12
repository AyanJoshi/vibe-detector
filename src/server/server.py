"""
Main server module for vibe detector
Handles WebSocket connections and data processing
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Dict, List
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store connected clients
connected_clients: Dict[str, WebSocket] = {}

# Sensor data buffer
sensor_buffer: List[dict] = []
BUFFER_SIZE = 30  # Store 30 seconds of data

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    connected_clients[client_id] = websocket
    logger.info(f"Client {client_id} connected")
    
    try:
        while True:
            # Receive sensor data
            data = await websocket.receive_text()
            sensor_data = json.loads(data)
            
            # Add timestamp
            sensor_data['timestamp'] = datetime.now().isoformat()
            
            # Process incoming data
            processed_data = process_sensor_data(sensor_data)
            
            # Update buffer
            update_sensor_buffer(processed_data)
            
            # Analyze vibe if enough data
            if len(sensor_buffer) >= BUFFER_SIZE:
                vibe = analyze_vibe()
                # Send vibe analysis result back to client
                await websocket.send_json({
                    'type': 'vibe_update',
                    'vibe': vibe
                })
                
    except Exception as e:
        logger.error(f"Error with client {client_id}: {e}")
    finally:
        # Clean up on disconnect
        if client_id in connected_clients:
            del connected_clients[client_id]
        logger.info(f"Client {client_id} disconnected")

def process_sensor_data(data: dict) -> dict:
    """Process incoming sensor data"""
    processed = {
        'timestamp': data['timestamp'],
        'temperature': data.get('temperature'),
        'humidity': data.get('humidity'),
        'motion': data.get('motion'),
        'sound_level': data.get('sound_level'),
        'light_level': data.get('light_level'),
        'activity_level': data.get('activity_level')
    }
    return processed

def update_sensor_buffer(data: dict):
    """Update the sensor data buffer"""
    sensor_buffer.append(data)
    if len(sensor_buffer) > BUFFER_SIZE:
        sensor_buffer.pop(0)

def analyze_vibe() -> str:
    """Analyze sensor data to determine the room's vibe"""
    # Calculate averages from buffer
    avg_temp = sum(d['temperature'] for d in sensor_buffer if d['temperature']) / len(sensor_buffer)
    avg_sound = sum(d['sound_level'] for d in sensor_buffer if d['sound_level']) / len(sensor_buffer)
    avg_motion = sum(d['motion'] for d in sensor_buffer if d['motion']) / len(sensor_buffer)
    avg_light = sum(d['light_level'] for d in sensor_buffer if d['light_level']) / len(sensor_buffer)
    
    # Simple vibe classification logic (to be expanded)
    if avg_sound > 70 and avg_motion > 0.7:  # High activity
        return 'party'
    elif avg_sound < 30 and avg_motion < 0.3:  # Low activity
        return 'chill'
    elif 30 <= avg_sound <= 50 and 0.3 <= avg_motion <= 0.5:  # Medium activity
        return 'focus'
    else:
        return 'neutral'

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
