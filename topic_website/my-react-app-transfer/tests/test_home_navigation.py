"""Docs navigation regressions; SQL is mocked and never modified."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
PAGES = next(ROOT.glob('su_data_*/data_preprocessing/output/pages'))
SPEC = importlib.util.spec_from_file_location('navigation_sql_api', PAGES / 'sql_api.py')
api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api)


class HomeNavigationTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {'WINDMIND_HOME_URL': ''})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.client = TestClient(api.app, base_url='http://127.0.0.1:8000')

    def test_local_docs_refresh_and_assets(self):
        for _ in range(2):
            page = self.client.get('/docs')
            self.assertEqual(page.status_code, 200)
            self.assertIn('data-home-url="http://127.0.0.1:5173/"', page.text)
            self.assertIn("url: '/openapi.json'", page.text)
            self.assertIn('SwaggerUIBundle', page.text)
        self.assertEqual(self.client.get('/docs/home-navigation.js').status_code, 200)
        self.assertEqual(self.client.get('/docs/oauth2-redirect').status_code, 200)

    def test_production_default_and_configured_home(self):
        client = TestClient(api.app, base_url='https://api.example.com')
        self.assertIn('data-home-url="/"', client.get('/docs').text)
        with patch.dict(os.environ, {'WINDMIND_HOME_URL': 'https://wind.example.com/?a=1&b="quoted"'}):
            page = client.get('/docs').text
            self.assertIn('data-home-url="https://wind.example.com/?a=1&amp;b=&quot;quoted&quot;"', page)
        with patch.dict(os.environ, {'WINDMIND_HOME_URL': '/windmind/'}):
            self.assertIn('data-home-url="/windmind/"', client.get('/docs').text)

    def test_unsafe_home_is_rejected(self):
        for value in ('javascript:alert(1)', '//evil.example', '/\\evil.example'):
            with self.subTest(value=value), patch.dict(os.environ, {'WINDMIND_HOME_URL': value}):
                with self.assertRaises(ValueError):
                    self.client.get('/docs')

    def test_reverse_proxy_paths(self):
        client = TestClient(api.app, root_path='/gateway')
        page = client.get('/docs').text
        self.assertIn("url: '/gateway/openapi.json'", page)
        self.assertIn('src="/gateway/docs/home-navigation.js"', page)
        self.assertIn('/gateway/docs/oauth2-redirect', page)

    def test_api_contract_and_read_only_endpoints(self):
        schema = self.client.get('/openapi.json')
        self.assertEqual(schema.status_code, 200)
        self.assertEqual(set(schema.json()['paths']), {'/api/health', '/api/ai', '/api/cnn'})
        with patch.object(api, 'connect', return_value=MagicMock()):
            self.assertTrue(self.client.get('/api/health').json()['connected'])
        with patch.object(api, 'safe_fetch', return_value=[]):
            ai = self.client.get('/api/ai')
            cnn = self.client.get('/api/cnn')
            self.assertEqual(ai.status_code, 200)
            self.assertIsNone(ai.json()['currentPrediction'])
            self.assertEqual(cnn.status_code, 200)
            self.assertEqual(cnn.json()['measurementHistory'], [])


if __name__ == '__main__':
    unittest.main()
