# Vibe Detector (work-in-progress)

A smart room atmosphere detection system that plays appropriate music through Spotify based on the room's vibe. Built using Raspberry Pi 5 and various sensors to detect environmental conditions.

## Features
- Real-time environment monitoring (temperature, humidity, motion, sound)
- Physical controls using rotary encoders for volume and track control
- Spotify integration for music playback
- Automated vibe detection and music selection

## Hardware Requirements
- Raspberry Pi 5 (8GB) with CanaKit Starter Kit PRO
- MPU-6050 (Accelerometer/Gyroscope)
- MAX4466 Microphone Amplifier
- DHT22 Temperature/Humidity Sensor
- Logitech C920x Webcam
- Amazon Basics Stereo Speakers
- 2x KY-040 Rotary Encoders
- Breadboard and jumper wires

## Setup
1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Configure Spotify credentials in config/spotify_credentials.py

3. Connect hardware components according to pin configuration in documentation

4. Run publisher python file in Raspberry Pi, run the subscriber file in your local machine (zmq)

## License
MIT
