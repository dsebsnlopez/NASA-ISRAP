import time
import logging
import threading
from queue import Queue
import config
from arduino_reader import ArduinoReader
from purpleair_client import PurpleAirReceiver
from WiFi_server import WiFiController
from logger import setup_system_logger, sort_chronological_logs

setup_system_logger()
logging.info("Starting Sensor Pipeline")


# Initialize queues and the synchronizing trigger
poll_trigger = threading.Event()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AppConductor:
    """Main application controller managing state transitions and outbound tasks."""
    def __init__(self):
        self.wifi = WiFiController()
        self.receiver = PurpleAirReceiver()

    def conductor_loop(self):
        """Main loop that triggers the synchronized poll and precesses queues."""
        # 1. Start both threads
        poll_trigger.set()

        # 2. Immediately clear it so it resets for the next cycle
        poll_trigger.clear()

        # 3. Wait for data to arrive in both queues

        # Logic for check queues and data pairing

        #4. Wait 10 seconds before triggering th enext synchornized poll
        time.sleep(config.PURPLEAIR_POLL_INTERVAL)

import time
import logging
import threading
from queue import Queue
import config
from arduino_reader import ArduinoReader
from purpleair_client import PurpleAirReceiver
from WiFi_server import WiFiController
from logger import setup_system_logger, sort_chronological_logs

setup_system_logger()
logging.info("Starting Sensor Pipeline")


# Initialize queues and the synchronizing trigger
poll_trigger = threading.Event()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AppConductor:
    """Main application controller managing state transitions and outbound tasks."""
    def __init__(self):
        self.wifi = WiFiController()
        self.receiver = PurpleAirReceiver()

    def conductor_loop(self):
        """Main loop that triggers the synchronized poll and precesses queues."""
        # 1. Start both threads
        poll_trigger.set()

        # 2. Immediately clear it so it resets for the next cycle
        poll_trigger.clear()

        # 3. Wait for data to arrive in both queues

        # Logic for check queues and data pairing

        #4. Wait 10 seconds before triggering th enext synchornized poll
        time.sleep(config.PURPLEAIR_POLL_INTERVAL)
