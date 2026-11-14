"""Verify existing Firebase users; never accept a role supplied by a browser."""
import base64
import hashlib
import hmac
import json
import os
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from fastapi import HTTPException

API_KEY = os.getenv('FIREBASE_WEB_API_KEY', 'AIzaSyBohWI2Yyz66OljCwNq9H9FxgaGWGsUzc0')
MEMBERS = frozenset(['g99226@gmail.com', 'chenhongrui416@gmail.com', 'p124826960@gmail.com',
                     '44o3249@gmaiil.com', 'xindongh522@gmail.com'])
_cache = {}
_lock = threading.Lock()


def firebase_identity(token):
    """Firebase REST validates signature, issuer and expiry before we trust identity.

    Any verified Google visitor can use the visitor monitoring features.
    No service-account key, unverified JWT role or query-string token is used.
    """
    key = hashlib.sha256(token.encode()).hexdigest()
    with _lock:
        cached = _cache.get(key)
        if cached and cached[0] > time.time():
            return cached[1]
    try:
        request = Request('https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=' + API_KEY,
                          data=json.dumps({'idToken': token}).encode(),
                          headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=8) as response:
            user = json.load(response)['users'][0]
        email = user.get('email', '').strip().lower()
        if not user.get('emailVerified') or user.get('disabled'):
            raise HTTPException(403, '需要已驗證的 Google 帳號')
        role = 'member' if email in MEMBERS else 'visitor'
        # This claim only shortens the cache after Firebase has validated the token.
        payload = token.split('.')[1]
        expiry = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))['exp']
        identity = {'uid': user['localId'], 'role': role, 'email': email}
        with _lock:
            if len(_cache) > 1024:
                _cache.clear()
            _cache[key] = (min(time.time() + 60, expiry), identity)
        return identity
    except HTTPException:
        raise
    except HTTPError as error:
        if error.code in (400, 401):
            raise HTTPException(401, '登入已失效，請重新登入') from error
        if error.code in (403, 404):
            raise HTTPException(403, '登入帳號沒有存取權限') from error
        raise HTTPException(503, '登入驗證服務暫時無法使用') from error
    except Exception as error:
        raise HTTPException(503, '登入驗證服務暫時無法使用') from error


def identity(request):
    secret = os.getenv('WINDMIND_SERVICE_TOKEN', '')
    supplied = request.headers.get('x-windmind-service', '')
    if secret and supplied and hmac.compare_digest(secret, supplied):
        return {'uid': 'local-monitor', 'role': 'member', 'email': ''}
    auth = request.headers.get('authorization', '')
    token = auth[7:] if auth.startswith('Bearer ') else request.cookies.get('windmind_session', '')
    if not token:
        raise HTTPException(401, '請先登入')
    return firebase_identity(token)


def member(request):
    user = identity(request)
    if user['role'] != 'member':
        raise HTTPException(403, '僅限員工使用')
    return user
