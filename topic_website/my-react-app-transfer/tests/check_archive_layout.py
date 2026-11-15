"""Verify the ten-minute split with session temp tables and the actual pages."""
from datetime import datetime,timedelta,timezone
import json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from check_hardware_monitor import TempDatabase,api,live,ROOT


def main():
    store=TempDatabase()
    now=datetime.now(timezone.utc)
    stamp=lambda minutes:(now-timedelta(minutes=minutes)).isoformat()
    common={'source_type':'hardware_live','is_real_device':1,'run_id':'arduino_archive_acceptance','source_file':'arduino_serial','inserted_at':stamp(0)}
    try:
        for uid,minutes,voltage in [('recent',1,12.34),('old',11,7.89)]:
            store.insert('dc_measurements',{**common,'measurement_uid':uid,'measurement_time':stamp(minutes),'vout2':voltage,'ids':.5,'load_power_est':voltage*.5})
            store.insert('ai_predictions',{**common,'prediction_uid':uid,'prediction_time':stamp(minutes),'predicted_class_key':'normal','predicted_class_zh':'目前資料' if uid=='recent' else '舊紀錄','confidence':.9,'probability_normal':.9,'probability_voltage_sag':.04,'probability_load_spike':.03,'probability_severe_anomaly':.03})
        current={'cnn':live.cnn_data(store.connect,api.MEAS_COLS,'member'),'ai':live.ai_data(store.connect,api.PRED_COLS,api.EVENT_COLS,'member')}
        archive={'cnn':live.archived_data(store.connect,'cnn',api.MEAS_COLS,'member'),'ai':live.archived_data(store.connect,'ai',api.PRED_COLS,'member',api.EVENT_COLS)}
        assert [row['measurement_uid'] for row in current['cnn']['measurementHistory']]==['recent']
        assert [row['measurement_uid'] for row in archive['cnn']['records']]==['old']
        assert current['ai']['currentPrediction']['prediction_uid']=='recent'
        assert archive['ai']['records'][0]['prediction_uid']=='old'
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            try:
                for kind in ('cnn','ai'):
                    page=browser.new_page()
                    def response(route):
                        path=urlparse(route.request.url).path
                        if path != '/api/'+kind: route.abort();return
                        route.fulfill(json=archive[kind] if 'archive=true' in route.request.url else current[kind])
                    page.route('http://127.0.0.1:18080/api/**',response)
                    page.goto(f'http://127.0.0.1:5173/tests/monitor_harness.html?role=member&kind={kind}')
                    page.locator('.archived-data tbody tr').first.wait_for()
                    assert page.get_by_role('heading',name='舊資料（超過 10 分鐘）').count()==1
                    if kind=='cnn':
                        assert page.locator('.monitor-kpi-card strong').first.inner_text()=='12.34'
                        assert '7.89' in page.locator('.archived-data').inner_text()
                    else:
                        assert page.locator('.result-main h3').inner_text()=='目前資料'
                        assert '舊紀錄' in page.locator('.archived-data').inner_text()
                    assert page.locator('.archived-data').evaluate("node => Boolean(document.querySelector('.refresh-status').compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING)")
                    page.screenshot(path=str(ROOT/f'.windmind-logs/{kind}-archive-below.png'),full_page=True)
                    page.close()
            finally:browser.close()
    finally:store.db.close()
    print(json.dumps({'ten_minute_split':'passed','cnn_old_below_new':'passed','ai_old_below_new':'passed','production_tables_changed':False}))


if __name__=='__main__':main()
