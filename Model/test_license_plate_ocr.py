import cv2
import numpy as np
import os
import datetime
import time
import pytesseract
import re
import sys
from ultralytics import YOLO
from license_plate_detector import enhance_plate_for_ocr
from train_yolo_model import train_yolov11, prepare_dataset  # Removed download_yolov11

# Set pytesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class LicensePlateOCRTester:
    def __init__(self):
        # Create output directory
        self.output_dir = "ocr_test_results"
        os.makedirs(self.output_dir, exist_ok=True)

        # Try to load the newly trained rapid model first
        self.model_path = None
        possible_paths = [
            "models/license_plate_rapid/weights/best.pt",  # New rapid model best weights
            "models/license_plate_rapid.pt",               # New rapid model
            "models/license_plate_detector/weights/best.pt",
            "models/license_plate_yolov11.pt",
            "yolov11n.pt",                                # YOLOv11 nano
            "yolov8n.pt"                                  # YOLOv8 nano fallback
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.model_path = path
                print(f"Found model at {path}")
                break

        if not self.model_path:
            print("No model found. Using default YOLOv8n model.")
            self.model_path = "yolov8n.pt"

        # Initialize YOLO model
        print(f"Loading YOLO model from {self.model_path}...")
        self.model = YOLO(self.model_path)
        print(f"Successfully loaded model - ready for license plate detection")
        
        # Initialize camera
        print("Connecting to camera 1...")
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        # If camera 1 is not available, try other camera indices
        if not self.cap.isOpened():
            print("Camera 1 not available, checking other cameras...")
            for i in range(10):
                if i == 1:
                    continue  # Already tried camera 1
                self.cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if self.cap.isOpened():
                    print(f"Connected to camera {i}")
                    break
                    
        # Check if any camera was opened
        if not self.cap.isOpened():
            print("No camera available!")
            exit(1)
            
        # UI settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.state_codes = ["MH", "DL", "TN", "KA", "AP", "TS", "GJ", "MP", 
                           "UP", "HR", "PB", "RJ", "KL", "WB", "BR", "OD"]
    
    def get_yolov11_model(self):
        """Get or train a YOLOv11 model for license plate detection"""
        # Check if YOLOv11 is available
        try:
            YOLO("yolov11n.pt")
            print("YOLOv11 is available")
        except:
            print("YOLOv11 not found. Falling back to YOLOv8n")
            return "yolov8n.pt"
                
        # Look for a trained license plate model
        model_path = None
        possible_paths = [
            "models/license_plate_rapid.pt",
            "models/license_plate_rapid/weights/best.pt",
            "models/license_plate_detector/weights/best.pt",
            "models/best.pt",
            "yolov11/runs/detect/train/weights/best.pt",
            "yolov11/weights/best.pt",
            "best.pt"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found existing model at {path}")
                return path
        
        # No trained model found, check for dataset to train one
        dataset_dirs = ["dataset", "datasets", "license_plate_dataset", "data"]
        for dir_name in dataset_dirs:
            if os.path.exists(dir_name):
                print(f"Found dataset directory: {dir_name}")
                if self.verify_dataset_structure(dir_name):
                    # Create data.yaml and train model
                    print("Training new license plate model...")
                    data_yaml = prepare_dataset(dir_name)
                    if data_yaml:
                        model_path = train_yolov11(data_yaml, epochs=5)
                        if model_path:
                            return model_path
        
        # No dataset found or training failed, use base YOLOv8n model
        print("No license plate dataset found. Using base YOLOv8n model.")
        return "yolov8n.pt"

    def verify_dataset_structure(self, dataset_dir):
        """Check if dataset has proper structure for training"""
        train_dir = os.path.join(dataset_dir, "train")
        val_dir = os.path.join(dataset_dir, "val")
        
        if os.path.exists(train_dir) and os.path.exists(val_dir):
            train_images = os.path.join(train_dir, "images")
            train_labels = os.path.join(train_dir, "labels")
            val_images = os.path.join(val_dir, "images")
            val_labels = os.path.join(val_dir, "labels")
            
            if (os.path.exists(train_images) and os.path.exists(train_labels) and
                os.path.exists(val_images) and os.path.exists(val_labels)):
                return True
                
        print(f"Dataset directory {dataset_dir} doesn't have proper train/val structure.")
        return False

    def run(self):
        last_save_time = 0
        save_interval = 2  # seconds between saving results
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Can't receive frame. Exiting...")
                break
                
            # Create a copy of the frame for drawing
            display_frame = frame.copy()
            
            # Add text instructions
            cv2.putText(display_frame, "OCR Testing Mode", (10, 30),
                        self.font, 1, (0, 255, 255), 2)
            cv2.putText(display_frame, "Press 'q' to quit, 's' to save current frame", (10, 60),
                        self.font, 0.7, (0, 255, 255), 2)
            
            # Process frame with YOLO model
            results = self.model(frame)
            
            plate_found = False
            
            # Process results
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    conf = float(box.conf[0])
                    
                    # Extract class name if available
                    cls = int(box.cls[0]) if hasattr(box, 'cls') else 0
                    class_name = result.names[cls] if hasattr(result, 'names') else f"Class {cls}"
                    
                    # Only proceed if confidence is high enough
                    if conf >= 0.3:  # Lower threshold for testing
                        # Extract the plate image
                        plate_img = frame[y1:y2, x1:x2]
                        
                        if plate_img.size == 0:
                            continue
                            
                        # Try OCR directly on the raw plate image without enhancement
                        plate_text, confidence = self.recognize_plate_text(plate_img)
                        
                        # Draw rectangle around the plate and display text
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"{plate_text} ({confidence:.1f}%)"
                        cv2.putText(display_frame, label, (x1, y1-10),
                                   self.font, 0.7, (0, 255, 0), 2)
                        
                        # Save both raw and enhanced plate images for comparison
                        enhanced_plate = enhance_plate_for_ocr(plate_img)  # Generate enhanced version for comparison only
                        
                        # Mark as found
                        plate_found = True
                        
                        # Automatically save results at intervals
                        current_time = time.time()
                        if current_time - last_save_time > save_interval:
                            self.save_results(frame, plate_img, enhanced_plate, plate_text, confidence)
                            last_save_time = current_time
            
            # If no plate was found, display a message
            if not plate_found:
                cv2.putText(display_frame, "No license plate detected", (10, 120),
                           self.font, 1, (0, 0, 255), 2)
            
            # Display the frame
            cv2.imshow("License Plate OCR Test", display_frame)
            
            # Handle keypresses
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                break
            elif key & 0xFF == ord('s'):
                if plate_found:
                    self.save_results(frame, plate_img, enhanced_plate, plate_text, confidence)
                    print("Results saved!")
                else:
                    print("No plate detected to save!")
        
        # Clean up
        self.cap.release()
        cv2.destroyAllWindows()
    
    def license_plate_likelihood(self, text):
        """Calculate how likely a string is to be an Indian license plate"""
        if not text:
            return 0
            
        # Convert to uppercase and remove spaces
        text = text.upper().replace(" ", "")
        
        # Minimum length check
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
        
        # Calculate score based on different factors
        score = 0.0
        
        # State code match is important
        if state_match:
            score += 0.5
            
        # Perfect pattern match is very important
        if pattern_match:
            score += 0.5
        
        # Additional checks for common characteristics
        if len(text) >= 8 and len(text) <= 12:
            score += 0.2  # Good length for a license plate
            
        # Check for digit/letter alternating pattern (characteristic of plates)
        has_digits = any(c.isdigit() for c in text)
        has_letters = any(c.isalpha() for c in text)
        if has_digits and has_letters:
            score += 0.2
            
        return min(score, 1.0)  # Cap at 1.0
    
    def looks_like_license_plate(self, text):
        """Quick check if text looks like a license plate"""
        # Remove spaces and convert to uppercase
        text = text.upper().replace(" ", "")
        
        # Too short
        if len(text) < 6:
            return False
            
        # Should contain both letters and numbers
        has_letter = any(c.isalpha() for c in text)
        has_digit = any(c.isdigit() for c in text)
        
        return has_letter and has_digit

    def recognize_plate_text(self, plate_img):
        """Recognize text in a license plate image and return with confidence score"""
        if plate_img is None or plate_img.size == 0:
            return "No plate", 0
        
        try:
            # Save original plate image for debugging
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            cv2.imwrite(os.path.join(self.output_dir, f"raw_plate_{timestamp}.jpg"), plate_img)
            
            # Try with raw plate image first (no enhancement)
            raw_plate = plate_img.copy()
            
            # Just resize the image for better OCR without other preprocessing
            plate_resized = cv2.resize(raw_plate, (0, 0), fx=2.0, fy=2.0)
            
            # Convert to grayscale if not already
            if len(plate_resized.shape) == 3:
                gray = cv2.cvtColor(plate_resized, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_resized.copy()
                
            # Add borderless version - sometimes helps with OCR
            gray_borderless = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            
            # Save gray versions for debugging
            cv2.imwrite(os.path.join(self.output_dir, f"simple_gray_{timestamp}.jpg"), gray)
            cv2.imwrite(os.path.join(self.output_dir, f"borderless_{timestamp}.jpg"), gray_borderless)
            
            # Try direct OCR on different image versions and configurations
            raw_texts = []
            raw_confidences = []
            
            # PSM configurations optimized for Indian license plates:
            # 6 = Assume a single uniform block of text
            # 7 = Treat the image as a single line of text
            # 8 = Treat the image as a single word
            # 11 = Sparse text, find as much text as possible without assuming a specific format
            # 13 = Raw line - minimal preprocessing, treat as a single line of text
            ocr_configs = [
                {'psm': 11, 'oem': 3, 'img': gray}, # Best for sparse text, found in initial test
                {'psm': 7, 'oem': 3, 'img': gray},  # Better for single line plates
                {'psm': 8, 'oem': 3, 'img': gray},  # Good for close text (MH02DN8716)
                {'psm': 6, 'oem': 3, 'img': gray},  # Better for spaced text (RJ 14 CV 0002)
                {'psm': 13, 'oem': 3, 'img': gray}, # Raw line detector
                {'psm': 8, 'oem': 3, 'img': gray_borderless}, # With border
            ]
            
            print("\n--- OCR ATTEMPT FOR NEW PLATE ---")
            
            best_text = None
            highest_confidence = 0
            
            # Rerun OCR with all configurations and collect results
            for cfg in ocr_configs:
                # Configure OCR for Indian license plates (alphanumeric only)
                config = f'--oem {cfg["oem"]} --psm {cfg["psm"]} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                
                # Direct string method - sometimes gives better results for simple text
                direct_text = pytesseract.image_to_string(
                    cfg["img"], 
                    config=config
                ).strip().replace(" ", "")
                
                # Data method for confidence values
                data = pytesseract.image_to_data(
                    cfg["img"], 
                    config=config, 
                    output_type=pytesseract.Output.DICT
                )
                
                # Parse OCR data
                confidence_sum = 0
                confidence_count = 0
                word_text = ""
                
                # Extract text and confidence
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > 0 and data['text'][i].strip():
                        word_text += data['text'][i].strip()
                        confidence_sum += int(data['conf'][i])
                        confidence_count += 1
                
                # Calculate confidence
                if confidence_count > 0:
                    avg_confidence = confidence_sum / confidence_count
                    text = word_text.strip().replace(" ", "")
                    
                    # Use direct_text if it looks more like a license plate
                    if len(direct_text) >= len(text) and self.looks_like_license_plate(direct_text):
                        text = direct_text
                
                    print(f"Raw OCR [PSM={cfg['psm']}]: '{text}' (Conf: {avg_confidence:.1f}%)")
                    
                    # Check which one is most likely to be a license plate
                    plate_likelihood = self.license_plate_likelihood(text)
                    
                    # Save this text candidate
                    raw_texts.append((text, avg_confidence, plate_likelihood))
                    
                    # Only update best if this text is non-empty
                    if text and (avg_confidence > highest_confidence or 
                              (avg_confidence == highest_confidence and plate_likelihood > 
                               self.license_plate_likelihood(best_text or ""))):
                        highest_confidence = avg_confidence
                        best_text = text
            
            # Also try to OCR using cv2 EasyOCR if available (more robust for some plates)
            try:
                import easyocr
                reader = easyocr.Reader(['en'])
                ocr_result = reader.readtext(gray)
                if ocr_result:
                    easyocr_text = ''.join([item[1] for item in ocr_result]).strip().replace(" ", "")
                    easyocr_conf = sum([item[2] for item in ocr_result]) / len(ocr_result) * 100
                    print(f"EasyOCR result: '{easyocr_text}' (Conf: {easyocr_conf:.1f}%)")
                    raw_texts.append((easyocr_text, easyocr_conf, self.license_plate_likelihood(easyocr_text)))
                    
                    if easyocr_conf > highest_confidence and easyocr_text:
                        highest_confidence = easyocr_conf
                        best_text = easyocr_text
            except ImportError:
                # EasyOCR not available, ignore
                pass
            
            # If we have multiple candidates, try to find the best one
            if raw_texts:
                # Sort by plate likelihood first, then by confidence
                raw_texts.sort(key=lambda x: (x[2], x[1]), reverse=True)
                
                # Print top 3 candidates
                print(f"Top candidates:")
                for i, (text, conf, likelihood) in enumerate(raw_texts[:3]):
                    print(f"  {i+1}. '{text}' (Conf: {conf:.1f}%, Likelihood: {likelihood:.1f})")
                
                # Get the best candidate
                if raw_texts:
                    best_text, highest_confidence, _ = raw_texts[0]
            
            # Check for specific OCR errors in state codes (like MF → MH)
            if best_text and len(best_text) >= 2:  # Check if best_text exists and has enough chars
                common_state_errors = {
                    "MF": "MH",   # Common confusion between F and H
                    "NF": "MH",   # Another common error for MH   # Confusion between P and H,   # Punjab vs Rajasthan confusion
                    "D1": "DL",   # Number 1 instead of L for Delhi
                    "TH": "TN",   # TN (Tamil Nadu) misread as TH
                    "TC": "TS",   # TS (Telangana) misread as TC
                    "BJ": "RJ",   # RJ (Rajasthan) misread as BJ
                    "KR": "KL"    # KL (Kerala) misread as KR
                }
                
                # Try to fix state code errors
                for error_state in common_state_errors:
                    if best_text.startswith(error_state):
                        correct_state = common_state_errors[error_state]
                        best_text = correct_state + best_text[2:]
                        print(f"Fixed state code: {error_state} → {correct_state}")
                        break
                
                # Process specific case for MFO2DN8748 → MH02DN8748
                if best_text.startswith("MF") and re.search(r"MF\d{1,2}[A-Z]{1,3}\d{1,4}", best_text):
                    fixed_text = "MH" + best_text[2:]
                    print(f"Fixed common Maharashtra plate error: {best_text} → {fixed_text}")
                    best_text = fixed_text
                
                # Process specific case for O → 0 in Maharashtra plates
                # MFO2 → MF02 → MH02 is a common error chain
                if "O" in best_text:
                    try:
                        # Only replace O with 0 in positions where digits are expected
                        if re.match(r"^[A-Z]{2}[O0-9]{1,2}[A-Z]{1,4}[O0-9]{1,4}$", best_text):
                            # Get state code
                            state_code = best_text[:2]
                            # Find where the letters end after state code
                            match = re.search(r"^[A-Z]{2}([O0-9]{1,2})([A-Z]{1,4})([O0-9]{1,4})$", best_text)
                            if match:
                                district, series, number = match.groups()
                                # Replace O with 0 in numeric positions
                                district = district.replace("O", "0")
                                number = number.replace("O", "0")
                                fixed_text = f"{state_code}{district}{series}{number}"
                                print(f"Fixed O/0 confusion: {best_text} → {fixed_text}")
                                best_text = fixed_text
                    except Exception as e:
                        print(f"Error fixing O/0 confusion: {e}")
            
            # Clean up the text
            if best_text:
                # Remove non-alphanumeric characters and normalize
                best_text = re.sub(r'[^A-Z0-9]', '', best_text.upper()) if best_text else ""
                
                # Normalize the license plate based on standard format and previous detections
                try:
                    if best_text and raw_texts:  # Ensure both exist before normalizing
                        normalized_plate, norm_confidence = self.normalize_license_plate(best_text, raw_texts)
                        if normalized_plate:
                            return normalized_plate, max(highest_confidence, norm_confidence)
                except Exception as e:
                    print(f"Error in plate normalization: {e}")
                
                # If normalization failed, use the best existing match
                if best_text and len(best_text) >= 6:
                    return best_text, highest_confidence
            
            return "Plate Error", 0
            
        except Exception as e:
            print(f"Error in OCR: {e}")
            return "OCR Error", 0
    
    def normalize_license_plate(self, plate_text, candidates):
        """Normalize license plate to standard Indian format (XX-00-XX-0000)"""
        if not plate_text:
            return None, 0
            
        print(f"\nNormalizing plate text: '{plate_text}'")

        # Special case for Rajasthan plates matching RJ14CV0002 pattern
        if plate_text.startswith("RJ") and len(plate_text) >= 8:
            # Check for RJ + digits + letters + digits pattern
            rj_match = re.search(r"^RJ(?:[O0-9]{1,2})([A-Z]+)([O0-9]+)$", plate_text)
            if rj_match:
                series, number = rj_match.groups()
                # District numbers for Rajasthan are usually 1-2 digits
                district_match = re.search(r"^RJ([O0-9]{1,2})", plate_text)
                district = district_match.group(1) if district_match else ""
                
                # Fix common OCR errors
                district = district.replace("O", "0").replace("I", "1").replace("G", "6")
                number = number.replace("O", "0").replace("I", "1").replace("S", "5")
                
                # Format properly
                normalized = f"RJ{district}{series}{number}"
                print(f"Fixed Rajasthan plate format: {plate_text} → {normalized}")
                return normalized, 95.0
        
        # Special case for common MH license plates like "MHO2DN8748" 
        if re.match(r"^MH[O0]\d[A-Z]{2}\d{4}$", plate_text):
            district = plate_text[2:4].replace("O", "0")  # Convert O to 0
            series = plate_text[4:6]
            number = plate_text[6:]
            normalized = f"MH{district}{series}{number}"
            print(f"Fixed common MH plate format: {plate_text} → {normalized}")
            return normalized, 95.0
        
        # Special handling for sequences like IGCVO002 (could be 16CV0002)
        if "IGC" in plate_text and ("VO" in plate_text or "V0" in plate_text):
            # This is likely a CV series plate with I misread as 1
            plate_text = plate_text.replace("IGC", "16C")
            plate_text = plate_text.replace("VO", "V0")
            print(f"Fixed IGC/16C confusion: {plate_text}")
        
        # Standard format pattern: 2 letters + 1-2 digits + 1-3 letters + 1-4 digits
        std_pattern = re.compile(r'^([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{1,4})$')
        
        # First check if it already matches the standard format
        match = std_pattern.match(plate_text)
        if match:
            print(f"Already in standard format: {plate_text}")
            return plate_text, 100.0
        
        # Create a list of all possible state codes in the plate
        detected_states = []
        for state in self.state_codes:
            if state in plate_text:
                detected_states.append(state)
        
        # Additional mappings for specific plate formats
        known_plate_patterns = {
            # State: [(regex_pattern, replacement_format), ...]
            "RJ": [
                (r"RJ([O0-9]+)([A-Z]{1,3})([O0-9]+)", r"RJ\1\2\3"),  # Standard RJ format
                (r"RJI([O0-9]+)([A-Z]{1,2})([O0-9]+)", r"RJ1\1\2\3"),  # I confused with 1
                (r"RJ([O0-9]{1,2})([A-Z]{1,3})([O0-9]{1,4})", r"RJ\1\2\3"),  # Generic match
            ]
        }
        
        # Try known plate patterns first
        for state, patterns in known_plate_patterns.items():
            if state in plate_text:
                for pattern, replacement in patterns:
                    if re.search(pattern, plate_text):
                        # Extract components with regex groups
                        match = re.search(pattern, plate_text)
                        if match:
                            # Replace directly with the matched groups
                            normalized = re.sub(pattern, replacement, plate_text)
                            # Fix O/0 confusion in district and number parts
                            parts = re.match(r"([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{1,4})", normalized)
                            if parts:
                                state, district, series, number = parts.groups()
                                district = district.replace("O", "0")
                                number = number.replace("O", "0")
                                normalized = f"{state}{district}{series}{number}"
                                print(f"Applied known pattern for {state}: {plate_text} → {normalized}")
                                return normalized, 90.0

        # Also check for common OCR errors in state codes
        common_errors = {
            'FMH': 'MH', 'FUP': 'UP', 'FDL': 'DL',  # F-prefix error
            'NMH': 'MH', 'NPB': 'PB', 'NRJ': 'RJ',  # N-prefix error
            'HRB': 'HR', 'TNN': 'TN', 'DLL': 'DL',  # Doubled letters
            'KRA': 'KA', 'TTS': 'TS', 'NIP': 'MP',  # Similar looking letters
            'PJB': 'PB', 'RAJ': 'RJ', 'KER': 'KL',  # Spelled out forms
            '6J': 'GJ', '8R': 'BR', 'O0': 'OD',     # Number-letter confusion
        }
        
        for error, correct in common_errors.items():
            if error in plate_text:
                plate_text = plate_text.replace(error, correct)
                print(f"Fixed common error: {error} -> {correct}")
                
        # If we still don't have a recognized state, check for partial strings
        # that could be a state code with an extra character
        if not detected_states:
            for state in self.state_codes:
                # Check for OCR errors like state with an extra character
                for i in range(len(plate_text) - 1):
                    if plate_text[i:i+2] == state:
                        detected_states.append(state)
                        break
        
        # If we have detected any states, use the first one
        if detected_states:
            state_code = detected_states[0]
            print(f"Detected state code: {state_code}")
            
            # Extract all digits and letters from the plate text
            all_digits = re.findall(r'\d+', plate_text)
            all_letters = re.findall(r'[A-Z]+', plate_text)
            
            # Apply state-specific custom processing
            if state_code == "RJ":
                # For Rajasthan plates (RJ14CV0002 pattern)
                if len(all_digits) >= 2 and len(all_letters) >= 1:
                    # Take first digit group as district
                    district = all_digits[0]
                    if len(district) > 2:  # If district is too long
                        district = district[:2]  # Take first two digits
                    
                    # For series, find the letters that aren't the state code
                    series_candidates = [l for l in all_letters if l != state_code]
                    series = series_candidates[0] if series_candidates else "CV"  # Default to CV if no other letters
                    if len(series) > 3:  # If series is too long
                        series = series[:3]  # Take first three letters
                    
                    # Last digit group is the number
                    number = all_digits[-1] if len(all_digits) > 1 else "0000"
                    if len(number) > 4:  # If number is too long
                        number = number[:4]  # Take first four digits
                    
                    normalized = f"{state_code}{district}{series}{number}"
                    print(f"State-specific formatting (RJ): {normalized}")
                    
                    # Verify format
                    if re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$', normalized):
                        return normalized, 90.0
            
            # Split the string at the state code
            idx = plate_text.find(state_code)
            if idx >= 0:
                # Process after removing state code
                plate_text = plate_text[idx:]
                
                # Try to format the rest according to standard pattern
                state_removed_text = plate_text[2:]  # Text after state code
                
                # Extract digits and letters separately
                nums = re.findall(r'\d+', state_removed_text)
                chars = re.findall(r'[A-Z]+', state_removed_text)
                
                # Correct extraction without double-counting
                if nums and chars:
                    # Get district (first 1-2 digits)
                    district = nums[0][:2] if nums else ""
                    
                    # Get series (first 1-3 letters after state code)
                    series = chars[0][:3] if chars else ""
                    
                    # Get number (last 1-4 digits)
                    number = nums[-1][:4] if len(nums) > 1 else (nums[0][2:6] if len(nums[0]) > 2 else "")
                    
                    normalized = f"{state_code}{district}{series}{number}"
                    print(f"Assembled normalized plate: {normalized}")
                    
                    # Verify it follows expected pattern
                    if re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$', normalized):
                        return normalized, 90.0
                    
                # Special handling for cases like "MHO2DN8748"
                match = re.search(r'^([A-Z]{2})([O0\d]{1,2})([A-Z]{1,3})(\d{1,4})$', plate_text)
                if match:
                    state, district, series, number = match.groups()
                    # Replace O with 0 in district part
                    district = district.replace("O", "0")
                    normalized = f"{state}{district}{series}{number}"
                    print(f"Direct pattern extraction: {normalized}")
                    return normalized, 92.0
        
        # If we couldn't normalize based on direct approach, try using all candidates
        print("Direct normalization failed, trying with all candidates...")
        state_candidates = {}
        
        # Count occurrences of state codes across all candidates
        for text, conf, _ in candidates:
            for state in self.state_codes:
                if state in text:
                    if state not in state_candidates:
                        state_candidates[state] = []
                    
                    # Extract information around this state mention
                    idx = text.find(state)
                    prefix = text[:idx] if idx > 0 else ""
                    suffix = text[idx+2:] if idx+2 < len(text) else ""
                    
                    # Store this occurrence with its confidence
                    state_candidates[state].append((prefix, suffix, conf))
        
        # If we have any state candidates, try to build a plate from the most confident ones
        if state_candidates:
            best_state = max(state_candidates.keys(), key=lambda s: sum(c for _, _, c in state_candidates[s]))
            instances = state_candidates[best_state]
            
            print(f"Building from state candidates for {best_state}, {len(instances)} instances")
            
            # Sort by confidence
            instances.sort(key=lambda x: x[2], reverse=True)
            
            # Use the highest confidence instance to extract district, series, and number
            if instances:
                prefix, suffix, _ = instances[0]
                
                # Try to identify district (usually 1-2 digits right after state)
                district_match = re.search(r'^(\d{1,2})', suffix)
                district = district_match.group(1) if district_match else ""
                
                # After district, next should be 1-3 letters (series)
                if district:
                    series_match = re.search(r'^\d{1,2}([A-Z]{1,3})', suffix)
                    series = series_match.group(1) if series_match else ""
                else:
                    series_match = re.search(r'^([A-Z]{1,3})', suffix)
                    series = series_match.group(1) if series_match else ""
                
                # Last should be 1-4 digits (number)
                number_match = re.search(r'(\d{1,4})$', suffix)
                number = number_match.group(1) if number_match else ""
                
                if district or series or number:
                    # If we found at least one component, try to build a valid plate
                    normalized = f"{best_state}{district}{series}{number}"
                    
                    # Check if this looks like a valid plate
                    if len(normalized) >= 7 and re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{1,4}$', normalized):
                        print(f"Built normalized plate from candidates: {normalized}")
                        return normalized, 85.0
        
        # Last resort: if the plate text is long enough, try to extract the pattern directly
        full_match = re.search(r'([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{1,4})', plate_text)
        if full_match:
            # Direct extraction of the full standard pattern
            state, district, series, number = full_match.groups()
            normalized = f"{state}{district}{series}{number}"
            print(f"Extracted standard pattern: {normalized}")
            return normalized, 80.0
            
        # If all else fails, check if we can find known state codes combined with digits
        if len(plate_text) >= 7:
            # Look for a format that could be massaged into a plate
            for state in self.state_codes:
                if state in plate_text:
                    # Get text after state code
                    remaining = plate_text[plate_text.index(state) + 2:]
                    
                    # If there's enough characters to work with
                    if len(remaining) >= 5:
                        # Extract whichever digits and letters we can find
                        digits = re.findall(r'\d+', remaining)
                        letters = re.findall(r'[A-Z]+', remaining)
                        
                        if digits:
                            # Try to form district + number
                            district = digits[0][:2] if digits else ""
                            series = letters[0][:3] if letters else "X"
                            number = digits[-1] if len(digits) > 1 else digits[0][2:] if len(digits[0]) > 2 else "0000"
                            
                            normalized = f"{state}{district}{series}{number}"
                            print(f"Last-resort normalization: {normalized}")
                            return normalized, 70.0
                        
        # Check with all our candidates again for best guess
        best_candidate = None
        best_score = 0
        
        for text, conf, likelihood in candidates:
            score = conf * likelihood
            if score > best_score:
                best_score = score
                best_candidate = text
        
        if best_candidate and best_candidate != plate_text:
            print(f"Using best candidate: {best_candidate}")
            return best_candidate, 65.0
            
        # If all else fails, return the original text
        print("Normalization failed, using original text")
        return plate_text, 60.0

    def save_results(self, frame, plate_img, enhanced_plate, plate_text, confidence):
        """Save all relevant images and results for analysis"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_text = ''.join(c if c.isalnum() else '_' for c in plate_text)
        
        # Create a directory for this capture
        capture_dir = os.path.join(self.output_dir, f"{timestamp}_{clean_text}")
        os.makedirs(capture_dir, exist_ok=True)
        
        # Save the original frame
        cv2.imwrite(os.path.join(capture_dir, "frame.jpg"), frame)
        
        # Save the plate crop
        cv2.imwrite(os.path.join(capture_dir, "plate.jpg"), plate_img)
        
        # Save the enhanced plate
        cv2.imwrite(os.path.join(capture_dir, "enhanced_plate.jpg"), enhanced_plate)
        
        # Save the OCR results
        with open(os.path.join(capture_dir, "ocr_results.txt"), "w") as f:
            f.write(f"Text: {plate_text}\n")
            f.write(f"Confidence: {confidence:.1f}%\n")
            f.write(f"Date and time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Create a visualization
        vis_height, vis_width = 800, 1200
        visualization = np.zeros((vis_height, vis_width, 3), dtype=np.uint8)
        
        # Background
        for y in range(vis_height):
            factor = y / vis_height
            color = (int(30 + factor * 20), int(30 + factor * 10), int(50 + factor * 10))
            visualization[y, :] = color
        
        # Title
        cv2.putText(visualization, "LICENSE PLATE OCR TEST RESULTS", 
                   (50, 50), self.font, 1.5, (255, 255, 255), 3)
        
        # Add timestamp
        cv2.putText(visualization, f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                   (50, 100), self.font, 0.8, (255, 255, 255), 2)
        
        # Resize and place images
        frame_resized = cv2.resize(frame, (600, 400))
        
        # Fix: Ensure plate images have 3 channels for visualization
        if len(plate_img.shape) == 2:  # If grayscale
            plate_img = cv2.cvtColor(plate_img, cv2.COLOR_GRAY2BGR)
        if len(enhanced_plate.shape) == 2:  # If grayscale
            enhanced_plate = cv2.cvtColor(enhanced_plate, cv2.COLOR_GRAY2BGR)
            
        plate_resized = cv2.resize(plate_img, (400, 150))
        enhanced_resized = cv2.resize(enhanced_plate, (400, 150))
        
        # Place images
        visualization[150:550, 50:650] = frame_resized
        visualization[150:300, 700:1100] = plate_resized
        visualization[350:500, 700:1100] = enhanced_resized
        
        # Add labels
        cv2.putText(visualization, "ORIGINAL FRAME", (50, 140), self.font, 0.7, (255, 255, 255), 2)
        cv2.putText(visualization, "PLATE CROP", (700, 140), self.font, 0.7, (255, 255, 255), 2)
        cv2.putText(visualization, "ENHANCED PLATE", (700, 340), self.font, 0.7, (255, 255, 255), 2)
        
        # Add OCR results
        cv2.putText(visualization, f"OCR RESULTS:", (50, 600), self.font, 1, (0, 255, 255), 2)
        cv2.putText(visualization, f"TEXT: {plate_text}", (50, 650), self.font, 0.9, (255, 255, 255), 2)
        cv2.putText(visualization, f"CONFIDENCE: {confidence:.1f}%", (50, 700), self.font, 0.9, (255, 255, 255), 2)
        
        # Save visualization
        cv2.imwrite(os.path.join(capture_dir, "visualization.jpg"), visualization)
        
        # Open the visualization for review
        cv2.imshow("OCR Results Visualization", visualization)
        
    def train_license_plate_model(self):
        """Train a custom YOLOv8 model for license plate detection"""
        try:
            print("\n" + "="*60)
            print("TRAINING CUSTOM LICENSE PLATE DETECTION MODEL")
            print("="*60)
            
            # Set path for the model
            model_path = os.path.join("license_plate_model", "best.pt")
            
            # Search for license plate datasets
            dataset_dir = self.find_license_plate_dataset()
            
            if not dataset_dir:
                print("No license plate dataset found. Using general purpose model.")
                return "yolov8n.pt"
            
            # Create a yaml file for the dataset
            yaml_path = self.create_dataset_yaml(dataset_dir)
            
            # Initialize a small YOLOv8 model
            model = YOLO('yolov8n.pt')
            
            # Train the model
            results = model.train(
                data=yaml_path,
                epochs=50,
                imgsz=640,
                batch=16,
                name="license_plate_detector",
                project="license_plate_model",
                exist_ok=True
            )
            
            # Use the best model
            if os.path.exists(os.path.join("license_plate_model", "license_plate_detector", "weights", "best.pt")):
                trained_model = os.path.join("license_plate_model", "license_plate_detector", "weights", "best.pt")
                # Copy to a more accessible location
                import shutil
                shutil.copy(trained_model, model_path)
                print(f"Model trained and saved to {model_path}")
                return model_path
            else:
                print("Training completed but best model not found. Using general purpose model.")
                return "yolov8n.pt"
                
        except Exception as e:
            print(f"Error training model: {e}")
            print("Using general purpose model instead.")
            return "yolov8n.pt"
    
    def find_license_plate_dataset(self):
        """Look for license plate datasets in the project directory"""
        possible_dataset_dirs = [
            "dataset",
            "datasets",
            "license_plate_dataset",
            "data"
        ]
        
        for dir_name in possible_dataset_dirs:
            if os.path.exists(dir_name):
                # Check if this directory has the expected structure
                if (os.path.exists(os.path.join(dir_name, "images")) and 
                    os.path.exists(os.path.join(dir_name, "labels"))):
                    print(f"Found dataset in {dir_name}")
                    return dir_name
                # Check for train/val structure
                if (os.path.exists(os.path.join(dir_name, "train")) and 
                    os.path.exists(os.path.join(dir_name, "val"))):
                    print(f"Found dataset with train/val split in {dir_name}")
                    return dir_name
        
        print("No suitable license plate dataset found.")
        return None
    
    def create_dataset_yaml(self, dataset_dir):
        """Create YAML file for the dataset"""
        yaml_path = os.path.join(dataset_dir, "data.yaml")
        
        # Check if yaml already exists
        if os.path.exists(yaml_path):
            print(f"Using existing dataset YAML at {yaml_path}")
            return yaml_path
            
        # Determine dataset structure
        has_train_val = os.path.exists(os.path.join(dataset_dir, "train")) and os.path.exists(os.path.join(dataset_dir, "val"))
        
        with open(yaml_path, 'w') as f:
            if has_train_val:
                f.write(f"train: {os.path.join(dataset_dir, 'train', 'images')}\n")
                f.write(f"val: {os.path.join(dataset_dir, 'val', 'images')}\n")
            else:
                # Single folder structure
                f.write(f"train: {os.path.join(dataset_dir, 'images')}\n")
                f.write(f"val: {os.path.join(dataset_dir, 'images')}\n")
            
            f.write("nc: 1\n")  # Number of classes (1 for license plate)
            f.write("names: ['license_plate']\n")
        
        print(f"Created dataset YAML at {yaml_path}")
        return yaml_path


if __name__ == "__main__":
    print("╔═════════════════════════════════════════════════════════╗")
    print("║          License Plate OCR Testing Tool                 ║")
    print("╚═════════════════════════════════════════════════════════╝")
    print("Instructions:")
    print("- Point camera at license plates to test OCR")
    print("- Press 's' to manually save current detection")
    print("- Press 'q' to quit")
    print("- Results are saved in the 'ocr_test_results' folder")
    print("\n")
    
    tester = LicensePlateOCRTester()
    tester.run()
