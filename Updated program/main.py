# main.py
import time
import threading
import math
import subprocess
import json
import hashlib
import requests
import serial
import pynmea2
from datetime import datetime
from config import CONFIG
from database import init_db, insert_row, get_unuploaded_data, delete_uploaded_data
from error_logger import ErrorLogger
from purpleair_thread import PurpleAirThread

# Pseudo-library for I2C (replace with actual DFRobot library integration)
import smbus2

class I2CThread:
    def __init__(self):
        self.bus = smbus2.SMBus(1)
        self.lock = threading.Lock()
        self.latest_data = {"o3": None, "no2": None}

    def read_sensors(self):
        with self.lock:
            try:
                # Raw byte reads translated to hardware specs
                o3_raw = self.bus.read_i2c_block_data(CONFIG["I2C_ADDRESSES"]["O3_ADDR"], 0x00, 2)
                self.latest_data["o3"] = (o3_raw[0] << 8 | o3_raw[1]) / 1000.0
            except Exception:
                self.latest_data["o3"] = None
                
            try:
                no2_raw = self.bus.read_i2c_block_data(CONFIG["I2C_ADDRESSES"]["NO2_ADDR"], 0x00, 2)
                self.latest_data["no2"] = (no2_raw[0] << 8 | no2_raw[1]) / 1000.0
            except Exception:
                self.latest_data["no2"] = None

    def get_data(self):
        with self.lock:
            return self.latest_data.copy()

class GPSReader:
    def __init__(self):
        try:
            self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        except serial.SerialException:
            self.ser = None

    def read_gps(self):
        if not self.ser: return {"lat": None, "lon": None}
        self.ser.reset_input_buffer()
        for _ in range(10): # Try reading up to 10 lines
            line = self.ser.readline().decode('ascii', errors='replace')
            if line.startswith('$GPGGA') or line.startswith('$GNRMC'):
                try:
                    msg = pynmea2.parse(line)
                    if msg.latitude != 0.0:
                        return {"lat": msg.latitude, "lon": msg.longitude}
                except pynmea2.ParseError:
                    continue
        return {"lat": None, "lon": None}

class Formatter:
    @staticmethod
    def compile(timestamp, gps, purple_air, i2c):
        # Maps each value to its column; inserts NULL for missing values
        return {
            "timestamp": timestamp,
            "latitude": gps.get("lat") if gps else None,
            "longitude": gps.get("lon") if gps else None,
            "device_id": CONFIG["DEVICE_ID"],
            "pm2_5": purple_air.get("pm2_5") if purple_air else None,
            "pm10": purple_air.get("pm10") if purple_air else None,
            "temp": purple_air.get("temp") if purple_air else None,
            "humidity": purple_air.get("humidity") if purple_air else None,
            "pressure": purple_air.get("pressure") if purple_air else None,
            "o3": i2c.get("o3") if i2c else None,
            "no2": i2c.get("no2") if i2c else None
        }

class Uploader:
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        if None in (lat1, lon1, lat2, lon2): return float('inf')
        R, phi1, phi2 = 6371000, math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def should_upload(self, gps_data):
        now = datetime.now()
        if not (CONFIG["UPLOAD_WINDOW"]["START_HOUR"] <= now.hour < CONFIG["UPLOAD_WINDOW"]["END_HOUR"]):
            return False
            
        for loc in CONFIG["TARGET_LOCATIONS"]:
            dist = self.haversine(gps_data.get("lat"), gps_data.get("lon"), loc["lat"], loc["lon"])
            if dist <= loc["radius_m"]:
                return True
        return False

    def toggle_wifi(self, mode):
        # Assumes NetworkManager (nmcli) is used on the Pi
        if mode == "client":
            subprocess.run(["nmcli", "connection", "down", CONFIG["WIFI_HOSTED"]["SSID"]], check=False)
            subprocess.run(["nmcli", "device", "wifi", "connect", CONFIG["WIFI_CLIENT"]["SSID"], "password", CONFIG["WIFI_CLIENT"]["PASS"]], check=False)
        else: # restore hosting
            subprocess.run(["nmcli", "connection", "up", CONFIG["WIFI_HOSTED"]["SSID"]], check=False)

    def execute_upload(self, error_logger):
        self.toggle_wifi("client")
        time.sleep(10) # Wait for connection
        
        error_logger.send_queued_emails()
        data = get_unuploaded_data()
        
        if data:
            payload = json.dumps(data)
            payload_hash = hashlib.sha256(payload.encode()).hexdigest()
            
            try:
                # Retry logic for push[cite: 1]
                for attempt in range(3):
                    resp = requests.post(
                        CONFIG["REMOTE_SERVER"]["URL"], 
                        json={"data": data, "hash": payload_hash},
                        headers={"Authorization": f"Bearer {CONFIG['REMOTE_SERVER']['API_KEY']}"},
                        timeout=30
                    )
                    if resp.status_code == 200:
                        # Verify cheap hash[cite: 1]
                        server_hash = resp.json().get("received_hash")
                        if server_hash == payload_hash:
                            uploaded_timestamps = [row["timestamp"] for row in data]
                            delete_uploaded_data(uploaded_timestamps)
                            break
                    time.sleep(5)
            except Exception as e:
                error_logger.log_critical(f"Upload failed: {e}")
                
        self.toggle_wifi("host")

def main():
    init_db()
    logger = ErrorLogger()
    
    pa_thread = PurpleAirThread()
    pa_thread.start()
    
    i2c_thread = I2CThread()
    gps_reader = GPSReader()
    uploader = Uploader()

    while True:
        cycle_start = time.time()
        timestamp = datetime.now().isoformat()
        
        # Trigger reads
        pa_thread.signal_read()
        i2c_thread.read_sensors()
        gps_data = gps_reader.read_gps()
        
        # End-of-day upload check[cite: 1]
        if uploader.should_upload(gps_data):
            uploader.execute_upload(logger)
            continue # Skip recording while window is active[cite: 1]

        # Fetch I2C under lock[cite: 1]
        i2c_data = i2c_thread.get_data()
        if i2c_data["o3"] is None: logger.log_minor("O3", "No data")
        else: logger.log_success("O3")
        
        # Fetch PA from queue[cite: 1]
        try:
            pa_data = pa_thread.data_queue.get(timeout=2)
            if pa_data is None: logger.log_minor("PurpleAir", "No data")
            else: logger.log_success("PurpleAir")
        except queue.Empty:
            pa_data = None
            logger.log_minor("PurpleAir", "Queue timeout")

        if gps_data.get("lat") is None: logger.log_minor("GPS", "No fix")
        else: logger.log_success("GPS")

        # Compile and Insert
        row_dict = Formatter.compile(timestamp, gps_data, pa_data, i2c_data)
        insert_row(row_dict)

        # Wait until exactly 10s has passed[cite: 1]
        elapsed = time.time() - cycle_start
        sleep_time = CONFIG["POLL_INTERVAL_SEC"] - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()