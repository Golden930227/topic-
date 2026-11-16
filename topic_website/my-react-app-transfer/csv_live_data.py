"""One shared, read-only CSV snapshot for the measurement API."""
import copy
import csv
import hashlib
import io
import math
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sql_live_data import data_kind, time_info

TAIPEI = timezone(timedelta(hours=8))
ALIASES = {
    'received_at': ('received_at', '接收時間', 'received_time'),
    'mqtt_topic': ('mqtt_topic', 'MQTT主題', 'topic'),
    'sample': ('sample', 'sample_id', '樣本', '樣本編號'),
    'timestamp_ms': ('timestamp_ms', 'timestamp (ms)', '時間戳毫秒'),
    'vin': ('vin', 'Vin(VN002)', 'Vin(N002)', 'V(N002)', 'vn002'),
    'vo': ('vo', 'vout2', 'Vo(vn005﹐n007)', 'Vo(vn005,n007)', 'Vo(vn005，n007)', 'V(N005,N007)', 'V(N005﹐N007)'),
    'vl': ('vl', 'VL(N004)', 'V(N004)', 'vn004'),
    'duty': ('duty', 'duty_cycle', 'PWM_Duty', 'Duty(%)'),
    'motor_level': ('motor_level', 'drive_level', 'fan_level', '檔位'),
}
VISITOR_FIELDS = {'measurement_uid', 'measurement_time', 'vout2', 'ids', 'load_power_est', 'rpm', 'received_at', '_time'}


def number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Non-finite measurement')
    return value


def parse_csv(payload, filename):
    reader = csv.DictReader(io.StringIO(payload.decode('utf-8-sig')), strict=True)
    headers = reader.fieldnames or []
    normalized = [name.strip().casefold() for name in headers]
    if len(normalized) != len(set(normalized)):
        raise ValueError('Duplicate CSV columns')
    mapping = {}
    for field, aliases in ALIASES.items():
        mapping[field] = next((headers[normalized.index(alias.casefold())]
                               for alias in aliases if alias.casefold() in normalized), None)
    if not all(mapping.values()):
        raise ValueError('Missing CSV contract columns')
    digest = hashlib.sha256(payload).hexdigest()
    rows = []
    for index, raw in enumerate(reader):
        if None in raw or any(value is None for value in raw.values()):
            raise ValueError('Incomplete CSV row')
        row = {key: raw[column] for key, column in mapping.items()}
        if not row['received_at'].strip() or not row['mqtt_topic'].strip():
            raise ValueError('Missing reception metadata')
        for key in ('sample', 'timestamp_ms', 'vin', 'vo', 'vl', 'motor_level', 'duty'):
            row[key] = number(row[key])
        if row['timestamp_ms'] < 0:
            raise ValueError('Negative device time')
        row['duty'] = row['duty'] / 100 if row['duty'] > 1 else row['duty']
        row.update({
            'measurement_uid': hashlib.sha256(f'{filename}:{digest}:{index}'.encode()).hexdigest(),
            'measurement_time': None,  # timestamp_ms is a device-relative clock.
            'vout2': row['vo'],
            # Match Grand: only explicitly simulated current is trusted;
            # run_id strings must never become measured current.
            'ids': number(raw['ids']) if raw.get('data_source') == 'simulation' and raw.get('ids', '').strip() else None,
            'load_current_est': row['vo'] / 80.0,
            'load_power_est': row['vo'] ** 2 / 80.0,
            'rpm': number(raw['rpm']) if raw.get('rpm', '').strip() else None,
            'run_id': raw.get('device_run_id') or raw.get('session_id') or raw.get('run_id', ''),
            'source_type': raw.get('source_type') or 'grand_dc_live',
            'source_file': filename,
            'is_real_device': 1,
            'data_source': raw.get('data_source', ''),
            '_relative_clock': True,
        })
        # Include explicit CSV test labels in provenance classification.
        row['raw_measurement_json'] = raw.get('data_source', '')
        rows.append(row)
    if not rows:
        raise ValueError('Empty CSV')
    return rows[-200:]


class CsvMeasurements:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None
        self.observed = {}
        self.current = None
        self.rows = []
        self.loaded_at = None
        self.error = None

    def start(self):
        self.thread = threading.Thread(target=self.run, name='csv-measurements', daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

    def run(self):
        while not self.stop_event.is_set():
            self.scan()
            self.stop_event.wait(1)

    def scan(self):
        try:
            candidates = []
            for path in self.folder.glob('*.csv'):
                try:
                    stat = path.stat()
                    candidates.append(((stat.st_mtime_ns, stat.st_size, path.name), path))
                except OSError:
                    continue
            candidates.sort(reverse=True)
            observed = {path.name: signature for signature, path in candidates}
            for signature, path in candidates:
                if signature == self.current:
                    break
                if self.current and signature[0] < self.current[0]:
                    break
                # Require size and mtime to remain unchanged over two scans.
                if self.observed.get(path.name) != signature:
                    continue
                try:
                    payload = path.read_bytes()
                    stat = path.stat()
                    if (stat.st_mtime_ns, stat.st_size, path.name) != signature:
                        continue
                    rows = parse_csv(payload, path.name)
                    stat = path.stat()
                    if (stat.st_mtime_ns, stat.st_size, path.name) != signature:
                        continue
                except (OSError, ValueError, csv.Error, UnicodeError, OverflowError):
                    self.error = '最新 CSV 尚未完成或格式無效；保留上次成功資料，下次重試。'
                    continue
                with self.lock:
                    switched = not self.current or self.current[2] != path.name
                    if switched:
                        self.loaded_at = datetime.now(TAIPEI).isoformat(timespec='milliseconds')
                    for row in rows:
                        row['_time'] = {'loadedAt': self.loaded_at}
                    self.rows = (self.rows + rows)[-200:] if switched else [r for r in self.rows if r['source_file'] != path.name] + rows
                    self.rows = self.rows[-200:]
                    self.current = signature
                    self.error = None
                break
            self.observed = observed
        except OSError:
            self.error = 'CSV 資料夾暫時無法讀取；保留上次成功資料。'

    def snapshot(self, role):
        with self.lock:
            rows = copy.deepcopy(self.rows)
            filename = self.current[2] if self.current else None
            loaded_at = self.loaded_at
            error = self.error
        for row in rows:
            timing = time_info(row, 'measurement_time')
            timing['loadedAt'] = row['_time']['loadedAt']
            # Explicit source classification never implies a device heartbeat.
            timing['dataKind'] = data_kind(row)
            row['_time'] = timing
        if role != 'member':
            rows = [{key: value for key, value in row.items() if key in VISITOR_FIELDS} for row in rows]
        return {
            'connected': True, 'sourcePolicy': 'csv-latest',
            'sourceFile': filename, 'loadedAt': loaded_at, 'readWarning': error,
            'latestMeasurement': rows[-1] if rows else None,
            'measurementHistory': rows, 'refreshSeconds': 1,
            'hasMore': False, 'nextCursor': None, 'windowSeconds': None,
            'hardwareHeartbeat': None,
            'serverNow': datetime.now(timezone.utc).isoformat(),
        }


measurements = CsvMeasurements(os.getenv('WINDMIND_CSV_DIR', r'D:\CSV接收區'))
