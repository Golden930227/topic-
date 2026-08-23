# Project Goal

This project is an IoT Gateway system for wind turbine sensor data testing.

The current repository flow:

- Simulates ESP32 sensor input using `fake_esp32.py`.
- Receives simulated ESP32 data through the Gateway main program, `Gateway.py`.
- Parses incoming JSON in `Gateway.py`.
- Sends parsed data into `FOR_CNN.py` for data usability checks.
- Uses the current `FOR_CNN.py` result as the CNN/anomaly judgment interface. The real CNN model is not fully connected in the current implementation.
- Stores valid CNN result records and summary records in SQL Server through SQL-writing functions currently defined in `Gateway.py`.
- Displays logs and SQL/dashboard previews through `streamlist.py`.

# Main Files

| Filename | Responsibility | Core flow or not | Notes |
| --- | --- | --- | --- |
| `fake_esp32.py` | Simulates ESP32 sensor output by printing JSON lines with `ch1` and `ch2`; periodically emits invalid string data (`"a"`, `"b"`) for testing. Also listens for Gateway messages from stdin. | Yes | Started by `Gateway.py` as a subprocess. |
| `Gateway.py` | Main Gateway program. Starts `fake_esp32.py`, reads sensor JSON from stdout, logs gateway messages, calls `FOR_CNN.py`, sends errors back to fake ESP32, buffers valid data, writes CNN results and summaries to SQL Server. | Yes | Current SQL Server config includes `server = r"LAPTOP-DSOT480A\SQLEXPRESS02"` and `database = "wind_turbine"`. |
| `FOR_CNN.py` | Receives parsed data from `Gateway.py`; checks `ch1`/`ch2` existence and verifies both values are `int`; returns a structured result object to the Gateway. | Yes | Current behavior validates usability but does not run a real CNN model or explicit abnormal-type classification. |
| `SQL.py` | Standalone SQL/ESP32 script that creates and writes to `ArduinoDataLog`. | Partial / legacy or separate flow | It starts `fake_esp32.py` directly and expects fields `a` and `b`, while the current simulator emits `ch1` and `ch2`. It is not imported by `Gateway.py`. |
| `FOR_CNN_TEST.py` | Matplotlib waveform simulation/demo for `ch1` and `ch2`. | No | Test/experiment only; not imported by the main Gateway flow. |
| `streamlist.py` | Streamlit monitoring dashboard for SQL tables and log files. | No | Monitoring/dashboard only. It reads `gateway.log`, `sql_preview.log`, `sensor_summary`, and `cnn_result_log`; it should not be treated as core processing logic. |
| `gateway.log` | Runtime Gateway log output. | Runtime output | Generated/cleared by `Gateway.py`; do not edit as source documentation. |
| `sql_preview.log` | Runtime preview log for SQL summary output. | Runtime output | Generated/cleared by `Gateway.py`; displayed by `streamlist.py`. |

# Data Flow

```text
fake_esp32.py
  - Generates JSON lines such as {"ch1": 1234, "ch2": 2345}
  - Periodically generates invalid test data such as {"ch1": "a", "ch2": "b"}
  - Receives Gateway error messages through stdin
  |
  v
Gateway.py
  - Starts fake_esp32.py as a subprocess
  - Reads one line at a time from fake_esp32.py stdout
  - Writes received lines to gateway.log
  |
  v
Gateway JSON parsing
  +-- Invalid JSON
  |    -> write Gateway error to gateway.log
  |    -> send error message back to fake_esp32.py
  |    -> skip current record
  |
  +-- Valid JSON
       |
       v
FOR_CNN.py / for_cnn_receive_from_gateway(data)
  - Checks whether ch1 exists
  - Checks whether ch2 exists
  - Checks whether ch1 is int
  - Checks whether ch2 is int
  |
  v
Is data usable?
  +-- No
  |    -> return cnn_ok = False and cnn_message to Gateway.py
  |    -> Gateway.py writes error result to gateway.log
  |    -> Gateway.py sends error message back to fake_esp32.py
  |    -> current implementation does not write invalid FOR_CNN results to SQL Server
  |
  +-- Yes
       -> return cnn_ok = True and returned_data to Gateway.py
       -> Gateway.py writes CNN result to dbo.cnn_result_log
       -> Gateway.py adds returned_data to summary buffer
       |
       v
     CNN/anomaly judgment
       - Current implementation is still simulated/interface-level.
       - FOR_CNN.py currently marks usable data as cnn_ok = True.
       - No explicit abnormal/normal branch or abnormal type is implemented yet.
       |
       v
     Summary interval
       +-- Less than 10 seconds since last save
       |    -> keep buffering valid records
       |
       +-- 10 seconds or more
            -> compute ch1/ch2 avg, max, min, count
            -> write summary preview to sql_preview.log
            -> write summary to dbo.sensor_summary
            -> clear summary buffer
```

# SQL Flow

`Gateway.py` contains the active SQL-writing functions used by the current main flow:

- `get_sql_connection()`
- `save_cnn_result_to_sql(cnn_result)`
- `save_summary_to_sql(summary)`
- `print_sql_preview(summary)`

The SQL Server configuration currently appears in `Gateway.py`:

```python
DB_CONFIG = {
    "driver": "{ODBC Driver 18 for SQL Server}",
    "server": r"LAPTOP-DSOT480A\SQLEXPRESS02",
    "database": "wind_turbine",
}
```

`streamlist.py` also contains SQL connection configuration for dashboard reads and dashboard-side clearing actions.

`SQL.py` contains a separate SQL connection and table-writing flow for `ArduinoDataLog`, but it is not called by `Gateway.py`.

# Monitoring / Dashboard Flow

`streamlist.py` is a monitoring/dashboard file only.

It can:

- Display recent rows from `dbo.sensor_summary`.
- Display recent rows from `dbo.cnn_result_log`.
- Display `gateway.log`.
- Display `sql_preview.log`.
- Clear dashboard-related SQL tables and log files through UI buttons.

It should not be described as core data processing logic.

# Files Passed Through

Possible Python files involved from input to output in the current repository:

1. `fake_esp32.py`
2. `Gateway.py`
3. `FOR_CNN.py`
4. `streamlist.py` for monitoring/dashboard display only

Additional Python files present but not part of the confirmed current core Gateway flow:

1. `SQL.py`
2. `FOR_CNN_TEST.py`

# Startup Order

For the confirmed file opening and execution order, see `docs/flow/startup_order.md`.

Short version:

```text
Gateway.py
  -> automatically starts fake_esp32.py
  -> imports/calls FOR_CNN.py
  -> writes SQL/log output

streamlist.py
  -> optional monitoring dashboard only
```

# Current Limitations

- CNN logic is still simulated or interface-level and is not fully connected to a real model.
- `FOR_CNN.py` currently validates data usability but does not implement explicit abnormal/normal classification or abnormal type recording.
- Invalid data returned by `FOR_CNN.py` is logged to `gateway.log` and sent back to `fake_esp32.py`; it is not currently written to SQL Server by the active `Gateway.py` flow.
- `sql_preview.log` currently records summary preview output from valid buffered data, not every SQL write and not the invalid FOR_CNN path.
- Do not hardcode SQL Server credentials outside proper config areas.
- Do not remove logging, because `gateway.log` and `sql_preview.log` are used by the monitoring flow.
- Do not refactor core logic unless explicitly requested.

# Uncertain Items Requiring Confirmation

- Whether `SQL.py` is intended to remain as a legacy/separate script or should later become the centralized SQL handler for `Gateway.py`.
- Whether future CNN behavior should add explicit abnormal/normal branches and abnormal type fields.
- Whether invalid FOR_CNN results should also be persisted to SQL Server in a future change.
- Whether `sql_preview.log` should preview only summary records, as it does now, or also preview CNN result/error records.
