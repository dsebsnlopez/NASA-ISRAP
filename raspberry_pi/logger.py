import logging
import sqlite3
import os
import re
import json
import csv
import time
import mimetypes
import urllib.request
import urllib.parse
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple
import config

# ==========================================
# SYSTEM LOGGING & FORMATTING
# ==========================================

def setup_system_logger(data_dir: str = "data", log_filename: str = "system_log.txt"):
    """
    Initializes the centralized logging system for the entire application.
    Must be called exactly once at the start of main.py
    """
    # Ensure the data directory actually exists before the script tries to write to it 
    os.makedirs(data_dir, exist_ok=True)
    log_path = os.path.join(data_dir, log_filename)

    if not os.path.exists(log_path):
        open(log_path, 'a').close()

    # 1. Create the base logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Set the baseline capture level

    # Clear any existing handlers to prevent duplicate logging
    if logger.hasHandlers():
        logger.handlers.clear()

    # 2. Define the unified format
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 3. Setup the console Handler (Prints to your terminal)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 4. Setup the Standard File Handler (Writes fast, but appends blindly)
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    email_handler = EmailLogHandler()
    email_handler.setFormatter(formatter)
    logger.addHandler(email_handler)

    logging.info("Centralized logging system initialized.")

def sort_chronological_logs(log_path: str = "data/system_log.txt"):
    """
    Reads a live log file, sorts all entries chronologically, injects daily separators, and safely
    rewrites the file
    """
    if not os.path.exists(log_path):
        return
    log_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
    valid_logs = []

    # 1. Read and parse the file
    with open(log_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = log_pattern.match(line)
            if match:
                timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                valid_logs.append((timestamp, line.strip()))

    # 2. Sort the logs chronologically by the datetime object
    valid_logs.sort(key=lambda x: x[0])

    # 3. Rebuild the file with perfect daily separators
    temp_log_path = log_path + ".tmp"
    last_date = None

    with open(temp_log_path, 'w', encoding='utf-8') as temp_file:
        for timestamp, log_line in valid_logs:
            current_date = timestamp.date()
            
            # Inject separator if the day has rolled over
            if last_date and current_date > last_date:
                separator = f"\n{'-'*25} [ END OF {last_date} | START OF {current_date} ] {'-'*25}\n\n"
                temp_file.write(separator)
            
            temp_file.write(log_line + "\n")
            last_date = current_date

    # 4. Safely overwrite the original file
    os.replace(temp_log_path, log_path)
    print("Logs successfully sorted and formatted.")


# ==========================================
# SQLITE DATABASE IMPLEMENTATION
# ==========================================

def get_db_connection(data_dir: str, device_id: str) -> sqlite3.Connection:
    """
    Safely creates the directory if needed, connects to the SQLite DB, 
    enables WAL mode for multi-threading, and sets up dictionary-like row access.
    """
    dir_path = Path(data_dir)
    
    # 1. Explicit existence check and directory creation
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created missing data directory at: {dir_path.resolve()}")

    db_path = dir_path / config.DB_FILENAME

    # 2. Connect. check_same_thread=False is required for multi-threaded applications 
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    
    # 3. Force name-based access over positional indexing (e.g. row["date"] instead of row[0])
    conn.row_factory = sqlite3.Row
    
    # 4. Enable WAL mode to support concurrent reads and writes
    conn.execute("PRAGMA journal_mode=WAL;")
    
    return conn

# --- MIGRATION SCRIPTS ---
# To add a column in the future, create a new function (e.g., migration_003_add_feature_column)
# that runs 'ALTER TABLE ... ADD COLUMN ...' and append it to the MIGRATIONS list below.

def migration_001_create_status_table(conn: sqlite3.Connection):
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {config.STATUS_TABLE} (
            date TEXT NOT NULL,
            device_id TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending upload',
            verified_time TEXT DEFAULT NULL,
            last_error TEXT DEFAULT NULL,
            PRIMARY KEY (date, device_id)
        )
    """)

def migration_002_create_sensor_data_table(conn: sqlite3.Connection):
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {config.DATA_TABLE} (
            date TEXT NOT NULL,
            device_id TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            altitude REAL,
            SIV INTEGER,
            NO2_ppm REAL,
            O3_ppm REAL,
            PurpleAir_sensor_id TEXT,
            temp_f REAL,
            humidity REAL,
            pressure REAL,
            "pm2.5_aqi" INTEGER,
            "pm2.5_aqi_b" INTEGER,
            pm1_0_atm REAL,
            pm2_5_atm REAL,
            pm10_0_atm REAL,
            pm1_0_atm_b REAL,
            pm2_5_atm_b REAL,
            pm10_0_atm_b REAL,
            p_0_3_um REAL,
            p_0_5_um REAL,
            p_1_0_um REAL,
            p_2_5_um REAL,
            p_5_0_um REAL,
            p_10_0_um REAL,
            p_0_3_um_b REAL,
            p_0_5_um_b REAL,
            p_1_0_um_b REAL,
            p_2_5_um_b REAL,
            p_5_0_um_b REAL,
            p_10_0_um_b REAL,
            UNIQUE(date, device_id)
        )
    """)

# Sequential execution list of all system migrations
MIGRATIONS = [
    ("001_create_status_table", migration_001_create_status_table),
    ("002_create_sensor_data_table", migration_002_create_sensor_data_table)
]

def apply_migrations(conn: sqlite3.Connection):
    """
    Lightweight, versioned schema migration engine.
    """
    cursor = conn.cursor()
    
    # 1. Ensure the tracking table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT UNIQUE NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()

    # 2. Fetch already applied migrations
    cursor.execute("SELECT migration_name FROM schema_migrations")
    applied_migrations = {row["migration_name"] for row in cursor.fetchall()}

    # 3. Apply missing migrations sequentially
    for name, func in MIGRATIONS:
        if name not in applied_migrations:
            logging.info(f"Applying database migration: {name}")
            try:
                func(conn)
                now_iso = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO schema_migrations (migration_name, applied_at) VALUES (?, ?)",
                    (name, now_iso)
                )
                conn.commit()
                logging.info(f"Migration {name} applied successfully.")
            except Exception as e:
                logging.exception(f"FATAL: Migration {name} failed: {e}")
                conn.rollback()
                raise

def setup_database(data_dir: str, device_id: str) -> sqlite3.Connection:
    """
    Master function to get a connection and ensure the schema is completely up to date.
    """
    conn = get_db_connection(data_dir, device_id)
    apply_migrations(conn)
    return conn

# --- DATA ACCESS PATTERNS ---

def upsert_status_record(
    conn: sqlite3.Connection, 
    date: str, 
    device_id: str, 
    row_count: int, 
    status: str = "pending upload", 
    verified_time: str = None, 
    last_error: str = None
):
    """
    Writes a record to the STATUS_TABLE using an explicit UPSERT.
    Guarantees exactly one row per device per day.
    """
    query = f"""
        INSERT INTO {config.STATUS_TABLE} (date, device_id, row_count, status, verified_time, last_error)
        VALUES (:date, :device_id, :row_count, :status, :verified_time, :last_error)
        ON CONFLICT(date, device_id) DO UPDATE SET
            row_count = excluded.row_count,
            status = excluded.status,
            verified_time = excluded.verified_time,
            last_error = excluded.last_error
    """
    conn.execute(query, {
        "date": date,
        "device_id": device_id,
        "row_count": row_count,
        "status": status,
        "verified_time": verified_time,
        "last_error": last_error
    })
    conn.commit()

# --- CSV EXPORT CAPABILITY ---

def export_table_to_csv(conn: sqlite3.Connection, table_name: str, data_dir: str, target_dates: List[str] = None) -> str:
    """
    Exports a SQLite table completely to a CSV file.
    If target_dates is provided (e.g., ['2026-08-11', '2026-08-12']), it filters the export to those specific days.    
    If target_dates is None, it exports the entire table.
    Replaces SQLite NULLs with the literal string "NULL".
    """
    cursor = conn.cursor()
    
    try:
        # 1. Verify the table exists in SQLite's master directory
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            raise ValueError(f"Table '{table_name}' does not exist in the database.")
            
        # 2. Fetch all data using name-based columns
        # (Table name is parameterized via string formatting because SQLite cannot parameterize identifiers.
        # This is safe because we just validated the table_name explicitly against sqlite_master).
        if target_dates:
            # Ensure it's a list just in case a single string was passed accidentally
            if isinstance(target_dates, str):
                target_dates = [target_dates]
            # Create the correct number of SQL placeholders (e.g., "?, ?, ?") to prevent SQL injection
            placeholders = ', '.join('?' for _ in target_dates)

            # Use SUBSTR to safely match 'YYY-MM-DD' against both full timestamps and date-only strings
            query = f"SELECT * FROM {table_name} WHERE SUBSTR(date, 1, 10) IN ({placeholders})"
            cursor.execute(query, target_dates)
        else:
            # Default behavior: grab everything
            cursor.execute(f"SELECT * FROM {table_name}") 
        rows = cursor.fetchall()
        
        # 3. Generate the timestamped output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if target_dates and len(target_dates) == 1:
            csv_filename = f"{table_name}_{target_dates[0]}_{timestamp}.csv"
        else:
            csv_filename = f"{table_name}_{timestamp}.csv"
        csv_path = os.path.join(data_dir, csv_filename)
        
        # 4. Write data to CSV, overwriting if the file exists ('w' mode)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if rows:
                # Extract headers dynamically from the first row's dictionary keys
                col_names = list(rows[0].keys())
                writer.writerow(col_names)
                
                # Write rows, transforming None to explicit "NULL" string
                for row in rows:
                    csv_row = ["NULL" if val is None else val for val in row]
                    writer.writerow(csv_row)
            else:
                # Edge case: If table is empty, we must query the schema to generate the headers
                cursor.execute(f"PRAGMA table_info({table_name})")
                col_names = [r["name"] for r in cursor.fetchall()]
                writer.writerow(col_names)
                
        logging.info(f"Successfully exported {table_name} to {csv_path}")
        return csv_path
        
    except ValueError as e:
        # Fulfills architectural requirement to explicitly raise the exception but fail loudly and safely return False
        logging.error(f"Export Failed: {e}")
        return False
    except Exception as e:
        logging.exception(f"Critical error during CSV export of {table_name}: {e}")
        return None

# ==========================================
# SERVER UPLOAD & VERIFICATION ABSTRACTION
# ==========================================

def get_data_for_date(conn: sqlite3.Connection, table_name: str, target_date: str) -> List[Dict[str, Any]]:
    """
    Fetches all rows from the specified table that match a specific 'YYYY-MM-DD' date.
    """
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM {table_name} WHERE SUBSTR(date, 1, 10) = ?", 
        (target_date,)
    )
    return [dict(r) for r in cursor.fetchall()]

def upload_data_to_server(data: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Uploads a JSON payload. 
    Returns a tuple: (Success Boolean, Error Message String or None)
    """
    url = f"{config.SERVER_URL}{config.UPLOAD_ENDPOINT}"
    payload = json.dumps({"device_id": config.DEVICE_ID, "data": data}).encode('utf-8')
    
    req = urllib.request.Request(
        url, 
        data=payload, 
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config.SERVER_API_KEY}'
        },
        method='POST'
    )
    
    try:
        logging.info(f"Uploading {len(data)} rows to {url}...")
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status in (200, 201):
                return True, None
            else:
                err_msg = f"HTTP Error: {response.status}"
                logging.error(f"Server rejected upload. {err_msg}")
                return False, err_msg
    except Exception as e:
        err_msg = f"Connection exception: {str(e)}"
        logging.error(err_msg)
        return False, err_msg

def fetch_server_backup(target_date: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Downloads data for verification.
    Returns a tuple: (Data List, Error Message String or None)
    """
    params = urllib.parse.urlencode({
        "device_id": config.DEVICE_ID, 
        "date": target_date
    })
    url = f"{config.SERVER_URL}{config.VERIFY_ENDPOINT}?{params}"
    
    req = urllib.request.Request(
        url, headers={'Authorization': f'Bearer {config.SERVER_API_KEY}'}
    )
    
    try:
        logging.info(f"Fetching verification data for {target_date}...")
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("data", []), None
    except Exception as e:
        err_msg = f"Fetch failed: {str(e)}"
        logging.error(err_msg)
        return [], err_msg

def verify_dataset_match(local_data: List[Dict[str, Any]], server_data: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Compares two lists of dictionaries.
    Returns a tuple: (Match Boolean, Error Message String or None)
    """
    if len(local_data) != len(server_data) or len(local_data) == 0:
        err_msg = f"Row count mismatch. Local: {len(local_data)}, Server: {len(server_data)}"
        logging.error(err_msg)
        return False, err_msg
        
    try:
        local_set = set(json.dumps(d, sort_keys=True) for d in local_data)
        server_set = set(json.dumps(d, sort_keys=True) for d in server_data)
        
        if local_set == server_set:
            return True, None
        else:
            return False, "Data contents do not perfectly align."
    except Exception as e:
        err_msg = f"Comparison error: {str(e)}"
        logging.exception(err_msg)
        return False, err_msg

def execute_daily_data_lifecycle(conn: sqlite3.Connection, table_name: str) -> None:
    """
    Master orchestrator function.
    Phase 1: Uploads the *previous* calendar day's data -> 'upload successful' / 'upload unsuccessful'.
    Phase 2: Promotes any 'upload successful' day that is 2+ days old to 'awaiting termination'.
    Phase 3: Verifies + deletes all data currently 'awaiting termination' ->
             'termination successful' / 'termination unsuccessful'.
    """
    cursor = conn.cursor()

    # Calculate yesterday's date (e.g., if running at 12:05 AM on 8/12, target is 8/11)
    yesterday = datetime.now() - timedelta(days=1)
    target_upload_date = yesterday.strftime("%Y-%m-%d")

    # --- PHASE 1: UPLOAD YESTERDAY'S DATA ---
    logging.info(f"Phase 1: Initiating upload cycle for yesterday: {target_upload_date}")
    
    local_data = get_data_for_date(conn, table_name, target_upload_date)
    row_count = len(local_data)

    if row_count == 0:
        logging.info(f"No local data found for {target_upload_date}. Nothing to upload.")
        # Skips to Phase 2
    else:
        # 1. Create the initial tracking entry BEFORE attempting the upload
        upsert_status_record(
            conn=conn,
            date=target_upload_date,
            device_id=config.DEVICE_ID,
            row_count=row_count,
            status="pending upload", 
            last_error=None
        )

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logging.info(f"Upload attempt {attempt} of {max_attempts} for {target_upload_date}...")
                
                # Step 1: Upload
                upload_success, err_msg = upload_data_to_server(local_data)
                if not upload_success:
                    raise RuntimeError(f"Server rejected payload: {err_msg}")

                # Step 2: Verify
                server_backup, fetch_err = fetch_server_backup(target_upload_date)
                if fetch_err:
                    raise RuntimeError(f"Failed to fetch verification backup: {fetch_err}")

                match, verify_err = verify_dataset_match(local_data, server_backup)
                if not match:
                    # Catastrophic Failure: The data transferred, but the server scrambled or dropped rows.
                    # Retrying might not fix this if the server ignores duplicate IDs, but we fail loudly here.
                    raise ValueError(f"Data verification failed: {verify_err or 'Mismatched sets'}")

                # Step 3: Success State
                upsert_status_record(
                    conn=conn,
                    date=target_upload_date,
                    device_id=config.DEVICE_ID,
                    row_count=row_count,
                    status="upload successful",
                    verified_time=datetime.now().isoformat(),
                    last_error=None
                )
                logging.info(f"SUCCESS: Data for {target_upload_date} fully verified and marked 'upload successful'.")
                break  # Exit the retry loop!

            except Exception as e:
                logging.warning(f"Attempt {attempt} failed: {e}")
                
                # Step 4: Failure State (Only logged to DB on the final failed attempt)
                if attempt == max_attempts:
                    upsert_status_record(
                        conn=conn,
                        date=target_upload_date,
                        device_id=config.DEVICE_ID,
                        row_count=row_count,
                        status="upload unsuccessful",
                        last_error=str(e)
                    )
                    logging.error(f"FAILURE: Marking {target_upload_date} as 'upload unsuccessful' after {max_attempts} attempts.")
                else:
                    # Allow the network to breathe before hitting it again (e.g., 2 seconds)
                    time.sleep(2)

    # --- PHASE 2: PROMOTE OLD 'UPLOAD SUCCESSFUL' DAYS TO 'AWAITING TERMINATION' ---
    logging.info("Phase 2: Promoting eligible days to 'awaiting termination'.")

    # If today is 8/12, timedelta(days=3) yields 8/09. 
    # Using <= ensures 8/9 and all older dates are flagged for cleanup.
    cutoff_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    try:
        
        # Update this back to 'date' if your database schema actually uses 'date'.
        cursor.execute(
            f"""
            UPDATE {config.STATUS_TABLE} 
            SET status = 'awaiting termination' 
            WHERE status = 'upload successful' AND date <= ? AND device_id = ?
            """,
            (cutoff_date, config.DEVICE_ID)
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            logging.info(f"Promoted {cursor.rowcount} day(s) on or before {cutoff_date} to 'awaiting termination'.")
        else:
            logging.info(f"No records found requiring promotion to 'awaiting termination' for cutoff {cutoff_date}.")
            
    except Exception as e:
        conn.rollback()
        logging.exception(f"Phase 2 failed while promoting days to 'awaiting termination': {e}")

    # --- PHASE 3: VERIFY AND DELETE ---
    logging.info("Phase 3: Processing termination queue.")

    try:
        cursor.execute(f"SELECT date FROM {config.STATUS_TABLE} WHERE status = 'awaiting termination' AND device_id = ?",
                       (config.DEVICE_ID,)
        )
        termination_list = [row["date"] for row in cursor.fetchall()]
    except Exception as e:
        logging.exception(f"Phase 3 failed to read the termination queue: {e}")
        return

    if not termination_list:
        logging.info("No dates currently awaiting termination.")
        return

    for term_date in termination_list:
        logging.info(f"Verification initiated for data: {term_date}")
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                local_old_data = get_data_for_date(conn, table_name, term_date)

                # Edge Case: The data is already gone locally, but status table missed the memo.
                if not local_old_data:
                    cursor.execute(
                        f"""UPDATE {config.STATUS_TABLE} 
                           SET status = 'termination successful', last_error = NULL 
                           WHERE date = ? AND device_id = ?""",
                        (term_date, config.DEVICE_ID)
                    )
                    conn.commit()
                    logging.info(f"{term_date}: no local data remained; marked 'termination successful'.")
                    break  # Exit retry loop for this date

                # Check the day's data exists uncorrupted on the server before deleting anything.
                server_backup, fetch_err = fetch_server_backup(term_date)
                if fetch_err:
                    # Standard network error: Raise RuntimeError to trigger a retry
                    raise RuntimeError(f"Network/Fetch error: {fetch_err}")

                match, verify_err = verify_dataset_match(local_old_data, server_backup)
                if not match:
                    # CATASTROPHIC ERROR: Raise ValueError. Retries won't fix corrupted data.
                    raise ValueError(verify_err or "Data contents do not perfectly align.")

                # Check passed -- safe to terminate (delete) the local copy.
                cursor.execute(f"DELETE FROM {table_name} WHERE SUBSTR(date, 1, 10) = ? AND device_id = ?", 
                               (term_date, config.DEVICE_ID)
                )

                cursor.execute(
                    f"""UPDATE {config.STATUS_TABLE} 
                       SET status = 'termination successful', last_error = NULL 
                       WHERE date = ? AND device_id = ?""",
                    (term_date, config.DEVICE_ID)
                )
                conn.commit()
                logging.info(f"SUCCESS: {term_date} verified and purged. Status set to 'termination successful'.")
                break  # Exit retry loop for this date on success

            except ValueError as ve:
                # Catastrophic Failure Block: Immediately abort retries for this date
                conn.rollback()
                err_msg = f"Catastrophic mismatch: {ve}"
                logging.error(f"ABORTING RETRIES for {term_date}. {err_msg}")
               
                cursor.execute(
                    f"UPDATE {config.STATUS_TABLE} SET status = 'termination unsuccessful', last_error = ? WHERE date = ? AND device_id = ?",
                    (err_msg, term_date, config.DEVICE_ID)
                )
                conn.commit()
                break  # Break out of the retry loop, move to the next date

            except Exception as e:
                # Non-Catastrophic Failure Block (Network drops, lock timeouts)
                conn.rollback()
                logging.warning(f"Attempt {attempt} failed for {term_date}: {e}")
                
                if attempt == max_attempts:
                    err_msg = str(e)
                    logging.error(f"FAILURE: termination unsuccessful for {term_date} after {max_attempts} attempts.")
                    try:
                        cursor.execute(
                            f"UPDATE {config.STATUS_TABLE} SET status = 'termination unsuccessful', last_error = ? WHERE date = ? AND device_id = ?",
                            (err_msg, term_date, config.DEVICE_ID)
                        )
                        conn.commit()
                    except Exception as inner_e:
                        conn.rollback()
                        logging.exception(f"Also failed to record the failure status for {term_date}: {inner_e}")
                else:
                    time.sleep(2)  # Give the system/network a moment to recover

def send_email(message: str, loglevel: str = "ERROR", sendto: str = config.ALERT_RECIPIENT, device_id: str = config.DEVICE_ID, attachment_path: str = None) -> bool:
    """
    Sends an email alert using SMTP credentials defiend in config.py. Because sendto, loglevel, and device_id
    have default values drawn from the config, only need to pass the 'message' parameter when calling this funciton
    """
    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = f"[{loglevel}] Alert from {device_id}"
        msg['From'] = config.SMTP_USER
        msg['To'] = sendto

        # Handle the CSV Attachment
        if attachment_path and os.path.exists(attachment_path):
            ctype, encoding = mimetypes.guess_type(attachment_path)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)

            with open(attachment_path, 'rb') as f:
                msg.add_attachment(
                    f.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=os.path.basename(attachment_path)
                )

        # Connect to SMTP server
        smtp_port = getattr(config, 'SMTP_PORT', 587)
        with smtplib.SMTP(config.SMTP_SERVER, smtp_port) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.send_message(msg)
        logging.info(f"Email aler successfully sent to {sendto}")
        return True
    
    except Exception as e:
        logging.error(f"Failed to send email alert: {e}")
        return False

def is_data_legible(row: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates a row of sensor data to ensure values are physically possible and not corrupted
    by hardware disconnets.
    Returns: 
        Tuple[bool, str]: (Is Legible, Reason)
    """
    # 1. Null Checks (Are the sensors actually reporting anything?)
    if row.get("pm2.5_aqi") is None and row.get("NO2_ppm") is None:
        return False, "Critical sensor fields are completely NULL."

    # 2. GPS Bounding (Latitude -90 to 90, Longitude -180 to 180)
    lat = row.get("latitude")
    lon = row.get("longitude")
    if lat is not None and not (-90.0 <= lat <= 90.0):
        return False, f"Corrupted GPS Latitude: {lat}"
    if lon is not None and not (-180.0 <= lon <= 180.0):
        return False, f"Corrupted GPS Longitude: {lon}"

    # 3. Environmental Bounding (Earth's atmospheric limits)
    temp_f = row.get("temp_f")
    # -50F to 150F covers virtually all extreme livable environments
    if temp_f is not None and not (-50.0 <= temp_f <= 150.0):
        return False, f"Hardware fault: Temperature read {temp_f}F"

    humidity = row.get("humidity")
    if humidity is not None and not (0.0 <= humidity <= 100.0):
        return False, f"Hardware fault: Humidty reads {humidity}%"

    # 4. Gas & Particulate Bounding (Cannot be negative)
    pm25 = row.get("pm2.5_aqi")
    if pm25 is not None and pm25 < 0:
        return False, f"Hardware fault: Negative PM2.5 AQI ({pm25})"
    no2 = row.get("NO2_ppm")
    if no2 is not None and no2 < 0:
        return False, f"Hardware fault: Negative NO2 ppm ({no2})"

    # If it passes all checks, the data is structuraly sound
    return True, "Data is legible"

class EmailLogHandler(logging.Handler):
    """
    A custom logging handler that intercepts logs, but only triggers an email
    if the 'send_email' flag is explicitly passed in the logging call.
    """
    def emit(self, record):
        # 1. Check if the 'send_email' flag exists and is True
        if getattr(record, 'send_email', False):
            try:
                log_entry = self.format(record)
                csv_file = getattr(record, 'attachment_path', None)
                # 2. Call send_email function
                send_email(
                    message=log_entry,
                    loglevel=record.levelname,
                    attachment_path=csv_file
                )
            except Exception:
                self.handleError(record)
