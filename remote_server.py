from flask import Flask, request, jsonify
import os
from api_auth_manager import APIAuthManager
from device_manager import DeviceManager
from location_tracker import LocationTracker
from evidence_capture import EvidenceCapture
from alarm_system import AlarmSystem
from event_logger import EventLogger
import threading

app = Flask(__name__)

def get_flask_secret():
    session_secret = os.environ.get('SESSION_SECRET')
    if session_secret:
        return session_secret
    
    api_auth_temp = APIAuthManager()
    return api_auth_temp.get_or_create_server_secret()

app.config['SECRET_KEY'] = get_flask_secret()

api_auth = APIAuthManager()
device_manager = DeviceManager()
location_tracker = LocationTracker()
evidence_capture = EvidenceCapture()
alarm_system = AlarmSystem()
event_logger = EventLogger()

def verify_api_key(api_key):
    return api_auth.verify_api_key(api_key)

@app.route('/api/status', methods=['GET'])
def get_status():
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({'error': 'Unauthorized'}), 401
    
    from lock_manager import LockManager
    lock_manager = LockManager()
    
    user_info = api_auth.get_user_info()
    device_info = device_manager.get_device_info()
    
    return jsonify({
        'device_id': device_manager.get_device_id(),
        'is_locked': lock_manager.is_locked(),
        'owner': user_info.get('name') if user_info else 'Unknown',
        'system': device_info
    })

@app.route('/api/lock', methods=['POST'])
def lock_device():
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({'error': 'Unauthorized'}), 401
    
    from lock_manager import LockManager
    lock_manager = LockManager()
    
    data = request.json or {}
    message = data.get('message', '')
    
    if not message:
        user_info = api_auth.get_user_info()
        if user_info:
            message = f"This laptop is stolen!\n\nOwner: {user_info.get('name')}\n\nPlease contact owner for reward!"
    
    success = lock_manager.set_lock_status(True, message)
    
    if success:
        event_logger.log_event("REMOTE_LOCK", "Device locked via remote API", 
                              include_location=True, include_evidence=True)
        return jsonify({
            'success': True,
            'message': 'Device locked successfully',
            'device_id': device_manager.get_device_id()
        })
    
    return jsonify({'error': 'Failed to lock device'}), 500

@app.route('/api/unlock', methods=['POST'])
def unlock_device():
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({'error': 'Unauthorized'}), 401
    
    from lock_manager import LockManager
    lock_manager = LockManager()
    
    success = lock_manager.set_lock_status(False, "")
    
    if success:
        event_logger.log_event("REMOTE_UNLOCK", "Device unlocked via remote API")
        return jsonify({
            'success': True,
            'message': 'Device unlocked successfully'
        })
    
    return jsonify({'error': 'Failed to unlock device'}), 500

@app.route('/api/location', methods=['GET'])
def get_location():
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({'error': 'Unauthorized'}), 401
    
    location_data = location_tracker.get_current_location()
    event_logger.log_event("REMOTE_LOCATION_CHECK", "Location checked via remote API", 
                          include_location=True)
    
    return jsonify({
        'success': True,
        'location': location_data
    })

@app.route('/api/alarm', methods=['POST'])
def trigger_alarm():
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json or {}
    duration = data.get('duration', 30)
    
    alarm_system.play_alarm(duration)
    event_logger.log_event("REMOTE_ALARM", f"Alarm triggered via remote API ({duration}s)", 
                          include_location=True, include_evidence=True)
    
    return jsonify({
        'success': True,
        'message': f'Alarm triggered for {duration} seconds'
    })

@app.route('/api/capture', methods=['POST'])
def capture_evidence():
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({'error': 'Unauthorized'}), 401
    
    def capture_async():
        result = evidence_capture.capture_evidence_set()
        event_logger.log_event("REMOTE_CAPTURE", "Evidence captured via remote API", 
                              include_evidence=True)
    
    thread = threading.Thread(target=capture_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Evidence capture initiated'
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({'error': 'Unauthorized'}), 401
    
    count = request.args.get('count', 20, type=int)
    events = event_logger.get_recent_events(count)
    
    return jsonify({
        'success': True,
        'events': events
    })

@app.route('/api/device-info', methods=['GET'])
def get_device_info():
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({'error': 'Unauthorized'}), 401
    
    from lock_manager import LockManager
    lock_manager = LockManager()
    
    return jsonify({
        'success': True,
        'device_id': device_manager.get_device_id(),
        'device_info': device_manager.get_device_info(),
        'is_locked': lock_manager.is_locked(),
        'lock_message': lock_manager.get_lock_message()
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'running',
        'device_id': device_manager.get_device_id()
    })

if __name__ == '__main__':
    api_creds = api_auth.get_api_credentials()
    
    if not api_creds:
        print("ERROR: Device not registered. Please run main.py first to register the device.")
    else:
        print(f"Anti-Theft Remote Server Starting...")
        print(f"Device ID: {device_manager.get_device_id()}")
        print(f"Owner: {api_creds.get('user_name')}")
        print(f"API Key: {api_creds.get('api_key')}")
        print("\nRemote API Endpoints:")
        print("  GET  /api/status        - Get device status")
        print("  POST /api/lock          - Lock device remotely")
        print("  POST /api/unlock        - Unlock device")
        print("  GET  /api/location      - Get current location")
        print("  POST /api/alarm         - Trigger alarm")
        print("  POST /api/alarm         - Capture evidence")
        print("  GET  /api/logs          - Get event logs")
        print("  GET  /api/device-info   - Get device information")
        print("\nUse header: X-API-Key: YOUR_API_KEY")
        print("\nServer listening on http://0.0.0.0:5000")
        
        app.run(host='0.0.0.0', port=5000, debug=False)
