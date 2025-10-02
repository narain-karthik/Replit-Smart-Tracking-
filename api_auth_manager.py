import json
import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import base64

class APIAuthManager:
    def __init__(self):
        self.data_dir = "data"
        self.api_auth_file = os.path.join(self.data_dir, "api_auth.enc")
        self.server_secret_file = os.path.join(self.data_dir, ".server_secret")
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_or_create_server_secret(self):
        if os.path.exists(self.server_secret_file):
            with open(self.server_secret_file, 'r') as f:
                return f.read().strip()
        else:
            import secrets
            server_secret = secrets.token_urlsafe(32)
            with open(self.server_secret_file, 'w') as f:
                f.write(server_secret)
            return server_secret
    
    def get_server_key(self):
        session_secret = os.environ.get('SESSION_SECRET')
        
        if not session_secret:
            session_secret = self.get_or_create_server_secret()
        
        from device_manager import DeviceManager
        device_manager = DeviceManager()
        device_id = device_manager.get_device_id()
        
        key_material = f"{session_secret}:{device_id}"
        salt = hashlib.sha256(device_id.encode()).digest()
        
        key = PBKDF2(key_material, salt, dkLen=32, count=50000)
        return key
    
    def save_api_credentials(self, api_key, user_email, user_name):
        try:
            key = self.get_server_key()
            
            api_data = {
                'api_key': api_key,
                'user_email': user_email,
                'user_name': user_name
            }
            
            cipher = AES.new(key, AES.MODE_EAX)
            ciphertext, tag = cipher.encrypt_and_digest(json.dumps(api_data).encode())
            encrypted = base64.b64encode(cipher.nonce + tag + ciphertext).decode()
            
            with open(self.api_auth_file, 'w') as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            print(f"Error saving API credentials: {e}")
            return False
    
    def get_api_credentials(self):
        try:
            if not os.path.exists(self.api_auth_file):
                return None
            
            with open(self.api_auth_file, 'r') as f:
                encrypted = base64.b64decode(f.read())
            
            key = self.get_server_key()
            nonce = encrypted[:16]
            tag = encrypted[16:32]
            ciphertext = encrypted[32:]
            
            cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
            data = cipher.decrypt_and_verify(ciphertext, tag)
            
            return json.loads(data.decode())
        except Exception as e:
            print(f"Error retrieving API credentials: {e}")
            return None
    
    def verify_api_key(self, provided_key):
        api_data = self.get_api_credentials()
        if not api_data:
            return False
        return api_data.get('api_key') == provided_key
    
    def get_user_info(self):
        api_data = self.get_api_credentials()
        if not api_data:
            return None
        return {
            'email': api_data.get('user_email'),
            'name': api_data.get('user_name')
        }
