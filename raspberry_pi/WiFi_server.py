import time
import logging
import subprocess
from typing import Optional, Dict, Any
import config

class WiFiController:
    """Manages system Wi-Fi state between Access Point (AP) and Station (STA) modes using Network Manager."""
    def __init__(self, ap_profile: str = "AP-Profile", sta_profile: str = "STA-Profile"):
        self.ap_profile = ap_profile
        self.sta_profile = sta_profile
        self.current_mode: Optional[str] = None
        self.interface = "wlan0"

    def profile_exists(self, profile_name: str) -> bool:
        """Checks if a NetworkManager connection profile already exists on the Pi."""
        result = subprocess.run(
            ["nmcli", "connection", "show", profile_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0

    def initialize_wifi_profiles(self):
        """Ensures required AP and STA profiles exist on the system; creates them if missing."""
        # 1. Initialize Access Point (AP) Profile
        if self.profile_exists(self.ap_profile):
            logging.info(f"Profile '{self.ap_profile}' already exists.")
        else:
            logging.info(f"Creating new AP profile '{self.ap_profile}'...")
            create_ap_cmd = [
                "sudo", "nmcli", "connection", "add", "type", "wifi",
                "ifname", self.interface, "mode", "ap",
                "con-name", self.ap_profile, "ssid", config.AP_SSID
            ]
            config_ap_cmd = [
                "sudo", "nmcli", "connection", "modify", self.ap_profile,
                "802-11-wireless-security.key-mgmt", "wpa-psk",
                "802-11-wireless-security.psk", config.AP_PASSWORD,
                "ipv4.method", "manual",
                "ipv4.addresses", config.AP_IP_ADDRESS
            ]
            if not (self._run_cmd(create_ap_cmd) and self._run_cmd(config_ap_cmd)):
                raise RuntimeError(f"Critical Failure: Could not create AP profile '{self.ap_profile}'.")
            logging.info(f"Successfully created AP profile '{self.ap_profile}'.")

        # 2. Initialize Station (STA) Client Profile
        if self.profile_exists(self.sta_profile):
            logging.info(f"Profile '{self.sta_profile}' already exists.")
        else:
            logging.info(f"Creating new STA profile '{self.sta_profile}'...")
            create_sta_cmd = [
                "sudo", "nmcli", "connection", "add", "type", "wifi",
                "ifname", self.interface,
                "con-name", self.sta_profile, "ssid", config.SCHOOL_WIFI_SSID
            ]
            config_sta_cmd = [
                "sudo", "nmcli", "connection", "modify", self.sta_profile,
                "802-11-wireless-security.key-mgmt", "wpa-psk",
                "802-11-wireless-security.psk", config.SCHOOL_WIFI_PASSWORD,
                "ipv4.method", "auto"
            ]
            if not (self._run_cmd(create_sta_cmd) and self._run_cmd(config_sta_cmd)):
                raise RuntimeError(f"Critical Failure: Could not create STA profile '{self.sta_profile}'.")
            logging.info(f"Successfully created STA profile '{self.sta_profile}'.")

    def _run_cmd(self, command: list) -> bool:
        """Executes system CLI commands safely."""
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {' '.join(command)}\nError: {e.stderr}")
            return False

    def switch_to_ap_mode(self) -> bool:
        """Switches interface to Access Point mode for local sensor connection."""
        logging.info("Switching to AP Mode...")
        if self._run_cmd(["sudo", "nmcli", "connection", "up", self.ap_profile]):
            self.current_mode = "AP"
            time.sleep(5) # Allow DHCP resolution
            return True
        return False

    def switch_to_sta_mode(self) -> bool:
        """Switches interace to Station mode to gain Internet access."""
        logging.info("Switching to STA Mode...")
        if self._run_cmd(["sudo", "nmcli", "connection", "up", self.sta_profile]):
            self.current_mode = "STA"
            time.sleep(5) # Allow DHCP resolution
            return True
        return False

    def check_internet_connection(self) -> bool:
        """Verifies active external Internet connectivity."""
        return self._run_cmd(["ping", "-c", "1", "-W", "2", "8.8.8.8"])
    
