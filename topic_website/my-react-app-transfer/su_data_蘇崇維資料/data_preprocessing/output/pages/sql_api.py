"""Read-only SQL Server API for both WindMind dashboards."""
import os
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime, timezone
import pyodbc
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from windmind_auth import identity, member
from sql_live_data import cnn_data, ai_data, archived_data
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

SERVER = os.getenv('SQL_SERVER', r'DESKTOP-H5OBRG3\SQLEXPRESS01')
DATABASE = os.getenv('SQL_DATABASE', 'wind_turbine')
ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174').split(',')
app = FastAPI(title='WindMind Live SQL API', docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_credentials=True, allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['*'])

def home_url(request: Request):
    configured = os.getenv('WINDMIND_HOME_URL', '').strip()
    if configured:
        parsed = urlsplit(configured)
        if (parsed.scheme in ('http', 'https') and parsed.netloc) or (
            configured.startswith('/') and not configured.startswith('//')
            and not parsed.scheme and not parsed.netloc and '\\' not in configured
        ):
            return configured
        raise ValueError('WINDMIND_HOME_URL must be an HTTP(S) URL or a site-relative path')
    if request.url.hostname in ('localhost', '127.0.0.1', '::1') and request.url.port == 8000:
        return str(request.url.replace(port=5173, path='/', query='', fragment=''))
    return '/'


@app.get('/docs', include_in_schema=False)
async def swagger_docs(request: Request):
    root = request.scope.get('root_path', '').rstrip('/')
    page = get_swagger_ui_html(
        openapi_url=f'{root}{app.openapi_url}',
        title=f'{app.title} - Swagger UI',
        oauth2_redirect_url=f'{root}{app.swagger_ui_oauth2_redirect_url}',
        init_oauth=app.swagger_ui_init_oauth,
        swagger_ui_parameters=app.swagger_ui_parameters,
    )
    navigation = f'''
    <style>
    .swagger-ui .info .title > a.windmind-home-link {{ color: inherit; font: inherit; text-decoration: none; cursor: pointer; }}
    .swagger-ui .info .title > a.windmind-home-link:focus-visible {{ outline: 2px solid currentColor; outline-offset: 4px; }}
    </style>
    <script src="{escape(root, quote=True)}/docs/home-navigation.js" data-home-url="{escape(home_url(request), quote=True)}"></script>
    '''
    return HTMLResponse(page.body.decode('utf-8').replace('</body>', navigation + '</body>'))


@app.get('/docs/home-navigation.js', include_in_schema=False)
async def docs_home_navigation():
    return FileResponse(Path(__file__).with_name('docs_home.js'), media_type='text/javascript')


@app.get('/docs/oauth2-redirect', include_in_schema=False)
async def docs_oauth_redirect():
    return get_swagger_ui_oauth2_redirect_html()


def connect():
    return pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};'
                          f'SERVER={SERVER};DATABASE={DATABASE};'
                          'Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;', timeout=5)

PRED_COLS = ['prediction_uid','prediction_time','predicted_class_key','predicted_class_zh','final_result','decision_state','confidence','probability_normal','probability_voltage_sag','probability_load_spike','probability_severe_anomaly','confirmed_event','review_required']
EVENT_COLS = ['event_uid','confirmation_time','last_detection_time','class_key','class_name_zh','confirmed_window_count','maximum_confidence']
MEAS_COLS = ['measurement_uid','measurement_time','vin_vpp','vin_vmax','vo_ground_avg','vout2','ids','load_current_est','load_power_est','motor_level','duty','rpm']

@app.get('/api/health')
def health():
    try:
        with connect() as conn:
            conn.cursor().execute('SELECT 1').fetchone()
        return {'connected': True, 'server': SERVER, 'database': DATABASE, 'checkedAt': datetime.now(timezone.utc).isoformat()}
    except pyodbc.Error:
        raise HTTPException(503, detail='SQL Server unavailable')

@app.get('/api/ai')
def ai(request: Request, event_after: str | None = None, archive: bool = False):
    try:
        if archive:
            return archived_data(connect, 'ai', PRED_COLS, request.state.user['role'], EVENT_COLS)
        return ai_data(connect, PRED_COLS, EVENT_COLS, request.state.user['role'], event_after)
    except pyodbc.Error as error:
        raise HTTPException(503, 'SQL Server unavailable or query failed') from error

@app.get('/api/cnn')
def cnn(request: Request, after: str | None = None, archive: bool = False):
    try:
        if archive:
            return archived_data(connect, 'cnn', MEAS_COLS, request.state.user['role'])
        return cnn_data(connect, MEAS_COLS, request.state.user['role'], after)
    except pyodbc.Error as error:
        raise HTTPException(503, 'SQL Server unavailable or query failed') from error


@app.get('/api/diagnostics', tags=['診斷'], summary='檢查 SQL、API、新鮮度與最新資料一致性')
def diagnostics(request: Request):
    """唯讀檢查；連線成功不代表資料即時、硬體在線或前端顯示正常。"""
    import sys
    from concurrent.futures import ThreadPoolExecutor
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from sql_monitor_core import probe_sql, probe_api, compare_latest
    base = f'http://127.0.0.1:{request.url.port or 8000}'
    with ThreadPoolExecutor(max_workers=4) as pool:
        sql_task = pool.submit(probe_sql)
        tasks = {path: pool.submit(probe_api, path, base, {key: value for key, value in request.headers.items() if key in ('authorization', 'cookie', 'x-windmind-service')}) for path in ('/api/health', '/api/ai', '/api/cnn')}
        sql = sql_task.result()
        apis = {path: task.result() for path, task in tasks.items()}
    comparisons = {
        'ai': compare_latest(sql, apis['/api/ai'], 'ai_predictions', 'currentPrediction'),
        'cnn': compare_latest(sql, apis['/api/cnn'], 'dc_measurements', 'latestMeasurement'),
    }
    for table in sql.get('tables', {}).values():
        table.pop('rows', None)
    for result in apis.values():
        result.pop('data', None)
    return {'checkedAt': datetime.now(timezone.utc).isoformat(), 'sql': sql, 'apis': apis,
            'comparisons': comparisons, 'frontend': '未驗證前端實際顯示', 'hardware': '未提供硬體心跳'}


@app.middleware('http')
async def authorize(request: Request, call_next):
    if request.method == 'OPTIONS' or request.url.path == '/ready' or (request.method == 'DELETE' and request.url.path == '/api/session'):
        return await call_next(request)
    try:
        if request.url.path in ('/api/cnn', '/api/ai', '/api/access', '/api/session'):
            request.state.user = await run_in_threadpool(identity, request)
        else:
            request.state.user = await run_in_threadpool(member, request)
    except HTTPException as error:
        return JSONResponse({'detail': error.detail}, status_code=error.status_code)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@app.get('/ready', include_in_schema=False)
def ready():
    return {'ready': True}


@app.get('/api/access', include_in_schema=False)
def access(request: Request):
    return {'role': request.state.user['role']}


@app.post('/api/session', include_in_schema=False)
def session(request: Request):
    token = request.headers.get('authorization', '')
    if not token.startswith('Bearer '):
        raise HTTPException(401, '需要登入憑證')
    response = JSONResponse({'role': request.state.user['role']})
    response.set_cookie('windmind_session', token[7:], httponly=True, secure=request.url.scheme == 'https' or request.headers.get('x-forwarded-proto') == 'https', samesite='lax', max_age=3600, path='/')
    return response


@app.delete('/api/session', include_in_schema=False)
def logout():
    response = JSONResponse({'signedOut': True})
    response.delete_cookie('windmind_session', path='/')
    return response
