# database.py
import sqlite3
import os
from contextlib import closing

DB_FILE = "air_quality.db"

def init_db():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    timestamp DATETIME PRIMARY KEY,
                    latitude REAL,
                    longitude REAL,
                    device_id TEXT,
                    pm2_5 REAL,
                    pm10 REAL,
                    temp REAL,
                    humidity REAL,
                    pressure REAL,
                    o3 REAL,
                    no2 REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_location ON readings (latitude, longitude)")

def insert_row(data_dict):
    query = """
        INSERT INTO readings (
            timestamp, latitude, longitude, device_id, pm2_5, pm10, 
            temp, humidity, pressure, o3, no2
        ) VALUES (
            :timestamp, :latitude, :longitude, :device_id, :pm2_5, :pm10, 
            :temp, :humidity, :pressure, :o3, :no2
        )
    """
    try:
        with closing(sqlite3.connect(DB_FILE)) as conn:
            with conn:
                conn.execute(query, data_dict)
    except sqlite3.Error as e:
        # Failsafe logging to be caught by main thread
        print(f"DB Insert Error: {e}")

def get_unuploaded_data():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM readings").fetchall()]

def delete_uploaded_data(timestamps):
    if not timestamps: return
    with closing(sqlite3.connect(DB_FILE)) as conn:
        with conn:
            conn.executemany("DELETE FROM readings WHERE timestamp = ?", [(ts,) for ts in timestamps])