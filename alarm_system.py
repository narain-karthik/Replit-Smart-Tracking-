import pygame
import os
import threading
import time
from datetime import datetime

class AlarmSystem:
    def __init__(self):
        try:
            pygame.mixer.init()
            self.audio_available = True
        except pygame.error:
            print("Warning: No audio device available. Alarm functionality will be disabled.")
            self.audio_available = False
        
        self.is_playing = False
        self.alarm_thread = None
        
        if self.audio_available:
            self.create_alarm_sound()
    
    def create_alarm_sound(self):
        self.alarm_file = "data/alarm.wav"
        if not os.path.exists("data"):
            os.makedirs("data")
        
        if not os.path.exists(self.alarm_file):
            duration = 1.0
            frequency = 1000
            sample_rate = 22050
            
            import numpy as np
            import wave
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            wave_data = np.sin(2 * np.pi * frequency * t)
            wave_data = (wave_data * 32767).astype(np.int16)
            
            with wave.open(self.alarm_file, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(wave_data.tobytes())
    
    def play_alarm(self, duration=10):
        if not self.audio_available:
            print("Warning: Cannot play alarm - no audio device available")
            return
        
        if self.is_playing:
            return
        
        self.is_playing = True
        self.alarm_thread = threading.Thread(target=self._alarm_loop, args=(duration,))
        self.alarm_thread.daemon = True
        self.alarm_thread.start()
    
    def _alarm_loop(self, duration):
        try:
            pygame.mixer.music.load(self.alarm_file)
            pygame.mixer.music.set_volume(1.0)
            
            end_time = time.time() + duration
            while time.time() < end_time and self.is_playing:
                pygame.mixer.music.play()
                time.sleep(1.2)
        except Exception as e:
            print(f"Alarm error: {e}")
        finally:
            self.is_playing = False
    
    def stop_alarm(self):
        self.is_playing = False
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def test_alarm(self, duration=3):
        self.play_alarm(duration)
    
    def trigger_theft_alarm(self):
        self.play_alarm(30)
        self.log_alarm_event("Theft alarm triggered")
    
    def log_alarm_event(self, message):
        log_file = "data/alarm_log.txt"
        with open(log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {message}\n")
