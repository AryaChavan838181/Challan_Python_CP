# 🚦 Automated Traffic Light Plate Detection & Boom Barrier System

## Overview

This project is a **real-time, AI-powered vehicle license plate detection and violation logging system** designed for smart traffic management at intersections, tolls, or restricted areas. It integrates computer vision, OCR, and Arduino-based hardware to detect vehicles, recognize license plates, log violations, and control a physical boom barrier—all with robust fallback mechanisms and API/email integration.

---

## Features

- **Real-time camera feed** with live overlays and status indicators
- **YOLOv11 deep learning** for accurate license plate detection
- **Haar Cascade fallback** for detection robustness
- **EasyOCR & Tesseract** for high-accuracy license plate text extraction
- **Ultrasonic sensor via Arduino** for vehicle presence detection
- **Automated boom barrier control** (via Arduino & servo)
- **Violation logging** with cooldown to prevent duplicates
- **Automatic violation image saving** for evidence
- **Email notifications** with payment links (Cashfree integration)
- **API integration** for backend logging and analytics
- **Keyboard simulation mode** for testing without hardware
- **Movable detection line** (drag with mouse)
- **Multi-threaded for smooth, real-time performance**

---

## System Architecture

1. **Camera** captures live video.
2. **Arduino** (with ultrasonic sensor) detects vehicle presence and controls the boom barrier.
3. **YOLO/Haar** detects license plates in the video frames.
4. **EasyOCR/Tesseract** extracts text from detected plates.
5. **Violation logic** checks if a vehicle is present and if a new violation should be logged.
6. **API/Email** sends notifications and logs events.
7. **Boom barrier** is opened/closed automatically for detected vehicles.

---

## How It Works

1. **Vehicle Detection:**  
   Arduino with an ultrasonic sensor detects when a vehicle is present (distance < 5cm) and signals the Python system.
2. **Frame Processing:**  
   When a vehicle is detected, the camera frame is processed for license plate detection using YOLO. If YOLO fails, Haar cascade is used as a fallback.
3. **Plate Cropping & Enhancement:**  
   Detected plate regions are cropped and enhanced for OCR.
4. **OCR:**  
   EasyOCR is used to extract the license plate number. If it fails, Tesseract is used as a backup.
5. **Violation Logging:**  
   If a valid plate is detected and not in cooldown, the violation is logged, an image is saved, and an email/API notification is sent.
6. **Boom Barrier Control:**  
   The recognized plate is sent to Arduino, which opens the boom barrier, waits, and then closes it.
7. **User Interface:**  
   The system displays the live feed with overlays, detection results, and status info. The detection line can be moved with the mouse.

---

## Hardware Requirements

- **Camera** (USB webcam or IP camera)
- **Arduino** (Uno/Nano) with:
  - Ultrasonic sensor (for vehicle detection)
  - Servo motor (for boom barrier)
  - LEDs (for status indication)
- **Computer** (Windows/Linux, with Python 3.x and a GPU for best YOLO performance)

---

## Getting Started

1. **Clone the repository** and install dependencies:
    ```bash
    pip install opencv-python numpy easyocr pytesseract ultralytics pyserial
    ```

2. **Connect your Arduino** (with ultrasonic sensor and servo) to your PC.

3. **Configure serial port** in the Python script (default: `COM17`).

4. **Place YOLO model weights** and Haar cascade XML in the specified paths.

5. **Run the main script:**
    ```bash
    python Final_detector.py
    ```

6. **Controls:**
    - `'q'`: Quit application
    - `'c'`: Clear violation history
    - Mouse drag: Move detection line
    - `'r'`/`'g'`: Simulate vehicle red/green light (keyboard mode)

---

## Project Structure

```
.
├── Arduino/
│   └── [Arduino code for sensor & boom]
├── models/
│   └── [YOLO weights]
├── violations/
│   └── [Saved violation images]
├── Final_detector.py
├── api_manager.py
└── ...
```

---

## Customization

- **Detection line position:** Drag with mouse in the UI.
- **Cooldown time:** Adjust `self.violation_timeout` in the code.
- **API/email logic:** Modify `api_manager.py` as needed.
- **Camera index:** Change in `start_camera()` if needed.

---

## Troubleshooting

- **YOLO not available:** Make sure model weights are in the correct path and dependencies are installed.
- **Arduino not detected:** Check COM port and wiring.
- **No camera:** Ensure your camera is connected and accessible.
- **OCR errors:** Try cleaning the camera lens or improving lighting.

---
