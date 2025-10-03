from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import os
from api_auth_manager import APIAuthManager
from auth_manager import AuthManager
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
auth_manager = AuthManager()
device_manager = DeviceManager()
location_tracker = LocationTracker()
evidence_capture = EvidenceCapture()
alarm_system = AlarmSystem()
event_logger = EventLogger()

def verify_api_key(api_key):
    return api_auth.verify_api_key(api_key)

def is_web_authenticated():
    return session.get('authenticated', False)

@app.route('/web/login', methods=['GET', 'POST'])
def web_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if auth_manager.verify_login(email, password):
            session['authenticated'] = True
            session['email'] = email
            event_logger.log_event("WEB_LOGIN", f"User {email} logged in via web interface")
            return redirect(url_for('web_dashboard'))
        else:
            return render_template_string(LOGIN_PAGE, error="Invalid credentials!")
    
    if is_web_authenticated():
        return redirect(url_for('web_dashboard'))
    
    return render_template_string(LOGIN_PAGE, error=None)

@app.route('/web/logout')
def web_logout():
    session.clear()
    return redirect(url_for('web_login'))

@app.route('/web/dashboard')
def web_dashboard():
    if not is_web_authenticated():
        return redirect(url_for('web_login'))
    
    user_data = auth_manager.get_user_data()
    device_info = device_manager.get_device_info()
    from lock_manager import LockManager
    lock_manager = LockManager()
    
    return render_template_string(DASHBOARD_PAGE, 
                                 user=user_data,
                                 device_id=device_manager.get_device_id(),
                                 is_locked=lock_manager.is_locked(),
                                 device_info=device_info)

@app.route('/web/action/lock', methods=['POST'])
def web_action_lock():
    if not is_web_authenticated():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    from lock_manager import LockManager
    lock_manager = LockManager()
    
    message = request.json.get('message', '')
    if not message:
        user_data = auth_manager.get_user_data()
        if user_data:
            message = f"This laptop is stolen!\n\nOwner: {user_data.get('name')}\nContact: {user_data.get('contact')}\n\nPlease contact owner for reward!"
    
    success = lock_manager.set_lock_status(True, message)
    if success:
        event_logger.log_event("WEB_LOCK", "Device locked via web dashboard", 
                              include_location=True, include_evidence=True)
    
    return jsonify({'success': success})

@app.route('/web/action/unlock', methods=['POST'])
def web_action_unlock():
    if not is_web_authenticated():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    from lock_manager import LockManager
    lock_manager = LockManager()
    
    success = lock_manager.set_lock_status(False, "")
    if success:
        event_logger.log_event("WEB_UNLOCK", "Device unlocked via web dashboard")
    
    return jsonify({'success': success})

@app.route('/web/action/location', methods=['GET'])
def web_action_location():
    if not is_web_authenticated():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    location_data = location_tracker.get_current_location()
    event_logger.log_event("WEB_LOCATION", "Location checked via web dashboard", 
                          include_location=True)
    
    return jsonify({'success': True, 'location': location_data})

@app.route('/web/action/alarm', methods=['POST'])
def web_action_alarm():
    if not is_web_authenticated():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    duration = request.json.get('duration', 30)
    alarm_system.play_alarm(duration)
    event_logger.log_event("WEB_ALARM", f"Alarm triggered via web dashboard ({duration}s)", 
                          include_location=True, include_evidence=True)
    
    return jsonify({'success': True, 'message': f'Alarm triggered for {duration} seconds'})

@app.route('/web/action/capture', methods=['POST'])
def web_action_capture():
    if not is_web_authenticated():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    def capture_async():
        evidence_capture.capture_evidence_set()
        event_logger.log_event("WEB_CAPTURE", "Evidence captured via web dashboard", 
                              include_evidence=True)
    
    thread = threading.Thread(target=capture_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Evidence capture initiated'})

@app.route('/web/action/logs', methods=['GET'])
def web_action_logs():
    if not is_web_authenticated():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    count = request.args.get('count', 20, type=int)
    events = event_logger.get_recent_events(count)
    
    return jsonify({'success': True, 'events': events})

@app.route('/web/action/status', methods=['GET'])
def web_action_status():
    if not is_web_authenticated():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    from lock_manager import LockManager
    lock_manager = LockManager()
    device_info = device_manager.get_device_info()
    user_data = auth_manager.get_user_data()
    
    return jsonify({
        'success': True,
        'device_id': device_manager.get_device_id(),
        'is_locked': lock_manager.is_locked(),
        'owner': user_data.get('name') if user_data else 'Unknown',
        'system': device_info
    })

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
                .btn { display: inline-block; padding: 12px 24px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔒 Laptop Anti-Theft Protection</h1>
                <div class="warning">
                    <h2>⚠️ Device Not Registered</h2>
                    <p>This device needs to be registered before you can use the remote features.</p>
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
                <h3>Available Features (After Registration)</h3>
                <ul>
                    <li><strong>Web Dashboard</strong> - Login and control device via web browser</li>
                    <li><strong>REST API</strong> - Programmatic control with API key</li>
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
        <title>Anti-Theft Protection</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #4CAF50; margin-bottom: 10px; }
            .status { background: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; margin: 10px 0; }
            .info-box { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; }
            .api-key-box { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ff9800; }
            .btn { display: inline-block; padding: 12px 24px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 10px 10px 10px 0; border: none; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #45a049; }
            code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 14px; }
            .copy-btn { background: #4CAF50; color: white; border: none; padding: 5px 15px; border-radius: 3px; cursor: pointer; margin-left: 10px; }
            .copy-btn:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔒 Laptop Anti-Theft Protection</h1>
            <div class="status">✓ Device Registered</div>
            
            <div class="info-box">
                <h3>Device Information</h3>
                <p><strong>Device ID:</strong> <code>''' + device_id + '''</code></p>
                <p><strong>Owner:</strong> ''' + owner + '''</p>
            </div>
            
            <div style="margin: 20px 0;">
                <a href="/web/login" class="btn">🖥️ Open Web Dashboard</a>
            </div>
            
            <div class="api-key-box">
                <h3>🔑 API Access</h3>
                <p><strong>API Key:</strong> <code id="apiKey">''' + api_key + '''</code>
                <button class="copy-btn" onclick="copyApiKey()">Copy</button></p>
                <p><small>⚠️ Keep this key secret! Use it for programmatic API access.</small></p>
            </div>
            
            <h2>📡 Access Methods</h2>
            
            <h3>1. Web Dashboard (Recommended)</h3>
            <p>Login with your email and password to control the device via web browser:</p>
            <a href="/web/login" class="btn">Login to Dashboard</a>
            
            <h3>2. REST API</h3>
            <p>Use the API key for programmatic access. All requests must include the header:</p>
            <code>X-API-Key: YOUR_API_KEY</code>
            
            <p><small>💡 Check the <code>README.md</code> file for complete API documentation.</small></p>
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

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Web Login - Anti-Theft Protection</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .login-container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); width: 100%; max-width: 400px; }
        h1 { color: #333; margin-bottom: 10px; text-align: center; }
        .subtitle { color: #666; text-align: center; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; color: #555; margin-bottom: 8px; font-weight: 500; }
        input[type="email"], input[type="password"] { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 16px; transition: border-color 0.3s; }
        input[type="email"]:focus, input[type="password"]:focus { outline: none; border-color: #667eea; }
        .btn-login { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        .btn-login:hover { transform: translateY(-2px); }
        .error { background: #ffebee; color: #c62828; padding: 12px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #c62828; }
        .device-info { background: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 20px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔒 Anti-Theft Protection</h1>
        <p class="subtitle">Login to Web Dashboard</p>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST" action="/web/login">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" required autofocus>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn-login">Login to Dashboard</button>
        </form>
        
        <div class="device-info">
            Use the same credentials from device registration
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Control Dashboard - Anti-Theft Protection</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header-content { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; }
        .user-info { font-size: 14px; opacity: 0.9; }
        .logout-btn { background: rgba(255,255,255,0.2); color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin-left: 15px; }
        .logout-btn:hover { background: rgba(255,255,255,0.3); }
        .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
        .status-bar { background: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .status-item { text-align: center; padding: 15px; }
        .status-item h3 { color: #666; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }
        .status-value { font-size: 24px; font-weight: bold; color: #333; }
        .status-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; }
        .status-unlocked { background: #4CAF50; color: white; }
        .status-locked { background: #f44336; color: white; }
        .controls-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .control-card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .control-card h2 { color: #333; margin-bottom: 15px; font-size: 20px; }
        .control-card p { color: #666; margin-bottom: 20px; font-size: 14px; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; width: 100%; transition: transform 0.2s, opacity 0.2s; }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-danger { background: #f44336; color: white; }
        .btn-success { background: #4CAF50; color: white; }
        .btn-primary { background: #2196F3; color: white; }
        .btn-warning { background: #ff9800; color: white; }
        .btn-info { background: #00bcd4; color: white; }
        .result-box { margin-top: 15px; padding: 12px; border-radius: 5px; font-size: 14px; display: none; }
        .result-success { background: #e8f5e9; color: #2e7d32; border-left: 4px solid #4CAF50; }
        .result-error { background: #ffebee; color: #c62828; border-left: 4px solid #f44336; }
        .location-data { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 15px; font-size: 14px; display: none; }
        .logs-container { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-height: 500px; overflow-y: auto; }
        .log-entry { padding: 12px; border-bottom: 1px solid #e0e0e0; font-size: 14px; }
        .log-entry:last-child { border-bottom: none; }
        .log-time { color: #666; font-size: 12px; }
        .log-type { display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; margin-right: 10px; }
        .log-message { color: #333; }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div>
                <h1>🔒 Anti-Theft Control Dashboard</h1>
                <div class="user-info">Welcome, {{ user.name }}</div>
            </div>
            <div>
                <a href="/web/logout" class="logout-btn">Logout</a>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="status-bar">
            <div class="status-grid">
                <div class="status-item">
                    <h3>Device Status</h3>
                    <div class="status-value">
                        <span id="lockStatus" class="status-badge {% if is_locked %}status-locked{% else %}status-unlocked{% endif %}">
                            {% if is_locked %}🔒 LOCKED{% else %}🔓 UNLOCKED{% endif %}
                        </span>
                    </div>
                </div>
                <div class="status-item">
                    <h3>Device ID</h3>
                    <div class="status-value" style="font-size: 16px; word-break: break-all;">{{ device_id }}</div>
                </div>
                <div class="status-item">
                    <h3>System</h3>
                    <div class="status-value" style="font-size: 18px;">{{ device_info.platform }}</div>
                </div>
            </div>
        </div>
        
        <div class="controls-grid">
            <div class="control-card">
                <h2>🔒 Lock Device</h2>
                <p>Lock this device remotely with a custom message</p>
                <button class="btn btn-danger" onclick="lockDevice()">Lock Device Now</button>
                <div id="lockResult" class="result-box"></div>
            </div>
            
            <div class="control-card">
                <h2>🔓 Unlock Device</h2>
                <p>Unlock this device remotely</p>
                <button class="btn btn-success" onclick="unlockDevice()">Unlock Device</button>
                <div id="unlockResult" class="result-box"></div>
            </div>
            
            <div class="control-card">
                <h2>📍 Get Location</h2>
                <p>Track device location using IP geolocation</p>
                <button class="btn btn-primary" onclick="getLocation()">Get Current Location</button>
                <div id="locationResult" class="result-box"></div>
                <div id="locationData" class="location-data"></div>
            </div>
            
            <div class="control-card">
                <h2>🚨 Trigger Alarm</h2>
                <p>Sound alarm on the device (30 seconds)</p>
                <button class="btn btn-warning" onclick="triggerAlarm()">Trigger Alarm</button>
                <div id="alarmResult" class="result-box"></div>
            </div>
            
            <div class="control-card">
                <h2>📸 Capture Evidence</h2>
                <p>Capture webcam photo and screenshot</p>
                <button class="btn btn-info" onclick="captureEvidence()">Capture Now</button>
                <div id="captureResult" class="result-box"></div>
            </div>
            
            <div class="control-card">
                <h2>🔄 Refresh Status</h2>
                <p>Update device status information</p>
                <button class="btn btn-primary" onclick="refreshStatus()">Refresh Now</button>
                <div id="refreshResult" class="result-box"></div>
            </div>
        </div>
        
        <div class="logs-container">
            <h2 style="margin-bottom: 20px;">📝 Recent Activity Logs</h2>
            <div id="logsContainer">Loading logs...</div>
        </div>
    </div>
    
    <script>
        function showResult(elementId, message, isSuccess) {
            const el = document.getElementById(elementId);
            el.className = 'result-box ' + (isSuccess ? 'result-success' : 'result-error');
            el.textContent = message;
            el.style.display = 'block';
            setTimeout(() => { el.style.display = 'none'; }, 5000);
        }
        
        function lockDevice() {
            fetch('/web/action/lock', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: ''})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('lockResult', '✓ Device locked successfully!', true);
                    setTimeout(refreshStatus, 1000);
                } else {
                    showResult('lockResult', '✗ Failed to lock device', false);
                }
            })
            .catch(() => showResult('lockResult', '✗ Error locking device', false));
        }
        
        function unlockDevice() {
            fetch('/web/action/unlock', {method: 'POST'})
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('unlockResult', '✓ Device unlocked successfully!', true);
                    setTimeout(refreshStatus, 1000);
                } else {
                    showResult('unlockResult', '✗ Failed to unlock device', false);
                }
            })
            .catch(() => showResult('unlockResult', '✗ Error unlocking device', false));
        }
        
        function getLocation() {
            fetch('/web/action/location')
            .then(r => r.json())
            .then(data => {
                if (data.success && data.location) {
                    const loc = data.location;
                    const locDiv = document.getElementById('locationData');
                    locDiv.innerHTML = `
                        <strong>Location:</strong> ${loc.city || 'Unknown'}, ${loc.region || ''} ${loc.country || ''}<br>
                        <strong>Coordinates:</strong> ${loc.latitude || 'N/A'}, ${loc.longitude || 'N/A'}<br>
                        <strong>ISP:</strong> ${loc.isp || 'Unknown'}<br>
                        <strong>IP:</strong> ${loc.ip || 'N/A'}
                    `;
                    locDiv.style.display = 'block';
                    showResult('locationResult', '✓ Location retrieved successfully!', true);
                } else {
                    showResult('locationResult', '✗ Failed to get location', false);
                }
            })
            .catch(() => showResult('locationResult', '✗ Error getting location', false));
        }
        
        function triggerAlarm() {
            fetch('/web/action/alarm', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({duration: 30})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('alarmResult', '✓ Alarm triggered for 30 seconds!', true);
                } else {
                    showResult('alarmResult', '✗ Failed to trigger alarm', false);
                }
            })
            .catch(() => showResult('alarmResult', '✗ Error triggering alarm', false));
        }
        
        function captureEvidence() {
            fetch('/web/action/capture', {method: 'POST'})
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showResult('captureResult', '✓ Evidence capture initiated!', true);
                } else {
                    showResult('captureResult', '✗ Failed to capture evidence', false);
                }
            })
            .catch(() => showResult('captureResult', '✗ Error capturing evidence', false));
        }
        
        function refreshStatus() {
            fetch('/web/action/status')
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    const lockStatus = document.getElementById('lockStatus');
                    if (data.is_locked) {
                        lockStatus.className = 'status-badge status-locked';
                        lockStatus.textContent = '🔒 LOCKED';
                    } else {
                        lockStatus.className = 'status-badge status-unlocked';
                        lockStatus.textContent = '🔓 UNLOCKED';
                    }
                    showResult('refreshResult', '✓ Status updated!', true);
                    loadLogs();
                } else {
                    showResult('refreshResult', '✗ Failed to refresh status', false);
                }
            })
            .catch(() => showResult('refreshResult', '✗ Error refreshing status', false));
        }
        
        function loadLogs() {
            fetch('/web/action/logs?count=10')
            .then(r => r.json())
            .then(data => {
                if (data.success && data.events) {
                    const logsDiv = document.getElementById('logsContainer');
                    if (data.events.length === 0) {
                        logsDiv.innerHTML = '<p style="color: #666;">No logs available</p>';
                        return;
                    }
                    logsDiv.innerHTML = data.events.map(event => `
                        <div class="log-entry">
                            <div class="log-time">${event.timestamp || 'N/A'}</div>
                            <span class="log-type" style="background: #e3f2fd; color: #1976d2;">${event.event_type || 'EVENT'}</span>
                            <span class="log-message">${event.description || ''}</span>
                        </div>
                    `).join('');
                }
            })
            .catch(() => {
                document.getElementById('logsContainer').innerHTML = '<p style="color: #f44336;">Error loading logs</p>';
            });
        }
        
        loadLogs();
        setInterval(loadLogs, 30000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    api_creds = api_auth.get_api_credentials()
    
    print(f"Anti-Theft Remote Server Starting...")
    print(f"Device ID: {device_manager.get_device_id()}")
    
    if not api_creds:
        print("\n⚠️  WARNING: Device not registered")
        print("To use the remote features, run main.py first to register the device.")
        print("The server will still start for setup purposes.")
    else:
        print(f"Owner: {api_creds.get('user_name')}")
        print(f"API Key: {api_creds.get('api_key')}")
        print("\nWeb Dashboard: http://0.0.0.0:5000/web/login")
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
