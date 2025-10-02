# Laptop Anti-Theft Protection Application

## Overview
A comprehensive Python-based anti-theft security application for laptops featuring device registration, remote lock, location tracking, evidence capture, alarm system, and event logging capabilities.

## Current State
MVP implementation complete with all core security features:
- ✅ Secure device registration and authentication with AES encryption
- ✅ Remote lock functionality with custom owner contact messages
- ✅ IP-based location tracking with Wi-Fi SSID scanning
- ✅ Webcam and screenshot evidence capture
- ✅ Loud alarm system with volume bypass capability
- ✅ Comprehensive event logging with export functionality
- ✅ Tkinter-based GUI for easy management

## Project Structure
```
├── main.py                  # Main application entry point with GUI
├── auth_manager.py          # User authentication and encryption
├── device_manager.py        # Device identification and info
├── location_tracker.py      # IP geolocation and WiFi scanning
├── evidence_capture.py      # Webcam and screenshot capture
├── alarm_system.py          # Alarm/siren functionality
├── event_logger.py          # Event logging and report export
├── control_panel.py         # Main control panel GUI
└── data/                    # Encrypted user data and evidence
    ├── auth.enc            # Encrypted user credentials
    ├── device_info.json    # Device identification
    ├── evidence/           # Captured photos and screenshots
    └── logs/               # Event logs
```

## Features Implemented

### 1. Device Registration & Security
- Secure user registration with email, password, contact info
- AES-256 encryption for all sensitive data
- Unique device ID generation
- Encrypted credential storage

### 2. Remote Lock
- Lock device with custom owner message
- Display contact information and reward offer
- Unlock with owner credentials
- Automatic evidence capture on lock

### 3. Location Tracking
- IP-based geolocation (city, region, coordinates)
- WiFi SSID scanning for network triangulation
- ISP and network information logging
- Location history tracking

### 4. Evidence Capture
- Webcam photo capture
- Full screen screenshots
- Multiple capture support with intervals
- Evidence file management and listing

### 5. Alarm System
- Loud siren that bypasses volume settings
- Test mode (3 seconds)
- Theft mode (30 seconds)
- Manual stop capability

### 6. Event Logging
- Comprehensive event tracking with timestamps
- Location data included in events
- Evidence attachments to events
- Export evidence reports for law enforcement

## Dependencies
- opencv-python: Webcam capture
- pillow: Screenshot capture
- pycryptodome: Data encryption with PBKDF2 key derivation
- requests: IP geolocation API
- psutil: System information
- flask: Web backend for remote commands
- pygame: Alarm sound playback

## System Requirements
- Python 3.11+
- OpenGL libraries (libGL, libGLU)
- Webcam (optional, for evidence capture)
- Network connection (for location tracking)
- Audio device (optional, for alarm functionality)

## Remote Access
The application includes a Flask-based remote API server that allows you to control the device from anywhere:

### Starting the Remote Server
```bash
python remote_server.py
```
The server runs on port 5000 and requires the device to be registered first.

### Remote API Endpoints
All endpoints require authentication via `X-API-Key` header.

- `GET /api/status` - Get device status
- `POST /api/lock` - Lock device remotely
- `POST /api/unlock` - Unlock device
- `GET /api/location` - Get current location
- `POST /api/alarm` - Trigger alarm
- `POST /api/capture` - Capture evidence
- `GET /api/logs` - Get event logs
- `GET /api/device-info` - Get device information

### Using the Remote Client
See `remote_client_example.py` for a Python client to control your device remotely.

## Usage
1. Run the application: `python main.py`
2. First time: Register device with owner information
3. Login with credentials to access control panel
4. Use tabs to manage: Status, Lock, Location, Evidence, Alarm, Logs

## Security Features
- All user data encrypted with AES-256-EAX mode
- Encryption key derived from user password using PBKDF2 (100,000 iterations)
- No plaintext encryption keys stored on disk
- Password hashing with SHA-256
- Secure API key generation for remote access (32-byte URL-safe tokens)
- Failed login attempt logging
- Credential-protected device management
- Salt-based key derivation with unique device salt

## Replit Environment Setup
This project is configured to run in Replit with the following setup:
- **Python 3.11** with all required dependencies installed
- **Flask Backend Server** running on port 5000 (remote_server.py)
- **System Dependencies**: OpenGL, SDL2 for graphics and audio support
- **Deployment**: Configured with Gunicorn for production (VM deployment)

### Running in Replit
The remote API server starts automatically and is accessible via the web preview.
- **Development**: `python remote_server.py` (runs automatically in workflow)
- **Production**: Gunicorn with 2 workers on port 5000

### Important Notes for Replit
- The GUI application (main.py) requires a graphical display and won't run in the web environment
- To use the full features, you need to register the device first by running main.py locally
- The remote server provides a REST API for controlling the device
- Audio features may be limited in headless environments

## Recent Changes
- 2025-10-02: Replit Environment Setup
  - Configured Python 3.11 environment with all dependencies
  - Set up Flask backend workflow on port 5000
  - Added deployment configuration with Gunicorn
  - Enhanced remote server to handle unregistered device state gracefully
  - Added root endpoint (/) with API documentation and status

- 2025-10-02: Security and Remote Access Update
  - **CRITICAL FIX**: Replaced insecure plaintext key storage with PBKDF2 password-based key derivation
  - **NEW**: Added Flask-based remote API server for actual remote control functionality
  - **NEW**: Implemented API key authentication for remote access
  - Added remote client example for controlling device from anywhere
  - Fixed audio device handling for headless environments
  - Enhanced encryption with secure salt-based key derivation

- 2025-10-02: Initial MVP implementation complete
  - Created all core modules
  - Implemented GUI with Tkinter
  - Added encryption and security features
  - Integrated location tracking and evidence capture
  - Built alarm system and event logging

## Future Enhancements (Phase 2)
- Bluetooth LE proximity locking with smartphone
- Automatic trigger detection (failed logins, boot changes)
- Geo-fencing with boundary alerts
- Remote wipe functionality
- Network blocking capability
- Background service/daemon mode with auto-restart
- Web-based remote control dashboard
- Multi-device management

## Notes
- GUI requires graphical display (X11/Wayland/Windows)
- In headless environments, consider Flask web interface
- Evidence files stored in data/evidence directory
- Logs exportable for law enforcement evidence
