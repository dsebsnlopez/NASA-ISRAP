# NASA ISRAP Air Quality Logger

A Raspberry Pi-based logger for the NASA ISRAP air quality research project. It reads air quality and gas sensors, tags each reading with a GPS location, stores everything in a local SQLite database, and uploads the data at the end of the day.

## Hardware

- Raspberry Pi (4GB)
- PurpleAir PA-II-SD (PM, temperature, humidity, pressure)
- DFRobot O3 and NO2 sensors (SEN0471)
- VK-162 G-Mouse USB GPS

## Project Files

The program consists of five core Python files, kept together in one directory:

- `main.py` (entry point run by the service; also holds the I2C reading, GPS, formatter, uploader, WiFi switching, and mailer)
- `purpleair_thread.py`
- `database.py`
- `error_logger.py`
- `config.py`

## Setup

The program should start automatically on boot and restart itself if it crashes. This is done with a systemd service, which lives outside the five core Python files. Python libraries are installed in a virtual environment (`venv`) inside the project folder, so they stay separate from the system Python.

### 1. Move the files

Move the five Python files to `/home/pi/air_logger/`.

### 2. Install system dependencies

```bash
sudo apt-get install network-manager python3-venv
```

### 3. Create the virtual environment and install libraries

```bash
cd /home/pi/air_logger
python3 -m venv venv
./venv/bin/pip install requests pyserial pynmea2 smbus2
```

To install another library later, use the venv's pip (no need to activate the environment):

```bash
/home/pi/air_logger/venv/bin/pip install <package-name>
```

To work in the environment interactively instead, run `source /home/pi/air_logger/venv/bin/activate` and `deactivate` when finished.

### 4. Create the service file

```bash
sudo nano /etc/systemd/system/airlogger.service
```

### 5. Add the service definition

The service runs `main.py` with the virtual environment's Python, so it can see the installed libraries.

```ini
[Unit]
Description=NASA ISRAP Air Quality Logger
After=network.target

[Service]
ExecStart=/home/pi/air_logger/venv/bin/python /home/pi/air_logger/main.py
WorkingDirectory=/home/pi/air_logger
StandardOutput=inherit
StandardError=inherit
Restart=always
RestartSec=10
User=pi

[Install]
WantedBy=multi-user.target
```

### 6. Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable airlogger.service
sudo systemctl start airlogger.service
```

## Managing the Service

```bash
sudo systemctl status airlogger.service    # check whether it is running
sudo systemctl restart airlogger.service   # restart after editing files or installing libraries
sudo systemctl stop airlogger.service      # stop the logger
sudo systemctl start airlogger.service     # start it again after stopping
journalctl -u airlogger.service -f         # follow live logs
```

The service restarts automatically 10 seconds after a crash (`Restart=always`, `RestartSec=10`). If you stop it manually, it stays off until you run the `start` command above or reboot the Pi.

## Configuring Each Pi

Every Pi runs the same code. Only `config.py` differs between devices, and only two things in it change. Keep every other setting identical across all Pis so the data is collected and uploaded consistently.

### Unique to each Pi

| Setting | What to change |
|---|---|
| Device ID | A different ID for every Pi, so each device's data can be told apart in the database. |
| Self-hosted WiFi network | A different network name (SSID), and password if you set one, for each Pi. Each Pi creates its own network for its PurpleAir sensor, so nearby Pis must not share a name or they will clash. |

When you change a Pi's self-hosted network, also point that Pi's PurpleAir sensor at the new network name, otherwise it will not be able to send data.

### Same on all Pis

- Poll interval
- Target locations (latitude/longitude point plus radius in meters)
- Upload window
- Server info for the end-of-day upload
- Upload network (client-mode WiFi) and email alert (SMTP) credentials, if these are stored in `config.py`

### Setting up a new Pi

1. Copy the same five files, venv setup, and service file to the new Pi (steps above).
2. Edit `config.py` and change only the device ID and the self-hosted WiFi name (and password).
3. Restart the service: `sudo systemctl restart airlogger.service`.
