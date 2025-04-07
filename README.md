# Vibe Detector (work-in-progress)

A smart room atmosphere detection system that plays appropriate music through Spotify based on the room's vibe. Built using Raspberry Pi 5 and various sensors to detect environmental conditions.

## Features
- Real-time environment monitoring (temperature, humidity, motion, sound)
- Physical controls using rotary encoders for volume and track control
- Spotify integration for music playback
- Automated vibe detection and music selection

---

**Vibe Detector: End-to-End Technical Summary**

**1. Project Goal:**
To automatically sense the atmosphere (vibe) of a room using environmental sensors and computer vision, and then curate an appropriate musical experience via Spotify. Simultaneously, log all relevant metrics to InfluxDB for real-time monitoring and historical analysis using Grafana.

**2. Data Acquisition (Raspberry Pi - *Implied Setup*):**
*   A Raspberry Pi (likely running a separate publisher script, not shown in the provided files) collects raw data from connected hardware:
    *   **DHT22 Sensor:** Measures ambient Temperature and Humidity.
    *   **Webcam (e.g., Logitech C920x):** Captures video frames of the room.
    *   *(Other sensors like MPU-6050/MAX4466 might be involved based on README but aren't directly used in the provided processing code for vibe classification and are yet to be implemented, sorry for the wait).*

**3. Data Transmission (ZeroMQ):**
*   The Raspberry Pi acts as a ZeroMQ **Publisher**.
*   It sends two types of data over the network to the processing machine (where `main_new.py` runs):
    *   **Sensor Data:** JSON strings containing `temperature`, `humidity`, and `timestamp` are published to `tcp://<pi_ip>:<sensor_port>` (e.g., 5555).
    *   **Video Data:** Encoded video frames (e.g., JPEG) along with metadata (potentially timestamp, frame number) are published to `tcp://<pi_ip>:<video_port>` (e.g., 5556).
*   The `main_new.py` script acts as a ZeroMQ **Subscriber**, connecting to these endpoints and listening for incoming data.

**4. Data Processing & Feature Extraction (`main_new.py` and Analyzers):**
This is the core logic running on the processing machine. `main_new.py` orchestrates receiving data and passing it to specialized analyzers.

*   **a. Receiving Data:**
    *   `receive_sensor_data()`: Waits for and parses the JSON sensor data from ZeroMQ. Stores the latest values.
    *   `receive_frame()`: Waits for and decodes the video frame data from ZeroMQ.

*   **b. Sensor Analysis (`SensorAnalyzer`):**
    *   **Input:** Raw `temperature` and `humidity` from the latest sensor data.
    *   **Processing:** Maintains a short history (`deque`) of recent readings to smooth out noise. Calculates the average temperature and humidity over this history.
    *   **Feature Extraction (`_determine_comfort`):** Based on predefined thresholds for average temperature and humidity (e.g., Temp 20-25°C AND Humidity 30-60% = "comfortable"), it categorizes the environment into comfort levels like "comfortable", "cold", "hot", "dry", "humid", "hot_and_humid".
    *   **Output:** `comfort` (string).

*   **c. Frame Analysis (`FrameAnalyzer` & `ActivityDetector`):**
    *   **Input:** The decoded video `frame`.
    *   **Brightness (`FrameAnalyzer.analyze_brightness`):** Converts frame to grayscale, calculates the mean pixel intensity. Categorizes based on thresholds into "dark", "dim", or "bright". Stores result in history (`deque`).
    *   **Color Temperature (`FrameAnalyzer.analyze_color_temperature`):** Converts frame to HSV color space. Calculates the ratio of "warm" pixels (reds/oranges/yellows - specific Hue ranges) vs "cool" pixels (greens/blues - other Hue ranges). Categorizes as "warm" or "cool" based on the ratio. Stores result in history (`deque`).
    *   **Activity Detection (`ActivityDetector.detect`):**
        *   Uses a pre-trained MobileNet SSD model via OpenCV's DNN module to perform object detection on the frame.
        *   Identifies common objects (`person`, `sofa`, `tvmonitor`, `diningtable`, `dog`, `cat`, etc.) with a confidence above a threshold (`0.5`).
        *   **Feature Extraction (`_interpret_activity`):** Applies rules based on the *combination* of detected objects. For example:
            *   No objects -> "empty"
            *   `person` count = 1, `sofa` detected -> "relaxing"
            *   `person` count > 1, `diningtable` detected -> "group_dining"
            *   No `person`, but `dog` or `cat` detected -> "pet_alone"
        *   **Output:** `activity` (string), `detected_objects` (list). The `activity` string is stored in `FrameAnalyzer.activity_history` (`deque`).

*   **d. Dominant Feature Consolidation (`FrameAnalyzer.get_dominant_features`):**
    *   To prevent decisions based on momentary glitches, this step looks at the recent history (`deque`) for brightness, color temperature, and activity.
    *   It determines the *most frequent* value (mode) for each feature within its history window.
    *   **Output:** `dominant_brightness`, `dominant_color_temp`, `dominant_activity`. These represent the stable, prevailing conditions over the last few analysis cycles.

**5. Vibe Classification (`VibeClassifier.classify`):**
*   **Input:** The consolidated features: `dominant_brightness`, `dominant_color_temp`, `dominant_activity`, and the `comfort` level from the sensor analysis.
*   **Logic:**
    *   Compares the input features against predefined profiles stored in `vibe_categories`. Each profile defines the typical characteristics of a vibe (e.g., "energetic_party" expects "bright" brightness, "warm" color, "group_activity", etc.).
    *   A scoring system awards points for each matching feature between the current state and a vibe profile (activity match is weighted higher).
    *   The vibe profile with the highest total score is selected as the `best_vibe`.
    *   A fallback vibe (e.g., "relaxed_chill") is chosen if no profile scores significantly high. I thought people just liked relaxed_chill music no matter what situation :D
*   **Output:** `best_vibe` (string), `playlist_uri` (corresponding Spotify playlist URI fetched from `config.py`), `vibe_scores` (for potential debugging in case we need to analyze why certain vibe is misplaced).

**6. Action & Output:**

*   **a. Spotify Control:**
    *   If the `best_vibe` changes from the previously detected vibe (and enough time has passed - `min_vibe_duration`), the system interacts with the Spotify API via `spotipy`.
    *   It finds an active Spotify device and uses `sp.start_playback` to play the `playlist_uri` associated with the new vibe, often starting at a random track.

*   **b. Metrics Logging (`MetricsSender.send_metrics`):**
    *   Key data points (raw `temperature`, raw `humidity`, `dominant_brightness`, `dominant_color_temp`, `dominant_activity`, `best_vibe`) are packaged into an InfluxDB Point.
    *   This point is written to the `vibe_detector` bucket under the `room_metrics` measurement in your InfluxDB instance (`http://localhost:8086`).

**7. Monitoring & Visualization (InfluxDB & Grafana):**
*   **InfluxDB:** Acts as the time-series database, storing the history of all metrics sent by `MetricsSender`.
*   **Grafana:** Connects to InfluxDB as a data source. Dashboards are built using panels that query InfluxDB (using the Flux language) to visualize:
    *   Current state (Stat panels for temp, humidity, activity, vibe).
    *   Trends over time (Time Series graphs for temp/humidity).
    *   State changes (State Timeline for brightness, color temp, activity, vibe).
    *   Raw data logs (Table panel).

**In Essence:** The system continuously senses the environment -> extracts key features (comfort, light, activity) -> uses these features to classify the room's current "vibe" based on predefined profiles -> triggers corresponding music on Spotify and logs the data for visualization. The use of historical smoothing (deques and dominant features) helps ensure stability in the classification.

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

4. Run publisher python file in Raspberry Pi, run the subscriber file in your local machine (zmq) [This is not vibe-detection, merely testing zmq]

5. Run the main_new.py in src while ensuring you have grafana and influxdb setup beforehand

## License
MIT
