import cv2
import numpy as np
import os
import datetime
import threading
import time
import pandas as pd
import pytesseract
import re
from license_plate_detector import enhance_plate_for_ocr
import torch
from ultralytics import YOLO

# Update the Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class TrafficLightSimulator:
    def __init__(self):
        # Initialize traffic light (0: Red, 1: Yellow, 2: Green)
        self.light_status = 0
        self.colors = [(0, 0, 255), (0, 255, 255), (0, 255, 0)]  # BGR format
        self.window_name = "Traffic Light"
        self.setup_window()
        
    def setup_window(self):
        # Create a window for the traffic light
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 100, 300)
        
        # Set up mouse callback for changing traffic light
        cv2.setMouseCallback(self.window_name, self.change_light)
    
    def change_light(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            height = 300
            if y < height / 3:
                self.light_status = 0  # Red
            elif y < 2 * height / 3:
                self.light_status = 1  # Yellow
            else:
                self.light_status = 2  # Green
    
    def get_light_status(self):
        return self.light_status
    
    def update_display(self):
        # Create a blank image for the traffic light
        img = np.zeros((300, 100, 3), dtype=np.uint8)
        
        # Draw the three circles (red, yellow, green)
        centers = [(50, 50), (50, 150), (50, 250)]
        for i, center in enumerate(centers):
            if i == self.light_status:
                cv2.circle(img, center, 40, self.colors[i], -1)
            else:
                cv2.circle(img, center, 40, (64, 64, 64), -1)
                
        # Add text indicators
        light_names = ["RED", "YELLOW", "GREEN"]
        cv2.putText(img, light_names[self.light_status], (10, 280), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Display the image
        cv2.imshow(self.window_name, img)
        cv2.waitKey(1)  # Add this to process the window events
    
    def run_light_cycle(self):
        # Auto-cycle through lights
        while True:
            self.light_status = 0  # Red
            self.update_display()
            time.sleep(5)
            
            self.light_status = 1  # Yellow
            self.update_display()
            time.sleep(2)
            
            self.light_status = 2  # Green
            self.update_display()
            time.sleep(5)


class YOLOLicensePlateDetector:
    """License plate detector using YOLO"""
    
    def __init__(self, model_path=None):
        """Initialize YOLO license plate detector"""
        # Look for models in multiple locations
        if model_path is None:
            possible_paths = [
                "models/license_plate_rapid/weights/best.pt",  # New rapid model best weights
                "models/license_plate_rapid.pt",               # New rapid model
                "models/license_plate_detector/weights/best.pt",
                "models/license_plate_yolov11.pt",
                "models/best.pt",
                "yolov11/runs/detect/train/weights/best.pt",
                "yolov11/weights/best.pt",
                "yolov11n.pt",                                # YOLOv11 nano
                "yolov8n.pt"                                  # YOLOv8 nano fallback
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    print(f"Found model at {path}")
                    break
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path) if model_path and os.path.dirname(model_path) else "models", exist_ok=True)
        
        try:
            if model_path is not None and os.path.exists(model_path):
                # Load YOLO model
                print(f"Loading YOLO model from {model_path}...")
                self.model = YOLO(model_path)
                print(f"Successfully loaded YOLO model from {model_path}")
            else:
                # If no model available, try using a pre-trained YOLO model
                try:
                    print("No custom model found. Using pre-trained YOLOv8n...")
                    self.model = YOLO('yolov8n.pt')
                    print("Using pre-trained YOLOv8n for detection")
                except Exception as e:
                    print(f"Could not load pre-trained model: {e}")
                    self.model = None
        except Exception as e:
            print(f"Failed to load YOLO model: {e}")
            print("Will try to find or download model later")
            self.model = None
            
        # Confidence threshold for detections
        self.conf_threshold = 0.3  # Lower threshold to detect more plates

    def detect_plates(self, image):
        """Detect license plates using YOLO"""
        if self.model is None:
            # Try to load model again
            try:
                self.model = YOLO('yolov8n.pt')
                print("Loaded default model")
            except:
                return []
            
        # Standard preprocessing for YOLO
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
        
        # Run inference
        results = self.model(img_rgb)
        
        plates = []
        for result in results:
            # Process each detection
            for box in result.boxes:
                # Get coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                conf = float(box.conf[0])
                
                # If confidence is high enough
                if conf >= self.conf_threshold:
                    # Extract plate image
                    w, h = x2 - x1, y2 - y1
                    plate_img = image[y1:y2, x1:x2]
                    
                    # This coordinates represent the entire plate, not just a vehicle
                    plates.append({
                        "img": plate_img,
                        "coords": (x1, y1, w, h),
                        "conf": conf,
                        "bottom_y": y2  # For line crossing detection
                    })
        
        return plates


class DirectLicensePlateViolationSystem:
    def __init__(self, video_source="OBS"):
        # Initialize traffic light
        self.traffic_light = TrafficLightSimulator()
        
        # Initialize license plate detector (advanced model)
        self.plate_detector = YOLOLicensePlateDetector()
        
        # Create beautiful visualization directory
        self.vis_dir = "visualizations"
        os.makedirs(self.vis_dir, exist_ok=True)
        
        # Setup video capture
        self.cap = None
        if video_source == "OBS":
            # Try to find OBS Virtual Camera
            self.connect_to_obs_camera()
        else:
            # Use specified source (number or path)
            self.cap = cv2.VideoCapture(video_source)
            if not self.cap.isOpened():
                print(f"Error: Could not open video source {video_source}")
                print("Trying alternative backend...")
                self.cap = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    print("Still couldn't open video source. Trying to connect to OBS Virtual Camera...")
                    self.connect_to_obs_camera()
        
        # Set up stop line (y-coordinate as a fraction of the frame height)
        self.stop_line_position = 0.6  # 60% from the top (adjust as needed)
        
        # Create directory for saving violations
        self.violations_dir = "violations"
        os.makedirs(self.violations_dir, exist_ok=True)
        
        # Create directory for saving plate images - ONLY actual license plates
        self.plates_dir = os.path.join(self.violations_dir, "plates")
        os.makedirs(self.plates_dir, exist_ok=True)
            
        # Create CSV for saving violation records
        self.violations_csv = os.path.join(self.violations_dir, "violations_record.csv")
        if not os.path.exists(self.violations_csv) or os.path.getsize(self.violations_csv) == 0:
            with open(self.violations_csv, 'w') as f:
                f.write("Date,Time,License Plate,Confidence,Image Path\n")
        
        # Add new folders for evidence
        self.evidence_dir = os.path.join(self.violations_dir, "evidence")
        os.makedirs(self.evidence_dir, exist_ok=True)
        
        # Add folder for debug images showing detection processing
        self.debug_dir = os.path.join(self.violations_dir, "debug")
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Track processing statistics
        self.stats = {
            "total_frames": 0,
            "plates_detected": 0,
            "violations": 0,
            "avg_confidence": 0
        }
        
        # Evidence overlay counter
        self.evidence_overlay_counter = 0
        self.last_violation_plate = ""
        
        # Violation tracking and optimization
        self.last_violation_time = 0
        self.cooldown_period = 1  # seconds between potential violations (lower for direct plate detection)
        self.min_confidence_threshold = 60  # minimum confidence percentage for OCR
        self.detected_plates = set()  # Track unique plates to avoid duplicates
        
        # State codes for validation
        self.state_codes = ["MH", "DL", "TN", "KA", "AP", "TS", "GJ", "MP", 
                           "UP", "HR", "PB", "RJ", "KL", "WB", "BR", "OD"]
        
        # UI settings
        self.ui_font = cv2.FONT_HERSHEY_SIMPLEX
        self.ui_colors = {
            "red": (0, 0, 255),
            "green": (0, 255, 0),
            "yellow": (0, 255, 255),
            "blue": (255, 0, 0),
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "orange": (0, 165, 255),
        }
        
        # Performance optimization
        self.frame_counter = 0
        self.processing_every_n_frames = 3  # Process every nth frame (skip frames for performance)

    def run(self):
        # Initialize the traffic light window
        self.traffic_light.update_display()
        
        # Start traffic light in a thread
        light_thread = threading.Thread(target=self.update_traffic_light)
        light_thread.daemon = True
        light_thread.start()
        
        # Create window with better resolution
        cv2.namedWindow("License Plate Violation Detection", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("License Plate Violation Detection", 1280, 720)
        
        # Main loop
        while True:
            # Read frame
            ret, frame = self.cap.read()
            if not ret:
                print("Can't receive frame. Retrying in 1 second...")
                time.sleep(1)
                continue
            
            # Get frame dimensions
            height, width = frame.shape[:2]
            stop_line_y = int(height * self.stop_line_position)
            
            # Draw the line
            cv2.line(frame, (0, stop_line_y), (width, stop_line_y), (255, 255, 255), 3)
            
            # Add text to describe the line
            cv2.putText(frame, "STOP LINE", (width // 2 - 60, stop_line_y - 10),
                       self.ui_font, 0.8, self.ui_colors["white"], 2)
            
            # Add traffic light status
            light_status = self.traffic_light.get_light_status()
            light_text = ["RED", "YELLOW", "GREEN"][light_status]
            light_color = self.traffic_light.colors[light_status]
            
            # Draw a nice background for the status display
            cv2.rectangle(frame, (10, 10), (250, 70), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, 10), (250, 70), light_color, 2)
            cv2.putText(frame, f"Signal: {light_text}", (20, 50), 
                        self.ui_font, 1.0, light_color, 2)
            
            # Process every Nth frame
            self.frame_counter += 1
            self.stats["total_frames"] += 1
            
            if self.frame_counter % self.processing_every_n_frames == 0:
                # Detect license plates
                plates = self.plate_detector.detect_plates(frame)
                
                if plates:
                    self.stats["plates_detected"] += len(plates)
                
                # RED LIGHT VIOLATION CHECK
                if light_status == 0:  # Red light
                    # Process each detected plate
                    for plate in plates:
                        plate_img = plate["img"]
                        x1, y1, w, h = plate["coords"]
                        plate_bottom_y = plate["bottom_y"]
                        
                        # Check if plate crosses the line
                        if plate_bottom_y > stop_line_y:
                            # Calculate crossing percentage
                            crossing_amount = (plate_bottom_y - stop_line_y) / h
                            
                            # Definite violation - plate significantly over the line
                            if crossing_amount > 0.2:
                                # Draw violation box in RED
                                cv2.rectangle(frame, (x1, y1), (x1+w, y1+h), self.ui_colors["red"], 3)
                                
                                # Check cooldown
                                current_time = time.time()
                                if current_time - self.last_violation_time > self.cooldown_period:
                                    # Process as violation
                                    plate_text, confidence = self.recognize_license_plate(plate_img)
                                    
                                    # Only record if OCR is confident
                                    if plate_text and confidence > self.min_confidence_threshold:
                                        # Display plate info on frame
                                        cv2.putText(frame, plate_text, (x1, y1-10),
                                                  self.ui_font, 0.8, self.ui_colors["red"], 2)
                                        cv2.putText(frame, f"RED LIGHT VIOLATION", (x1, y1-35),
                                                  self.ui_font, 0.7, self.ui_colors["red"], 2)
                                        
                                        # Check for duplicate plate
                                        if plate_text not in self.detected_plates:
                                            # Save evidence package
                                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                            clean_text = ''.join(c if c.isalnum() else '_' for c in plate_text)
                                            evidence_path = self.save_evidence_package(
                                                frame, plate_img, plate_text, confidence,
                                                timestamp, clean_text
                                            )
                                            
                                            # Create violation visualization
                                            self.create_violation_visualization(frame, plate_img, plate_text, confidence)
                                            
                                            # Save to CSV
                                            self.save_violation_record(frame, plate_text, confidence, evidence_path)
                                            
                                            # Update stats
                                            self.stats["violations"] += 1
                                            self.detected_plates.add(plate_text)
                                            
                                            # Show evidence saved overlay
                                            self.evidence_overlay_counter = 50  # Show for 50 frames
                                            self.last_violation_plate = plate_text
                                            
                                            # Terminal feedback
                                            print("\n" + "="*50)
                                            print(f"✅ VIOLATION RECORDED: {plate_text}")
                                            print(f"📊 Confidence: {confidence:.1f}%")
                                            print(f"📂 Evidence saved to: {evidence_path}")
                                            print("="*50 + "\n")
                                        else:
                                            # Plate already recorded
                                            cv2.putText(frame, "(ALREADY RECORDED)", (x1, y1-60),
                                                      self.ui_font, 0.6, self.ui_colors["yellow"], 2)
                                    else:
                                        # Low confidence plate
                                        cv2.putText(frame, "Unknown plate", (x1, y1-10),
                                                  self.ui_font, 0.7, self.ui_colors["yellow"], 2)
                                    
                                    self.last_violation_time = current_time
                            else:
                                # Just touching the line - warning
                                cv2.rectangle(frame, (x1, y1), (x1+w, y1+h), self.ui_colors["orange"], 2)
                        else:
                            # Before the line - safe
                            cv2.rectangle(frame, (x1, y1), (x1+w, y1+h), self.ui_colors["green"], 2)
                else:
                    # Not red light - just display plates
                    for plate in plates:
                        x1, y1, w, h = plate["coords"]
                        box_color = self.ui_colors["green"] if light_status == 2 else self.ui_colors["yellow"]
                        cv2.rectangle(frame, (x1, y1), (x1+w, y1+h), box_color, 2)
            
            # Show evidence overlay if active
            if self.evidence_overlay_counter > 0:
                # Semi-transparent overlay
                h, w = frame.shape[:2]
                overlay = frame.copy()
                cv2.rectangle(overlay, (w//2 - 250, h//2 - 50), (w//2 + 250, h//2 + 50), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
                
                # Add text
                cv2.putText(frame, f"VIOLATION RECORDED", (w//2 - 200, h//2 - 10), 
                           self.ui_font, 1, (0, 0, 255), 2)
                cv2.putText(frame, f"Plate: {self.last_violation_plate}", (w//2 - 180, h//2 + 30), 
                           self.ui_font, 0.8, (255, 255, 255), 2)
                
                self.evidence_overlay_counter -= 1
            
            # Add stats display
            cv2.rectangle(frame, (10, height-100), (250, height-20), (0, 0, 0), -1)
            cv2.putText(frame, f"Plates detected: {self.stats['plates_detected']}", 
                       (20, height-70), self.ui_font, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Violations: {self.stats['violations']}", 
                       (20, height-45), self.ui_font, 0.6, (0, 0, 255), 1)
            
            # Display the frame
            cv2.imshow("License Plate Violation Detection", frame)
            
            # Break on q key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Clean up
        self.cap.release()
        cv2.destroyAllWindows()
    
    def update_traffic_light(self):
        """Update the traffic light display continuously"""
        while True:
            self.traffic_light.update_display()
            time.sleep(0.05)
            
    def recognize_license_plate(self, plate_img):
        """Advanced license plate recognition with multiple techniques"""
        if plate_img is None or plate_img.size == 0:
            return None, 0
        
        try:
            # Create a timestamp for debugging
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            
            # Resize the image for better OCR
            plate_resized = cv2.resize(plate_img, (0, 0), fx=2.0, fy=2.0)
            
            # Convert to grayscale if not already
            if len(plate_resized.shape) == 3:
                gray = cv2.cvtColor(plate_resized, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_resized.copy()
                
            # Add a version with border - sometimes helps with OCR
            gray_bordered = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            
            # Try direct OCR with different configurations
            raw_texts = []
            
            # PSM configurations optimized for license plates
            ocr_configs = [
                {'psm': 11, 'oem': 3, 'img': gray},      # Good for sparse text
                {'psm': 7, 'oem': 3, 'img': gray},       # Single line of text
                {'psm': 8, 'oem': 3, 'img': gray},       # Single word
                {'psm': 6, 'oem': 3, 'img': gray},       # Uniform block of text
                {'psm': 13, 'oem': 3, 'img': gray},      # Raw line
                {'psm': 8, 'oem': 3, 'img': gray_bordered},  # Single word with border
            ]
            
            best_text = None
            highest_confidence = 0
            
            # Try all OCR configurations
            for cfg in ocr_configs:
                config = f'--oem {cfg["oem"]} --psm {cfg["psm"]} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                
                # Direct string extraction
                direct_text = pytesseract.image_to_string(
                    cfg["img"], 
                    config=config
                ).strip().replace(" ", "")
                
                # Detailed data with confidence values
                data = pytesseract.image_to_data(
                    cfg["img"], 
                    config=config, 
                    output_type=pytesseract.Output.DICT
                )
                
                # Extract text and confidence
                confidence_sum = 0
                confidence_count = 0
                word_text = ""
                
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > 0 and data['text'][i].strip():
                        word_text += data['text'][i].strip()
                        confidence_sum += int(data['conf'][i])
                        confidence_count += 1
                
                # Calculate confidence
                if confidence_count > 0:
                    avg_confidence = confidence_sum / confidence_count
                    text = word_text.strip().replace(" ", "")
                    
                    # Use direct text if it looks better
                    if len(direct_text) >= len(text) and self.looks_like_license_plate(direct_text):
                        text = direct_text
                    
                    # Check if it looks like a license plate
                    plate_likelihood = self.license_plate_likelihood(text)
                    
                    # Save this candidate
                    raw_texts.append((text, avg_confidence, plate_likelihood))
                    
                    # Update best text if better than current
                    if text and (avg_confidence > highest_confidence or 
                              (avg_confidence == highest_confidence and plate_likelihood > 
                               self.license_plate_likelihood(best_text or ""))):
                        highest_confidence = avg_confidence
                        best_text = text
            
            # Try EasyOCR if available (often better for license plates)
            try:
                import easyocr
                reader = easyocr.Reader(['en'])
                ocr_result = reader.readtext(gray)
                if ocr_result:
                    easyocr_text = ''.join([item[1] for item in ocr_result]).strip().replace(" ", "")
                    easyocr_conf = sum([item[2] for item in ocr_result]) / len(ocr_result) * 100
                    raw_texts.append((easyocr_text, easyocr_conf, self.license_plate_likelihood(easyocr_text)))
                    
                    if easyocr_conf > highest_confidence and easyocr_text:
                        highest_confidence = easyocr_conf
                        best_text = easyocr_text
            except ImportError:
                # EasyOCR not available, ignore
                pass
            
            # Sort candidates by likelihood and confidence
            if raw_texts:
                raw_texts.sort(key=lambda x: (x[2], x[1]), reverse=True)
                
                # Get the best candidate
                if raw_texts:
                    best_text, highest_confidence, _ = raw_texts[0]
            
            # Perform state code correction and normalization
            if best_text and len(best_text) >= 2:
                best_text = self.normalize_license_plate(best_text, raw_texts)
            
            # Clean up the final text
            if best_text:
                best_text = re.sub(r'[^A-Z0-9]', '', best_text.upper())
                
                # Return the final plate text and confidence
                return best_text, highest_confidence
            
            return None, 0
            
        except Exception as e:
            print(f"Error in license plate recognition: {e}")
            return None, 0

    def normalize_license_plate(self, plate_text, candidates=None):
        """Normalize license plate text for Indian plates"""
        if not plate_text:
            return plate_text
        
        # Fix common state code errors
        common_state_errors = {
            "MF": "MH",   # Common confusion between F and H
            "NF": "MH",   # Another common error for MH
            "MP": "MH",   # Confusion between P and H
            "D1": "DL",   # Number 1 instead of L for Delhi
            "TH": "TN",   # TN (Tamil Nadu) misread as TH
            "TC": "TS",   # TS (Telangana) misread as TC
            "BJ": "RJ",   # RJ (Rajasthan) misread as BJ
            "KR": "KL"    # KL (Kerala) misread as KR
        }
        
        # Try to fix state code errors
        for error_state, correct_state in common_state_errors.items():
            if plate_text.startswith(error_state):
                plate_text = correct_state + plate_text[2:]
                print(f"Fixed state code: {error_state} → {correct_state}")
                break
                
        # Special case for Rajasthan plates (RJ14CV0002)
        if plate_text.startswith("RJ") and "IGC" in plate_text:
            plate_text = plate_text.replace("IGC", "16C")
            print(f"Fixed common RJ plate error: IGC → 16C")
            
        # Special case for Maharashtra (MHO2DN8716 format)
        if re.match(r"^MH[O0]\d[A-Z]{2}\d{4}$", plate_text):
            district = plate_text[2:4].replace("O", "0")  # O → 0
            series = plate_text[4:6]
            number = plate_text[6:]
            plate_text = f"MH{district}{series}{number}"
            print(f"Fixed MH plate format: {plate_text}")
        
        # Fix O → 0 confusion in numbers
        if "O" in plate_text:
            match = re.search(r"^([A-Z]{2})([O0-9]{1,2})([A-Z]{1,3})([O0-9]{1,4})$", plate_text)
            if match:
                state, district, series, number = match.groups()
                district = district.replace("O", "0")
                number = number.replace("O", "0")
                plate_text = f"{state}{district}{series}{number}"
                print(f"Fixed O/0 confusion: {plate_text}")
        
        return plate_text
    
    def looks_like_license_plate(self, text):
        """Quick check if text looks like a license plate"""
        if not text or len(text) < 6:
            return False
            
        # Should contain both letters and numbers
        has_letter = any(c.isalpha() for c in text)
        has_digit = any(c.isdigit() for c in text)
        
        # Check for state codes
        has_state_code = any(text.startswith(state) for state in self.state_codes)
        
        return has_letter and has_digit
    
    def license_plate_likelihood(self, text):
        """Calculate how likely a string is to be an Indian license plate"""
        if not text:
            return 0
            
        # Convert to uppercase and remove spaces
        text = text.upper().replace(" ", "")
        
        # Too short
        if len(text) < 6:
            return 0.1
            
        # Check for starting with state code
        state_match = False
        for state in self.state_codes:
            if text.startswith(state):
                state_match = True
                break
                
        # Check pattern: 2 letters + 2 digits + 1-4 letters + 1-4 digits
        pattern_match = bool(re.search(r'^[A-Z]{2}\d{1,2}[A-Z]{1,4}\d{1,4}$', text))
        
        # Calculate score
        score = 0.0
        
        # State code match is important
        if state_match:
            score += 0.5
            
        # Perfect pattern match is important
        if pattern_match:
            score += 0.5
        
        # Good length for a license plate
        if len(text) >= 8 and len(text) <= 12:
            score += 0.2
            
        # Must have digits and letters
        has_digits = any(c.isdigit() for c in text)
        has_letters = any(c.isalpha() for c in text)
        if has_digits and has_letters:
            score += 0.2
            
        return min(score, 1.0)  # Cap at 1.0
    
    def process_violation(self, frame, plate_img, plate_text, confidence):
        """Process a violation by saving the data and creating a visualization"""
        try:
            # Generate timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Clean text for filenames
            clean_text = ''.join(c if c.isalnum() else '_' for c in plate_text)
            
            # Save just the license plate image
            plate_filename = f"plate_{timestamp}_{clean_text}.jpg"
            plate_path = os.path.join(self.plates_dir, plate_filename)
            cv2.imwrite(plate_path, plate_img)
            
            # Save full evidence package with multiple images
            self.save_evidence_package(frame, plate_img, plate_text, confidence, timestamp, clean_text)
            
            # Create the violation visualization
            self.create_violation_visualization(frame, plate_img, plate_text, confidence)
            
            # Save violation to CSV
            self.save_violation_record(frame, plate_text, confidence, plate_path)
            
            # Update stats
            self.stats["violations"] += 1
            self.stats["avg_confidence"] = (self.stats["avg_confidence"] * (self.stats["violations"] - 1) + 
                                           confidence) / self.stats["violations"]
            
            # Display on console with more visibility
            print("\n" + "="*50)
            print(f"✅ VIOLATION RECORDED: {plate_text}")
            print(f"📊 Confidence: {confidence:.1f}%")
            print(f"📂 Evidence saved to: {self.evidence_dir}/{timestamp}_{clean_text}")
            print(f"🕒 Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"Error processing violation: {e}")
    
    def save_evidence_package(self, frame, plate_img, plate_text, confidence, timestamp, clean_text):
        """Save a complete package of evidence for the violation"""
        try:
            # Create a unique folder for this violation's evidence
            evidence_folder = os.path.join(self.evidence_dir, f"{timestamp}_{clean_text}")
            os.makedirs(evidence_folder, exist_ok=True)
            
            # Save original frame with violation
            cv2.imwrite(os.path.join(evidence_folder, "1_full_scene.jpg"), frame)
            
            # Save cropped original plate
            cv2.imwrite(os.path.join(evidence_folder, "2_plate_crop.jpg"), plate_img)
            
            # Save enhanced plate for better visibility
            enhanced = enhance_plate_for_ocr(plate_img)
            cv2.imwrite(os.path.join(evidence_folder, "3_plate_enhanced.jpg"), enhanced)
            
            # Create a zoomed in view showing just the violation area
            h, w = frame.shape[:2]
            stop_line_y = int(h * self.stop_line_position)
            
            # Save a marked version showing the violation clearly
            marked_frame = frame.copy()
            
            # Get plate coordinates from plate_img size
            plate_height, plate_width = plate_img.shape[:2]
            
            # Extract plate coordinates (we don't have x1, y1 here, so we'll need to draw 
            # the rectangle again based on finding it in the frame)
            # Use an approximate approach to identify the plate area
            
            # Save the marked evidence
            cv2.imwrite(os.path.join(evidence_folder, "4_violation_marked.jpg"), marked_frame)
            
            # Save text file with all details
            with open(os.path.join(evidence_folder, "violation_details.txt"), "w") as f:
                f.write(f"LICENSE PLATE: {plate_text}\n")
                f.write(f"CONFIDENCE: {confidence:.1f}%\n")
                f.write(f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d')}\n")
                f.write(f"TIME: {datetime.datetime.now().strftime('%H:%M:%S')}\n")
                f.write(f"VIOLATION: Crossed stop line during red light\n")
                f.write(f"SYSTEM: YOLO + OCR license plate detection\n")
                
            return evidence_folder
            
        except Exception as e:
            print(f"Error saving evidence package: {e}")
            return None