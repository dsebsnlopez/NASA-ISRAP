import os

"""
config.py

Centralizes all configurable constants, thresholds, and placeholder secrets for the environmental 
sensor data pipeline. Values are loaded from environment variables (e.g., via a .env file) 
to prevent hardcoding sensitive credentials in the source code.
"""

# ==========================================
# SYSTEM & DEVICE
# ==========================================
# Identifies this specific Raspberry Pi unit in local logs and server payloads.
DEVICE_ID = os.environ.get("DEVICE_ID", "RPI5_STATION_01")

# Directory where the SQLite database (sensors.db) and local logs will be stored.
DATA_DIR = os.environ.get("DATA_DIR", "data")


# ==========================================
# ARDUINO CONFIGURATION
# ==========================================
# Serial communication settings for the wired Arduino connection.
ARDUINO_PORT = os.environ.get("ARDUINO_PORT", "/dev/ttyUSB0")
ARDUINO_BAUD = int(os.environ.get("ARDUINO_BAUD", 115200))

# The BCM GPIO pin on the Pi used to detect when the Arduino is ready to send data.
# [ACTION REQUIRED]: Verify Arduino logic voltage. If the Arduino outputs 5V, 
# you MUST use a level shifter or voltage divider before connecting to this 3.3V Pi pin.
ARDUINO_READY_PIN = int(os.environ.get("ARDUINO_READY_PIN", 17)) 

# [ACTION REQUIRED]: Exact Arduino acknowledgment protocol. 
# This byte string must perfectly match what the Arduino's C++ code expects to receive.
ARDUINO_ACK_MSG = b"ACK\n"

# Polling frequency and retry limits for serial reads.
ARDUINO_POLL_INTERVAL = float(os.environ.get("ARDUINO_POLL_INTERVAL", 10.0))
ARDUINO_RETRY_COUNT = 2


# ==========================================
# NETWORK & WIFI CONFIGURATION
# ==========================================
# Pi Hotspot (Access Point) Credentials - The network the Pi broadcasts for the PurpleAir.
# [ACTION REQUIRED]: Change the default AP_PASSWORD in your .env file before deployment.
AP_SSID = os.environ.get("AP_SSID", "PiAirflow_Network")
AP_PASSWORD = os.environ.get("AP_PASSWORD", "SecurePassword123")
AP_IP_ADDRESS = os.environ.get("AP_IPADDRESS", "192.168.4.1/24")

# School/University (Station) Credentials - The network the Pi uses to upload data.
# [ACTION REQUIRED]: Update these with the actual university Wi-Fi credentials in your .env file.
SCHOOL_WIFI_SSID = os.environ.get("SCHOOL_WIFI_SSID", "University_IoT_Net")
SCHOOL_WIFI_PASSWORD = os.environ.get("SCHOOL_WIFI_PASSWORD", "SchoolWifiPassword123")


# ==========================================
# PURPLEAIR CONFIGURATION
# ==========================================
# [ACTION REQUIRED]: The Pi hotspot defaults to the 10.42.0.x subnet. 
# Run `nmcli dev wifi` on the Pi after the sensor connects to find its exact IP, then update this.
PURPLEAIR_IP = os.environ.get("PURPLEAIR_IP", "10.42.0.X") 
PURPLEAIR_URL = f"http://{PURPLEAIR_IP}/json"

# Polling frequency and retry limits for the PurpleAir local API.
PURPLEAIR_POLL_INTERVAL = os.environ.get("PURPLEAIR_POLL_INTERVAL", 10.0)
PURPLEAIR_RETRY_COUNT = 2


# ==========================================
# QUEUES & RETRIES
# ==========================================
# [ACTION REQUIRED]: Maximum number of readings held in RAM before dropping new ones. 
# Adjust based on expected polling rates and Pi memory constraints.
QUEUE_MAX_SIZE = int(os.environ.get("QUEUE_MAX_SIZE", 50))

# Exponential backoff parameters (in seconds) used by the PurpleAir client for retries.
BACKOFF_BASE = 2.0
BACKOFF_MAX = 30.0


# ==========================================
# SQLITE & STORAGE
# ==========================================
# Full file path for the local SQLite database.
DB_FILENAME = os.environ.get("DB_FILENAME", "DATA_PIPELINE.db")
DB_PATH = os.path.join(DATA_DIR, DB_FILENAME)
STATUS_TABLE = os.environ.get("STATUS_TABLE", "STATUS_TABLE")
DATA_TABLE = os.environ.get("DATA_TABLE", "SENSOR_DATA")



# ==========================================
# GPS & TRANSFER SITE 
# ==========================================
# [ACTION REQUIRED]: The physical coordinates where the Pi is allowed to upload data.
TARGET_LAT = float(os.environ.get("TARGET_LAT", 0.0))
TARGET_LON = float(os.environ.get("TARGET_LON", 0.0))

# [ACTION REQUIRED]: How close (in meters) the Pi must be to the TARGET coordinates to trigger an upload.
LOCATION_RADIUS_M = float(os.environ.get("LOCATION_RADIUS_M", 100.0))


# ==========================================
# UPLOAD & SERVER
# ==========================================
# [ACTION REQUIRED]: The daily time window (24-hour local time) when uploads are permitted.
UPLOAD_WINDOW_START = os.environ.get("UPLOAD_WINDOW_START", "00:05")
UPLOAD_WINDOW_END = os.environ.get("UPLOAD_WINDOW_END", "1:00")

# [ACTION REQUIRED]: University server API details. 
# Replace the URL and set a real AUTH_TOKEN in your .env file once the API spec is provided.
SERVER_URL = os.environ.get("SERVER_URL", "https://REPLACE_WITH_UNIVERSITY_SERVER/api/upload")
UPLOAD_ENDPOINT = os.environ.get("UPLOAD_ENDPOINT", "/api/upload")
VERIFY_ENDPOINT = os.environ.get("VERIFY_ENDPOINT", "/api/verify")
SERVER_API_KEY = os.environ.get("SERVER_API_KEY", "REPLACE_ME")
SERVER_TIMEOUT = int(os.environ.get("SERVER_TIMEOUT", 30))


# ==========================================
# DIAGNOSTIC SERVER & SECRETS
# ==========================================
# Local Flask server settings. Binding to 10.42.0.1 keeps it strictly on the local Pi hotspot network.
DIAGNOSTIC_HOST = os.environ.get("DIAGNOSTIC_HOST", "10.42.0.1") 
DIAGNOSTIC_PORT = int(os.environ.get("DIAGNOSTIC_PORT", 8080))

# [ACTION REQUIRED]: The API key required to access the local diagnostic dashboard endpoints.
LOCAL_API_KEY = os.environ.get("LOCAL_API_KEY", "REPLACE_WITH_SECURE_KEY")


# ==========================================
# ALERTING 
# ==========================================
# [ACTION REQUIRED]: SMTP settings for sending warning emails if data fails to upload for 2+ days.
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.example.com")
SMTP_USER = os.environ.get("SMTP_USER", "alerts@example.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "email_password")
ALERT_RECIPIENT = os.environ.get("ALERT_RECIPIENT", "admin@example.com")