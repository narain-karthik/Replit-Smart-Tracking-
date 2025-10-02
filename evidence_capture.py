import cv2
import os
from PIL import ImageGrab
from datetime import datetime
import threading

class EvidenceCapture:
    def __init__(self):
        self.evidence_dir = "data/evidence"
        self.ensure_evidence_directory()
    
    def ensure_evidence_directory(self):
        if not os.path.exists(self.evidence_dir):
            os.makedirs(self.evidence_dir)
    
    def capture_webcam_photo(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Cannot access webcam")
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(self.evidence_dir, f"webcam_{timestamp}.jpg")
                cv2.imwrite(filename, frame)
                return filename
        except Exception as e:
            print(f"Webcam capture error: {e}")
        return None
    
    def capture_screenshot(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.evidence_dir, f"screenshot_{timestamp}.png")
            screenshot = ImageGrab.grab()
            screenshot.save(filename)
            return filename
        except Exception as e:
            print(f"Screenshot capture error: {e}")
        return None
    
    def capture_evidence_set(self):
        results = {
            'timestamp': datetime.now().isoformat(),
            'webcam': None,
            'screenshot': None
        }
        
        webcam_file = self.capture_webcam_photo()
        if webcam_file:
            results['webcam'] = webcam_file
        
        screenshot_file = self.capture_screenshot()
        if screenshot_file:
            results['screenshot'] = screenshot_file
        
        return results
    
    def capture_multiple_photos(self, count=3, interval=2):
        captured = []
        for i in range(count):
            result = self.capture_evidence_set()
            captured.append(result)
            if i < count - 1:
                import time
                time.sleep(interval)
        return captured
    
    def get_evidence_files(self):
        files = []
        if os.path.exists(self.evidence_dir):
            for filename in os.listdir(self.evidence_dir):
                filepath = os.path.join(self.evidence_dir, filename)
                if os.path.isfile(filepath):
                    files.append({
                        'filename': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                    })
        return sorted(files, key=lambda x: x['modified'], reverse=True)
