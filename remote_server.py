from flask import Flask, request, jsonify, render_template_string
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

@app.route('/', methods=['GET'])
def index():
    api_creds = api_auth.get_api_credentials()
    device_id = device_manager.get_device_id()
    
    if not api_creds:
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Anti-Theft API - Not Registered</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
                .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #ff9800; }
                .warning { background: #fff3cd; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0; }
                .device-id { background: #e3f2fd; padding: 10px; border-radius: 5px; font-family: monospace; }
                code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔒 Laptop Anti-Theft Protection API</h1>
                <div class="warning">
                    <h2>⚠️ Device Not Registered</h2>
                    <p>This device needs to be registered before you can use the remote API.</p>
                </div>
                <h3>Device Information</h3>
                <div class="device-id">Device ID: ''' + device_id + '''</div>
                <h3>Setup Instructions</h3>
                <ol>
                    <li>Run <code>python main.py</code> on this device</li>
                    <li>Register the device with your information</li>
                    <li>Save the API Key that is displayed</li>
                    <li>Restart this server</li>
                </ol>
                <h3>Available Endpoints (After Registration)</h3>
                <ul>
                    <li><code>GET /health</code> - Health check (no auth required)</li>
                    <li>All other endpoints require device registration and API key</li>
                </ul>
            </div>
        </body>
        </html>
        '''
        return render_template_string(html)
    
    owner = api_creds.get('user_name')
    api_key = api_creds.get('api_key')
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Anti-Theft API Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #4CAF50; margin-bottom: 10px; }
            .status { background: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; margin: 10px 0; }
            .info-box { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; }
            .api-key-box { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ff9800; }
            .endpoint { background: #f9f9f9; padding: 12px; margin: 8px 0; border-left: 4px solid #4CAF50; border-radius: 3px; }
            .method { display: inline-block; padding: 4px 8px; border-radius: 3px; font-weight: bold; font-size: 12px; margin-right: 10px; }
            .get { background: #2196F3; color: white; }
            .post { background: #ff9800; color: white; }
            code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 14px; }
            .copy-btn { background: #4CAF50; color: white; border: none; padding: 5px 15px; border-radius: 3px; cursor: pointer; margin-left: 10px; }
            .copy-btn:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔒 Laptop Anti-Theft Protection API</h1>
            <div class="status">✓ Server Running</div>
            
            <div class="info-box">
                <h3>Device Information</h3>
                <p><strong>Device ID:</strong> <code>''' + device_id + '''</code></p>
                <p><strong>Owner:</strong> ''' + owner + '''</p>
            </div>
            
            <div class="api-key-box">
                <h3>🔑 Your API Key</h3>
                <p><code id="apiKey">''' + api_key + '''</code>
                <button class="copy-btn" onclick="copyApiKey()">Copy</button></p>
                <p><small>⚠️ Keep this key secret! Anyone with this key can control your device.</small></p>
            </div>
            
            <h2>📡 API Endpoints</h2>
            <p>All requests must include the header: <code>X-API-Key: YOUR_API_KEY</code></p>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/status</code>
                <p>Get device status and system information</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/lock</code>
                <p>Lock the device remotely with a custom message</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/unlock</code>
                <p>Unlock the device remotely</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/location</code>
                <p>Get current device location (IP-based)</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/alarm</code>
                <p>Trigger the alarm on the device</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/api/capture</code>
                <p>Capture evidence (webcam photo + screenshot)</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/logs</code>
                <p>Get recent event logs</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <code>/api/device-info</code>
                <p>Get detailed device information and lock status</p>
            </div>
            
            <h2>📖 Example Usage</h2>
            <pre style="background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto;">
curl -X GET http://localhost:5000/api/status \\
  -H "X-API-Key: ''' + api_key + '''"
            </pre>
            
            <p><small>💡 Check the <code>README.md</code> file for complete documentation and Python examples.</small></p>
        </div>
        
        <script>
            function copyApiKey() {
                const apiKey = document.getElementById('apiKey').innerText;
                navigator.clipboard.writeText(apiKey).then(() => {
                    alert('API Key copied to clipboard!');
                });
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    api_creds = api_auth.get_api_credentials()
    
    print(f"Anti-Theft Remote Server Starting...")
    print(f"Device ID: {device_manager.get_device_id()}")
    
    if not api_creds:
        print("\n⚠️  WARNING: Device not registered")
        print("To use the remote API, run main.py first to register the device.")
        print("The server will still start for setup purposes.")
    else:
        print(f"Owner: {api_creds.get('user_name')}")
        print(f"API Key: {api_creds.get('api_key')}")
        print("\nRemote API Endpoints:")
        print("  GET  /api/status        - Get device status")
        print("  POST /api/lock          - Lock device remotely")
        print("  POST /api/unlock        - Unlock device")
        print("  GET  /api/location      - Get current location")
        print("  POST /api/alarm         - Trigger alarm")
        print("  POST /api/capture       - Capture evidence")
        print("  GET  /api/logs          - Get event logs")
        print("  GET  /api/device-info   - Get device information")
        print("\nUse header: X-API-Key: YOUR_API_KEY")
    
    print("\nServer listening on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
