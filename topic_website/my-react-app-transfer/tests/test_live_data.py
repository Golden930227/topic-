"""Role, pagination, cache and replay regressions; no SQL writes."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
import sql_live_data as live
import windmind_auth

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('live_api_test', next(ROOT.glob('su_data_*/data_preprocessing/output/pages/sql_api.py')))
api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api)


class LiveDataTests(unittest.TestCase):
    def setUp(self):
        live._cache.clear()

    def test_live_snapshots_always_query_sql_for_both_roles(self):
        sample = {'rows': [], 'nextCursor': None, 'hasMore': False}
        with patch.object(live, 'read_page', return_value=sample) as query:
            first = live.cnn_data(None, [], 'visitor')
            live.cnn_data(None, [], 'visitor')
            self.assertEqual(query.call_count, 2)
            self.assertEqual(first['refreshSeconds'], 1)
            self.assertEqual(live.cnn_data(None, [], 'member')['refreshSeconds'], 1)
            self.assertEqual(query.call_count, 3)
            self.assertEqual(query.call_args.args[3], 200)
            live.cnn_data(None, [], 'member', live.cursor_for('stamp', 'uid'))
            self.assertEqual(query.call_args.args[3], 20)
        with self.assertRaises(HTTPException):
            live.cnn_data(None, [], 'visitor', 'anything')

    def test_keyset_uses_tie_breaker_and_returns_only_twenty(self):
        class Cursor:
            def execute(self, sql, *params):
                self.sql, self.params = sql, params
                return self

            def fetchall(self):
                if 'INFORMATION_SCHEMA' in self.sql:
                    return [(c,) for c in ('measurement_time', 'measurement_uid', 'vout2', 'inserted_at')]
                self_test.assertIn('TOP (21)', self.sql)
                self_test.assertIn('[measurement_uid] > ?', self.sql)
                self_test.assertIn('ASC', self.sql)
                self_test.assertEqual(self.params, ('same-time', 'same-time', 'uid-000'))
                return [('sample-time', f'uid-{i:03}', float(i), 'same-time', 'same-time') for i in range(1, 22)]
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def cursor(self): return Cursor()
        self_test = self
        result = live.read_page(Connection, 'dc_measurements', ['measurement_time', 'measurement_uid', 'vout2'], 20, live.cursor_for('same-time', 'uid-000'))
        self.assertEqual(len(result['rows']), 20)
        self.assertTrue(result['hasMore'])
        self.assertEqual(live.decode_cursor(result['nextCursor']), ['same-time', 'uid-020'])
        self.assertIsNone(result['rows'][0].get('rpm'))

    def test_invalid_cursor_rejected_and_provenance_overrides_real_flag(self):
        for cursor in ('not-json', live.cursor_for('x', '') , 'x' * 3000):
            with self.assertRaises(HTTPException): live.decode_cursor(cursor)
        self.assertEqual(live.decode_cursor(live.cursor_for('', 'device-id')), ['', 'device-id'])
        self.assertIsNone(live.utc_timestamp('2000-01-01T00:01:00+00:00'))
        self.assertIsNone(live.utc_timestamp('2026-11-15T08:13:33'))
        self.assertEqual(live.utc_timestamp('2026-11-15T16:13:33+08:00'), '2026-11-15T08:13:33.000+00:00')
        self.assertEqual(live.time_info({}, 'measurement_time')['freshness'], 'unknown')

    def test_hardware_filter_fails_closed_without_provenance(self):
        self.assertEqual(live.hardware_filter({'measurement_time'}, 'measurement_time'), '1=0')
        sql = live.hardware_filter({'measurement_time','is_real_device','source_type','run_id','source_file'}, 'measurement_time')
        self.assertIn('TRY_CONVERT(int,[is_real_device]) = 1', sql)
        self.assertIn("NOT LIKE '%synthetic%'", sql)
        self.assertIn("NOT LIKE '%replay%'", sql)
        self.assertNotIn('2001-01-01', sql)
        self.assertIn('grand_dc_live', sql)
        self.assertIn("NOT LIKE '%aug_train%'", sql)
        self.assertNotIn('DATEADD(minute,-10,SYSDATETIMEOFFSET())', live.monitoring_filter({'measurement_time','is_real_device','source_type'}, 'measurement_time'))

    def test_ai_normal_current_still_returns_separately_stored_events(self):
        def page(connect, table, fields, limit, after=None):
            return {'rows':[{'prediction_uid':'normal-later', 'predicted_class_key':'normal'}] if table == 'ai_predictions'
                    else [{'event_uid':'anomaly-between-refreshes'}], 'nextCursor':'event-cursor', 'hasMore':False}
        with patch.object(live, 'read_page', side_effect=page):
            result = live.ai_data(None, [], [], 'visitor')
        self.assertEqual(result['currentPrediction']['predicted_class_key'], 'normal')
        self.assertEqual(result['recentEvents'][0]['event_uid'], 'anomaly-between-refreshes')


class PermissionTests(unittest.TestCase):
    def test_direct_tool_urls_and_api_require_identity(self):
        client = TestClient(api.app)
        for path in ['/api/cnn', '/api/ai', '/docs', '/openapi.json', '/api/diagnostics', '/api/health']:
            self.assertEqual(client.get(path).status_code, 401, path)
        self.assertEqual(client.get('/ready').status_code, 200)
        with patch.object(windmind_auth, 'firebase_identity', return_value={'uid':'visitor', 'role':'visitor'}):
            client.headers['Authorization'] = 'Bearer validated-test-fixture'
            for path in ['/docs', '/openapi.json', '/api/diagnostics', '/api/health']:
                self.assertEqual(client.get(path).status_code, 403, path)
            with patch.object(api, 'cnn_data', return_value={'connected':True}) as cnn:
                self.assertEqual(client.get('/api/cnn').status_code, 200)
                self.assertEqual(cnn.call_args.args[2], 'visitor')
        # A forged browser role/header cannot authorize itself.
        self.assertEqual(TestClient(api.app).get('/docs', headers={'X-Role':'member'}).status_code, 401)


if __name__ == '__main__':
    unittest.main()
