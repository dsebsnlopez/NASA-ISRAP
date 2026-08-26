<<<<<<< HEAD
# IRAM ISRAP Environmental Sensor Pipeline

This application runs on a Raspberry Pi 5 to collect, store, and upload environmental data from an Arduino and a PurpleAir sensor.

## Hardware & Wiring Warnings ⚠️
**CRITICAL:** The Raspberry Pi 5 uses 3.3V logic for its GPIO pins and is **NOT 5V tolerant**. 
If your Arduino outputs a 5V ready signal, connecting it directly to the Pi will permanently damage the Pi. 
* **Resolution:** You must use a logic level shifter or a voltage divider if the Arduino uses 5V logic.

## Setup & Installation

1. **Install OS Dependencies:**
   Ensure the Pi is updated and uses NetworkManager (the default on newer Pi OS installs like Bullseye/Bookworm).
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3-pip python3-venv nmcli -y
    ```

2. Configure Pi as a Hotspot:
Use NetworkManager to broadcast PiAirflow_Network.
Once the PurpleAir sensor connects, find its IP (usually starting with 10.42.0.x) and update the PURPLEAIR_IP environment variable.

3. Python Environment
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

4.Environment Variables:
Create a .env file or export secrets before running. Do NOT hardcode passwords or API keys in config.py.
=======
# NASA-ISRAP
>>>>>>> 5df0bff0bf7b1abe9ffa39e79bf6ac0a9ac136df
