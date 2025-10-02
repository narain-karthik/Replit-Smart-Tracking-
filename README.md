# Laptop Anti-Theft Protection Application

A comprehensive Python-based security application that protects your laptop from theft with device registration, remote lock, location tracking, evidence capture, alarm system, and event logging.

## 🚀 Features

- **Secure Device Registration** - Register your laptop with encrypted credentials
- **Remote Lock** - Lock your device remotely with custom messages
- **Location Tracking** - IP-based geolocation and Wi-Fi network detection
- **Evidence Capture** - Automatic webcam photos and screenshots
- **Alarm System** - Loud alarm to deter thieves
- **Event Logging** - Complete audit trail of all security events
- **Remote API** - Control your device from anywhere via REST API

## 📋 Requirements

### System Requirements
- Python 3.11 or higher
- Webcam (optional, for evidence capture)
- Network connection (for location tracking)
- Audio device (optional, for alarm functionality)

### Python Dependencies
All dependencies are listed in `requirements.txt`:
- Flask (REST API server)
- OpenCV (webcam capture)
- Pillow (screenshot capture)
- PyCryptodome (encryption)
- Requests (API calls)
- psutil (system information)
- pygame (alarm sounds)
- numpy (audio generation)
- gunicorn (production server)

## 🔧 Installation

### Local Installation (Windows/Mac/Linux)

1. **Clone or download this repository**

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Running on Replit

The application is pre-configured to run on Replit:

1. The Flask API server starts automatically on port 5000
2. Access the API through the web preview
3. The desktop GUI (main.py) requires a graphical display and won't run in the web environment

## 📖 How to Use

### First Time Setup

1. **Register Your Device**
   - Run `python main.py` to launch the GUI application
   - Fill in your information:
     - Owner Name
     - Email
     - Password (minimum 6 characters)
     - Contact Number
   - Click "Register Device"
   - **IMPORTANT**: Save the API Key shown - you'll need it for remote access!

2. **Login**
   - After registration, login with your email and password
   - You'll see the main control panel with multiple tabs

### Using the Desktop Application (GUI)

The control panel has several tabs:

#### 📊 Status Tab
- View device information
- Check registration status
- See system details (CPU, memory, disk)

#### 🔒 Lock Tab
- Lock your device locally
- Set a custom message for anyone who finds it
- Unlock with your credentials

#### 📍 Location Tab
- Get current location (IP-based)
- View Wi-Fi networks nearby
- See location history

#### 📸 Evidence Tab
- Capture webcam photos
- Take screenshots
- View captured evidence files
- Capture evidence sets (multiple photos + screenshots)

#### 🚨 Alarm Tab
- Test alarm (3 seconds)
- Trigger theft alarm (30 seconds)
- Stop alarm manually

#### 📝 Logs Tab
- View all security events
- Export evidence report for law enforcement
- Track all activities with timestamps

### Using the Remote API

The Flask API server allows you to control your device remotely.

#### Starting the API Server

```bash
python remote_server.py
```

The server runs on `http://0.0.0.0:5000` (or your Replit URL)

#### API Endpoints

All API requests require authentication using your API key in the header:
```
X-API-Key: YOUR_API_KEY_HERE
```

**Available Endpoints:**

1. **Get Device Status**
   ```bash
   GET /api/status
   ```

2. **Lock Device Remotely**
   ```bash
   POST /api/lock
   Content-Type: application/json
   
   {
     "message": "Custom lock message (optional)"
   }
   ```

3. **Unlock Device**
   ```bash
   POST /api/unlock
   ```

4. **Get Location**
   ```bash
   GET /api/location
   ```

5. **Trigger Alarm**
   ```bash
   POST /api/alarm
   Content-Type: application/json
   
   {
     "duration": 30
   }
   ```

6. **Capture Evidence**
   ```bash
   POST /api/capture
   ```

7. **Get Event Logs**
   ```bash
   GET /api/logs?count=20
   ```

8. **Get Device Info**
   ```bash
   GET /api/device-info
   ```

#### Example API Usage (Python)

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "http://your-replit-url.repl.co"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Lock the device
response = requests.post(
    f"{BASE_URL}/api/lock",
    headers=headers,
    json={"message": "This laptop is stolen! Contact owner for reward!"}
)
print(response.json())

# Get location
response = requests.get(f"{BASE_URL}/api/location", headers=headers)
print(response.json())
```

See `remote_client_example.py` for a complete Python client implementation.

## 🔐 Security Features

- **AES-256 Encryption** - All sensitive data is encrypted
- **PBKDF2 Key Derivation** - Secure password-based encryption (100,000 iterations)
- **No Plaintext Keys** - Encryption keys never stored on disk
- **API Key Authentication** - Secure 32-byte URL-safe tokens for remote access
- **Failed Login Tracking** - Logs all unauthorized access attempts
- **Salt-based Encryption** - Unique device salt for enhanced security

## 📁 Data Storage

All sensitive data is stored in the `data/` directory:
- `data/auth.enc` - Encrypted user credentials
- `data/api_auth.enc` - Encrypted API credentials
- `data/device_info.json` - Device identification
- `data/evidence/` - Captured photos and screenshots
- `data/logs/` - Event logs
- `data/.server_secret` - Flask session secret

**Important**: Never share these files or commit them to version control!

## ⚠️ Important Notes

1. **Keep Your API Key Safe** - Anyone with your API key can control your device
2. **Remember Your Password** - Password recovery is not available (by design for security)
3. **GUI Requires Display** - The desktop application needs a graphical environment
4. **Audio May Be Limited** - Headless environments may not support alarm functionality
5. **Location Accuracy** - IP-based location is approximate; not GPS-accurate

## 🚀 Deployment

The project is configured for deployment on Replit using Gunicorn:

```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 remote_server:app
```

Click the "Deploy" button in Replit to publish your API server to production.

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'Crypto'"
Install dependencies: `pip install pycryptodome`

### "No audio device available"
Normal in headless environments. Alarm functionality will be disabled but all other features work.

### "Device not registered"
Run `python main.py` first to register your device through the GUI.

### API returns "Unauthorized"
Check that you're using the correct API key in the `X-API-Key` header.

## 📄 License

This project is for educational and personal use. Use responsibly and legally.

## 🤝 Contributing

This is a personal security tool. Please use and modify according to your needs.

## ⚖️ Legal Disclaimer

This software is intended for protecting YOUR OWN devices. Do not use it to track or monitor devices you don't own. Always comply with local laws and regulations regarding privacy and surveillance.
