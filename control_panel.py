import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from location_tracker import LocationTracker
from evidence_capture import EvidenceCapture
from alarm_system import AlarmSystem
from event_logger import EventLogger
from lock_manager import LockManager

class ControlPanel:
    def __init__(self, root, auth_manager, device_manager):
        self.root = root
        self.auth_manager = auth_manager
        self.device_manager = device_manager
        
        self.location_tracker = LocationTracker()
        self.evidence_capture = EvidenceCapture()
        self.alarm_system = AlarmSystem()
        self.event_logger = EventLogger()
        self.lock_manager = LockManager()
        
        self.create_control_panel()
    
    def create_control_panel(self):
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header = tk.Frame(main_frame, bg="#2196F3", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        user_data = self.auth_manager.get_user_data()
        title = tk.Label(header, text=f"🛡️ Protection Active - {user_data.get('name', 'User')}", 
                        font=("Arial", 18, "bold"), bg="#2196F3", fg="white")
        title.pack(side=tk.LEFT, padx=20, pady=20)
        
        device_id = tk.Label(header, text=f"Device: {self.device_manager.get_device_id()[:8]}...", 
                           font=("Arial", 10), bg="#2196F3", fg="white")
        device_id.pack(side=tk.RIGHT, padx=20)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_status_tab(notebook)
        self.create_lock_tab(notebook)
        self.create_location_tab(notebook)
        self.create_evidence_tab(notebook)
        self.create_alarm_tab(notebook)
        self.create_logs_tab(notebook)
    
    def create_status_tab(self, notebook):
        tab = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(tab, text="📊 Status")
        
        status_frame = tk.LabelFrame(tab, text="Device Status", font=("Arial", 12, "bold"),
                                     bg="#f0f0f0", padx=20, pady=20)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        device_info = self.device_manager.get_device_info()
        
        info_text = f"""
System: {device_info['system']} {device_info['release']}
Hostname: {device_info['hostname']}
CPU: {device_info['cpu_count']} cores
Memory: {device_info['memory_total']}
Disk Usage: {device_info['disk_usage']}

Protection Status: ACTIVE ✅
Lock Status: {'LOCKED 🔒' if self.lock_manager.is_locked() else 'UNLOCKED 🔓'}
        """
        
        info_label = tk.Label(status_frame, text=info_text, font=("Arial", 11),
                             bg="#f0f0f0", fg="#333", justify=tk.LEFT)
        info_label.pack()
        
        event_summary = self.event_logger.get_event_summary()
        summary_text = f"""
Total Events Logged: {event_summary['total_events']}
        """
        
        summary_label = tk.Label(status_frame, text=summary_text, font=("Arial", 11),
                                bg="#f0f0f0", fg="#666", justify=tk.LEFT)
        summary_label.pack(pady=10)
    
    def create_lock_tab(self, notebook):
        tab = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(tab, text="🔒 Lock Control")
        
        lock_frame = tk.LabelFrame(tab, text="Remote Lock Settings", font=("Arial", 12, "bold"),
                                   bg="#f0f0f0", padx=20, pady=20)
        lock_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        is_locked = self.lock_manager.is_locked()
        
        status_label = tk.Label(lock_frame, 
                               text=f"Current Status: {'LOCKED 🔒' if is_locked else 'UNLOCKED 🔓'}",
                               font=("Arial", 14, "bold"), bg="#f0f0f0",
                               fg="red" if is_locked else "green")
        status_label.pack(pady=10)
        
        tk.Label(lock_frame, text="Lock Message (shown to thief):",
                font=("Arial", 11), bg="#f0f0f0").pack(pady=5)
        
        self.lock_message = scrolledtext.ScrolledText(lock_frame, height=5, width=50,
                                                       font=("Arial", 10))
        self.lock_message.pack(pady=10)
        
        current_message = self.lock_manager.get_lock_message()
        if current_message:
            self.lock_message.insert(tk.END, current_message)
        else:
            user_data = self.auth_manager.get_user_data()
            if user_data:
                default_msg = f"This laptop is stolen!\n\nOwner: {user_data.get('name')}\nContact: {user_data.get('contact')}\n\nReward for return!"
            else:
                default_msg = "This laptop is stolen!\n\nPlease return to owner for reward!"
            self.lock_message.insert(tk.END, default_msg)
        
        btn_frame = tk.Frame(lock_frame, bg="#f0f0f0")
        btn_frame.pack(pady=20)
        
        if is_locked:
            unlock_btn = tk.Button(btn_frame, text="🔓 Unlock Device",
                                  font=("Arial", 12, "bold"), bg="#4CAF50", fg="white",
                                  padx=20, pady=10, command=self.unlock_device)
            unlock_btn.pack(side=tk.LEFT, padx=10)
        else:
            lock_btn = tk.Button(btn_frame, text="🔒 Lock Device",
                                font=("Arial", 12, "bold"), bg="#f44336", fg="white",
                                padx=20, pady=10, command=self.lock_device)
            lock_btn.pack(side=tk.LEFT, padx=10)
    
    def lock_device(self):
        message = self.lock_message.get("1.0", tk.END).strip()
        if self.lock_manager.set_lock_status(True, message):
            self.event_logger.log_event("LOCK", "Device locked from control panel", 
                                       include_location=True, include_evidence=True)
            messagebox.showinfo("Success", "Device has been locked!")
            self.root.quit()
        else:
            messagebox.showerror("Error", "Failed to lock device!")
    
    def unlock_device(self):
        if self.lock_manager.set_lock_status(False, ""):
            self.event_logger.log_event("UNLOCK", "Device unlocked by owner")
            messagebox.showinfo("Success", "Device has been unlocked!")
            self.root.quit()
        else:
            messagebox.showerror("Error", "Failed to unlock device!")
    
    def create_location_tab(self, notebook):
        tab = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(tab, text="📍 Location")
        
        location_frame = tk.LabelFrame(tab, text="Location Tracking", font=("Arial", 12, "bold"),
                                       bg="#f0f0f0", padx=20, pady=20)
        location_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.location_text = scrolledtext.ScrolledText(location_frame, height=15, width=70,
                                                        font=("Courier", 10))
        self.location_text.pack(pady=10)
        
        btn_frame = tk.Frame(location_frame, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        
        track_btn = tk.Button(btn_frame, text="🌍 Get Current Location",
                             font=("Arial", 11, "bold"), bg="#2196F3", fg="white",
                             padx=20, pady=8, command=self.update_location)
        track_btn.pack()
    
    def update_location(self):
        self.location_text.delete("1.0", tk.END)
        self.location_text.insert(tk.END, "Tracking location...\n\n")
        
        def track():
            summary = self.location_tracker.get_location_summary()
            self.location_text.delete("1.0", tk.END)
            self.location_text.insert(tk.END, summary)
            self.event_logger.log_event("LOCATION_CHECK", "Location tracked manually", 
                                       include_location=True)
        
        thread = threading.Thread(target=track)
        thread.daemon = True
        thread.start()
    
    def create_evidence_tab(self, notebook):
        tab = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(tab, text="📸 Evidence")
        
        evidence_frame = tk.LabelFrame(tab, text="Evidence Capture", font=("Arial", 12, "bold"),
                                       bg="#f0f0f0", padx=20, pady=20)
        evidence_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        btn_frame = tk.Frame(evidence_frame, bg="#f0f0f0")
        btn_frame.pack(pady=20)
        
        webcam_btn = tk.Button(btn_frame, text="📷 Capture Webcam",
                              font=("Arial", 11, "bold"), bg="#FF9800", fg="white",
                              padx=20, pady=10, command=self.capture_webcam)
        webcam_btn.grid(row=0, column=0, padx=10, pady=10)
        
        screenshot_btn = tk.Button(btn_frame, text="🖥️ Take Screenshot",
                                  font=("Arial", 11, "bold"), bg="#9C27B0", fg="white",
                                  padx=20, pady=10, command=self.capture_screenshot)
        screenshot_btn.grid(row=0, column=1, padx=10, pady=10)
        
        full_btn = tk.Button(btn_frame, text="📸 Capture All Evidence",
                            font=("Arial", 11, "bold"), bg="#f44336", fg="white",
                            padx=20, pady=10, command=self.capture_full_evidence)
        full_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        
        self.evidence_text = scrolledtext.ScrolledText(evidence_frame, height=10, width=70,
                                                        font=("Courier", 9))
        self.evidence_text.pack(pady=10)
        
        self.update_evidence_list()
    
    def capture_webcam(self):
        result = self.evidence_capture.capture_webcam_photo()
        if result:
            messagebox.showinfo("Success", f"Webcam photo saved: {result}")
            self.event_logger.log_event("WEBCAM_CAPTURE", f"Manual webcam capture: {result}")
            self.update_evidence_list()
        else:
            messagebox.showerror("Error", "Failed to capture webcam photo!")
    
    def capture_screenshot(self):
        result = self.evidence_capture.capture_screenshot()
        if result:
            messagebox.showinfo("Success", f"Screenshot saved: {result}")
            self.event_logger.log_event("SCREENSHOT_CAPTURE", f"Manual screenshot: {result}")
            self.update_evidence_list()
        else:
            messagebox.showerror("Error", "Failed to capture screenshot!")
    
    def capture_full_evidence(self):
        def capture():
            result = self.evidence_capture.capture_evidence_set()
            self.event_logger.log_event("FULL_EVIDENCE_CAPTURE", 
                                       "Manual full evidence capture", 
                                       include_location=True, include_evidence=True)
            messagebox.showinfo("Success", 
                              f"Evidence captured!\nWebcam: {result['webcam']}\nScreenshot: {result['screenshot']}")
            self.update_evidence_list()
        
        thread = threading.Thread(target=capture)
        thread.daemon = True
        thread.start()
    
    def update_evidence_list(self):
        self.evidence_text.delete("1.0", tk.END)
        files = self.evidence_capture.get_evidence_files()
        
        if files:
            self.evidence_text.insert(tk.END, f"Evidence Files ({len(files)}):\n\n")
            for f in files[:20]:
                self.evidence_text.insert(tk.END, 
                    f"{f['filename']} - {f['size']/1024:.1f} KB - {f['modified'][:19]}\n")
        else:
            self.evidence_text.insert(tk.END, "No evidence files captured yet.")
    
    def create_alarm_tab(self, notebook):
        tab = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(tab, text="🚨 Alarm")
        
        alarm_frame = tk.LabelFrame(tab, text="Alarm System", font=("Arial", 12, "bold"),
                                    bg="#f0f0f0", padx=20, pady=20)
        alarm_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        info = tk.Label(alarm_frame, 
                       text="Trigger a loud alarm to alert people nearby.\nThe alarm will play even if system volume is low.",
                       font=("Arial", 11), bg="#f0f0f0", fg="#666")
        info.pack(pady=20)
        
        btn_frame = tk.Frame(alarm_frame, bg="#f0f0f0")
        btn_frame.pack(pady=20)
        
        test_btn = tk.Button(btn_frame, text="🔔 Test Alarm (3 sec)",
                            font=("Arial", 11, "bold"), bg="#FF9800", fg="white",
                            padx=20, pady=10, command=self.test_alarm)
        test_btn.grid(row=0, column=0, padx=10, pady=10)
        
        alarm_btn = tk.Button(btn_frame, text="🚨 Trigger Theft Alarm (30 sec)",
                             font=("Arial", 11, "bold"), bg="#f44336", fg="white",
                             padx=20, pady=10, command=self.trigger_alarm)
        alarm_btn.grid(row=0, column=1, padx=10, pady=10)
        
        stop_btn = tk.Button(btn_frame, text="⏹️ Stop Alarm",
                            font=("Arial", 11, "bold"), bg="#4CAF50", fg="white",
                            padx=20, pady=10, command=self.stop_alarm)
        stop_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
    
    def test_alarm(self):
        self.alarm_system.test_alarm(3)
        self.event_logger.log_event("ALARM_TEST", "Alarm test triggered")
    
    def trigger_alarm(self):
        self.alarm_system.trigger_theft_alarm()
        self.event_logger.log_event("ALARM_TRIGGERED", "Theft alarm triggered", 
                                   include_location=True, include_evidence=True)
        messagebox.showwarning("Alarm", "Theft alarm has been triggered for 30 seconds!")
    
    def stop_alarm(self):
        self.alarm_system.stop_alarm()
        self.event_logger.log_event("ALARM_STOPPED", "Alarm manually stopped")
    
    def create_logs_tab(self, notebook):
        tab = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(tab, text="📝 Logs")
        
        logs_frame = tk.LabelFrame(tab, text="Event Logs & Export", font=("Arial", 12, "bold"),
                                   bg="#f0f0f0", padx=20, pady=20)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        btn_frame = tk.Frame(logs_frame, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        
        refresh_btn = tk.Button(btn_frame, text="🔄 Refresh Logs",
                               font=("Arial", 11, "bold"), bg="#2196F3", fg="white",
                               padx=20, pady=8, command=self.refresh_logs)
        refresh_btn.grid(row=0, column=0, padx=10)
        
        export_btn = tk.Button(btn_frame, text="📄 Export Evidence Report",
                              font=("Arial", 11, "bold"), bg="#4CAF50", fg="white",
                              padx=20, pady=8, command=self.export_report)
        export_btn.grid(row=0, column=1, padx=10)
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=15, width=80,
                                                    font=("Courier", 9))
        self.logs_text.pack(pady=10)
        
        self.refresh_logs()
    
    def refresh_logs(self):
        self.logs_text.delete("1.0", tk.END)
        events = self.event_logger.get_recent_events(20)
        
        if events:
            self.logs_text.insert(tk.END, f"Recent Events (Last {len(events)}):\n\n")
            for event in reversed(events):
                self.logs_text.insert(tk.END, f"[{event['timestamp'][:19]}] ")
                self.logs_text.insert(tk.END, f"{event['type']}: {event['description']}\n")
                if 'location' in event and event['location'] and event['location'].get('ip_location'):
                    ip_loc = event['location']['ip_location']
                    self.logs_text.insert(tk.END, 
                        f"  📍 {ip_loc.get('city', 'Unknown')}, {ip_loc.get('country', 'Unknown')} ({ip_loc.get('ip', 'N/A')})\n")
                if 'evidence' in event and event['evidence']:
                    ev = event['evidence']
                    if ev.get('webcam'):
                        self.logs_text.insert(tk.END, f"  📷 Webcam captured\n")
                    if ev.get('screenshot'):
                        self.logs_text.insert(tk.END, f"  🖥️ Screenshot captured\n")
                self.logs_text.insert(tk.END, "\n")
        else:
            self.logs_text.insert(tk.END, "No events logged yet.")
    
    def export_report(self):
        report_file = self.event_logger.export_evidence_report()
        messagebox.showinfo("Success", f"Evidence report exported to:\n{report_file}")
        self.event_logger.log_event("REPORT_EXPORT", f"Evidence report exported: {report_file}")
