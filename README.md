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

# ROUV Plastic Waste Detection System

## Installation and User Guide

This guide explains how to set up and run the Real-Time Plastic Waste Detection System on the laptop, Raspberry Pi, and ESP8266.

---

# 1. Laptop Setup

### Step 1. Download the Project

Download the ZIP file and extract it to any folder on your computer.

---

### Step 2. Install the Required Python Libraries

Double-click **`install_requirements.bat`**.

The installer will automatically download and install all required Python packages listed in `requirements.txt`.

Please wait until the installation is completed before proceeding.

---

### Step 3. Start the Detection Server

Double-click **`start_server.bat`**.

This will:

* Launch the detection server.
* Open a Command Prompt window.
* Load the YOLO model.
* Automatically open the web-based user interface (HTML) in your default browser.

Keep the Command Prompt window open while using the system.

---

# 2. Raspberry Pi Setup

### Step 1. Configure the Stream Client

Open **`stream_client.py`** using **Thonny** or any Python IDE available on the Raspberry Pi.

Locate the server IP address in the code and replace it with your laptop's local IP address.

> **Important:**
> Make sure that the Raspberry Pi and the laptop are connected to the same local network.

---

### Step 2. Run the Program

Execute **`stream_client.py`**.

The Raspberry Pi will start capturing video from the camera and transmit the video stream to the laptop for real-time object detection.

---

# 3. ESP8266 Setup

### Step 1. Upload the Firmware

Connect the ESP8266 module to the laptop using a USB cable.

Open **Arduino IDE**, then open the file:

**`esp8266_rouv_serial.ino`**

Select the correct board and COM port, then click **Upload**.

Wait until the upload process completes successfully.

---

### Step 2. Connect to Raspberry Pi

Disconnect the ESP8266 from the laptop.

Reconnect the ESP8266 to the Raspberry Pi using a USB cable.

The ESP8266 is now ready to communicate with the Raspberry Pi for motor control and system commands.

---

# System Startup Sequence

For proper operation, start the system in the following order:

1. Upload the firmware to the ESP8266 (only required once unless the firmware is updated).
2. Connect the ESP8266 to the Raspberry Pi.
3. Run **`stream_client.py`** on the Raspberry Pi.
4. Run **`start_server.bat`** on the laptop.
5. Wait for the web interface to open automatically.
6. The system is now ready for real-time underwater plastic waste detection.

---

# Project Files

| File                       | Description                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------ |
| `best.pt`                  | Trained YOLO11n model used for object detection.                                                 |
| `detection_server.py`      | Backend server that performs real-time object detection and communicates with the web interface. |
| `stream_client.py`         | Raspberry Pi client that captures camera frames and sends them to the laptop.                    |
| `esp8266_rouv_serial.ino`  | ESP8266 firmware for communication and ROUV control.                                             |
| `index.html`               | Web-based control dashboard and monitoring interface.                                            |
| `requirements.txt`         | List of required Python libraries.                                                               |
| `install_requirements.bat` | Automatically installs all required Python packages.                                             |
| `start_server.bat`         | Starts the detection server and launches the web interface.                                      |


## 📊 Performance

The system achieved:

| Metric                  |                       Result |
| ----------------------- | ---------------------------: |
| **YOLO Inference Time** |                        54 ms |
| **End-to-End Latency**  |                      92.8 ms |
| **Processing Approach** |     Distributed AI Inference |
| **Deployment Type**     | Edge Device + Remote Backend |


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
