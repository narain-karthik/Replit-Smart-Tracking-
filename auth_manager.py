import json
import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import base64
from datetime import datetime
import secrets

class AuthManager:
    def __init__(self):
        self.data_dir = "data"
        self.auth_file = os.path.join(self.data_dir, "auth.enc")
        self.salt_file = os.path.join(self.data_dir, ".salt")
        self.cached_password = None
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_api_key(self):
        return secrets.token_urlsafe(32)
    
    def get_or_create_salt(self):
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            salt = get_random_bytes(32)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return salt
    
    def derive_key_from_password(self, password):
        salt = self.get_or_create_salt()
        key = PBKDF2(password.encode(), salt, dkLen=32, count=100000)
        return key
    
    def encrypt_data(self, data, password):
        key = self.derive_key_from_password(password)
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(json.dumps(data).encode())
        return base64.b64encode(cipher.nonce + tag + ciphertext).decode()
    
    def decrypt_data(self, password=None):
        if not os.path.exists(self.auth_file):
            return None
        
        if password is None:
            password = self.cached_password
        
        if password is None:
            return None
        
        try:
            with open(self.auth_file, 'r') as f:
                encrypted = base64.b64decode(f.read())
            
            key = self.derive_key_from_password(password)
            nonce = encrypted[:16]
            tag = encrypted[16:32]
            ciphertext = encrypted[32:]
            
            cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
            data = cipher.decrypt_and_verify(ciphertext, tag)
            return json.loads(data.decode())
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
    
    def is_device_registered(self):
        return os.path.exists(self.auth_file)
    
    def register_device(self, name, email, password, contact):
        try:
            api_key = self.generate_api_key()
            
            user_data = {
                'name': name,
                'email': email,
                'password': self.hash_password(password),
                'contact': contact,
                'api_key': api_key,
                'registered_at': datetime.now().isoformat(),
                'is_locked': False,
                'lock_message': ''
            }
            
            encrypted = self.encrypt_data(user_data, password)
            with open(self.auth_file, 'w') as f:
                f.write(encrypted)
            
            from api_auth_manager import APIAuthManager
            api_auth = APIAuthManager()
            api_auth.save_api_credentials(api_key, email, name)
            
            self.cached_password = password
            return True
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def verify_login(self, email, password):
        try:
            data = self.decrypt_data(password)
            if not data:
                return False
            
            if data['email'] == email and data['password'] == self.hash_password(password):
                self.cached_password = password
                return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_user_data(self):
        try:
            return self.decrypt_data()
        except:
            return None
    
    def update_lock_status(self, is_locked, message=""):
        try:
            data = self.decrypt_data()
            if data:
                data['is_locked'] = is_locked
                data['lock_message'] = message
                encrypted = self.encrypt_data(data, self.cached_password)
                with open(self.auth_file, 'w') as f:
                    f.write(encrypted)
                return True
        except Exception as e:
            print(f"Update lock status error: {e}")
        return False
    
    def is_device_locked(self):
        try:
            data = self.decrypt_data()
            return data.get('is_locked', False) if data else False
        except:
            return False
    
    def get_lock_message(self):
        try:
            data = self.decrypt_data()
            return data.get('lock_message', '') if data else ''
        except:
            return ''
    
    def log_failed_attempt(self, email):
        log_file = os.path.join(self.data_dir, "failed_attempts.log")
        with open(log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - Failed login attempt: {email}\n")
