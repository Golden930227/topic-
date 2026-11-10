"""Opt-in read-only integration check against real SQL/API; never starts Gateway."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline_monitor.core import EventStore, gateway_evidence, probe_api, probe_sql, utcnow


def main():
    from streamlit import config
    from streamlit.testing.v1 import AppTest
    sql = probe_sql()
    apis = {path: probe_api(path) for path in ('/api/health', '/api/ai', '/api/cnn')}
    snapshot = {'timestamp': utcnow(), 'sql': sql, 'apis': apis, 'gateway': gateway_evidence()}
    with tempfile.TemporaryDirectory() as folder:
        store = EventStore(Path(folder) / 'live-check.sqlite3')
        store.record('P2/P3', 'SQL read probe', sql)
        for path, result in apis.items():
            store.record('P3', path, result)

        class SnapshotCollector:
            def __init__(self):
                self.store = store

            def read(self):
                return snapshot

        config.set_option('server.address', '127.0.0.1')
        with patch.dict(os.environ, {'WINDMIND_MONITOR_ACCESS_CODE': 'integration-test-only'}), patch('pipeline_monitor.core.Collector', SnapshotCollector):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'pipeline_monitor/app.py'))
            app.session_state['local_access'] = True
            app.run()
            assert not app.exception, str(app.exception)
            for page in list(app.radio[0].options):
                app.radio[0].set_value(page).run()
                assert not app.exception, str(app.exception)
        print(json.dumps({'sql_ok': sql.get('ok'), 'tables': {
            table: {'available': result.get('available'), 'status': result.get('status'),
                    'sample_count': len(result.get('rows', [])), 'per_minute': result.get('per_minute')}
            for table, result in sql.get('tables', {}).items()},
            'api_status': {path: r.get('http_status') for path, r in apis.items()},
            'four_pages_rendered': True}, indent=2, ensure_ascii=True))
        if not sql.get('ok'):
            raise SystemExit('SQL did not succeed; UI failure-state check passed, live SQL check incomplete.')


if __name__ == '__main__':
    main()
