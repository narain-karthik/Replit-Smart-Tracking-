import requests
import json

class AntiTheftRemoteClient:
    def __init__(self, server_url, api_key):
        self.server_url = server_url.rstrip('/')
        self.headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
    
    def get_status(self):
        response = requests.get(f"{self.server_url}/api/status", headers=self.headers)
        return response.json()
    
    def lock_device(self, message=None):
        data = {'message': message} if message else {}
        response = requests.post(f"{self.server_url}/api/lock", 
                                headers=self.headers, json=data)
        return response.json()
    
    def unlock_device(self):
        response = requests.post(f"{self.server_url}/api/unlock", headers=self.headers)
        return response.json()
    
    def get_location(self):
        response = requests.get(f"{self.server_url}/api/location", headers=self.headers)
        return response.json()
    
    def trigger_alarm(self, duration=30):
        data = {'duration': duration}
        response = requests.post(f"{self.server_url}/api/alarm", 
                                headers=self.headers, json=data)
        return response.json()
    
    def capture_evidence(self):
        response = requests.post(f"{self.server_url}/api/capture", headers=self.headers)
        return response.json()
    
    def get_logs(self, count=20):
        response = requests.get(f"{self.server_url}/api/logs?count={count}", 
                               headers=self.headers)
        return response.json()
    
    def get_device_info(self):
        response = requests.get(f"{self.server_url}/api/device-info", headers=self.headers)
        return response.json()

if __name__ == "__main__":
    SERVER_URL = "http://your-device-ip:5000"
    API_KEY = "your-api-key-here"
    
    client = AntiTheftRemoteClient(SERVER_URL, API_KEY)
    
    print("Anti-Theft Remote Client - Example Usage\n")
    print("1. Get Status")
    print("2. Lock Device")
    print("3. Unlock Device")
    print("4. Get Location")
    print("5. Trigger Alarm")
    print("6. Capture Evidence")
    print("7. Get Logs")
    print("8. Get Device Info")
    
    choice = input("\nSelect an option (1-8): ")
    
    try:
        if choice == "1":
            result = client.get_status()
            print(f"\nDevice Status:\n{json.dumps(result, indent=2)}")
        
        elif choice == "2":
            message = input("Enter lock message (or press Enter for default): ")
            result = client.lock_device(message if message else None)
            print(f"\nLock Result:\n{json.dumps(result, indent=2)}")
        
        elif choice == "3":
            result = client.unlock_device()
            print(f"\nUnlock Result:\n{json.dumps(result, indent=2)}")
        
        elif choice == "4":
            print("Retrieving location (this may take a moment)...")
            result = client.get_location()
            print(f"\nLocation:\n{json.dumps(result, indent=2)}")
        
        elif choice == "5":
            duration = input("Enter alarm duration in seconds (default 30): ")
            duration = int(duration) if duration else 30
            result = client.trigger_alarm(duration)
            print(f"\nAlarm Result:\n{json.dumps(result, indent=2)}")
        
        elif choice == "6":
            print("Capturing evidence...")
            result = client.capture_evidence()
            print(f"\nCapture Result:\n{json.dumps(result, indent=2)}")
        
        elif choice == "7":
            count = input("Number of logs to retrieve (default 20): ")
            count = int(count) if count else 20
            result = client.get_logs(count)
            print(f"\nLogs:\n{json.dumps(result, indent=2)}")
        
        elif choice == "8":
            result = client.get_device_info()
            print(f"\nDevice Info:\n{json.dumps(result, indent=2)}")
        
        else:
            print("Invalid choice!")
    
    except Exception as e:
        print(f"Error: {e}")
