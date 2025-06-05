import serial
import cv2
import numpy as np
import pytesseract
import re
import os
import sys
import time
import threading
import uuid
from datetime import datetime
from queue import Queue, Empty
import concurrent.futures
import easyocr

from api_manager import APIManager

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✅ YOLO available for license plate detection")
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ YOLO not available, using Haar cascades only")

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

try:
    ser = serial.Serial('COM8', 9600)
    ARDUINO_AVAILABLE = True
    print("✅ Arduino connected successfully on COM7")
except:
    ARDUINO_AVAILABLE = False
    print("⚠️ Arduino not available - Using keyboard controls")

class OptimizedTrafficLightPlateDetector:
    def __init__(self):
        self.red_light_active = False
        self.detection_line_y = 400
        self.camera = None
        self.running = False
        self.detected_plates = []
        
        # Add missing state tracking variables
        self.last_arduino_state = None  # Track last state to avoid spam
        self.boom_opened = False  # Track boom state
        self.waiting_for_vehicle = False  # Track if we're waiting for a vehicle
        
        self.api_manager = APIManager()
        
        print("🌐 Testing API connection on startup...")
        if self.api_manager.test_api_connection():
            print("🚀 API system ready for violations!")
        else:
            print("⚠️ API system offline - violations will be saved locally")
        
        self.violation_cooldown = {}
        self.violation_timeout = 60
        
        self.fine_amount = 1
        
        self.frame_skip = 5
        self.frame_count = 0
        self.detection_queue = Queue(maxsize=2)
        self.latest_frame = None
        self.display_frame = None
        self.detection_results = []
        
        self.target_fps = 5
        self.min_fps = 3
        self.max_fps = 30
        self.frame_delay = 1.0 / self.target_fps
        self.fps_display = "FPS: --"
        
        self.actual_fps = 0
        self.last_fps_time = time.time()
        self.fps_counter = 0
        
        self.detection_thread = None
        self.camera_thread = None
        self.arduino_thread = None
        self.detection_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        self.keyboard_mode = not ARDUINO_AVAILABLE
        if self.keyboard_mode:
            print("🎮 Keyboard simulation mode active:")
            print("   Press 'r' for RED light (activate detection)")
            print("   Press 'g' for GREEN light (deactivate detection)")
        
        self.yolo_model = None
        if YOLO_AVAILABLE:
            model_paths = [
                '../../models/license_plate_rapid/weights/best.pt',
                '../../models/license_plate_rapid.pt',
                '../../yolo11n.pt',
                '../../models/yolo11n.pt'
            ]
            
            for model_path in model_paths:
                try:
                    if os.path.exists(model_path):
                        self.yolo_model = YOLO(model_path)
                        print(f"✅ Loaded YOLO model: {model_path}")
                        break
                except Exception as e:
                    print(f"Failed to load {model_path}: {e}")
        
        self.haar_cascade = None
        haar_path = "../../haarcascade_russian_plate_number.xml"
        if os.path.exists(haar_path):
            self.haar_cascade = cv2.CascadeClassifier(haar_path)
            print(f"✅ Loaded Haar cascade: {haar_path}")
        
        self.easyocr_reader = easyocr.Reader(['en'], gpu=True)
        
        self.mouse_pressed = False
        
        if ARDUINO_AVAILABLE:
            self.start_arduino_communication()
            time.sleep(0.5)
        
        self.start_camera()
    
    def red_led_triggered(self):
        """Vehicle detected - Arduino sends '3' when distance < 5cm"""
        if self.last_arduino_state != "VEHICLE_DETECTED":
            print("🚗 Vehicle detected at sensor - Activating license plate detection!")
            self.last_arduino_state = "VEHICLE_DETECTED"
        self.red_light_active = True
        self.waiting_for_vehicle = True

    def green_led_triggered(self):
        """No vehicle - Arduino sends '1' when distance >= 5cm"""
        if self.last_arduino_state != "NO_VEHICLE":
            print("🟢 No vehicle detected - Deactivating license plate detection!")
            self.last_arduino_state = "NO_VEHICLE"
        self.red_light_active = False
        self.waiting_for_vehicle = False
    
    def handle_keyboard_simulation(self, key):
        if self.keyboard_mode:
            if key == ord('r'):
                self.red_led_triggered()
                return True
            elif key == ord('g'):
                self.green_led_triggered()
                return True
        return False
    
    def check_violation_eligibility(self, license_plate):
        current_time = time.time()
        
        if license_plate in self.violation_cooldown:
            time_since_last = current_time - self.violation_cooldown[license_plate]
            if time_since_last < self.violation_timeout:
                remaining_time = self.violation_timeout - time_since_last
                print(f"⏰ Plate {license_plate} in cooldown. {remaining_time:.0f} seconds remaining")
                return False
        
        return True
    def boom_boom(self, license_plate):
        """Send license plate to Arduino for boom control"""
        try:
            if ARDUINO_AVAILABLE and self.waiting_for_vehicle:
                # Send '1' to indicate we want to send plate data
                ser.write(b'1')
                time.sleep(0.1)  # Small delay for Arduino to process
                
                # Send the license plate followed by newline
                plate_data = f"{license_plate}\n"
                ser.write(plate_data.encode())
                
                print(f"🚧 Sent license plate to Arduino: {license_plate}")
                print(f"🚧 Arduino will control boom barrier automatically")
                
                # Arduino will handle the boom control sequence:
                # 1. Turn green LED on
                # 2. Open servo (boom)
                # 3. Wait 3 seconds
                # 4. Close servo (boom)
                # 5. Turn red LED back on
                
                self.boom_opened = True
                
                # Reset boom status after Arduino's sequence (approximately 6 seconds)
                def reset_boom_status():
                    time.sleep(6)  # Wait for Arduino's full sequence
                    self.boom_opened = False
                    print(f"🚧 Boom sequence completed by Arduino")
                
                threading.Thread(target=reset_boom_status, daemon=True).start()
                
            elif not ARDUINO_AVAILABLE:
                print(f"🚧 BOOM SIMULATION: Would send plate {license_plate} to Arduino")
                
        except Exception as e:
            print(f"❌ Error sending plate to Arduino: {e}")

    def arduino_communication_loop(self):
        print("🔌 Arduino communication thread started")
        
        try:
            while self.running:
                if ser.in_waiting:
                    line = ser.readline().decode().strip()
                    
                    # Arduino sends '3' when vehicle detected (distance < 5cm)
                    if line == '3' and self.last_arduino_state != "VEHICLE_DETECTED":
                        print(f"📡 Arduino signal: {line} (Vehicle detected at sensor)")
                        self.red_led_triggered()
                    # Arduino sends '1' when no vehicle (distance >= 5cm)
                    elif line == '1' and self.last_arduino_state != "NO_VEHICLE":
                        print(f"📡 Arduino signal: {line} (No vehicle detected)")
                        self.green_led_triggered()
                    # Arduino may send license plate confirmations
                    elif line.startswith('Plate: '):
                        plate = line.replace('Plate: ', '')
                        print(f"📡 Arduino confirmed plate processing: {plate}")
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"❌ Arduino communication error: {e}")
    
    def start_arduino_communication(self):
        self.running = True
        self.arduino_thread = threading.Thread(target=self.arduino_communication_loop, daemon=True)
        self.arduino_thread.start()
        print("🚀 Arduino communication started in background")
    
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.mouse_pressed = True
        elif event == cv2.EVENT_LBUTTONUP:
            self.mouse_pressed = False
        elif event == cv2.EVENT_MOUSEMOVE and self.mouse_pressed:
            self.detection_line_y = y
            print(f"Detection line moved to Y: {y}")
    
    def enhance_plate_image(self, plate_img, for_easyocr=True):
        if plate_img.size == 0:
            return None, None
        
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img.copy()
        
        gray = cv2.resize(gray, (240, 60), interpolation=cv2.INTER_CUBIC)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        if for_easyocr:
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            return gray, None
        else:
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            return gray, binary

    def extract_text_from_plate(self, plate_img):
        gray, _ = self.enhance_plate_image(plate_img, for_easyocr=True)
        best_text = ""
        best_confidence = 0
        max_processing_time = 0.3
        start_time = time.time()
        
        try:
            result = self.easyocr_reader.readtext(gray, detail=1, paragraph=False, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            for bbox, text, conf in result:
                cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
                if len(cleaned) >= 4 and conf > best_confidence:
                    best_text = cleaned
                    best_confidence = conf * 100
            if best_confidence > 60:
                ocr_time = time.time() - start_time
                if ocr_time > 0.1:
                    print(f"EasyOCR processing took {ocr_time:.3f}s - {'Successful' if best_confidence > 60 else 'Failed'}")
                return best_text
        except Exception as e:
            pass
        
        if time.time() - start_time < max_processing_time:
            gray, binary = self.enhance_plate_image(plate_img, for_easyocr=False)
            config = '--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            try:
                data = pytesseract.image_to_data(binary, config=config, output_type=pytesseract.Output.DICT)
                text_parts = []
                total_confidence = 0
                valid_words = 0
                for i, conf in enumerate(data['conf']):
                    if int(conf) > 30:
                        text = data['text'][i].strip()
                        if text:
                            text_parts.append(text)
                            total_confidence += int(conf)
                            valid_words += 1
                if valid_words > 0:
                    avg_confidence = total_confidence / valid_words
                    combined_text = ''.join(text_parts)
                    cleaned_text = re.sub(r'[^A-Z0-9]', '', combined_text.upper())
                    if len(cleaned_text) >= 4 and avg_confidence > best_confidence:
                        best_text = cleaned_text
                        best_confidence = avg_confidence
            except Exception as e:
                pass
        
        ocr_time = time.time() - start_time
        if ocr_time > 0.1:
            print(f"OCR processing took {ocr_time:.3f}s - {'Successful' if best_confidence > 60 else 'Failed'}")
        return best_text if best_confidence > 60 else ""

    def detect_plates_with_yolo(self, frame):
        if not self.yolo_model:
            return []
        
        try:
            results = self.yolo_model(frame, conf=0.3, verbose=False)
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        confidence = float(box.conf[0])
                        
                        padding = 10
                        x1 = max(0, x1 - padding)
                        y1 = max(0, y1 - padding)
                        x2 = min(frame.shape[1], x2 + padding)
                        y2 = min(frame.shape[0], y2 + padding)
                        
                        detections.append({
                            'bbox': (x1, y1, x2, y2),
                            'confidence': confidence,
                            'method': 'YOLO'
                        })
            
            return detections
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return []
    
    def detect_plates_with_haar(self, frame):
        if not self.haar_cascade:
            return []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            plates = self.haar_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 30)
            )
            
            detections = []
            for (x, y, w, h) in plates:
                detections.append({
                    'bbox': (x, y, x + w, y + h),
                    'confidence': 0.8,
                    'method': 'Haar'
                })
            
            return detections
        except Exception as e:
            print(f"Haar detection error: {e}")
            return []
    
    def process_detections_background(self, frame):
        detections = []
        
        if self.yolo_model:
            detections = self.detect_plates_with_yolo(frame)
        if not detections and self.haar_cascade:
            detections = self.detect_plates_with_haar(frame)
        
        valid_plates = []
        detection_results = []
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            method = detection['method']
            
            plate_center_y = (y1 + y2) // 2
            
            result = {
                'bbox': (x1, y1, x2, y2),
                'confidence': confidence,
                'method': method,
                'below_line': plate_center_y > self.detection_line_y,
                'text': '',
                'already_detected': False
            }
            
            already_detected = False
            
            if plate_center_y > self.detection_line_y and self.red_light_active:
                plate_img = frame[y1:y2, x1:x2]
                
                if plate_img.size > 0 and min(plate_img.shape[0:2]) >= 20 and confidence > 0.6:
                    skip_ocr = False
                    current_time = time.time()
                    
                    for prev_plate in self.detected_plates[-10:]:
                        if current_time - prev_plate.get('timestamp', 0) < 3.0:
                            prev_x1, prev_y1, prev_x2, prev_y2 = prev_plate.get('bbox', (0,0,0,0))
                            if (abs(prev_x1 - x1) < 30 and abs(prev_y1 - y1) < 30):
                                skip_ocr = True
                                result['text'] = prev_plate.get('text', '')
                                result['already_detected'] = True
                                break
                    
                    if not skip_ocr:
                        plate_text = self.extract_text_from_plate(plate_img)
                        result['text'] = plate_text
                        if plate_text and len(plate_text) >= 4:
                            if self.check_violation_eligibility(plate_text):
                                current_time = time.time()
                                self.violation_cooldown[plate_text] = current_time
                                
                                plate_info = {
                                    'text': plate_text,
                                    'bbox': (x1, y1, x2, y2),
                                    'confidence': confidence,
                                    'method': method,
                                    'timestamp': current_time,
                                    'violation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                valid_plates.append(plate_info)
                                self.detected_plates.append(plate_info)
                                
                                violation_image_path = self.save_violation_image(frame, plate_info)
                                
                                # Fixed boom control - only if Arduino is available
                                if ARDUINO_AVAILABLE:
                                    self.boom_boom(plate_text)
                                
                                try:
                                    print(f"🚀 Attempting to send violation email for {plate_text}...")
                                    violation_id = self.api_manager.send_violation_email(
                                        plate_text, violation_image_path, self.fine_amount
                                    )
                                    print(f"🚨 TOLL CROSS DETECTED: {plate_text} at {plate_info['violation_time']}")
                                    print(f"📧 Email processing completed with toll ID: {violation_id}")
                                    print(f"💰 Fine amount: ₹{self.fine_amount}")
                                    print(f"🌐 Check templates folder for HTML version and payment links")
                                    
                                    time.sleep(1)
                                    
                                except Exception as e:
                                    print(f"❌ Error sending toll email: {e}")
                                    print(f"📧 Email failed, but toll still recorded locally")
                                    print(f"🚨 TOLL CROSS DETECTED: {plate_text} (email failed - check templates folder)")

                                    toll_id = str(uuid.uuid4())[:8].upper()
                                    print(f"🆔 Local toll ID: {toll_id}")

                        result['already_detected'] = already_detected
            
            detection_results.append(result)
        
        return detection_results
    
    def detection_worker(self):
        while self.running:
            try:
                frame = self.detection_queue.get(timeout=0.1)
                
                results = self.process_detections_background(frame)
                
                self.detection_results = results
                
                self.detection_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                print(f"Detection worker error: {e}")
                continue
    
    def draw_detections_on_frame(self, frame, detection_results):
        for result in detection_results:
            x1, y1, x2, y2 = result['bbox']
            method = result['method']
            text = result['text']
            below_line = result['below_line']
            already_detected = result['already_detected']
            
            if below_line and self.red_light_active:
                if text:
                    color = (0, 255, 0) if not already_detected else (255, 0, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{text} ({method})", 
                               (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                    cv2.putText(frame, f"Plate? ({method})", 
                               (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (128, 128, 128), 1)
                cv2.putText(frame, "Above line" if not below_line else "Green light", 
                           (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)
        
        return frame
    
    def save_violation_image(self, frame, plate_info):
        try:
            os.makedirs("../../violations", exist_ok=True)
            filename = f"../../violations/violation_{plate_info['text']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, frame)
            print(f"💾 Saved violation image: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving violation image: {e}")
            return ""
    
    def camera_capture_loop(self):
        if not self.camera:
            print("⚠️ No camera available for capture loop")
            return
            
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            self.latest_frame = frame.copy()
            self.frame_count += 1
            
            if (self.red_light_active and 
                self.frame_count % self.frame_skip == 0 and 
                not self.detection_queue.full()):
                try:
                    self.detection_queue.put_nowait(frame.copy())
                except:
                    pass
            
            time.sleep(0.01)
    
    def start_camera(self):
        if not self.running:
            self.running = True
        
        print("🔍 Trying to open camera...")
        self.camera = cv2.VideoCapture(1)
        if not self.camera.isOpened():
            print("📹 Camera 1 not available, trying camera 0...")
            self.camera = cv2.VideoCapture(0)
        
        if not self.camera.isOpened():
            print("❌ Error: Could not open any camera. Please check camera connection.")
            print("🔧 Continuing without camera for Arduino testing...")
            self.camera = None
        else:
            print("✅ Camera opened successfully!")
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.camera_thread = threading.Thread(target=self.camera_capture_loop, daemon=True)
            self.camera_thread.start()
        
        self.detection_thread = threading.Thread(target=self.detection_worker, daemon=True)
        self.detection_thread.start()
        
        cv2.namedWindow('Traffic Light Plate Detection')
        cv2.setMouseCallback('Traffic Light Plate Detection', self.mouse_callback)
        print("🎥 Camera system started. Detection ready...")
        
        self.start_display_loop()
    
    def start_display_loop(self):
        fps_counter = 0
        fps_start_time = time.time()
        frame_time = time.time()
        
        while self.running:
            elapsed = time.time() - frame_time
            sleep_time = max(0, self.frame_delay - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
            frame_time = time.time()
            
            if self.latest_frame is not None:
                frame = self.latest_frame.copy()
                
                # Update detection line color based on vehicle presence
                line_color = (0, 0, 255) if self.red_light_active else (255, 255, 255)
                cv2.line(frame, (0, self.detection_line_y), (frame.shape[1], self.detection_line_y), line_color, 3)
                cv2.putText(frame, "Detection Line (drag to move)", 
                           (10, self.detection_line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, line_color, 2)
                
                if self.detection_results:
                    frame = self.draw_detections_on_frame(frame, self.detection_results)
                
                # Update status display
                if self.red_light_active:
                    cv2.putText(frame, "VEHICLE DETECTED - SCANNING LICENSE PLATE", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, "NO VEHICLE - WAITING FOR APPROACH", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                fps_counter += 1
                if fps_counter % 30 == 0:
                    fps = 30 / (time.time() - fps_start_time)
                    fps_start_time = time.time()
                    self.fps_display = f"FPS: {fps:.1f}"
                
                if hasattr(self, 'fps_display'):
                    cv2.putText(frame, self.fps_display, 
                               (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.putText(frame, f"Frame: {self.frame_count} | Total Violations: {len(self.detected_plates)}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Update status info
                vehicle_status = "PRESENT" if self.waiting_for_vehicle else "ABSENT"
                boom_status = "OPEN" if hasattr(self, 'boom_opened') and self.boom_opened else "CLOSED"
                cv2.putText(frame, f"Vehicle: {vehicle_status} | Boom: {boom_status}", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                if self.keyboard_mode:
                    cv2.putText(frame, "Controls: 'q' quit, 'c' clear, 'r' RED, 'g' GREEN", 
                               (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                else:
                    cv2.putText(frame, "Controls: 'q' quit, 'c' clear violations, mouse drag line", 
                               (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                cv2.imshow('Traffic Light Plate Detection', frame)
            else:
                status_frame = np.zeros((400, 800, 3), dtype=np.uint8)
                
                if self.red_light_active:
                    status_text = "VEHICLE DETECTED" if ARDUINO_AVAILABLE else "RED LIGHT - KEYBOARD MODE"
                    cv2.putText(status_frame, status_text, 
                               (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                    cv2.rectangle(status_frame, (350, 100), (450, 200), (0, 0, 255), -1)
                else:
                    status_text = "NO VEHICLE DETECTED" if ARDUINO_AVAILABLE else "GREEN LIGHT - KEYBOARD MODE"
                    cv2.putText(status_frame, status_text, 
                               (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                    cv2.rectangle(status_frame, (350, 100), (450, 200), (0, 255, 0), -1)
                
                cv2.putText(status_frame, "NO CAMERA - TEST MODE", 
                           (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                
                if self.keyboard_mode:
                    cv2.putText(status_frame, "Press 'r' for VEHICLE, 'g' for NO VEHICLE", 
                               (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                else:
                    cv2.putText(status_frame, "Move vehicle near ultrasonic sensor", 
                               (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Fixed boom status for status frame
                boom_status = "OPEN" if hasattr(self, 'boom_opened') and self.boom_opened else "CLOSED"
                cv2.putText(status_frame, f"Boom Status: {boom_status}", 
                           (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(status_frame, "Press 'q' to quit", 
                           (300, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow('Traffic Light Plate Detection', status_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.stop_detection()
                break
            elif key == ord('c'):
                self.detected_plates.clear()
                self.violation_cooldown.clear()
                print("🗑️ Cleared violation history and cooldowns")
            elif self.handle_keyboard_simulation(key):
                pass

    def stop_detection(self):
        self.running = False
        
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1)
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1)
        if ARDUINO_AVAILABLE and self.arduino_thread and self.arduino_thread.is_alive():
            self.arduino_thread.join(timeout=1)
        
        if self.camera:
            self.camera.release()
        
        self.detection_executor.shutdown(wait=False)
        
        cv2.destroyAllWindows()
        print("🛑 Detection stopped")

detector = OptimizedTrafficLightPlateDetector()

print("📋 System Features:")
print("   🎥 Camera always on for smooth performance")
print("   🚗 Vehicle detection via ultrasonic sensor")
print("   ⚪ Movable white violation line (drag with mouse)")
print("   🚗 Optimized YOLO + Haar cascade detection")
print("   💾 Automatic violation image saving")
print("   📧 Email notifications with Cashfree payment links")
print("   🌐 API integration for violation logging")
print("   🚧 Arduino-controlled boom barrier with servo")
print("   🎯 Only registers plates when vehicle is detected")
print("   ⚡ Frame skipping and background processing for better performance")
print("   📡 Smart Arduino communication (ultrasonic sensor based)")
if detector.keyboard_mode:
    print("   🎮 Keyboard simulation mode (Arduino not available)")
print()
print("🎮 Controls:")
print("   'q' key: Quit application")
print("   'c' key: Clear violation history")
print("   Mouse drag: Move detection line")
if detector.keyboard_mode:
    print("   'r' key: Simulate VEHICLE DETECTED")
    print("   'g' key: Simulate NO VEHICLE")
print()
print("✅ System ready! Arduino will control boom based on license plates.")
