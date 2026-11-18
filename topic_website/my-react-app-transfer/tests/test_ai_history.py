"""AI history bounds must preserve latest prediction and event pagination."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sql_live_data

class AiHistoryTests(unittest.TestCase):
    def test_role_limits_and_latest_prediction(self):
        for role, expected in [('visitor', 10), ('member', 50)]:
            def read_page(connect, table, fields, limit, after=None):
                if table == 'ai_predictions':
                    return {'rows': [{'prediction_uid': str(i)} for i in range(limit)]}
                return {'rows': [], 'nextCursor': None, 'hasMore': False}
            with self.subTest(role=role), patch.object(sql_live_data, 'read_page', side_effect=read_page):
                result = sql_live_data.ai_data(None, [], [], role)
                self.assertEqual(len(result['predictionHistory']), expected)
                self.assertEqual(result['currentPrediction'], result['predictionHistory'][0])

    def test_event_pagination_is_unchanged_for_both_roles(self):
        for role in ['visitor', 'member']:
            def read_page(connect, table, fields, limit, after=None):
                if table == 'ai_predictions':
                    return {'rows': []}
                self.assertEqual(limit, 200)
                self.assertEqual(after, 'incoming-cursor')
                return {'rows': [{'event_uid': 'a'}, {'event_uid': 'b'}], 'nextCursor': 'outgoing-cursor', 'hasMore': True}
            with self.subTest(role=role), patch.object(sql_live_data, 'read_page', side_effect=read_page):
                result = sql_live_data.ai_data(None, [], [], role, 'incoming-cursor')
                self.assertEqual(result['recentEvents'], [{'event_uid': 'b'}, {'event_uid': 'a'}])
                self.assertEqual(result['eventCursor'], 'outgoing-cursor')
                self.assertTrue(result['eventsHaveMore'])

if __name__ == '__main__':
    unittest.main()
