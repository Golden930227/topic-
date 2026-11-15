"""Real 8001/React checks plus insertion regression in SQL session temp tables.

Browser-only module overrides supply the existing service identity; production
Firebase login and database records are never modified.
"""
import json
import sys
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import uvicorn
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from check_hardware_monitor import TempDatabase, TempCursor, api


def request(path, token):
    with urlopen(Request('http://127.0.0.1:8001' + path,
                         headers={'X-Windmind-Service': token}), timeout=10) as response:
        assert response.status == 200
        assert 'no-store' in response.headers['Cache-Control']
        return json.load(response)


def mount(browser, kind, token, port=8001):
    page = browser.new_page()
    errors, calls = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: calls.append(time.monotonic())
            if f':{port}/api/{kind}' in r.url and 'archive=true' not in r.url else None)
    # Mount the actual route component with test credentials only in this page.
    component = 'CNNMonitorPage' if kind == 'cnn' else 'AiModelPage'
    page.route('**/src/main.jsx*', lambda route: route.fulfill(
        content_type='application/javascript', body=f'''
        import React from '/node_modules/.vite/deps/react.js';
        import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
        import Component from '/src/pages/{component}.jsx';
        ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(Component,{{role:'member'}}));
        '''))
    page.route('**/src/utils/monitorClient.js*', lambda route: route.fulfill(
        content_type='application/javascript', body=f'''
        export const apiBase='http://127.0.0.1:{port}';
        export async function getMonitorToken() {{ return 'browser-test-only'; }}
        export async function syncSession() {{}}
        '''))
    def authorize(route):
        route.continue_(headers={**route.request.headers, 'X-Windmind-Service': token})
    page.route(f'http://127.0.0.1:{port}/api/**', authorize)
    page.goto('http://127.0.0.1:5173/' + ('cnn-monitor' if kind == 'cnn' else 'ai-model'))
    try:
        page.wait_for_function("/20[0-9]{2}-/.test(document.querySelector('[data-testid=last-success]')?.textContent || '')", timeout=12000)
    except Exception:
        print('Browser failure:', errors, calls, page.locator('body').inner_text(), flush=True)
        raise
    return page, errors, calls


def check_cadence(calls):
    gaps = [b-a for a, b in zip(calls, calls[1:])]
    assert len(gaps) >= 2, gaps
    assert all(.65 < gap < 1.65 for gap in gaps), gaps
    return [round(gap, 3) for gap in gaps]


def main():
    token = (ROOT / '.windmind-logs/service-token.txt').read_text().strip()
    cnn, ai = request('/api/cnn', token), request('/api/ai', token)
    for path in ('/api/cnn', '/api/ai'):
        try:
            urlopen('http://127.0.0.1:8001' + path, timeout=10)
            raise AssertionError('Anonymous API access must remain denied')
        except HTTPError as error:
            assert error.code == 401
        preflight = Request('http://127.0.0.1:8001' + path, method='OPTIONS', headers={
            'Origin':'http://127.0.0.1:5173', 'Access-Control-Request-Method':'GET',
            'Access-Control-Request-Headers':'authorization,x-windmind-service'})
        with urlopen(preflight, timeout=10) as response:
            assert response.headers['Access-Control-Allow-Origin'] == 'http://127.0.0.1:5173'
        with urlopen(Request('http://127.0.0.1:5173' + path, headers={'X-Windmind-Service':token}), timeout=10) as response:
            assert response.status == 200
    latest = cnn['latestMeasurement']
    assert latest and latest['_time']['receivedAt']
    assert latest['_time']['freshness'] in ('fresh', 'stale')
    print('Production API:', json.dumps({'cnn_uid': latest['measurement_uid'],
          'voltage': latest['vout2'], 'received': latest['_time']['receivedAt'],
          'freshness': latest['_time']['freshness'],
          'ai_prediction': ai['currentPrediction'] is not None}, ensure_ascii=True))
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True,
            args=['--disable-background-timer-throttling','--disable-renderer-backgrounding'])
        try:
            for kind in ('cnn', 'ai'):
                page, errors, calls = mount(browser, kind, token)
                if kind == 'cnn':
                    assert page.locator('.monitor-kpi-card strong').first.inner_text() == f"{float(latest['vout2']):.2f}"
                    if latest['_time']['freshness'] == 'stale':
                        assert '超過 30 秒未更新' in page.locator('body').inner_text()
                elif ai['currentPrediction'] is None:
                    page.get_by_text('尚無預測資料', exact=True).first.wait_for()
                page.wait_for_timeout(3200)
                assert not errors, errors
                print('Production React', kind, '8001 polling gaps:', check_cadence(calls))
                page.close()

            # All inserts below affect SQL session temp tables only.
            store = TempDatabase()
            store.db.execute('ALTER TABLE #wm_dc_measurements ADD vo FLOAT')
            store.columns['dc_measurements'].append('vo')
            original = TempCursor.execute
            def grand_cursor(cursor, sql, *args):
                for grand, old in [('grand_measurements','dc_measurements'),
                                   ('grand_ai_predictions','ai_predictions'),
                                   ('grand_anomaly_events','anomaly_events')]:
                    sql = sql.replace(f'dbo.[{grand}]', f'dbo.[{old}]')
                    args = tuple(old if arg == grand else arg for arg in args)
                return original(cursor, sql, *args)
            server = uvicorn.Server(uvicorn.Config(api.app, host='127.0.0.1', port=18080, log_level='error'))
            with patch.object(api, 'connect', store.connect), patch.object(api, 'identity', lambda r: {'uid':'isolated-test','role':'member'}), patch.object(TempCursor, 'execute', grand_cursor):
                thread = threading.Thread(target=server.run, daemon=True)
                thread.start()
                try:
                    for _ in range(100):
                        if server.started: break
                        time.sleep(.05)
                    page, errors, calls = mount(browser, 'cnn', token, 18080)
                    page.get_by_text('等待資料', exact=True).wait_for()
                    now = datetime.now(timezone.utc)
                    common = {'source_type':'grand_dc_live','is_real_device':1,
                              'measurement_time':'2000-01-01T00:03:45+00:00',
                              'received_at':now.isoformat(), 'inserted_at':now.isoformat(),
                              'source_file':'wind_device_acceptance.csv', 'run_id':'esp32_acceptance'}
                    started = time.monotonic()
                    store.insert('dc_measurements', {**common,'measurement_uid':'isolated-genuine-device','vo':12.34})
                    page.wait_for_function("document.querySelector('.monitor-kpi-card strong')?.textContent === '12.34'")
                    delay = time.monotonic()-started
                    assert delay < 1.8, delay
                    # Same UID update must also be rendered on the next snapshot.
                    with store.lock:
                        store.db.execute("UPDATE #wm_dc_measurements SET vo=23.45 WHERE measurement_uid='isolated-genuine-device'")
                        store.db.commit()
                    page.wait_for_function("document.querySelector('.monitor-kpi-card strong')?.textContent === '23.45'")
                    store.insert('dc_measurements', {**common,'measurement_uid':'isolated-simulation','source_file':'wind_simulation.csv','vo':99})
                    page.wait_for_function("document.querySelector('.monitor-kpi-card strong')?.textContent === '99.00'")
                    stale = (now-timedelta(minutes=20)).isoformat()
                    with store.lock:
                        store.db.execute("UPDATE #wm_dc_measurements SET received_at=?", stale)
                        store.db.commit()
                    page.get_by_text('資料超過 30 秒未更新；裝置心跳未提供。', exact=True).wait_for()
                    assert page.locator('.monitor-kpi-card strong').first.inner_text() == '99.00'
                    assert not errors, errors
                    print('SQL temp insertion -> actual CNN React:', round(delay, 3), 'seconds; same-UID update, all new SQL rows displayed, stale status PASS')
                    page.close()
                    page, errors, calls = mount(browser, 'ai', token, 18080)
                    page.get_by_text('尚無預測資料', exact=True).first.wait_for()
                    store.insert('ai_predictions', {
                        'prediction_uid':'isolated-grand-prediction', 'source_type':'grand_dc_live',
                        'is_real_device':1, 'received_at':now.isoformat(), 'inserted_at':now.isoformat(),
                        'prediction_time':'2000-01-01T00:03:45+00:00',
                        'predicted_class_key':'normal', 'predicted_class_zh':'正常',
                        'confidence':.95, 'final_result':'正常', 'probability_normal':.95,
                        'probability_voltage_sag':.02, 'probability_load_spike':.02,
                        'probability_severe_anomaly':.01})
                    page.wait_for_selector('.prediction-panel')
                    assert not errors, errors
                    print('SQL temp prediction -> actual AI React: no-data to prediction PASS')
                    page.close()
                finally:
                    server.should_exit=True
                    thread.join(timeout=10)
                    store.db.close()
        finally:
            browser.close()


if __name__ == '__main__':
    main()
