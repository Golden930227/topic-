import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pyodbc

from FOR_CNN import for_cnn_receive_from_gateway


BASE_DIR = Path(__file__).resolve().parent
FAKE_ESP32_PATH = BASE_DIR / "fake_esp32.py"
SQL_LOG_FILE = BASE_DIR / "sql_preview.log"
GATEWAY_LOG_FILE = BASE_DIR / "gateway.log"

DB_CONFIG = {
    "driver": "{ODBC Driver 18 for SQL Server}",
    "server": r"LAPTOP-DSOT480A\SQLEXPRESS02",
    "database": "wind_turbine",
}

SUMMARY_INTERVAL_SECONDS = 10

buffer = []
window_start_time = None
last_save_time = time.time()


def print_gateway_log(text):
    print(text, flush=True)
    with open(GATEWAY_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text + "\n")


def print_sql_preview(text):
    print(text, flush=True)
    with open(SQL_LOG_FILE, "a", encoding="utf-8") as file:
        file.write(text + "\n")


def reset_log_files():
    for log_file in (SQL_LOG_FILE, GATEWAY_LOG_FILE):
        with open(log_file, "w", encoding="utf-8") as file:
            file.write("")


def start_fake_esp32():
    return subprocess.Popen(
        [sys.executable, str(FAKE_ESP32_PATH)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def drain_process_stderr(process):
    for line in process.stderr:
        print_gateway_log(line.rstrip())


def send_problem_to_fake_esp32(process, message):
    if process.stdin is None:
        return

    command = {
        "problem1": 1,
        "message": message,
    }
    process.stdin.write(json.dumps(command, ensure_ascii=False) + "\n")
    process.stdin.flush()


def get_sql_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def ensure_sql_tables(cursor):
    cursor.execute(
        """
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='cnn_result_log' AND xtype='U'
        )
        CREATE TABLE dbo.cnn_result_log (
            id INT IDENTITY(1,1) PRIMARY KEY,
            created_at DATETIME,
            cnn_ok BIT,
            cnn_message NVARCHAR(255),
            elapsed_time FLOAT,
            sample_count INT,
            ch1_latest INT NULL,
            ch2_latest INT NULL
        )
        """
    )

    cursor.execute(
        """
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='sensor_summary' AND xtype='U'
        )
        CREATE TABLE dbo.sensor_summary (
            id INT IDENTITY(1,1) PRIMARY KEY,
            [date] DATE,
            start_time DATETIME,
            end_time DATETIME,
            ch1_avg FLOAT,
            ch1_max INT,
            ch1_min INT,
            ch2_avg FLOAT,
            ch2_max INT,
            ch2_min INT,
            [count] INT
        )
        """
    )


def save_cnn_result_to_sql(cnn_result):
    sql = """
    INSERT INTO dbo.cnn_result_log (
        created_at,
        cnn_ok,
        cnn_message,
        elapsed_time,
        sample_count,
        ch1_latest,
        ch2_latest
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    try:
        with get_sql_connection() as conn:
            cursor = conn.cursor()
            ensure_sql_tables(cursor)
            cursor.execute(
                sql,
                cnn_result["created_at"],
                cnn_result["cnn_ok"],
                cnn_result["cnn_message"],
                cnn_result["elapsed_time"],
                cnn_result["sample_count"],
                cnn_result["ch1_latest"],
                cnn_result["ch2_latest"],
            )
            conn.commit()

        print_sql_preview(f"cnn_result_log write OK: {cnn_result}")
    except Exception as error:
        print_sql_preview(f"cnn_result_log write failed: {error}; data={cnn_result}")


def add_to_buffer(data):
    global window_start_time

    if window_start_time is None:
        window_start_time = datetime.now()

    buffer.append(data)


def should_save_summary():
    return time.time() - last_save_time >= SUMMARY_INTERVAL_SECONDS


def compute_summary():
    global last_save_time
    global window_start_time

    if not buffer:
        return None

    ch1_values = [item["ch1"] for item in buffer]
    ch2_values = [item["ch2"] for item in buffer]

    summary = {
        "date": window_start_time.date(),
        "start_time": window_start_time,
        "end_time": datetime.now(),
        "ch1_avg": sum(ch1_values) / len(ch1_values),
        "ch1_max": max(ch1_values),
        "ch1_min": min(ch1_values),
        "ch2_avg": sum(ch2_values) / len(ch2_values),
        "ch2_max": max(ch2_values),
        "ch2_min": min(ch2_values),
        "count": len(buffer),
    }

    last_save_time = time.time()
    window_start_time = None
    return summary


def clear_buffer():
    buffer.clear()


def save_summary_to_sql(summary):
    sql = """
    INSERT INTO dbo.sensor_summary (
        [date],
        start_time,
        end_time,
        ch1_avg,
        ch1_max,
        ch1_min,
        ch2_avg,
        ch2_max,
        ch2_min,
        [count]
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        with get_sql_connection() as conn:
            cursor = conn.cursor()
            ensure_sql_tables(cursor)
            cursor.execute(
                sql,
                summary["date"],
                summary["start_time"],
                summary["end_time"],
                summary["ch1_avg"],
                summary["ch1_max"],
                summary["ch1_min"],
                summary["ch2_avg"],
                summary["ch2_max"],
                summary["ch2_min"],
                summary["count"],
            )
            conn.commit()

        print_sql_preview(f"sensor_summary write OK: {summary}")
    except Exception as error:
        print_sql_preview(f"sensor_summary write failed: {error}; data={summary}")


def handle_line(process, line):
    print_gateway_log(f"Gateway received ESP32 data: {line}")

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        message = "Gateway: invalid JSON"
        print_gateway_log(message)
        send_problem_to_fake_esp32(process, message)
        return

    cnn_result = for_cnn_receive_from_gateway(data)
    print_gateway_log(cnn_result["cnn_message"])

    save_cnn_result_to_sql(cnn_result)

    if not cnn_result["cnn_ok"]:
        print_gateway_log(f"Gateway rejected data: {cnn_result['received_data']}")
        send_problem_to_fake_esp32(process, cnn_result["cnn_message"])
        return

    print_gateway_log(f"Gateway accepted data from FOR_CNN: {cnn_result['returned_data']}")
    add_to_buffer(cnn_result["returned_data"])

    if should_save_summary():
        summary = compute_summary()
        if summary is not None:
            save_summary_to_sql(summary)
            clear_buffer()


def main():
    reset_log_files()
    process = start_fake_esp32()
    threading.Thread(target=drain_process_stderr, args=(process,), daemon=True).start()

    print_gateway_log("Gateway started")
    print_gateway_log(f"Started fake ESP32: {FAKE_ESP32_PATH}")

    try:
        while True:
            line = process.stdout.readline()
            if not line:
                continue

            handle_line(process, line.strip())
    except KeyboardInterrupt:
        print_gateway_log("Gateway stopped by user")
    finally:
        process.terminate()


if __name__ == "__main__":
    main()
