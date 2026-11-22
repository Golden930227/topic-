"""Read CNN measurements from the latest received Grand SQLite file."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException
from sql_live_data import time_info, utc_timestamp


def _recent_measurements(folder):
    # Keep the existing newest-file and within-file order. Older batches only
    # fill the history; they never replace a measurement from the newest batch.
    paths = sorted(folder.glob('*.sqlite3'),
                   key=lambda p: (p.stat().st_mtime_ns, p.name), reverse=True)
    newest_first = []
    seen = set()
    for index, path in enumerate(paths):
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
                db.execute('PRAGMA query_only=ON')
                db.row_factory = sqlite3.Row
                batch = [dict(row) for row in db.execute(
                    'SELECT * FROM grand_measurements '
                    'ORDER BY inserted_at DESC, sample DESC, measurement_uid DESC LIMIT 200')]
        except (OSError, sqlite3.Error):
            if index == 0:
                raise
            # An unavailable old batch must not break the current measurement.
            continue
        for row in batch:
            uid = row['measurement_uid']
            if uid in seen:
                continue
            seen.add(uid)
            newest_first.append(row)
            if index > 0 and len(newest_first) >= 50:
                break
        if len(newest_first) >= 50:
            break
    return list(reversed(newest_first))


def snapshot():
    folder = Path('D:/sql\u63a5\u6536\u5340')
    try:
        rows = _recent_measurements(folder)
    except (OSError, sqlite3.Error) as error:
        raise HTTPException(503, 'SQLite measurement data unavailable') from error
    for row in rows:
        row['_relative_clock'] = True
        row['_sql_measurement'] = True
        row['_time'] = time_info(row, 'measurement_time')
        row['measurement_time'] = None
        row['inserted_at'] = utc_timestamp(row['inserted_at'])
        row.pop('raw_measurement_json', None)
    latest = rows[-1] if rows else None
    return {'connected': True, 'sourcePolicy': 'sqlite-latest',
            'latestMeasurement': latest, 'measurementHistory': rows,
            'sourceFile': latest['source_file'] if latest else None,
            'loadedAt': latest['inserted_at'] if latest else None,
            'refreshSeconds': 1, 'nextCursor': None, 'hasMore': False,
            'windowSeconds': None, 'serverNow': datetime.now(timezone.utc).isoformat()}
