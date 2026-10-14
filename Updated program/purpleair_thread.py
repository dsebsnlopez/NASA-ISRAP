# purpleair_thread.py
import threading
import requests
import queue
import time
from config import CONFIG

class PurpleAirThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.trigger = threading.Event()
        self.data_queue = queue.Queue()
        self.running = True
        self.ip = CONFIG["WIFI_HOSTED"]["PURPLEAIR_IP"]

    def run(self):
        while self.running:
            self.trigger.wait()
            self.trigger.clear()
            
            try:
                # 3-second timeout ensures it doesn't block the 10-second cycle
                response = requests.get(f"http://{self.ip}/json", timeout=3.0)
                if response.status_code == 200:
                    data = response.json()
                    self.data_queue.put({
                        "pm2_5": data.get("pm2.5_aqi"),
                        "pm10": data.get("pm10_aqi"),
                        "temp": data.get("current_temp_f"),
                        "humidity": data.get("current_humidity"),
                        "pressure": data.get("pressure")
                    })
                else:
                    self.data_queue.put(None)
            except requests.RequestException:
                self.data_queue.put(None)

    def signal_read(self):
        self.trigger.set()