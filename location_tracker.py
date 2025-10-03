import requests
import subprocess
import re
import platform
from datetime import datetime

class LocationTracker:
    def __init__(self):
        self.location_file = "data/location_history.json"
    
    def get_ip_location(self):
        try:
            response = requests.get('https://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'ip': data.get('ip'),
                    'city': data.get('city'),
                    'region': data.get('region'),
                    'country': data.get('country_name'),
                    'postal': data.get('postal'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'org': data.get('org'),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"IP location error: {e}")
        return None
    
    def get_wifi_networks(self):
        networks = []
        system = platform.system()
        
        try:
            if system == "Windows":
                result = subprocess.run(['netsh', 'wlan', 'show', 'networks'], 
                                       capture_output=True, 
                                       encoding='utf-8', 
                                       errors='ignore',
                                       timeout=5)
                
                if result.returncode != 0:
                    return []
                
                output = result.stdout
                ssids = re.findall(r'SSID \d+ : (.+)', output)
                signals = re.findall(r'Signal\s+:\s+(\d+)%', output)
                
                for i, ssid in enumerate(ssids):
                    networks.append({
                        'ssid': ssid.strip(),
                        'signal': signals[i] if i < len(signals) else 'N/A'
                    })
            
            elif system == "Linux":
                result = subprocess.run(['nmcli', '-f', 'SSID,SIGNAL', 'dev', 'wifi'], 
                                       capture_output=True,
                                       encoding='utf-8', 
                                       errors='ignore',
                                       timeout=5)
                
                if result.returncode != 0:
                    return []
                
                lines = result.stdout.split('\n')[1:]
                for line in lines:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            networks.append({
                                'ssid': ' '.join(parts[:-1]),
                                'signal': parts[-1]
                            })
            
            elif system == "Darwin":
                result = subprocess.run(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'], 
                                       capture_output=True,
                                       encoding='utf-8', 
                                       errors='ignore',
                                       timeout=5)
                
                if result.returncode != 0:
                    return []
                
                lines = result.stdout.split('\n')[1:]
                for line in lines:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            networks.append({
                                'ssid': parts[0],
                                'signal': parts[2] if len(parts) > 2 else 'N/A'
                            })
        except Exception:
            pass
        
        return networks
    
    def get_current_location(self):
        ip_location = self.get_ip_location()
        wifi_networks = self.get_wifi_networks()
        
        location_data = {
            'timestamp': datetime.now().isoformat(),
            'ip_location': ip_location,
            'wifi_networks': wifi_networks[:10]
        }
        
        return location_data
    
    def get_location_summary(self):
        location = self.get_current_location()
        
        summary = "Location Information:\n\n"
        
        if location['ip_location']:
            ip_loc = location['ip_location']
            summary += f"IP Address: {ip_loc.get('ip', 'Unknown')}\n"
            summary += f"Location: {ip_loc.get('city', 'Unknown')}, {ip_loc.get('region', 'Unknown')}, {ip_loc.get('country', 'Unknown')}\n"
            summary += f"Coordinates: {ip_loc.get('latitude', 'N/A')}, {ip_loc.get('longitude', 'N/A')}\n"
            summary += f"ISP: {ip_loc.get('org', 'Unknown')}\n"
        else:
            summary += "IP Location: Unable to retrieve\n"
        
        summary += f"\nNearby WiFi Networks: {len(location['wifi_networks'])}\n"
        for i, wifi in enumerate(location['wifi_networks'][:5], 1):
            summary += f"  {i}. {wifi['ssid']} (Signal: {wifi['signal']})\n"
        
        return summary
