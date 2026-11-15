"""Read-only bounded SQL snapshots and keyset pages shared by both roles."""
import base64
import copy
import json
import threading
import time
from datetime import datetime, timezone

from fastapi import HTTPException

TABLES = {
    'dc_measurements': ('measurement_time', 'measurement_uid'),
    'ai_predictions': ('prediction_time', 'prediction_uid'),
    'anomaly_events': ('confirmation_time', 'event_uid'),
}
META = ['inserted_at', 'received_at', 'source_type', 'is_real_device', 'source_file',
        'source_files', 'source_file_at_end', 'run_id', 'raw_measurement_json', 'raw_result_json', 'candidate_first_detection_time', 'occurred_at', 'event_time', 'source_file_at_start']
_cache = {}
_lock = threading.RLock()


def cached(key, load, ttl=0.5):
    # Serialize a cache miss as well: simultaneous visitors share one SQL result.
    with _lock:
        entry = _cache.get(key)
        if entry and entry[0] > time.monotonic():
            return copy.deepcopy(entry[1])
        result = load()
        if len(_cache) > 256:
            _cache.clear()
        _cache[key] = (time.monotonic() + ttl, copy.deepcopy(result))
        return result


def cursor_for(stamp, uid):
    return base64.urlsafe_b64encode(json.dumps([str(stamp), str(uid)], separators=(',', ':')).encode()).decode().rstrip('=')


def decode_cursor(value):
    try:
        if len(value) > 2048:
            raise ValueError()
        result = json.loads(base64.urlsafe_b64decode(value + '=' * (-len(value) % 4)))
        if not isinstance(result, list) or len(result) != 2 or not all(isinstance(x, str) and len(x) <= 512 for x in result) or not result[1]:
            raise ValueError()
        return result
    except Exception as error:
        raise HTTPException(422, '無效的資料游標') from error


def utc_timestamp(value):
    if value is None:
        return None
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.year <= 2000:
            return None
        return parsed.astimezone(timezone.utc).isoformat(timespec='milliseconds')
    except (ValueError, TypeError):
        return None


def hardware_filter(available, stamp):
    # Old imports incorrectly set is_real_device=1. Require positive provenance,
    # reject file/simulation batches, and reject relative/epoch-placeholder dates.
    if 'is_real_device' not in available:
        return '1=0'
    conditions = ['TRY_CONVERT(int,[is_real_device]) = 1']
    positive = []
    if 'source_type' in available:
        positive.append("LOWER([source_type]) IN ('dc_live','hardware_live','device_live','arduino','esp32')")
    if 'run_id' in available:
        positive.append("([run_id] LIKE 'arduino[_]%' OR [run_id] LIKE 'esp32[_]%' OR [run_id] LIKE 'device[_]%')")
    conditions.append('(' + ' OR '.join(positive) + ')' if positive else '1=0')
    for column in ('source_type','run_id','source_file','source_files','source_file_at_start','source_file_at_end','raw_measurement_json','raw_result_json'):
        if column in available:
            evidence = f"LOWER(COALESCE(CONVERT(nvarchar(max),[{column}]),''))"
            for marker in ('replay','synthetic','simulation','simulated','.csv','fake','mock'):
                conditions.append(f"{evidence} NOT LIKE '%{marker}%'")
    for column in (stamp, 'candidate_first_detection_time', 'occurred_at', 'event_time'):
        if column in available:
            conditions.append(f"([{column}] IS NULL OR [{column}] = '' OR TRY_CONVERT(datetimeoffset,[{column}]) >= CONVERT(datetimeoffset,'2001-01-01T00:00:00+00:00'))")
    return '(' + ' AND '.join(conditions) + ')'


def time_info(row, stamp):
    sampled = utc_timestamp(row.get(stamp))
    received = utc_timestamp(row.get('received_at'))
    inserted = utc_timestamp(row.get('inserted_at'))
    basis = received or (sampled if stamp == 'measurement_time' else None)
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(basis)).total_seconds() if basis else None
    freshness = 'unknown' if age is None or age < -5 else 'fresh' if age <= 30 else 'stale'
    # Confirmation is not substituted for the actual first detection time.
    occurred = utc_timestamp(row.get('occurred_at') or row.get('event_time') or row.get('candidate_first_detection_time'))
    return {'sampleAt': sampled, 'occurredAt': occurred, 'receivedAt': received, 'insertedAt': inserted,
            'freshness': freshness, 'ageSeconds': age,
            'freshnessBasis': 'received_at' if received else stamp if basis else None}


def monitoring_filter(available, stamp):
    event_columns = [column for column in ('occurred_at','event_time','candidate_first_detection_time') if column in available] if stamp == 'confirmation_time' else []
    time_expression = 'COALESCE(' + ','.join(f'TRY_CONVERT(datetimeoffset,[{column}])' for column in event_columns) + ',NULL)' if event_columns else f'TRY_CONVERT(datetimeoffset,[{stamp}])'
    return hardware_filter(available, stamp) + f" AND {time_expression} >= DATEADD(minute,-10,SYSDATETIMEOFFSET())"


def read_page(connect, table, fields, limit=200, after=None, archived=False):
    stamp, uid = TABLES[table]
    limit = min(max(int(limit), 1), 200)
    pair = decode_cursor(after) if after else None
    with connect() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=? AND TABLE_NAME=?', 'dbo', table)
        available = {row[0] for row in cursor.fetchall()}
        if not {stamp, uid}.issubset(available):
            raise HTTPException(503, '缺少資料排序欄位')
        columns = list(dict.fromkeys(c for c in fields + META if c in available))
        order = f"COALESCE(NULLIF([inserted_at], ''), [{stamp}], '')" if 'inserted_at' in available else f"COALESCE([{stamp}], '')"
        condition = monitoring_filter(available, stamp)
        where = ' WHERE ' + (f'CASE WHEN ({condition}) THEN 1 ELSE 0 END = 0' if archived else condition)
        if pair:
            where += f' AND ({order} > ? OR ({order} = ? AND [{uid}] > ?))'
        direction = 'ASC' if pair else 'DESC'
        query = f'SELECT TOP ({limit + 1}) ' + ','.join(f'[{c}]' for c in columns)
        query += f', {order} AS [_order] FROM dbo.[{table}]' + where + f' ORDER BY {order} {direction}, [{uid}] {direction}'
        cursor.execute(query, pair[0], pair[0], pair[1]) if pair else cursor.execute(query)
        raw = [dict(zip(columns + ['_order'], row)) for row in cursor.fetchall()]
    has_more = bool(pair and len(raw) > limit)
    raw = raw[:limit]
    if not pair:
        raw.reverse()
    public = []
    for row in raw:
        item = {field: utc_timestamp(row.get(field)) if field.endswith(('_time','_at')) else row.get(field) for field in fields}
        item['_time'] = time_info(row, stamp)
        item['_cursor'] = cursor_for(row['_order'], row[uid])
        public.append(item)
    return {'rows': public, 'nextCursor': public[-1]['_cursor'] if public else after, 'hasMore': has_more}


def cnn_data(connect, fields, role, after=None):
    if after and role != 'member':
        raise HTTPException(403, '訪客僅能讀取監測快照')
    def load():
        visible = fields if role == 'member' else [field for field in fields if field in {'measurement_uid', 'measurement_time', 'vout2', 'ids', 'load_power_est', 'rpm'}]
        page = read_page(connect, 'dc_measurements', visible, 20 if after else 200, after)
        return {'connected': True, 'sourcePolicy':'hardware-only', 'latestMeasurement': page['rows'][-1] if page['rows'] else None,
                'measurementHistory': page['rows'], 'nextCursor': page['nextCursor'], 'hasMore': page['hasMore'],
                'refreshSeconds': 1, 'windowSeconds':600, 'serverNow':datetime.now(timezone.utc).isoformat()}
    return cached(('cnn',), load) if role == 'visitor' else load()


def ai_data(connect, pred_fields, event_fields, role, event_after=None):
    def load():
        predictions = read_page(connect, 'ai_predictions', pred_fields, 50 if role == 'member' else 1)['rows']
        events = read_page(connect, 'anomaly_events', event_fields, 200, event_after)
        return {'connected': True, 'sourcePolicy':'hardware-only', 'currentPrediction': predictions[-1] if predictions else None,
                'predictionHistory': list(reversed(predictions)), 'recentEvents': list(reversed(events['rows'])),
                'eventCursor': events['nextCursor'], 'eventsHaveMore': events['hasMore'],
                'refreshSeconds': 1, 'windowSeconds':600, 'serverNow':datetime.now(timezone.utc).isoformat()}
    return cached(('ai', event_after), load) if role == 'visitor' else load()


def archived_data(connect, kind, fields, role, event_fields=None):
    def load():
        table = 'dc_measurements' if kind == 'cnn' else 'ai_predictions'
        visible = fields if role == 'member' or kind != 'cnn' else [field for field in fields if field in {'measurement_uid','measurement_time','vout2','ids','load_power_est','rpm'}]
        rows = read_page(connect, table, visible, 200 if kind == 'cnn' else 50, archived=True)['rows']
        events = read_page(connect,'anomaly_events',event_fields,50,archived=True)['rows'] if kind=='ai' and event_fields else []
        return {'connected':True, 'records':list(reversed(rows)), 'events':list(reversed(events)), 'limit':200 if kind=='cnn' else 50}
    return cached(('archive',kind,role),load,ttl=10)
