import requests
import logging
import json
import config

def send_batch(readings: list) -> bool:
    """
    Transforms and uploads SQLite records to the university server.
    Only returns True if receipt AND schema validation are confirmed by the server.
    """
    if not readings:
        return True

    try:
        # OPEN ITEM: Server API format. 
        # Transforming SQLite rows back into a list of nested dicts.
        payload = []
        for row in readings:
            payload.append({
                "local_id": row["id"],
                "device_id": row["device_id"],
                "timestamp": row["timestamp"],
                "sensors": {
                    "arduino": _safe_json_load(row["arduino_data"]),
                    "purpleair": _safe_json_load(row["purpleair_data"])
                },
                "calculations": _safe_json_load(row["calculations"]),
                "gps": {
                    "latitude": row["gps_lat"],
                    "longitude": row["gps_lon"],
                    "fix_age": row["gps_fix_age"]
                }
            })

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.SERVER_AUTH_TOKEN}"
        }

        # OPEN ITEM: University server endpoint and TLS verification rules.
        response = requests.post(
            config.SERVER_URL, 
            json=payload, 
            headers=headers, 
            timeout=config.SERVER_TIMEOUT,
            verify=True # Use HTTPS
        )
        
        response.raise_for_status()
        
        # Validate that the server actually acknowledged receipt and schema
        # OPEN ITEM: Final university server response format.
        server_resp = response.json()
        if server_resp.get("status") == "success":
            logging.info(f"Successfully uploaded batch of {len(readings)} records.")
            return True
        else:
            logging.error(f"Server rejected batch: {server_resp}")
            return False

    except Exception:
        logging.exception("Failed to communicate with university server.")
        return False

def _safe_json_load(data_str: str):
    """Helper to cleanly parse stored database strings back to objects."""
    if data_str == "(reading unsuccessful)" or data_str is None:
        return "(reading unsuccessful)"
    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        return data_str