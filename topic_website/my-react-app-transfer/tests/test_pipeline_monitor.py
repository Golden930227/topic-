"""Failure-injection fixtures are tests only; never used by the live monitor."""
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from pipeline_monitor.core import EventStore, compare_latest, freshness, gateway_evidence, probe_api, probe_sql


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/bad':
            self.send_response(503)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({'connected': True}).encode())

    def log_message(self, *args):
        pass


class MonitorTests(unittest.TestCase):
    def test_sql_read_uses_safe_columns_and_converted_text_timestamps(self):
        class Cursor:
            description = []

            def execute(self, query):
                self.query = query
                if query.startswith('SELECT TOP'):
                    import re
                    self.description = [(column,) for column in re.findall(r'\[([^\]]+)\]', query.split(' FROM ')[0])]
                    self.assert_safe(query)
                return self

            def assert_safe(self, query):
                assert '[run_id]' not in query
                assert 'raw_measurement_json' not in query

            def fetchall(self):
                if 'INFORMATION_SCHEMA' in self.query:
                    return [(table, column) for table, stamp, uid in (
                        ('dc_measurements','measurement_time','measurement_uid'),
                        ('ai_predictions','prediction_time','prediction_uid'),
                        ('anomaly_events','confirmation_time','event_uid'))
                        for column in (stamp, uid, 'inserted_at', 'run_id', 'raw_measurement_json')]
                return [tuple('fixture-id' if column[0].endswith('_uid') else '2000-01-01T00:00:00+00:00'
                              for column in self.description)]

            def fetchone(self):
                assert 'CONVERT(nvarchar(64),MAX(' in self.query
                return ('2000-01-01 00:00:00 +00:00', 0, 900000000)

        class Connection:
            def cursor(self):
                return Cursor()

            def close(self):
                pass

        with patch('pyodbc.connect', return_value=Connection()):
            result = probe_sql()
        self.assertTrue(result['ok'])
        self.assertEqual(result['tables']['dc_measurements']['status'], '警告')
        self.assertEqual(result['tables']['dc_measurements']['inserts_per_minute'], 0)

    def test_freshness_empty_stale_future(self):
        self.assertEqual(freshness(None), '未啟動')
        self.assertEqual(freshness(None, False), '未知')
        self.assertEqual(freshness(4), '正常')
        self.assertEqual(freshness(60), '警告')
        self.assertEqual(freshness(-600), '未知')

    def test_live_http_success_error_stopped(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            self.assertTrue(probe_api('/ok', base)['ok'])
            failed = probe_api('/bad', base)
            self.assertEqual(failed['http_status'], 503)
            self.assertFalse(failed['ok'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        self.assertFalse(probe_api('/ok', base)['ok'])

    def test_sql_connection_failure_is_sanitized(self):
        with patch('pyodbc.connect', side_effect=RuntimeError('password=DO_NOT_EXPOSE')):
            result = probe_sql()
        self.assertFalse(result['ok'])
        self.assertNotIn('DO_NOT_EXPOSE', json.dumps(result))

    def test_gateway_missing_never_green(self):
        with patch('pathlib.Path.is_file', return_value=False):
            result = gateway_evidence()
        self.assertEqual(result['status'], '未知')
        self.assertEqual(result['files'], [])
        self.assertIn('fake_esp32', result['reason'])

    def test_sql_api_consistency_not_frontend_confirmation(self):
        row = {'measurement_uid': 'test-only-uid', 'measurement_time': '2026-11-10T00:00:00', 'duty': 0.5}
        sql = {'ok': True, 'tables': {'dc_measurements': {'available': True, 'rows': [row]}}}
        api = {'ok': True, 'data': {'latestMeasurement': dict(row)}}
        result = compare_latest(sql, api, 'dc_measurements', 'latestMeasurement')
        self.assertIn('React 顯示仍未確認', result)
        api['data']['latestMeasurement']['duty'] = 0.8
        self.assertIn('欄位不同', compare_latest(sql, api, 'dc_measurements', 'latestMeasurement'))
        api['ok'] = False
        self.assertTrue(compare_latest(sql, api, 'dc_measurements', 'latestMeasurement').startswith('未知'))

    def test_event_history_unique_trace_ids_no_run_id(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'events.sqlite3'
            store = EventStore(path)
            for _ in range(2):
                store.record('P3', 'test', {'ok': False, 'latency_ms': 1, 'error_message': 'HTTP 503'})
            rows = store.history()
            self.assertEqual(len(rows), 2)
            self.assertNotEqual(rows[0]['trace_id'], rows[1]['trace_id'])
            self.assertNotIn('run_id', rows[0])


class FakeCollector:
    def __init__(self):
        self.folder = tempfile.TemporaryDirectory()
        self.store = EventStore(Path(self.folder.name) / 'ui.sqlite3')

    def read(self):
        return {'sql': {}, 'apis': {}, 'gateway': {'reason':'測試：Gateway 停止', 'model':'測試：未載入模型', 'files':[]}}


class AppTests(unittest.TestCase):
    def test_access_lock_and_all_four_empty_pages(self):
        from streamlit import config
        from streamlit.testing.v1 import AppTest
        config.set_option('server.address', '127.0.0.1')
        app_path = Path(__file__).resolve().parents[1] / 'pipeline_monitor/app.py'
        with patch.dict(os.environ, {'WINDMIND_MONITOR_ACCESS_CODE': 'test-only-local-code'}), patch('pipeline_monitor.core.Collector', FakeCollector):
            locked = AppTest.from_file(str(app_path)).run()
            self.assertFalse(locked.exception)
            self.assertEqual(len(locked.radio), 0)
            locked.text_input[0].set_value('wrong')
            locked.button[0].click().run()
            self.assertEqual(len(locked.radio), 0)
            self.assertTrue(locked.error)
            app = AppTest.from_file(str(app_path))
            app.session_state['local_access'] = True
            app.run()
            self.assertFalse(app.exception)
            options = list(app.radio[0].options)
            self.assertEqual(len(options), 4)
            for page in options:
                app.radio[0].set_value(page).run()
                self.assertFalse(app.exception, page)

    def test_public_bind_fails_closed(self):
        from streamlit import config
        from streamlit.testing.v1 import AppTest
        config.set_option('server.address', '0.0.0.0')
        try:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'pipeline_monitor/app.py')).run()
            self.assertTrue(app.error)
            self.assertEqual(len(app.radio), 0)
        finally:
            config.set_option('server.address', '127.0.0.1')


if __name__ == '__main__':
    unittest.main()
