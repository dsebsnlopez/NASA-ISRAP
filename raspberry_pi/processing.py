import math
from datetime import datetime
import logging
import config

def get_current_gps_fix() -> dict:
    """
    OPEN ITEM: Fetch real GPS data from hardware.
    Using placeholders for now.
    """
    try:
        # Placeholder implementation
        return {
            "latitude": 29.7604,  # e.g., Houston, TX
            "longitude": -95.3698,
            "fix_age": 0.5 # seconds since last valid NMEA sentence
        }
    except Exception:
        logging.exception("Error acquiring GPS fix.")
        return {"latitude": None, "longitude": None, "fix_age": None}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance in meters between two GPS coordinates."""
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
        
    R = 6371000 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def is_at_transfer_site() -> bool:
    gps = get_current_gps_fix()
    dist = haversine_distance(
        gps.get("latitude"), gps.get("longitude"),
        config.TARGET_LAT, config.TARGET_LON
    )
    return dist <= config.LOCATION_RADIUS_M

def process_paired_reading(arduino_raw: dict, purpleair_raw: dict) -> dict:
    """Takes the outputs from both queues and generates the final JSON payload."""
    
    arduino_val = arduino_raw.get("data") if arduino_raw.get("status") == "success" else arduino_raw.get("reason")
    purpleair_val = purpleair_raw.get("data") if purpleair_raw.get("status") == "success" else purpleair_raw.get("reason")

    gps_data = get_current_gps_fix()
    
    # OPEN ITEM: Exact calculations based on sensor data.
    calculations = {}
    if arduino_raw.get("status") == "success" and purpleair_raw.get("status") == "success":
        calculations["example_metric"] = "Derived value goes here"
    
    payload = {
        "device_id": config.DEVICE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sensors": {
            "arduino": arduino_val,
            "purpleair": purpleair_val
        },
        "calculations": calculations,
        "gps": gps_data
    }
    return payload