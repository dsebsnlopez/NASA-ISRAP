# NASA ISRAP Air Quality Logger

A Raspberry Pi-based logger for the NASA ISRAP air quality research project. It reads air quality and gas sensors, tags each reading with a GPS location, stores everything in a local SQLite database, and uploads the data at the end of the day.

## Hardware

- Raspberry Pi (4GB)
- PurpleAir PA-II-SD (PM, temperature, humidity, pressure)
- DFRobot O3 and NO2 sensors (I2C)
- VK-162 G-Mouse USB GPS

## Project Files

The program consists of five core Python files, kept together in one directory:

- `main.py`
- `purpleair_thread.py`
- `database.py`
- `error_logger.py`
- `config.py`

## Setup

The program should start automatically on boot and restart itself if it crashes. This is done with a systemd service, which lives outside the five core Python files.

### 1. Install dependencies

```bash
sudo apt-get install network-manager
pip install requests pyserial pynmea2 smbus2
```

### 2. Move the files

Move the five Python files to `/home/pi/air_logger/`.

### 3. Create the service file

```bash
sudo nano /etc/systemd/system/airlogger.service
```

### 4. Add the service definition

```ini
[Unit]
Description=NASA ISRAP Air Quality Logger
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/air_logger/main.py
WorkingDirectory=/home/pi/air_logger
StandardOutput=inherit
StandardError=inherit
Restart=always
RestartSec=10
User=pi

[Install]
WantedBy=multi-user.target
```

### 5. Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable airlogger.service
sudo systemctl start airlogger.service
```

## Managing the Service

```bash
sudo systemctl status airlogger.service    # check whether it is running
sudo systemctl restart airlogger.service   # restart after editing files
sudo systemctl stop airlogger.service      # stop the logger
journalctl -u airlogger.service -f         # follow live logs
```

The service restarts automatically 10 seconds after a crash (`Restart=always`, `RestartSec=10`).