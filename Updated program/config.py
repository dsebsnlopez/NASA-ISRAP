# config.py
CONFIG = {
    "DEVICE_ID": "PI_LOGGER_01",
    "POLL_INTERVAL_SEC": 10.0,
    
    "WIFI_HOSTED": {
        "SSID": "ISRAP_AirLogger",
        "PASS": "nasa_israp_2026",
        "PURPLEAIR_IP": "192.168.4.2" # Static DHCP lease recommended
    },
    "WIFI_CLIENT": {
        "SSID": "Target_Upload_Network",
        "PASS": "upload_password"
    },
    
    "UPLOAD_WINDOW": {
        "START_HOUR": 2, # 02:00
        "END_HOUR": 3,   # 03:00
        "TIMEZONE": "America/Chicago"
    },
    "TARGET_LOCATIONS": [
        {"lat": 29.5845, "lon": -98.6180, "radius_m": 100} # UTSA Campus placeholder
    ],
    
    "REMOTE_SERVER": {
        "URL": "https://api.yourdomain.com/upload",
        "API_KEY": "your_secure_api_key"
    },
    
    "ALERT_EMAIL": {
        "SENDER": "logger.alerts@gmail.com",
        "APP_PASSWORD": "abcd efgh ijkl mnop",
        "RECIPIENT": "admin@gmail.com"
    },
    
    "I2C_ADDRESSES": {
        "O3_ADDR": 0x72,
        "NO2_ADDR": 0x73
    }
}