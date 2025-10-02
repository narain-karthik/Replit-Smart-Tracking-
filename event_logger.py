import json
import os
from datetime import datetime
from location_tracker import LocationTracker
from evidence_capture import EvidenceCapture

class EventLogger:
    def __init__(self):
        self.log_dir = "data/logs"
        self.log_file = os.path.join(self.log_dir, "events.json")
        self.ensure_log_directory()
        self.location_tracker = LocationTracker()
        self.evidence_capture = EvidenceCapture()
    
    def ensure_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def load_events(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_events(self, events):
        with open(self.log_file, 'w') as f:
            json.dump(events, f, indent=2)
    
    def log_event(self, event_type, description, include_location=False, include_evidence=False):
        event = {
            'event_id': len(self.load_events()) + 1,
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'description': description
        }
        
        if include_location:
            location = self.location_tracker.get_current_location()
            event['location'] = location
        
        if include_evidence:
            evidence = self.evidence_capture.capture_evidence_set()
            event['evidence'] = evidence
        
        events = self.load_events()
        events.append(event)
        self.save_events(events)
        
        return event
    
    def get_recent_events(self, count=10):
        events = self.load_events()
        return events[-count:] if len(events) > count else events
    
    def export_evidence_report(self, output_file=None):
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/evidence_report_{timestamp}.txt"
        
        events = self.load_events()
        
        with open(output_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("LAPTOP ANTI-THEFT EVIDENCE REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Events Logged: {len(events)}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("EVENT LOG\n")
            f.write("=" * 80 + "\n\n")
            
            for event in events:
                f.write(f"\nEvent ID: {event.get('event_id', 'N/A')}\n")
                f.write(f"Timestamp: {event.get('timestamp', 'N/A')}\n")
                f.write(f"Type: {event.get('type', 'N/A')}\n")
                f.write(f"Description: {event.get('description', 'N/A')}\n")
                
                if 'location' in event and event['location']:
                    loc = event['location']
                    if loc.get('ip_location'):
                        ip_loc = loc['ip_location']
                        f.write(f"\nLocation Information:\n")
                        f.write(f"  IP: {ip_loc.get('ip', 'N/A')}\n")
                        f.write(f"  City: {ip_loc.get('city', 'N/A')}\n")
                        f.write(f"  Region: {ip_loc.get('region', 'N/A')}\n")
                        f.write(f"  Country: {ip_loc.get('country', 'N/A')}\n")
                        f.write(f"  Coordinates: {ip_loc.get('latitude', 'N/A')}, {ip_loc.get('longitude', 'N/A')}\n")
                        f.write(f"  ISP: {ip_loc.get('org', 'N/A')}\n")
                    
                    if loc.get('wifi_networks'):
                        f.write(f"\nNearby WiFi Networks ({len(loc['wifi_networks'])}):\n")
                        for i, wifi in enumerate(loc['wifi_networks'][:5], 1):
                            f.write(f"  {i}. {wifi.get('ssid', 'N/A')} (Signal: {wifi.get('signal', 'N/A')})\n")
                
                if 'evidence' in event and event['evidence']:
                    ev = event['evidence']
                    f.write(f"\nEvidence Captured:\n")
                    if ev.get('webcam'):
                        f.write(f"  Webcam Photo: {ev['webcam']}\n")
                    if ev.get('screenshot'):
                        f.write(f"  Screenshot: {ev['screenshot']}\n")
                
                f.write("\n" + "-" * 80 + "\n")
        
        return output_file
    
    def get_event_summary(self):
        events = self.load_events()
        
        event_types = {}
        for event in events:
            event_type = event.get('type', 'Unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            'total_events': len(events),
            'event_types': event_types,
            'first_event': events[0]['timestamp'] if events else None,
            'last_event': events[-1]['timestamp'] if events else None
        }
