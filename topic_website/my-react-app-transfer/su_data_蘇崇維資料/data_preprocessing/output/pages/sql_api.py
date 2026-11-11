"""Read-only SQL Server API for both WindMind dashboards."""
import os
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime, timezone
import pyodbc
from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

SERVER = os.getenv('SQL_SERVER', r'.\SQLEXPRESS01')
DATABASE = os.getenv('SQL_DATABASE', 'wind_turbine')
ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174').split(',')
app = FastAPI(title='WindMind Live SQL API', docs_url=None)
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=['GET'], allow_headers=['*'])

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

def fetch(table, columns, limit):
    # Fixed whitelist: no user-controlled table/column interpolation.
    allowed = {
        'ai_predictions': ('prediction_time', 'prediction_uid'),
        'anomaly_events': ('confirmation_time', 'event_uid'),
        'dc_measurements': ('measurement_time', 'measurement_uid'),
    }
    if table not in allowed:
        raise ValueError('unsupported table')
    limit = max(1, min(int(limit), 200))
    order, uid = allowed[table]
    with connect() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=? AND TABLE_NAME=?', 'dbo', table)
        available = {r[0] for r in cur.fetchall()}
        missing = set(columns) - available
        if missing:
            raise HTTPException(503, detail={'table': table, 'missing_columns': sorted(missing)})
        query = f'SELECT TOP ({limit}) {", ".join("["+c+"]" for c in columns)} FROM dbo.[{table}] ORDER BY [{order}] DESC, [{uid}] DESC'
        cur.execute(query)
        return [dict(zip(columns, row)) for row in cur.fetchall()]

def safe_fetch(table, columns, limit):
    try:
        return fetch(table, columns, limit)
    except pyodbc.Error as exc:
        raise HTTPException(503, detail='SQL Server unavailable or query failed') from exc

PRED_COLS = ['prediction_uid','prediction_time','predicted_class_key','predicted_class_zh','final_result','decision_state','confidence','probability_normal','probability_voltage_sag','probability_load_spike','probability_severe_anomaly','confirmed_event','review_required']
EVENT_COLS = ['event_uid','confirmation_time','last_detection_time','class_key','class_name_zh','confirmed_window_count','maximum_confidence']
MEAS_COLS = ['measurement_uid','measurement_time','vin_vpp','vin_vmax','vo_ground_avg','vout2','ids','load_current_est','load_power_est','motor_level','duty']

@app.get('/api/health')
def health():
    try:
        with connect() as conn:
            conn.cursor().execute('SELECT 1').fetchone()
        return {'connected': True, 'server': SERVER, 'database': DATABASE, 'checkedAt': datetime.now(timezone.utc).isoformat()}
    except pyodbc.Error:
        raise HTTPException(503, detail='SQL Server unavailable')

@app.get('/api/ai')
def ai():
    return {'connected': True, 'currentPrediction': (p[0] if (p := safe_fetch('ai_predictions', PRED_COLS, 50)) else None),
            'predictionHistory': p, 'recentEvents': safe_fetch('anomaly_events', EVENT_COLS, 50)}

@app.get('/api/cnn')
def cnn():
    m = safe_fetch('dc_measurements', MEAS_COLS, 24)
    return {'connected': True, 'latestMeasurement': m[0] if m else None, 'measurementHistory': list(reversed(m))}
