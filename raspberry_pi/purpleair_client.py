<<<<<<< HEAD
import time
import logging
import subprocess
import requests
from typing import Optional, Dict, Any
from threading import Thread, Event
from queue import Queue, Full
import config

class PurpleAirReceiver:
    """Polls the local PurpleAir sensor API for JSON telemetry."""
    def __init__(self, poll_trigger: Event, host: str = config.PURPLEAIR_IP, output_queue: Queue):
        self.host = host
        self.url = f"http://{self.host}/json"
        self.poll_trigger = poll_trigger
        self.output_queue = output_queue
        self.poll_thread: Optional[Thread] = None
        self._stop_event = False

    def start(self):
        """Starts the polling loop on a background thread."""
        logging.info(f"Starting PurpleAir polling thread for {self.url}...")
        self._stop_event = False
        self.poll_thread = Thread(target=self._poll_sensor, daemon=True)
        self.poll_thread.start()

    def stop(self):
        """Gracefully stops the polling thread."""
        self._stop_event = True
        self.poll_trigger.set()
        if self.poll_thread:
            self.poll_thread.join(timeout=2)
        logging.info("PurpleAir polling thread stopped.")

    def _poll_sensor(self):
        """Continously polls the sensor at the configured interval."""
        while not self._stop_event:
            try:
                # 1. Wait for the exact same trigger as the Arduino
                self.poll_trigger.wait()

                # 2. Capture the identical timestamp
                exact_poll_time = time.time()

                # 3. Make the network request
                response = requests.get(self.url, timeout=5)
                response.raise_for_status()

                # 4. Bundle the response with the pre-network timestamp
                payload = {
                    "poll_time": exact_poll_time,
                    "data": response.json()
                }
                # 5. Push safely to the queue
                try:
                    self.output_queue.put_nowait(payload)
                    logging.info("Successfully polled PurpleAir sensor.")
                except Full:
                    logging.error("PurpleAir queue filled up; reading dropped.")

            except Exception:
                logging.exception(f"Critical failure while polling PurpleAir sensor at {self.url}")


=======
import time
import logging
import subprocess
import requests
from typing import Optional, Dict, Any
from threading import Thread, Event
from queue import Queue, Full
import config

class PurpleAirReceiver:
    """Polls the local PurpleAir sensor API for JSON telemetry."""
    def __init__(self, poll_trigger: Event, host: str = config.PURPLEAIR_IP, output_queue: Queue):
        self.host = host
        self.url = f"http://{self.host}/json"
        self.poll_trigger = poll_trigger
        self.output_queue = output_queue
        self.poll_thread: Optional[Thread] = None
        self._stop_event = False

    def start(self):
        """Starts the polling loop on a background thread."""
        logging.info(f"Starting PurpleAir polling thread for {self.url}...")
        self._stop_event = False
        self.poll_thread = Thread(target=self._poll_sensor, daemon=True)
        self.poll_thread.start()

    def stop(self):
        """Gracefully stops the polling thread."""
        self._stop_event = True
        self.poll_trigger.set()
        if self.poll_thread:
            self.poll_thread.join(timeout=2)
        logging.info("PurpleAir polling thread stopped.")

    def _poll_sensor(self):
        """Continously polls the sensor at the configured interval."""
        while not self._stop_event:
            try:
                # 1. Wait for the exact same trigger as the Arduino
                self.poll_trigger.wait()

                # 2. Capture the identical timestamp
                exact_poll_time = time.time()

                # 3. Make the network request
                response = requests.get(self.url, timeout=5)
                response.raise_for_status()

                # 4. Bundle the response with the pre-network timestamp
                payload = {
                    "poll_time": exact_poll_time,
                    "data": response.json()
                }
                # 5. Push safely to the queue
                try:
                    self.output_queue.put_nowait(payload)
                    logging.info("Successfully polled PurpleAir sensor.")
                except Full:
                    logging.error("PurpleAir queue filled up; reading dropped.")

            except Exception:
                logging.exception(f"Critical failure while polling PurpleAir sensor at {self.url}")


>>>>>>> 5df0bff0bf7b1abe9ffa39e79bf6ac0a9ac136df
