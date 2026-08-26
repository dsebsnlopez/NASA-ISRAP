<<<<<<< HEAD
import config
import time
import logging
import serial
import json
from threading import Thread, Event
from queue import Queue, Full
from typing import Optional


class ArduinoReader:
    """Manages serial connection to Arduino, sends heartbeats, and reads Json data"""
    def __init__(self, poll_trigger: Event, port: str = config.ARDUINO_PORT, baudrate: int = 115200, output_queue: Queue = None):
          
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.poll_trigger = self.poll_trigger

        self.output_queue = output_queue if output_queue else Queue(maxsize=config.QUEUE_MAX_SIZE)
        self.poll_thread: Optional[Thread] = None
        self._stop_event = False

    def start(self):
        """Starts the serial polling loop on a background thread."""
        logging.info(f"Starting Arduino serial reader on {self.port} at {self.baudrate} baud...")
        self._stop_event = False
        self.poll_thread = Thread(target=self._poll_sensor, daemon=True)
        self.poll_thread.start()

    def stop(self):
        """Gracefully stops the polling thread and closes the serial connection."""
        self._stop_event = True
        self.poll_trigger.set()
        if self.poll_thread:
            self.poll_thread.join(timeout=2)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        logging.info("Arduino polling thread stopped.")

    def _poll_sensor(self):
        """Sends 'S' command at configured intervals and reads the JSON response."""
        while not self._stop_event:
            try:
                if self.serial_conn is None or not self.serial_conn.is_open:
                    self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=2.0)

                # 1. Block and wait for main.py to signal the poll
                triggered = self.poll_trigger.wait(timeout=1.0)
                if triggered:
                    self.poll_trigger.clear()
                    
                    # 2. IMMEDIATELY capture the poll timestamp (vefore any I/O delay)
                    exact_poll_time = time.time()

                    # 3. Request the sample from Arduino
                    self.serial_conn.write(b'S')
                    self.serial_conn.flush()
                    logging.debug("Sent 'S' polling command to Arduino.")

                    # 4. Wait for and read the response
                    raw_line = self.serial_conn.readline().decode('utf-8').strip()

                    if raw_line:
                        try:
                            parsed_data = json.loads(raw_line)
                            payload = {
                                "poll_time": exact_poll_time,
                                "data": parsed_data
                            }
                            try:
                                self.output_queue.put_nowait(payload)
                                logging.info("Successfully polled Arduino and pushed to queue.")
                            except Full:
                                logging.warning("Arduino queue filled up; reading dropped.")
                        except json.JSONDecodeError:
                            logging.error(f"Received malformed JSON from Arduino: {raw_line}")
                    else:
                        logging.warning("Arduino did not respond to 'S' command within timeout.")
                else:
                    self.serial_conn.write(b'H')
                    self.serial_conn.flush()

            except serial.SerialException as e:
                logging.error(f"Serial connection lost or failed to open: {e}. Retrying...")
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                self.serial_conn = None
                time.sleep(config.BACKOFF_BASE)

            except Exception:
                logging.exception(f"Critical failure while polling Arduino sensor")
                time.sleep(config.BACKOFF_BASE)

=======
import config
import time
import logging
import serial
import json
from threading import Thread, Event
from queue import Queue, Full
from typing import Optional


class ArduinoReader:
    """Manages serial connection to Arduino, sends heartbeats, and reads Json data"""
    def __init__(self, poll_trigger: Event, port: str = config.ARDUINO_PORT, baudrate: int = 115200, output_queue: Queue = None):
          
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.poll_trigger = self.poll_trigger

        self.output_queue = output_queue if output_queue else Queue(maxsize=config.QUEUE_MAX_SIZE)
        self.poll_thread: Optional[Thread] = None
        self._stop_event = False

    def start(self):
        """Starts the serial polling loop on a background thread."""
        logging.info(f"Starting Arduino serial reader on {self.port} at {self.baudrate} baud...")
        self._stop_event = False
        self.poll_thread = Thread(target=self._poll_sensor, daemon=True)
        self.poll_thread.start()

    def stop(self):
        """Gracefully stops the polling thread and closes the serial connection."""
        self._stop_event = True
        self.poll_trigger.set()
        if self.poll_thread:
            self.poll_thread.join(timeout=2)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        logging.info("Arduino polling thread stopped.")

    def _poll_sensor(self):
        """Sends 'S' command at configured intervals and reads the JSON response."""
        while not self._stop_event:
            try:
                if self.serial_conn is None or not self.serial_conn.is_open:
                    self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=2.0)

                # 1. Block and wait for main.py to signal the poll
                triggered = self.poll_trigger.wait(timeout=1.0)
                if triggered:
                    self.poll_trigger.clear()
                    
                    # 2. IMMEDIATELY capture the poll timestamp (vefore any I/O delay)
                    exact_poll_time = time.time()

                    # 3. Request the sample from Arduino
                    self.serial_conn.write(b'S')
                    self.serial_conn.flush()
                    logging.debug("Sent 'S' polling command to Arduino.")

                    # 4. Wait for and read the response
                    raw_line = self.serial_conn.readline().decode('utf-8').strip()

                    if raw_line:
                        try:
                            parsed_data = json.loads(raw_line)
                            payload = {
                                "poll_time": exact_poll_time,
                                "data": parsed_data
                            }
                            try:
                                self.output_queue.put_nowait(payload)
                                logging.info("Successfully polled Arduino and pushed to queue.")
                            except Full:
                                logging.warning("Arduino queue filled up; reading dropped.")
                        except json.JSONDecodeError:
                            logging.error(f"Received malformed JSON from Arduino: {raw_line}")
                    else:
                        logging.warning("Arduino did not respond to 'S' command within timeout.")
                else:
                    self.serial_conn.write(b'H')
                    self.serial_conn.flush()

            except serial.SerialException as e:
                logging.error(f"Serial connection lost or failed to open: {e}. Retrying...")
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                self.serial_conn = None
                time.sleep(config.BACKOFF_BASE)

            except Exception:
                logging.exception(f"Critical failure while polling Arduino sensor")
                time.sleep(config.BACKOFF_BASE)

>>>>>>> 5df0bff0bf7b1abe9ffa39e79bf6ac0a9ac136df
