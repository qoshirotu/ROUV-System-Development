🚀 Underwater Plastic Waste Detection

Role: AI Engineer & Embedded Systems Developer

Duration: 6 Months

Domain: Computer Vision • Robotics • Embedded AI

Tech Stack: Python, YOLO11n, OpenCV, Raspberry Pi, Flask, WebSocket

Outcome: Real-time AI Detection with 54 ms inference time and 92.8 ms latency.

Overview

This project focused on developing an intelligent underwater monitoring system capable of detecting plastic waste in real time using Artificial Intelligence and computer vision. The solution integrates a custom-built Remotely Operated Underwater Vehicle (ROUV), embedded systems, and a YOLO11n object detection model to assist environmental monitoring in aquatic environments.

To overcome the computational limitations of embedded hardware, the system implements a distributed processing architecture where the Raspberry Pi 4 handles video acquisition and communication, while AI inference is executed on a remote backend server. The result is a responsive, low-latency underwater detection system suitable for real-time operation.

System Architecture

One of the major challenges encountered during development was the limited processing capability of the Raspberry Pi 4. Running video streaming, motor control, and YOLO inference simultaneously resulted in reduced frame rates and increased latency.

To solve this problem, I redesigned the architecture using a distributed processing approach. The Raspberry Pi acts as the onboard controller responsible for video acquisition and communication, while a separate laptop performs the computationally intensive YOLO inference. The two devices communicate through WebSocket and UART protocols, allowing the embedded system to focus on control tasks while maintaining stable AI performance.



Web-Based Monitoring Dashboard

The dashboard provides several real-time features, including:

Live underwater video streaming

Plastic waste detection visualization

Vehicle movement control

Ballast control

Recording session management

Telemetry monitoring

System statistics and logging



Tools Used

Artificial Intelligence

YOLO11n

ONNX

OpenCV

Python

Embedded Systems

Raspberry Pi 4

NodeMCU ESP8266

UART Communication

Web Technologies

WebSocket

HTML

JavaScript

Flask

Robotics

Remotely Operated Underwater Vehicle (ROUV)

DC Motor Control

Stepper Motor Control

Underwater Camera Integration
