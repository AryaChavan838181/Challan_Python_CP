# License Plate Detection & Traffic Violation System

An advanced computer vision system that detects vehicle license plates and monitors for traffic violations. The system uses YOLO object detection and advanced OCR techniques to detect, recognize, and normalize Indian license plates.

## Features

### License Plate Testing Module
- Tests accuracy of license plate detection and recognition
- Uses multiple OCR configurations for optimal recognition
- Normalizes Indian license plates to standard format (XX-00-XX-0000)
- Fixes common OCR errors in state codes (MF→MH, D1→DL, etc.)
- Supports live camera feed for real-time testing
- Creates detailed visualizations of recognized plates

### Traffic Violation Detection System
- Monitors for red light violations using license plate detection
- Directly focuses on license plates crossing the stop line
- Creates comprehensive evidence packages with all violation details
- Deduplicates violations (records each unique plate only once)
- Interactive traffic light simulation for testing
- Real-time violation notifications with overlay
- Advanced visualization and reporting

## Requirements

- Python 3.8+
- OpenCV
- PyTorch
- Ultralytics (YOLO)
- Tesseract OCR
- EasyOCR (optional, for improved accuracy)

### Hardware Requirements
- CUDA-compatible GPU recommended for optimal performance
- 8GB+ RAM
- Webcam or video source

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR:
   - [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt install tesseract-ocr`
   - Mac: `brew install tesseract`

3. Update the Tesseract path in the code if necessary:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Usage

### License Plate Testing

Run the testing module to verify license plate detection accuracy:

```bash
python test_license_plate_ocr.py
```

- Press 's' to save current detection
- Press 'q' to quit
- Results are saved in the "ocr_test_results" folder

### Traffic Violation Detection

Run the violation detection system:

```bash
python traffic_violation_detector.py
```

- Left-click on the traffic light to change its state
- Press 'q' to quit
- Violations are saved in the "violations" folder with detailed evidence
- Each unique license plate is recorded only once

## How It Works

1. **License Plate Detection**: 
   - YOLO model detects license plate locations in the frame
   - Specialized model trained for Indian license plates

2. **Text Recognition**:
   - Multiple OCR techniques used in parallel for best results
   - Advanced confidence scoring for reliability estimation

3. **License Plate Normalization**:
   - State code correction (fixes common OCR errors)
   - Format standardization (XX-00-XX-0000)
   - Character substitution (O→0 in numeric positions)

4. **Violation Detection**:
   - Tracks license plates crossing the stop line during red light
   - Creates comprehensive evidence package with multiple images
   - Maintains database of violations in CSV format

## Evidence Package for Violations

For each violation, the system creates:
- Full scene image showing the violation
- Cropped license plate image
- Enhanced license plate image for better visibility
- Marked image showing violation details
- Text file with complete violation details

## Training Custom Models

Train your own YOLO model for license plate detection:

```bash
python train_yolo_model.py path/to/dataset
```

Prepare your dataset with the following structure:

