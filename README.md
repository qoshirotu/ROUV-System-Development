# 🚀 Underwater Plastic Waste Detection System

An AI-powered underwater monitoring system designed to detect plastic waste in real time using computer vision, embedded systems, and a custom-built Remotely Operated Underwater Vehicle (ROUV).

## 📌 Project Overview

| Item               | Details                                  |
| ------------------ | ---------------------------------------- |
| **Role**           | AI Engineer & Embedded Systems Developer |
| **Duration**       | 6 Months                                 |
| **Domain**         | Computer Vision • Robotics • Embedded AI |
| **Model**          | YOLO11n                                  |
| **Inference Time** | 54 ms                                    |
| **System Latency** | 92.8 ms                                  |

This project integrates an underwater ROUV, Raspberry Pi 4, a YOLO11n object detection model, and a web-based monitoring dashboard to identify plastic waste in aquatic environments.

## 🎯 Objectives

* Detect underwater plastic waste in real time.
* Stream live camera footage from the ROUV.
* Control vehicle movement through a web dashboard.
* Monitor telemetry and system status.
* Reduce Raspberry Pi processing load through distributed AI inference.

## 🏗️ System Architecture

The system uses a distributed processing architecture to maintain stable performance.

```text
Underwater Camera
        │
        ▼
Raspberry Pi 4
Video Streaming + Vehicle Control
        │
WebSocket / UART Communication
        │
        ▼
Remote Backend Server
YOLO11n AI Inference
        │
        ▼
Web Monitoring Dashboard
Detection Results + Controls + Telemetry
```

The Raspberry Pi 4 handles video acquisition, communication, and hardware control. The backend server performs YOLO inference to reduce computational load on the embedded device.

## ✨ Key Features

* Real-time underwater video streaming
* Plastic waste detection using YOLO11n
* Bounding box and confidence visualization
* ROUV movement control
* Ballast control
* DC motor and stepper motor control
* Live telemetry monitoring
* Recording session management
* System statistics and logging
* WebSocket-based communication
* UART communication between embedded components

## 🛠️ Tech Stack

### Artificial Intelligence

* YOLO11n
* ONNX
* OpenCV
* Python

### Embedded Systems

* Raspberry Pi 4
* NodeMCU ESP8266
* UART Communication
* Underwater Camera
* DC Motor Control
* Stepper Motor Control

### Web Technologies

* Flask
* WebSocket
* HTML
* JavaScript

### Robotics

* Remotely Operated Underwater Vehicle
* Motor Driver Integration
* Ballast System Control
* Underwater Camera Integration

## 📂 Project Structure

```text
ROUV-System-Development/
│
├── ui/                         # Web dashboard files
├── best.pt                     # Trained YOLO model
├── detection_server.py         # Backend detection server
├── README.md
└── requirements.txt
```

> Rename `detection_server copy 4.py` to `detection_server.py` so the filename is cleaner and easier to run.

## ⚙️ Installation

Clone this repository:

```bash
git clone https://github.com/qoshirotu/ROUV-System-Development.git
cd ROUV-System-Development
```

Install the required Python libraries:

```bash
pip install ultralytics opencv-python flask flask-socketio onnxruntime
```

## ▶️ Running the System

Start the backend detection server:

```bash
python detection_server.py
```

Then open the dashboard URL shown in the terminal.

Ensure that:

* The YOLO model file `best.pt` is available in the project directory.
* The Raspberry Pi and backend server are connected to the same network.
* Camera streaming and UART configuration match your hardware setup.
* Required serial ports and device addresses are configured correctly.

## 📊 Performance

The system achieved:

| Metric                  |                       Result |
| ----------------------- | ---------------------------: |
| **YOLO Inference Time** |                        54 ms |
| **End-to-End Latency**  |                      92.8 ms |
| **Processing Approach** |     Distributed AI Inference |
| **Deployment Type**     | Edge Device + Remote Backend |

## 🧠 Technical Challenge

Running video streaming, motor control, and AI inference simultaneously on Raspberry Pi 4 reduced frame rate and increased latency.

To address this limitation, the AI inference workload was moved to a remote backend server. This allowed the Raspberry Pi to focus on video acquisition, communication, and ROUV control while maintaining responsive detection performance.

## 🔮 Future Improvements

* Add GPS or underwater positioning support.
* Improve underwater image enhancement.
* Add multiple waste-class detection.
* Integrate cloud-based logging and analytics.
* Add alert notifications for detected plastic waste.
* Optimize inference using TensorRT or edge accelerators.
* Deploy the dashboard through a cloud server.

## 👤 Author

**Qoshirotu Thorfi**
AI Engineer • Embedded Systems Developer • Computer Vision Enthusiast
