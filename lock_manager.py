import json
import os
from datetime import datetime

class LockManager:
    def __init__(self):
        self.data_dir = "data"
        self.lock_file = os.path.join(self.data_dir, "lock_status.json")
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def set_lock_status(self, is_locked, message=""):
        try:
            lock_data = {
                'is_locked': is_locked,
                'lock_message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error setting lock status: {e}")
            return False
    
    def is_locked(self):
        try:
            if os.path.exists(self.lock_file):
                with open(self.lock_file, 'r') as f:
                    data = json.load(f)
                    return data.get('is_locked', False)
        except:
            pass
        return False
    
    def get_lock_message(self):
        try:
            if os.path.exists(self.lock_file):
                with open(self.lock_file, 'r') as f:
                    data = json.load(f)
                    return data.get('lock_message', '')
        except:
            pass
        return ''
