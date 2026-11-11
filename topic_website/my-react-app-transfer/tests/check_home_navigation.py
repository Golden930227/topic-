"""Browser checks: python tests/check_home_navigation.py (requires playwright).

Uses installed Edge and a temporary API server; does not restart user services.
The main and standalone AI Vite apps must already be running on 5173 and 5174.
"""
import importlib.util
import os
from pathlib import Path
import threading
import time
import urllib.request

import uvicorn
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = next(ROOT.glob('su_data_*/data_preprocessing/output/pages'))
HOME = 'http://127.0.0.1:5173/'


def check():
    spec = importlib.util.spec_from_file_location('browser_sql_api', PAGES / 'sql_api.py')
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    previous_home = os.environ.get('WINDMIND_HOME_URL')
    os.environ['WINDMIND_HOME_URL'] = HOME
    server = uvicorn.Server(uvicorn.Config(api.app, host='127.0.0.1', port=18000, log_level='warning'))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(.1)
        assert server.started, 'Temporary API did not start'
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.goto(HOME)
            page.get_by_role('button', name='訪客登入', exact=True).click()
            page.wait_for_url(HOME + 'visitor')
            for source in (HOME + 'ai-model', 'http://127.0.0.1:5174/'):
                for selector in ('.brand-mark', '.brand strong', '.brand small'):
                    page.goto(source)
                    brand = page.locator('.topbar .brand')
                    assert brand.get_attribute('href') == HOME
                    assert brand.evaluate('(a) => getComputedStyle(a).cursor') == 'pointer'
                    page.locator('.topbar ' + selector).click()
                    page.wait_for_url(HOME)
                page.goto(source)
                page.reload()
                page.locator('.topbar .brand').focus()
                assert page.locator('.topbar .brand').evaluate('(a) => a === document.activeElement')
                page.keyboard.press('Enter')
                page.wait_for_url(HOME)
                print('PASS AI logo, title, subtitle, keyboard and refresh:', source)

            docs = 'http://127.0.0.1:18000/docs'
            page.goto(docs)
            title = page.locator('.info .title > a.windmind-home-link')
            title.wait_for()
            assert title.inner_text().strip() == 'WindMind Live SQL API'
            assert title.get_attribute('href') == HOME
            assert title.evaluate('(a) => getComputedStyle(a).cursor') == 'pointer'
            assert title.evaluate('(a) => getComputedStyle(a).color === getComputedStyle(a.parentElement).color')
            assert title.evaluate('(a) => getComputedStyle(a).fontSize === getComputedStyle(a.parentElement).fontSize')
            assert page.locator('.info .title pre').count() > 0, 'Swagger version badges lost'
            title.click()
            page.wait_for_url(HOME)
            page.goto(docs)
            page.reload()
            title = page.locator('.windmind-home-link')
            title.wait_for()
            title.focus()
            page.keyboard.press('Enter')
            page.wait_for_url(HOME)
            print('PASS Swagger title, appearance, keyboard and refresh')

            page.goto(docs)
            page.locator('.windmind-home-link').wait_for()
            for path in ('/api/health', '/api/ai', '/api/cnn'):
                operation = page.locator('.opblock').filter(has=page.locator(f'.opblock-summary-path[data-path="{path}"]'))
                operation.locator('.opblock-summary').click()
                operation.get_by_role('button', name='Try it out').click()
                with page.expect_response(lambda response: response.url == f'http://127.0.0.1:18000{path}') as result:
                    operation.get_by_role('button', name='Execute', exact=True).click()
                assert result.value.status == 200, (path, result.value.status)
                print('PASS Swagger Try it out + Execute:', path)
            browser.close()
        for path in ('/docs', '/openapi.json', '/api/health', '/api/ai', '/api/cnn'):
            with urllib.request.urlopen('http://127.0.0.1:18000' + path, timeout=15) as response:
                assert response.status == 200
        print('PASS all five API routes return HTTP 200 (live SQL reads)')
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        if previous_home is None:
            os.environ.pop('WINDMIND_HOME_URL', None)
        else:
            os.environ['WINDMIND_HOME_URL'] = previous_home


if __name__ == '__main__':
    check()
