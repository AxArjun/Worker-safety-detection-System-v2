# 🦺 Worker Safety Detection System v2

> AI-powered workplace safety monitoring system that detects safety violations in real time using Computer Vision and Deep Learning.

---

# 🚀 Overview

Worker Safety Detection System v2 is an intelligent computer vision application designed to improve workplace safety by automatically monitoring workers and identifying safety compliance violations.

Using object detection models and real-time video analysis, the system can detect whether workers are wearing mandatory safety equipment such as helmets, safety vests, and personal protective equipment (PPE).

The platform helps reduce workplace accidents, improve compliance, and support proactive industrial safety management.

---

# 🎯 Problem Statement

Industrial environments such as:

* Construction sites
* Manufacturing plants
* Warehouses
* Mining facilities
* Production units

often face safety challenges due to:

* Missing PPE equipment
* Human monitoring limitations
* Delayed violation reporting
* Large-scale workforce supervision

Manual safety inspection is difficult to scale and prone to human error.

This project automates safety monitoring using Artificial Intelligence and Computer Vision.

---

# 💡 Key Features

## 🦺 PPE Detection

Detects worker safety equipment such as:

* Safety helmets
* Safety vests
* Protective gear

---

## 🎥 Real-Time Monitoring

Processes:

* Live camera feeds
* Video streams
* Recorded footage

for continuous workplace monitoring.

---

## ⚠️ Safety Violation Detection

Automatically identifies:

* Missing helmets
* Missing safety equipment
* Non-compliant workers

---

## 📊 Visual Detection Output

Displays:

* Bounding boxes
* Detection labels
* Confidence scores

for detected objects and workers.

---

## 🤖 AI-Based Automation

Reduces dependency on manual inspection through automated safety surveillance.

---

# 🏗️ System Architecture

```text
                 ┌────────────────────┐
                 │ CCTV / Camera Feed │
                 └──────────┬─────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │ Frame Processing   │
                 │ Image Extraction   │
                 └──────────┬─────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │ YOLO Detection     │
                 │ Object Recognition │
                 └──────────┬─────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │ PPE Validation     │
                 │ Safety Analysis    │
                 └──────────┬─────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │ Violation Detection│
                 └──────────┬─────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │ Alert & Monitoring │
                 └────────────────────┘
```

---

# 🧠 AI Pipeline

```text
Video Feed
    │
    ▼
Frame Capture
    │
    ▼
Object Detection Model
    │
    ▼
Worker Detection
    │
    ▼
PPE Classification
    │
    ▼
Safety Compliance Check
    │
    ▼
Violation Detection
    │
    ▼
Visual Output & Alerts
```

---

# 🛠️ Technology Stack

## Programming Language

* Python

## Computer Vision

* OpenCV

## Deep Learning

* YOLO
* Object Detection Models

## AI / Machine Learning

* Computer Vision
* Real-Time Detection

## Development Tools

* VS Code
* Git
* GitHub

---

# 📂 Project Structure

```bash
Worker-safety-detection-System-v2/
│
├── models/
├── datasets/
├── outputs/
├── assets/
├── detection/
├── main.py
├── requirements.txt
└── README.md
```

*(Update structure according to your actual repository.)*

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/AxArjun/Worker-safety-detection-System-v2.git
```

## Navigate to Project

```bash
cd Worker-safety-detection-System-v2
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Application

```bash
python main.py
```

---

# 🎯 Detection Capabilities

| Feature                      | Supported |
| ---------------------------- | --------- |
| Worker Detection             | ✅         |
| Helmet Detection             | ✅         |
| PPE Monitoring               | ✅         |
| Real-Time Processing         | ✅         |
| Video Analysis               | ✅         |
| Safety Compliance Monitoring | ✅         |

---

# 🌍 Real-World Applications

### Construction Sites

Monitor helmet compliance and worker safety.

### Manufacturing Plants

Automate PPE inspections.

### Industrial Facilities

Improve operational safety standards.

### Warehouses

Ensure workforce compliance with safety regulations.

### Smart Surveillance Systems

Integrate AI-powered safety monitoring into existing CCTV infrastructure.

---

# 📈 Future Enhancements

* Multi-Camera Monitoring
* Safety Violation Dashboard
* SMS / Email Alerts
* Worker Tracking
* Face Recognition Integration
* Cloud Deployment
* Edge AI Deployment
* Incident Logging System
* Safety Analytics Dashboard
* Mobile Monitoring Application

---

# 📊 Engineering Highlights

* Real-Time Computer Vision Pipeline
* YOLO-Based Object Detection
* PPE Compliance Monitoring
* Automated Safety Inspection
* Scalable Industrial Use Cases
* AI-Powered Workplace Surveillance

---

# 🎓 Learning Outcomes

This project demonstrates:

* Computer Vision
* Deep Learning
* Object Detection
* Real-Time Video Processing
* Industrial AI Applications
* Workplace Safety Automation

---

# 👨‍💻 Author

**Arjun R K**


GitHub:
https://github.com/AxArjun

---

# 📜 License

Licensed under the MIT License.
