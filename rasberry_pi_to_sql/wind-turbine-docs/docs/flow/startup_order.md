# Startup Order

This document describes the confirmed file opening and execution order for the current project flow.

# Recommended Order

```text
1. Gateway.py
   - Main entry point.
   - Start this file first.
   - It automatically starts fake_esp32.py.
   - It imports and calls FOR_CNN.py.
   - It writes SQL records and log output.

2. streamlist.py
   - Optional monitoring dashboard.
   - Start this separately only when a dashboard view is needed.
   - It reads SQL tables and log files.
```

# Detailed Execution Chain

```text
User starts Gateway.py
  |
  v
Gateway.py starts fake_esp32.py through subprocess.Popen()
  |
  v
fake_esp32.py continuously outputs simulated ESP32 JSON data
  |
  v
Gateway.py reads fake_esp32.py stdout line by line
  |
  v
Gateway.py parses JSON
  |
  v
Gateway.py calls FOR_CNN.py / for_cnn_receive_from_gateway(data)
  |
  v
FOR_CNN.py validates ch1/ch2 and returns result to Gateway.py
  |
  v
Gateway.py writes logs and SQL records
```

# File Opening Notes

| File | Open manually? | Reason |
| --- | --- | --- |
| `Gateway.py` | Yes | Main processing entry point. |
| `fake_esp32.py` | Usually no | Automatically started by `Gateway.py`. Open manually only for standalone simulator debugging. |
| `FOR_CNN.py` | No | Imported and called by `Gateway.py`; not the main entry point. |
| `SQL.py` | No for current main flow | Separate or legacy SQL script. `Gateway.py` does not import it. |
| `streamlist.py` | Optional | Monitoring/dashboard only. Run separately when viewing logs or SQL tables. |
| `FOR_CNN_TEST.py` | No | Standalone waveform test/demo, not part of the current Gateway flow. |

# Current Main Flow Summary

The correct startup flow is:

```text
Gateway.py
  -> automatically starts fake_esp32.py
  -> imports/calls FOR_CNN.py
  -> writes SQL/log output

streamlist.py
  -> optional dashboard only
```

# Important Notes

- Do not start `fake_esp32.py` separately when using the normal Gateway flow, because `Gateway.py` already starts it.
- Do not treat `SQL.py` as the current core SQL handler for `Gateway.py`; current SQL write functions are inside `Gateway.py`.
- Do not treat `streamlist.py` as core processing logic; it is only for monitoring and preview.
