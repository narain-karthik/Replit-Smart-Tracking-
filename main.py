import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from auth_manager import AuthManager
from device_manager import DeviceManager
from control_panel import ControlPanel

class AntiTheftApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Laptop Anti-Theft Protection")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        self.auth_manager = AuthManager()
        self.device_manager = DeviceManager()
        
        self.current_frame = None
        
        if self.auth_manager.is_device_registered():
            self.show_login_screen()
        else:
            self.show_registration_screen()
    
    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
    
    def show_registration_screen(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        title = tk.Label(self.current_frame, text="🔒 Device Registration", 
                        font=("Arial", 24, "bold"), bg="#f0f0f0", fg="#333")
        title.pack(pady=40)
        
        subtitle = tk.Label(self.current_frame, 
                           text="Register this device to protect it from theft",
                           font=("Arial", 12), bg="#f0f0f0", fg="#666")
        subtitle.pack(pady=10)
        
        form_frame = tk.Frame(self.current_frame, bg="#f0f0f0")
        form_frame.pack(pady=30)
        
        tk.Label(form_frame, text="Owner Name:", font=("Arial", 11), 
                bg="#f0f0f0", fg="#333").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.reg_name = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.reg_name.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(form_frame, text="Email:", font=("Arial", 11), 
                bg="#f0f0f0", fg="#333").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.reg_email = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.reg_email.grid(row=1, column=1, padx=10, pady=10)
        
        tk.Label(form_frame, text="Password:", font=("Arial", 11), 
                bg="#f0f0f0", fg="#333").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.reg_password = tk.Entry(form_frame, font=("Arial", 11), width=30, show="*")
        self.reg_password.grid(row=2, column=1, padx=10, pady=10)
        
        tk.Label(form_frame, text="Contact Number:", font=("Arial", 11), 
                bg="#f0f0f0", fg="#333").grid(row=3, column=0, sticky="e", padx=10, pady=10)
        self.reg_contact = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.reg_contact.grid(row=3, column=1, padx=10, pady=10)
        
        register_btn = tk.Button(self.current_frame, text="Register Device", 
                                font=("Arial", 12, "bold"), bg="#4CAF50", fg="white",
                                padx=40, pady=10, command=self.register_device)
        register_btn.pack(pady=20)
    
    def register_device(self):
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        contact = self.reg_contact.get().strip()
        
        if not all([name, email, password, contact]):
            messagebox.showerror("Error", "All fields are required!")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters!")
            return
        
        success = self.auth_manager.register_device(name, email, password, contact)
        if success:
            device_id = self.device_manager.generate_device_id()
            user_data = self.auth_manager.get_user_data()
            api_key = user_data.get('api_key', 'N/A') if user_data else 'N/A'
            
            messagebox.showinfo("Success", 
                              f"Device registered successfully!\n\n"
                              f"Device ID: {device_id}\n"
                              f"API Key: {api_key}\n\n"
                              f"IMPORTANT: Save your API key for remote access!\n"
                              f"You can use it to control this device remotely.")
            self.show_login_screen()
        else:
            messagebox.showerror("Error", "Registration failed!")
    
    def show_login_screen(self):
        self.clear_frame()
        self.current_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        title = tk.Label(self.current_frame, text="🔐 Anti-Theft Login", 
                        font=("Arial", 24, "bold"), bg="#f0f0f0", fg="#333")
        title.pack(pady=60)
        
        form_frame = tk.Frame(self.current_frame, bg="#f0f0f0")
        form_frame.pack(pady=30)
        
        tk.Label(form_frame, text="Email:", font=("Arial", 11), 
                bg="#f0f0f0", fg="#333").grid(row=0, column=0, sticky="e", padx=10, pady=15)
        self.login_email = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.login_email.grid(row=0, column=1, padx=10, pady=15)
        
        tk.Label(form_frame, text="Password:", font=("Arial", 11), 
                bg="#f0f0f0", fg="#333").grid(row=1, column=0, sticky="e", padx=10, pady=15)
        self.login_password = tk.Entry(form_frame, font=("Arial", 11), width=30, show="*")
        self.login_password.grid(row=1, column=1, padx=10, pady=15)
        
        login_btn = tk.Button(self.current_frame, text="Login", 
                             font=("Arial", 12, "bold"), bg="#2196F3", fg="white",
                             padx=50, pady=10, command=self.login)
        login_btn.pack(pady=20)
        
        device_info = tk.Label(self.current_frame, 
                              text=f"Device ID: {self.device_manager.get_device_id()}",
                              font=("Arial", 9), bg="#f0f0f0", fg="#999")
        device_info.pack(side=tk.BOTTOM, pady=20)
    
    def login(self):
        email = self.login_email.get().strip()
        password = self.login_password.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter email and password!")
            return
        
        if self.auth_manager.verify_login(email, password):
            self.show_control_panel()
        else:
            messagebox.showerror("Error", "Invalid credentials!")
            self.auth_manager.log_failed_attempt(email)
    
    def show_control_panel(self):
        self.clear_frame()
        control_panel = ControlPanel(self.root, self.auth_manager, self.device_manager)

def main():
    root = tk.Tk()
    app = AntiTheftApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
