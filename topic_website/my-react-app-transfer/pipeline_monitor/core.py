"""Bounded read-only probes. No Gateway imports, model execution, or SQL writes."""
import copy
import json
import os
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.windmind-logs'
TABLES = {
    'dc_measurements': ('measurement_time', 'measurement_uid'),
    'ai_predictions': ('prediction_time', 'prediction_uid'),
    'anomaly_events': ('confirmation_time', 'event_uid'),
    'cnn_result_log': ('created_at', 'id'),
    'sensor_summary': ('end_time', 'id'),
}
SAFE_COLUMNS = {
    'source_type', 'input_type', 'is_real_device', 'model_version', 'inserted_at',
    'predicted_class_key', 'predicted_class_zh', 'final_result', 'decision_state', 'confidence',
    'probability_normal', 'probability_voltage_sag', 'probability_load_spike',
    'probability_severe_anomaly', 'confirmed_event', 'review_required',
    'last_detection_time', 'class_key', 'class_name_zh', 'confirmed_window_count', 'maximum_confidence',
    'vin_vpp', 'vin_vmax', 'vo_ground_avg', 'vout2', 'ids', 'load_current_est', 'load_power_est',
    'motor_level', 'duty', 'cnn_ok', 'sample_count', 'ch1_latest', 'ch2_latest',
    'start_time', 'end_time', 'count', 'ch1_avg', 'ch2_avg',
}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def freshness(age, exists=True, threshold=30):
    if not exists:
        return '未知'
    if age is None:
        return '未啟動'
    if age < -5:
        return '未知'
    return '正常' if age <= threshold else '警告'


def probe_api(path, base=None):
    start = time.perf_counter()
    base = base or 'http://127.0.0.1:8000'
    result = {'timestamp': utcnow(), 'path': path, 'ok': False, 'http_status': None, 'data': None}
    try:
        with urlopen(base + path, timeout=2) as response:
            result['http_status'] = response.status
            result['data'] = json.loads(response.read(2_000_000))
            result['ok'] = response.status == 200
            payload = result['data']
            if path.startswith('/api/'):
                required = {'/api/ai': 'predictionHistory', '/api/cnn': 'measurementHistory'}.get(path)
                result['ok'] = (result['ok'] and isinstance(payload, dict) and payload.get('connected') is True
                                and (required is None or isinstance(payload.get(required), list)))
                if not result['ok']:
                    result['error_message'] = 'API 回應結構或 connected 狀態不符'
    except HTTPError as error:
        result['http_status'] = error.code
        result['error_message'] = f'HTTP {error.code}'
    except Exception:
        # Never expose connection strings, tokens, or raw exception text.
        result['error_message'] = 'API 無法連線或回應格式無效'
    result['latency_ms'] = round((time.perf_counter() - start) * 1000, 2)
    return result


def probe_sql():
    import pyodbc
    start = time.perf_counter()
    result = {'timestamp': utcnow(), 'ok': False, 'tables': {}}
    try:
        connection = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            f"SERVER={os.getenv('SQL_SERVER', r'.\SQLEXPRESS01')};"
            f"DATABASE={os.getenv('SQL_DATABASE', 'wind_turbine')};"
            'Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;', timeout=3)
        try:
            connection.timeout = 3
            cursor = connection.cursor()
            schema = cursor.execute("SELECT TABLE_NAME,COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo'").fetchall()
            available = {}
            for table, column in schema:
                available.setdefault(table, set()).add(column)
            for table, (stamp, uid) in TABLES.items():
                if not {stamp, uid}.issubset(available.get(table, set())):
                    result['tables'][table] = {'available': False, 'reason': '資料表或必要欄位未提供'}
                    continue
                try:
                    # Fixed whitelist identifiers; server time avoids guessing SQL timezone.
                    converted = f'TRY_CONVERT(datetimeoffset,[{stamp}])'
                    query = f'''SELECT CONVERT(nvarchar(64),MAX({converted})),
                        SUM(CASE WHEN {converted} >= DATEADD(second,-60,SYSDATETIMEOFFSET()) AND {converted} <= SYSDATETIMEOFFSET() THEN 1 ELSE 0 END),
                        DATEDIFF(second,MAX({converted}),SYSDATETIMEOFFSET()) FROM dbo.[{table}]'''
                    last, count, age = cursor.execute(query).fetchone()
                    selected = sorted(({stamp, uid} | SAFE_COLUMNS) & available[table])
                    projection = ','.join(f'[{c}]' for c in selected)
                    cursor.execute(f'SELECT TOP (100) {projection} FROM dbo.[{table}] ORDER BY [{stamp}] DESC,[{uid}] DESC')
                    columns = [c[0] for c in cursor.description]
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    ids = [str(r[uid]) for r in rows]
                    insertion = {}
                    if 'inserted_at' in available[table]:
                        inserted, insert_count, insert_age = cursor.execute(f'''SELECT
                            CONVERT(nvarchar(64),MAX(TRY_CONVERT(datetimeoffset,inserted_at))),
                            SUM(CASE WHEN TRY_CONVERT(datetimeoffset,inserted_at) BETWEEN DATEADD(second,-60,SYSDATETIMEOFFSET()) AND SYSDATETIMEOFFSET() THEN 1 ELSE 0 END),
                            DATEDIFF(second,MAX(TRY_CONVERT(datetimeoffset,inserted_at)),SYSDATETIMEOFFSET()) FROM dbo.[{table}]''').fetchone()
                        insertion = {'last_inserted_at': str(inserted) if inserted else None,
                                     'inserts_per_minute': int(insert_count or 0), 'insert_age_seconds': insert_age}
                    result['tables'][table] = {'available': True, 'last_success': str(last) if last else None,
                        'per_minute': int(count or 0), 'age_seconds': age, 'status': freshness(age),
                        'rows': json.loads(json.dumps(rows, default=str)), 'duplicate_ids_in_sample': len(ids)-len(set(ids)), **insertion}
                except pyodbc.Error:
                    result['tables'][table] = {'available': False, 'reason': '讀取失敗（請檢查欄位或權限）'}
            result['connected'] = True
            result['ok'] = all(result['tables'].get(table, {}).get('available')
                               for table in ('dc_measurements', 'ai_predictions', 'anomaly_events'))
            if not result['ok']:
                result['error_message'] = 'SQL 已連線，但網站資料表缺少或讀取失敗'
        finally:
            connection.close()
    except Exception:
        result['error_message'] = 'SQL 連線或結構查詢失敗；未顯示原始連線資訊'
    result['latency_ms'] = round((time.perf_counter()-start)*1000, 2)
    return result


def gateway_evidence():
    """The only discovered Gateway launches fake_esp32; never call it live hardware."""
    topic = ROOT.parents[1]
    folder = topic / 'rasberry_pi_to_sql/wind-turbine-docs/docs/flow/gateway_and_sql'
    files = []
    for name in ('gateway.log', 'sql_preview.log'):
        path = folder / name
        if path.is_file():
            stat = path.stat()
            files.append({'檔案': name, '大小': stat.st_size,
                          '最後修改': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()})
    return {'status': '未知', 'source': str(folder), 'files': files,
            'reason': '已發現的 Gateway 僅接 fake_esp32；沒有真實硬體心跳或帶時間戳的接收事件。',
            'model': '未提供：FOR_CNN 僅驗證 ch1/ch2 整數，沒有載入 CNN 模型。'}


def compare_latest(sql, api, table, key):
    sample = sql.get('tables', {}).get(table, {})
    if not sql.get('ok') or not sample.get('available') or not api.get('ok'):
        return '未知：缺少 SQL 或 API 成功樣本'
    sql_rows = sample.get('rows', [])
    api_row = (api.get('data') or {}).get(key)
    if not sql_rows and not api_row:
        return '尚無資料'
    if not sql_rows or not api_row:
        return '警告：SQL 與 API 筆數不一致（非同一交易快照）'
    uid = TABLES[table][1]
    if str(sql_rows[0].get(uid)) != str(api_row.get(uid)):
        return '警告：最新識別碼不同（非同一時間快照，請再次確認）'
    # Compare all API fields, including timestamp formatting differences.
    def normalize(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value)
        if len(text) >= 19 and text[4:5] == '-' and text[7:8] == '-':
            try:
                return datetime.fromisoformat(text).isoformat()
            except ValueError:
                pass
        return text
    differences = [k for k, v in api_row.items() if normalize(sql_rows[0].get(k)) != normalize(v)]
    return '警告：同筆資料欄位不同' if differences else 'SQL/API 最新樣本一致；React 顯示仍未確認'


class EventStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS events (
                timestamp TEXT, pipeline TEXT, component TEXT, event_type TEXT,
                status TEXT, latency_ms REAL, error_message TEXT, trace_id TEXT PRIMARY KEY)''')
            db.execute('CREATE INDEX IF NOT EXISTS events_timestamp ON events(timestamp)')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=1)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def record(self, pipeline, component, result):
        with self.connect() as db:
            db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',
                (utcnow(), pipeline, component, 'probe', '正常' if result['ok'] else '異常',
                 result.get('latency_ms'), result.get('error_message'), str(uuid.uuid4())))
            # Bound persistent history to seven days. This only touches monitor SQLite.
            db.execute("DELETE FROM events WHERE timestamp < strftime('%Y-%m-%dT%H:%M:%S','now','-7 days')")

    def history(self, limit=500, failures_only=False):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            where = "WHERE status != '正常'" if failures_only else ''
            return [dict(row) for row in db.execute(f'SELECT * FROM events {where} ORDER BY timestamp DESC LIMIT ?', (limit,))]


class Collector:
    """One process-wide collector, independent of browser/session refresh count."""
    def __init__(self, path=None):
        self.store = EventStore(path or RUNTIME / 'pipeline-events.sqlite3')
        self.lock = threading.Lock()
        self.snapshot = {'apis': {}, 'sql': {}, 'gateway': gateway_evidence()}
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def read(self):
        with self.lock:
            return copy.deepcopy(self.snapshot)

    def run(self):
        due_sql = 0
        with ThreadPoolExecutor(max_workers=4) as pool:
            while not self.stop_event.is_set():
                # Data APIs perform SQL reads too. Bound all probes to one batch / 15s.
                tasks = {path: pool.submit(probe_api, path) for path in ('/api/health', '/api/ai', '/api/cnn')}
                sql_task = pool.submit(probe_sql) if time.monotonic() >= due_sql else None
                apis = {path: task.result() for path, task in tasks.items()}
                sql = sql_task.result() if sql_task else None
                if sql_task:
                    due_sql = time.monotonic() + 15
                try:
                    for path, result in apis.items():
                        self.store.record('P3', path, result)
                    if sql:
                        self.store.record('P2/P3', 'SQL read probe', sql)
                except sqlite3.Error:
                    # Monitoring storage failure must not affect the production path.
                    pass
                with self.lock:
                    self.snapshot.update({'timestamp': utcnow(), 'apis': apis, 'gateway': gateway_evidence()})
                    if sql:
                        self.snapshot['sql'] = sql
                self.stop_event.wait(15)
