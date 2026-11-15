"""Real T-SQL filtering and Edge four-state acceptance using session temp tables.

No production table is inserted, updated or deleted. Device rows here are
explicit test fixtures, not a claim that a physical turbine is connected.
"""
import importlib.util
import json
from pathlib import Path
import threading
import time
from datetime import datetime,timezone,timedelta
from unittest.mock import patch

import pyodbc
import uvicorn
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('hardware_acceptance_api', next(ROOT.glob('su_data_*/data_preprocessing/output/pages/sql_api.py')))
api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api)
import sql_live_data as live


class TempDatabase:
    def __init__(self):
        self.db = api.connect()
        self.lock = threading.RLock()
        self.fail = False
        self.columns = {}
        numeric = {'vout2','ids','load_power_est','load_current_est','rpm','vin_vpp','vin_vmax','vo_ground_avg','motor_level','duty',
                   'confidence','probability_normal','probability_voltage_sag','probability_load_spike','probability_severe_anomaly',
                   'confirmed_event','review_required','confirmed_window_count','maximum_confidence','is_real_device'}
        for table,fields in [('dc_measurements',api.MEAS_COLS),('ai_predictions',api.PRED_COLS),('anomaly_events',api.EVENT_COLS)]:
            columns = list(dict.fromkeys(fields+live.META))
            self.columns[table] = columns
            definitions = ','.join(f'[{column}] '+('FLOAT' if column in numeric else 'NVARCHAR(MAX)') for column in columns)
            self.db.execute(f'CREATE TABLE [#wm_{table}] ({definitions})')
        self.db.commit()

    def insert(self,table,values):
        with self.lock:
            columns = list(values)
            self.db.execute(f'INSERT INTO [#wm_{table}] ('+','.join(f'[{c}]' for c in columns)+') VALUES ('+','.join('?' for _ in columns)+')',*[values[c] for c in columns])
            self.db.commit()

    def connect(self):
        if self.fail: raise pyodbc.OperationalError('injected acceptance outage')
        return self

    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self,*args): self.lock.release()

    def cursor(self): return TempCursor(self)


class TempCursor:
    def __init__(self,store): self.store=store; self.rows=None; self.cursor=store.db.cursor()
    def execute(self,sql,*params):
        if 'INFORMATION_SCHEMA.COLUMNS' in sql:
            self.rows=[(column,) for column in self.store.columns[params[-1]]]
        else:
            self.rows=None
            for table in self.store.columns: sql=sql.replace(f'dbo.[{table}]',f'[#wm_{table}]')
            self.cursor.execute(sql,*params)
        return self
    def fetchall(self): return self.rows if self.rows is not None else self.cursor.fetchall()


def main():
    store=TempDatabase()
    base=datetime.now(timezone.utc)-timedelta(seconds=10)
    at=lambda second:(base+timedelta(seconds=second)).isoformat()
    display=lambda second:(base+timedelta(seconds=second)).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    common={'source_type':'dc_live','is_real_device':1,'inserted_at':at(5)}
    for table,uid,stamp in [('dc_measurements','measurement_uid','measurement_time'),('ai_predictions','prediction_uid','prediction_time'),('anomaly_events','event_uid','confirmation_time')]:
        store.insert(table,{**common,uid:'old-relative',stamp:'2000-01-01T00:01:00+00:00','source_file':'synthetic.csv'})
        store.insert(table,{**common,uid:'disguised-import',stamp:at(0),'run_id':'synthetic_replay_hidden'})
    server=uvicorn.Server(uvicorn.Config(api.app,host='127.0.0.1',port=18080,log_level='error'))
    reports=[]
    with patch.object(api,'connect',store.connect), patch.object(api,'identity',lambda request:{'role':'member','uid':'test-only'}):
        worker=threading.Thread(target=server.run,daemon=True);worker.start()
        try:
            for _ in range(100):
                if server.started: break
                time.sleep(.1)
            assert server.started
            # Test the real SQL filter on every monitored table, including imports
            # whose is_real_device flag and timestamp look plausible.
            assert live.cnn_data(store.connect,api.MEAS_COLS,'member')['measurementHistory']==[]
            old_ai=live.ai_data(store.connect,api.PRED_COLS,api.EVENT_COLS,'member')
            assert old_ai['currentPrediction'] is None and old_ai['recentEvents']==[]
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(channel='msedge',headless=True,args=['--disable-background-timer-throttling','--disable-renderer-backgrounding'])
                try:
                    pages=[]
                    for kind in ('cnn','ai'):
                        page=browser.new_page(viewport={'width':1440,'height':1100})
                        errors=[];calls=[]
                        page.on('pageerror',lambda error,errors=errors:errors.append(str(error)))
                        page.on('request',lambda request,calls=calls,kind=kind:calls.append(time.monotonic()) if f'/api/{kind}' in request.url and 'archive=true' not in request.url else None)
                        page.goto(f'http://127.0.0.1:5173/tests/monitor_harness.html?role=member&kind={kind}')
                        page.get_by_text('等待實機資料',exact=True).first.wait_for()
                        page.wait_for_function("document.querySelector('[data-testid=last-success]')?.textContent !== '未提供'")
                        assert '2000-' not in page.locator('body').inner_text()
                        assert '重播' not in page.locator('body').inner_text()
                        page.evaluate('''() => {
                          window.seenMonitorMessages = [];
                          new MutationObserver(() => {
                            const text = document.querySelector('.refresh-status [role=status]')?.textContent;
                            if (text && !window.seenMonitorMessages.includes(text)) window.seenMonitorMessages.push(text);
                          }).observe(document.body,{subtree:true,childList:true,characterData:true});
                        }''')
                        pages.append((kind,page,errors,calls))
                    device={**common,'source_type':'hardware_live','run_id':'arduino_acceptance','source_file':'arduino_serial','received_at':at(1)}
                    store.insert('dc_measurements',{**device,'measurement_uid':'real-measurement-fixture','measurement_time':at(0),'vout2':12.34,'ids':1.25,'load_power_est':15.425})
                    store.insert('ai_predictions',{**device,'prediction_uid':'real-prediction-fixture','prediction_time':at(2),'predicted_class_key':'normal','predicted_class_zh':'輕載','final_result':'輕載','confidence':.95,'probability_normal':.95,'probability_voltage_sag':.02,'probability_load_spike':.02,'probability_severe_anomaly':.01})
                    store.insert('anomaly_events',{**device,'event_uid':'real-event-fixture','confirmation_time':at(3),'candidate_first_detection_time':at(-1),'last_detection_time':at(4),'class_key':'voltage_sag','class_name_zh':'電壓驟降'})
                    for kind,page,errors,calls in pages:
                        page.bring_to_front()
                        page.wait_for_function("window.seenMonitorMessages.includes('收到新資料')")
                        page.wait_for_selector('.monitor-kpi-card' if kind=='cnn' else '.prediction-panel')
                        assert (display(0) if kind=='cnn' else display(2)) in page.locator('body').inner_text()
                        if kind=='cnn':
                            assert page.locator('.monitor-kpi-card strong').first.inner_text()=='12.34'
                            assert display(0) in page.locator('svg title').first.text_content()
                        else:
                            assert page.locator('.events-table th').all_text_contents()==['發生時間','異常類型','狀態','描述']
                            assert page.locator('.events-table tbody td').first.inner_text()==display(-1)
                        page.get_by_text('監測頁刷新正常 · 暫無新資料',exact=True).wait_for()
                        before=page.locator('[data-testid=last-success]').inner_text()
                        markup=page.locator('.monitor-kpi-card strong' if kind=='cnn' else '.result-main h3').all_text_contents()
                        try:
                            page.wait_for_function("before => document.querySelector('[data-testid=last-success]').textContent !== before",arg=before,timeout=8000)
                        except Exception:
                            print('CLOCK DEBUG',kind,page.locator('body').inner_text(),calls)
                            raise
                        assert page.locator('.monitor-kpi-card strong' if kind=='cnn' else '.result-main h3').all_text_contents()==markup
                        assert page.locator('.refresh-dot.pulse').count()==1
                        page.set_viewport_size({'width':390,'height':844})
                        if kind=='ai':
                            assert page.locator('.events-table th').count()==4 and page.locator('.events-table tbody tr').first.locator('td').count()==4
                        page.screenshot(path=str(ROOT/f'.windmind-logs/{kind}-hardware-mobile.png'),full_page=True)
                    store.fail=True
                    for kind,page,errors,calls in pages:
                        page.get_by_text('刷新失敗，重試中',exact=True).first.wait_for()
                        last=page.locator('[data-testid=last-success]').inner_text()
                        page.wait_for_timeout(1200)
                        assert page.locator('[data-testid=last-success]').inner_text()==last
                        assert page.locator('.monitor-kpi-card' if kind=='cnn' else '.prediction-panel').count()>0
                        body=page.locator('body').inner_text()
                        assert '重播' not in body and '2000-' not in body and 'T08:13' not in body
                        assert not errors,errors
                        gaps=[round(b-a,3) for a,b in zip(calls,calls[1:])]
                        assert len(gaps)>=3 and all(.75<=gap<=2 for gap in gaps),gaps
                        reports.append({'page':kind,'old_imports_excluded':True,'new_hardware_fixture_displayed':True,'unchanged_success_refreshes_clock':True,'failure_preserves_data':True,'taipei_times_verified':True,'mobile_event_columns':4 if kind=='ai' else None,'request_gaps_seconds':gaps})
                    browser.close()
                finally:
                    if browser.is_connected(): browser.close()
        finally:
            server.should_exit=True;worker.join(timeout=10);store.db.close()
    (ROOT/'.windmind-logs/hardware-monitor-acceptance.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'production_tables_changed':False,'test_storage':'SQL Server session temp tables','cases':reports},ensure_ascii=True,indent=2))


if __name__=='__main__':main()
