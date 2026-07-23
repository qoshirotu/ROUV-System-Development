# 🚀 Underwater Plastic Waste Detection System

An AI-powered underwater monitoring system for real-time plastic waste detection using computer vision, embedded systems, and a custom-built Remotely Operated Underwater Vehicle (ROUV).

---

# 📌 Project Overview

| Item | Details |
|------|---------|
| **Role** | AI Engineer & Embedded Systems Developer |
| **Duration** | 6 Months |
| **Domain** | Computer Vision • Robotics • Embedded AI |
| **Model** | YOLO11n |
| **Inference Time** | 54 ms |
| **System Latency** | 92.8 ms |

This project integrates a Raspberry Pi 4, an ESP8266 microcontroller, a YOLO11n object detection model, and a web-based monitoring dashboard to perform real-time underwater plastic waste detection through remote AI inference.

---

# 🎯 Objectives

- Detect underwater plastic waste in real time.
- Stream live underwater video from the ROUV.
- Perform AI inference on a remote laptop.
- Control the ROUV through a web-based dashboard.
- Monitor telemetry and detection results simultaneously.

---

# 🏗️ System Architecture

```text
Underwater Camera
        │
        ▼
 Raspberry Pi 4
(Video Streaming & Vehicle Control)
        │
 WebSocket / UART
        │
        ▼
 Laptop Backend Server
 (YOLO11n Inference)
        │
        ▼
 Web Dashboard
 Detection • Telemetry • Control
```

The Raspberry Pi captures video, controls the ROUV hardware, and transmits camera frames to the laptop. The laptop performs real-time YOLO11n inference and hosts the monitoring dashboard for visualization and control.

---

# ✨ Features

- Real-time underwater video streaming
- YOLO11n plastic waste detection
- Remote AI inference
- Web-based monitoring dashboard
- Thruster control
- Ballast control
- ESP8266 serial communication
- Live telemetry monitoring
- Detection confidence visualization
- Session recording
- WebSocket communication

---

# 🛠 Hardware Requirements

- Laptop (Windows 10/11)
- Raspberry Pi 4 Model B
- ESP8266 NodeMCU
- Underwater Camera
- USB Cable
- Local Wi-Fi Network

---

# 💻 Software Requirements

- Python 3.10 or newer
- Arduino IDE
- Thonny IDE (recommended)
- Google Chrome or Microsoft Edge

---

# 📂 Project Structure

```text
ROUV_Plastic_Detection/
│
├── best.pt
├── detection_server.py
├── stream_client.py
├── esp8266_rouv_serial.ino
├── index.html
├── requirements.txt
├── install_requirements.bat
├── start_server.bat
└── README.md
```

---

# ⚙️ Installation Guide

## 1. Laptop Setup

### Step 1 — Download the Project

Download the ZIP file and extract it to any folder on your computer.

---

### Step 2 — Install Python Dependencies

Run:

```bash
install_requirements.bat
```

or manually install all required libraries using:

```bash
pip install -r requirements.txt
```

Wait until the installation process is completed.

---

### Step 3 — Start the Detection Server

Run:

```bash
start_server.bat
```

The program will automatically:

- Load the YOLO11n model.
- Start the backend server.
- Launch the web dashboard in your default web browser.

> **Important:** Keep the Command Prompt window open while the system is running.

---

## 2. Raspberry Pi Setup

### Step 1 — Configure the Server IP Address

Open:

```python
stream_client.py
```

using **Thonny** or any Python IDE.

Locate the server IP configuration and replace it with your laptop's local IP address.

> **Note:** The Raspberry Pi and the laptop must be connected to the same local network.

---

### Step 2 — Run the Stream Client

Execute:

```bash
python3 stream_client.py
```

The Raspberry Pi will start capturing camera frames and stream them to the laptop for real-time object detection.

---

## 3. ESP8266 Setup

### Step 1 — Upload the Firmware

1. Connect the ESP8266 to your laptop using a USB cable.
2. Open **Arduino IDE**.
3. Open:

```text
esp8266_rouv_serial.ino
```

4. Select the correct board and COM port.
5. Click **Upload** and wait until the upload process finishes.

---

### Step 2 — Connect the ESP8266 to the Raspberry Pi

After the upload is complete:

1. Disconnect the ESP8266 from the laptop.
2. Connect it to the Raspberry Pi via USB.

The ESP8266 is now ready to communicate with the Raspberry Pi for motor control and command execution.

---

# ▶ System Startup Sequence

To ensure proper operation, start the system in the following order:

1. Upload the firmware to the ESP8266 (only required once unless the firmware is updated).
2. Connect the ESP8266 to the Raspberry Pi.
3. Run `stream_client.py` on the Raspberry Pi.
4. Run `start_server.bat` on the laptop.
5. Wait until the web dashboard opens automatically.
6. The system is now ready for real-time underwater plastic waste detection.

---

# 📄 Project Files

| File | Description |
|------|-------------|
| **best.pt** | Trained YOLO11n model for plastic waste detection. |
| **detection_server.py** | Backend server responsible for YOLO inference and communication with the dashboard. |
| **stream_client.py** | Raspberry Pi client that captures and streams camera frames to the laptop. |
| **esp8266_rouv_serial.ino** | ESP8266 firmware for motor control and serial communication. |
| **index.html** | Web-based monitoring and control dashboard. |
| **requirements.txt** | List of required Python packages. |
| **install_requirements.bat** | Automatically installs all required Python libraries. |
| **start_server.bat** | Starts the backend server and launches the dashboard. |

---

# 📊 Performance

| Metric | Result |
|---------|-------:|
| **YOLO11n Inference Time** | 54 ms |
| **End-to-End System Latency** | 92.8 ms |
| **Deployment Strategy** | Remote AI Inference |
| **Architecture** | Raspberry Pi + Laptop |

---

# ⚠ Important Notes

- Ensure the laptop and Raspberry Pi are connected to the **same local network**.
- Keep the backend server running while operating the dashboard.
- Do not close the Command Prompt window during system operation.
- Ensure `best.pt` remains in the project directory.

---

# 🔮 Future Improvements

- Multi-class plastic waste detection
- Underwater image enhancement
- TensorRT optimization
- Cloud deployment
- GPS or underwater localization support
- Automatic detection notifications

---

# 👤 Author

**Qoshirotu Thorfi Gibran Yusuf**

Bachelor of Physics — Universitas Negeri Jakarta

Computer Vision • Artificial Intelligence • Embedded Systems • Robotics
