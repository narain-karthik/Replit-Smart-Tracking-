import uuid
import os
import json
import platform
import psutil
from datetime import datetime

class DeviceManager:
    def __init__(self):
        self.data_dir = "data"
        self.device_file = os.path.join(self.data_dir, "device_info.json")
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def generate_device_id(self):
        if os.path.exists(self.device_file):
            with open(self.device_file, 'r') as f:
                data = json.load(f)
                return data.get('device_id')
        
        device_id = str(uuid.uuid4())
        device_info = {
            'device_id': device_id,
            'hostname': platform.node(),
            'system': platform.system(),
            'processor': platform.processor(),
            'registered_at': datetime.now().isoformat()
        }
        
        with open(self.device_file, 'w') as f:
            json.dump(device_info, f, indent=2)
        
        return device_id
    
    def get_device_id(self):
        if os.path.exists(self.device_file):
            with open(self.device_file, 'r') as f:
                data = json.load(f)
                return data.get('device_id', 'Unknown')
        return self.generate_device_id()
    
    def get_device_info(self):
        info = {
            'hostname': platform.node(),
            'system': platform.system(),
            'release': platform.release(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
            'disk_usage': f"{psutil.disk_usage('/').percent}%"
        }
        return info
