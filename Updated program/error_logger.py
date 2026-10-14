# error_logger.py
import logging
import smtplib
from email.message import EmailMessage
from config import CONFIG
from datetime import datetime

logging.basicConfig(
    filename='system_errors.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ErrorLogger:
    def __init__(self):
        self.strikes = {"PurpleAir": 0, "O3": 0, "NO2": 0, "GPS": 0}
        self.email_queue = []

    def log_minor(self, sensor_name, issue):
        logging.warning(f"MINOR: {sensor_name} - {issue}")
        self.strikes[sensor_name] += 1
        if self.strikes[sensor_name] >= 6:
            self.log_critical(f"{sensor_name} failed for 6 consecutive cycles.")
            self.strikes[sensor_name] = 0 # Reset after escalation

    def log_success(self, sensor_name):
        self.strikes[sensor_name] = 0

    def log_critical(self, message):
        logging.error(f"CRITICAL: {message}")
        self.email_queue.append(f"{datetime.now()}: {message}")

    def send_queued_emails(self):
        if not self.email_queue:
            return
            
        msg = EmailMessage()
        msg.set_content("\n".join(self.email_queue))
        msg['Subject'] = f"CRITICAL ALERT: {CONFIG['DEVICE_ID']}"
        msg['From'] = CONFIG['ALERT_EMAIL']['SENDER']
        msg['To'] = CONFIG['ALERT_EMAIL']['RECIPIENT']

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(CONFIG['ALERT_EMAIL']['SENDER'], CONFIG['ALERT_EMAIL']['APP_PASSWORD'])
                server.send_message(msg)
            self.email_queue.clear()
        except Exception as e:
            logging.error(f"Failed to send alert email: {e}")