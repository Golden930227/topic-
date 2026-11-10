"""Run using the loopback-only launcher; do not expose this app publicly."""
import hmac
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import plotly.express as px
import streamlit as st

from pipeline_monitor.core import Collector, compare_latest

st.set_page_config(page_title='WindMind — Pipeline Monitoring Center', page_icon='📡', layout='wide')
st.markdown('''<style>
.stApp {background:#0b1120;color:#e4edff}
h1,h2,h3 {color:#e4edff !important}
[data-testid="stMetric"] {background:#152138;padding:18px;border:1px solid #253b60;border-radius:12px}
[data-testid="stMetricValue"] {font-size:1.8rem}
.stMarkdown p {font-size:1.06rem}
</style>''', unsafe_allow_html=True)

# Fail closed even if someone manually starts Streamlit with a public bind.
if st.get_option('server.address') != '127.0.0.1':
    st.error('僅允許 127.0.0.1 本機開發監聽，請使用 start_all.cmd。')
    st.stop()

st.title('WindMind — Pipeline Monitoring Center')
st.warning('僅供本機開發：尚未完成 Firebase 員工身分驗證，禁止公開部署。訪客網站不提供此入口。')
secret = os.getenv('WINDMIND_MONITOR_ACCESS_CODE', '')
if not secret:
    st.error('未設定本機存取碼，監控資料已鎖定。請使用一鍵啟動。')
    st.stop()

if not st.session_state.get('local_access'):
    st.info('請由本機專案的 .windmind-logs/monitor-access.txt 取得存取碼；這不是正式員工身分驗證。')
    with st.form('local-access'):
        entered = st.text_input('本機開發存取碼', type='password')
        submitted = st.form_submit_button('開啟本機監控')
    if submitted:
        if hmac.compare_digest(entered.encode('utf-8'), secret.encode('utf-8')):
            st.session_state['local_access'] = True
            st.rerun()
        else:
            st.error('存取碼不正確')
    st.stop()


@st.cache_resource
def collector():
    return Collector()


monitor = collector()
page = st.sidebar.radio('監控頁面', ['0. 總覽 Dashboard', '1. P1：硬體 → Gateway',
                                    '2. P2：CNN → Gateway → SQL', '3. P3：SQL → FastAPI → React'])
auto = st.sidebar.toggle('每 3 秒更新畫面', value=True)
st.sidebar.caption('畫面每 3 秒更新；SQL/API 每 15 秒探測一次，共用單一背景收集器，切換頁面不重複查詢。')
if st.sidebar.button('手動重新整理'):
    st.rerun()
if st.sidebar.button('鎖定監控'):
    st.session_state.pop('local_access', None)
    st.rerun()

COLORS = {'正常':'🟢', '警告':'🟡', '異常':'🔴', '未知':'⚪', '未啟動':'⚫'}


def state_label(state):
    return f'{COLORS.get(state, "⚪")} {state}'


def table_metrics(sample, title):
    st.subheader(title)
    if not sample or not sample.get('available'):
        st.info('未提供：' + sample.get('reason', '尚未取得資料'))
        return
    cols = st.columns(4)
    cols[0].metric('資料新鮮度', state_label(sample['status']))
    cols[1].metric('最近一分鐘資料時間範圍內筆數', sample['per_minute'])
    cols[2].metric('最後資料距今（秒）', sample['age_seconds'] if sample['age_seconds'] is not None else '尚無資料')
    cols[3].metric('最近 100 筆重複識別碼', sample['duplicate_ids_in_sample'])
    st.caption('最後資料時間：' + (sample['last_success'] or '尚無資料') + '；為資料欄位時間，非寫入完成時間。')
    if 'last_inserted_at' in sample:
        st.write('最後 inserted_at：', sample['last_inserted_at'] or '尚無資料',
                 '｜最近一分鐘 inserted_at 筆數：', sample['inserts_per_minute'])
        st.caption('inserted_at 是來源記錄的入庫時間，不等同已量測的 SQL commit 延遲。')


def event_history():
    st.subheader('監控探測歷史與最近異常事件時間軸')
    errors_only = st.checkbox('只看異常探測', key='failures-only')
    events = monitor.store.history(500, errors_only)
    if not events:
        st.info('尚無資料')
        return
    frame = pd.DataFrame(events)
    st.dataframe(frame, hide_index=True, width='stretch')
    st.caption('此處只顯示經清理的監控事件，不提供原始錯誤日誌。歷史保留 7 天，最多顯示最近 500 筆。')
    latency = frame.dropna(subset=['latency_ms'])
    if not latency.empty:
        st.plotly_chart(px.line(latency.sort_values('timestamp'), x='timestamp', y='latency_ms',
                               color='component', template='plotly_dark', title='各探測階段回應時間（ms）'), width='stretch')


@st.fragment(run_every=3 if auto else None)
def render():
    data = monitor.read()
    sql = data['sql']
    apis = data['apis']
    tables = sql.get('tables', {})
    st.caption('最後收集：' + data.get('timestamp', '尚無資料'))
    if page.startswith('0.'):
        columns = st.columns(3)
        with columns[0]:
            st.subheader('P1 硬體 → Gateway')
            st.metric('健康狀態', state_label('未知'))
            st.write('真實硬體事件：未提供')
            st.write('最後成功／每分鐘筆數／接收延遲：未提供')
        with columns[1]:
            st.subheader('P2 CNN → SQL')
            st.metric('整體健康', state_label('異常' if sql and not sql.get('ok') else '未知'))
            st.write('CNN 尚未接入；不以 SQL 可連線推定推論正常。')
            st.write('SQL 讀取探測：' + state_label('正常' if sql.get('ok') else '異常' if sql else '未知'))
            st.write('最後成功入庫／每分鐘成功寫入：未提供')
        with columns[2]:
            st.subheader('P3 SQL → API → React')
            api_failed = any(not r['ok'] for r in apis.values())
            failed = api_failed or (bool(sql) and not sql.get('ok'))
            stale = any(sample.get('status') == '警告' for sample in tables.values())
            st.metric('整體健康', state_label('異常' if failed else '警告' if stale else '未知'))
            st.write('API 探測：' + ('異常' if api_failed else '正常' if apis else '尚無資料'))
            st.write('React 顯示：未知（沒有前端確認回報）')
        for name in ('dc_measurements', 'ai_predictions'):
            table_metrics(tables.get(name, {}), name)
        st.caption('端到端延遲、Gateway 接收率與 CNN 寫入率：未提供；下方折線為實際探測延遲。')
        event_history()
    elif page.startswith('1.'):
        st.header('P1：硬體 → Gateway')
        st.warning(data['gateway']['reason'])
        st.metric('硬體接收狀態', state_label('未知'))
        st.dataframe(pd.DataFrame([
            {'指標': name, '結果': '未提供'} for name in (
                '最後真實接收時間', '每秒／每分鐘接收筆數', '格式驗證成功／失敗',
                '空值／異常值／缺少欄位', '接收失敗次數', '通訊中斷', '來源至 Gateway 延遲')]), hide_index=True)
        st.info('最近真實接收紀錄與即時接收率圖：尚無資料。不能用 SQL 資料量替代硬體接收率。')
        st.caption('已發現的範例日誌僅作來源盤點，不作即時健康判斷。')
        st.dataframe(pd.DataFrame(data['gateway']['files']), hide_index=True)
    elif page.startswith('2.'):
        st.header('P2：CNN → Gateway → SQL')
        st.warning(data['gateway']['model'])
        st.write('模型載入／版本／推論成功失敗／推論耗時／SQL 寫入成功失敗與延遲：未提供。')
        st.caption('FOR_CNN.elapsed_time 是程式啟動後經過時間，不能解讀成推論耗時。')
        st.metric('SQL 連線與讀取', state_label('正常' if sql.get('ok') else '異常' if sql else '未知'))
        if sql.get('error_message'):
            st.error(sql['error_message'])
        st.info('要求的四類：normal、voltage_sag、load_spike、severe_fault。現有 API 使用 probability_severe_anomaly；保留來源標籤，不自行改名或宣稱等價。')
        table_metrics(tables.get('ai_predictions', {}), '預測資料（僅在 SQL 實際存在時顯示）')
        predictions = tables.get('ai_predictions', {}).get('rows', [])
        if predictions:
            fields = ['prediction_time','predicted_class_key','confidence','decision_state']
            frame = pd.DataFrame(predictions)
            st.dataframe(frame[[c for c in fields if c in frame]], hide_index=True)
            st.write('SQL 樣本記錄的模型版本（非目前已載入證據）：',
                     sorted({str(r.get('model_version')) for r in predictions if r.get('model_version')}))
            st.caption('來源 source_type / is_real_device 為上游自行填寫，不能單憑欄位證明真實硬體在線。')
            if {'prediction_time', 'confidence'}.issubset(frame.columns):
                st.plotly_chart(px.line(frame.sort_values('prediction_time'), x='prediction_time', y='confidence', template='plotly_dark'), width='stretch')
        else:
            st.info('預測結果／信心度：尚無資料')
        for table in ('dc_measurements', 'cnn_result_log', 'sensor_summary'):
            table_metrics(tables.get(table, {}), table)
        st.write('缺漏樣本數與端到端追蹤：未提供；沒有可信連續序號／追蹤事件，不能推估。')
        anomalies = tables.get('anomaly_events', {}).get('rows', [])
        st.subheader('SQL 最近異常事件')
        if anomalies:
            st.dataframe(pd.DataFrame(anomalies), hide_index=True)
        else:
            st.info('尚無資料')
    else:
        st.header('P3：SQL → FastAPI → React')
        st.metric('SQL 讀取', state_label('正常' if sql.get('ok') else '異常' if sql else '未知'))
        for path in ('/api/health', '/api/ai', '/api/cnn'):
            result = apis.get(path, {})
            st.subheader(path)
            cols = st.columns(3)
            cols[0].metric('API 狀態', state_label('正常' if result.get('ok') else '異常' if result else '未知'))
            cols[1].metric('回應時間 ms', result.get('latency_ms', '未提供'))
            cols[2].metric('HTTP', result.get('http_status') or '無回應')
            if result.get('error_message'):
                st.error(result['error_message'])
            payload = result.get('data') or {}
            if path != '/api/health':
                records = payload.get('predictionHistory', payload.get('measurementHistory'))
                st.write('API 回傳筆數：' + (str(len(records)) if isinstance(records, list) else '未提供'))
        st.subheader('SQL/API 最新資料比較')
        st.write(compare_latest(sql, apis.get('/api/ai', {}), 'ai_predictions', 'currentPrediction'))
        st.write(compare_latest(sql, apis.get('/api/cnn', {}), 'dc_measurements', 'latestMeasurement'))
        st.warning('React 前端資料取得／實際顯示／與 SQL 一致性：未提供。沒有前端確認回報機制，API 成功不等於前端正常。')
        history = monitor.store.history(500)
        frame = pd.DataFrame(history)
        if not frame.empty:
            failures = frame[(frame.pipeline == 'P3') & (frame.status == '異常')]
            st.metric('探測失敗次數（最近最多 500 個監控事件）', len(failures))
            st.caption('只計本中心主動探測，不是全站 HTTP 錯誤總數。')
            for component in ('/api/health','/api/ai','/api/cnn'):
                successes = frame[(frame.component == component) & (frame.status == '正常')]
                st.write(component + ' 最後成功探測：' + (successes.iloc[0].timestamp if not successes.empty else '尚無資料'))
        for table in ('dc_measurements','ai_predictions'):
            table_metrics(tables.get(table, {}), table)
        event_history()


render()
