import cv2
import numpy as np
import time
import os

class EasyLicensePlateDetector:
    """Simplified license plate detector focused on reliability"""
    
    def __init__(self):
        cascade_files = [
            'haarcascade_russian_plate_number.xml',
            'haarcascade_license_plate_rus_16stages.xml',
            'indian_license_plate.xml',
            # Add paths to any other cascade files here
        ]
        
        self.plate_cascade = None
        for cascade_file in cascade_files:
            try:
                # Try with OpenCV's built-in path
                cascade = cv2.CascadeClassifier(cv2.data.haarcascades + cascade_file)
                if not cascade.empty():
                    print(f"Loaded cascade classifier: {cascade_file}")
                    print("Found a match!")
                    self.plate_cascade = cascade
                    break
                    
                # If not found, try in the current directory
                elif os.path.exists(cascade_file):
                    cascade = cv2.CascadeClassifier(cascade_file)
                    if not cascade.empty():
                        print(f"Loaded cascade classifier from current directory: {cascade_file}")
                        self.plate_cascade = cascade
                        break
            except Exception as e:
                print(f"Failed to load cascade file {cascade_file}: {e}")
        
        # If no cascade can be loaded, use our backup plan
        if self.plate_cascade is None:
            print("No license plate cascade found. Using basic detection method.")
    
    def detect_plates(self, image):
        """Detect license plates in an image using a reliable approach"""
        if image is None or image.size == 0:
            return []
            
        # Create grayscale version
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        debug_dir = "debug_plates"
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = int(time.time())
        cv2.imwrite(f"{debug_dir}/enhanced_{timestamp}.jpg", gray)
        
        plates = []
        
        # Method 1: Try Haar cascade if available
        if self.plate_cascade is not None:
            try:
                detected_plates = self.plate_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 20), maxSize=(300, 100)
                )
                
                for (x, y, w, h) in detected_plates:
                    ratio = float(w) / h
                    if 2.0 < ratio < 6.0:  # License plate aspect ratio
                        plate_img = image[y:y+h, x:x+w]
                        plates.append((plate_img, (x, y, w, h)))
                        
                        # Save detected plate for inspection
                        cv2.imwrite(f"{debug_dir}/cascade_plate_{timestamp}_{len(plates)}.jpg", plate_img)
            except Exception as e:
                print(f"Haar cascade detection failed: {e}")
        
        # Method 2: Use edge detection - finding the boundaries
        # Sometimes we need to find the edges to appreciate what's inside
        if not plates:
            try:
                # Edge detection 
                edges = cv2.Canny(gray, 100, 200)
                cv2.imwrite(f"{debug_dir}/edges_{timestamp}.jpg", edges)
                
                # Find contours - tracing the shapes that matter
                contours, _ = cv2.findContours(edges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
                # Sort contours by area (largest first) - focusing on what's important
                contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]
                
                # Draw all contours on a copy for debugging
                contour_img = image.copy()
                cv2.drawContours(contour_img, contours, -1, (0, 255, 0), 2)
                cv2.imwrite(f"{debug_dir}/contours_{timestamp}.jpg", contour_img)
                
                for i, contour in enumerate(contours):
                    # Approximate the contour 
                    peri = cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

                    # If it's a rectangle (4 points)
                    if len(approx) == 4:
                        x, y, w, h = cv2.boundingRect(approx)
                        ratio = float(w) / h
                        area = w * h

                        # Filter by aspect ratio and size
                        if 2.0 < ratio < 6.0 and 1000 < area < 30000:
                            try:
                                # Make sure it's within image boundaries
                                if y >= 0 and x >= 0 and y+h <= image.shape[0] and x+w <= image.shape[1]:
                                    plate_img = image[y:y+h, x:x+w]
                                    plates.append((plate_img, (x, y, w, h)))
                                    
                                    # Save for debugging
                                    cv2.imwrite(f"{debug_dir}/contour_plate_{timestamp}_{i}.jpg", plate_img)
                            except Exception as e:
                                print(f"Error extracting plate: {e}")
            except Exception as e:
                print(f"Contour-based detection failed: {e}")
                
        # Method 3: If all else fails, try traditional rectangular shape detection
        if not plates:
            try:
                # Use simple rectangular detection
                gray_blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                thresh = cv2.adaptiveThreshold(gray_blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                              cv2.THRESH_BINARY_INV, 11, 2)
                                              
                cv2.imwrite(f"{debug_dir}/thresh_{timestamp}.jpg", thresh)
                
                # Find horizontal and vertical lines - structure matters
                vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
                horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
                
                vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
                horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
                
                combined = cv2.add(vertical_lines, horizontal_lines)
                cv2.imwrite(f"{debug_dir}/lines_{timestamp}.jpg", combined)
                
                # Find contours of potential rectangles
                contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    ratio = float(w) / h
                    area = w * h
                    
                    if 2.0 < ratio < 6.0 and 1000 < area < 30000:
                        try:
                            if y >= 0 and x >= 0 and y+h <= image.shape[0] and x+w <= image.shape[1]:
                                plate_img = image[y:y+h, x:x+w]
                                plates.append((plate_img, (x, y, w, h)))
                        except:
                            pass
            except Exception as e:
                print(f"Rectangle detection failed: {e}")
        
        print(f"Found {len(plates)} potential license plates - searching for the perfect match")
        return plates


def enhance_plate_for_ocr(plate_img):
    """Enhance a license plate image for better OCR results"""
    if plate_img is None or plate_img.size == 0:
        return None
    
    try:
        # Create a directory for our enhanced images
        debug_dir = "enhanced_plates"
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = int(time.time())
        
        # Save the original for comparison
        cv2.imwrite(f"{debug_dir}/original_{timestamp}.jpg", plate_img)

        # Resize to larger dimensions
        h, w = plate_img.shape[:2]
        plate_img = cv2.resize(plate_img, (w*3, h*3))
        
        # Convert to grayscale - focusing on what matters
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(f"{debug_dir}/gray_{timestamp}.jpg", gray)
        
        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(gray, 11, 17, 17)
        cv2.imwrite(f"{debug_dir}/filtered_{timestamp}.jpg", filtered)
        
        # Try multiple preprocessing methods - I like to be thorough for you
        
        # Method 1: Adaptive threshold
        thresh1 = cv2.adaptiveThreshold(filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        cv2.imwrite(f"{debug_dir}/thresh1_{timestamp}.jpg", thresh1)
        
        # Method 2: OTSU threshold 
        _, thresh2 = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite(f"{debug_dir}/thresh2_{timestamp}.jpg", thresh2)
        
        # Method 3: Edge enhancement
        edges = cv2.Canny(filtered, 30, 200)
        kernel = np.ones((3,3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)
        cv2.imwrite(f"{debug_dir}/edges_{timestamp}.jpg", dilated_edges)

        # Choose the best method
        # For OCR, usually the adaptive threshold works well
        processed = thresh1
        
        # Final touch - make the text stand out even more
        kernel = np.ones((2, 1), np.uint8)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        # Save our final masterpiece
        cv2.imwrite(f"{debug_dir}/final_{timestamp}.jpg", processed)
        
        print("Enhanced your plate to perfection!")
        return processed
        
    except Exception as e:
        print(f"Error enhancing plate image: {e}")
        return plate_img
