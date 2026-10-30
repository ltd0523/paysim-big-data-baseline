"""Read-only browser evidence. Run in the existing Playwright test container."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from bson import json_util
from playwright.sync_api import sync_playwright
from pymongo import MongoClient

ROOT = Path('/workspace')
EVIDENCE = ROOT / 'dashboard_evidence_20261030_charts'
parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['before', 'after'])
parser.add_argument('--views', nargs='+', choices=['baseline', 'operations', 'report', 'studio'])
args = parser.parse_args()
OUT = Path('/tmp/paysim-charts') / args.stage
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = EVIDENCE / 'before-source' if args.stage == 'before' else ROOT / 'dashboard'
DB = 'paysim_ui_evidence_20261028_194420'
db = MongoClient('mongodb://mongodb:27017', tz_aware=True)[DB]


def fingerprint():
    return {n: hashlib.sha256(json_util.dumps(list(db[n].find().sort('_id', 1)),
            sort_keys=True).encode()).hexdigest() for n in db.list_collection_names()}


original = fingerprint()
assert db.runs.count_documents({}) and db.pipeline_metrics.count_documents({})
views = args.views or (['operations'] if args.stage == 'before' else ['baseline', 'operations', 'report', 'studio'])
previous = OUT / 'browser-results.json'
report = [r for r in json.loads(previous.read_text()) if r['view'] not in views] if previous.exists() else []
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for view in views:
        entry = OUT / f'{view}.py'
        entry.write_text(f'import sys\nsys.path.insert(0, {str(SOURCE)!r})\nfrom dashboard_core import render\n' +
                         ('render()\n' if view == 'baseline' else f'import view_{view} as view\nrender(view)\n'))
        with (OUT / f'{view}-server.log').open('w') as log:
            proc = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(entry),
                '--server.port=8520', '--server.address=127.0.0.1', '--server.headless=true',
                '--browser.gatherUsageStats=false', '--theme.base=light'],
                env={**os.environ, 'MONGO_URI': 'mongodb://mongodb:27017', 'MONGO_DATABASE': DB},
                stdout=log, stderr=log)
            try:
                for _ in range(100):
                    try:
                        urllib.request.urlopen('http://127.0.0.1:8520/_stcore/health', timeout=1)
                        break
                    except Exception:
                        time.sleep(.2)
                for width, height in [(1440, 900), (1600, 900), (390, 844)]:
                    page = browser.new_page(viewport={'width': width, 'height': height})
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.goto('http://127.0.0.1:8520')
                    page.get_by_text('Nguồn đã phát', exact=True).first.wait_for(timeout=30000)
                    for i in range(4):
                        sidebar = page.locator('[data-testid="stSidebar"]')
                        if view == 'baseline' and width == 390:
                            collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
                            if sidebar.count() and sidebar.get_attribute('aria-expanded') == 'true' and collapse.count() and collapse.is_visible():
                                collapse.click()
                                page.wait_for_timeout(250)
                        if view == 'operations' and width == 390 and sidebar.get_attribute('aria-expanded') != 'true':
                            page.get_by_role('button', name='keyboard_double_arrow_right').click()
                        if view == 'operations':
                            page.locator('.st-key-dashboard_page button').nth(i).click()
                        elif view == 'baseline':
                            page.locator('[data-testid="stRadio"] [role="radiogroup"] label').nth(i).click()
                        elif view == 'report':
                            page.get_by_role('combobox').click()
                            page.get_by_role('option').nth(i).click()
                        else:
                            name = ['Live Control Room', 'Metrics theo 10 tracks', 'Fraud & Business', 'Dòng dữ liệu mới'][i]
                            page.get_by_role('button', name=name, exact=False).click()
                        expected = ['Tốc độ ingest và xử lý', '01. Ingestion',
                                    'Rule baseline vs Spark MLlib', 'Giao dịch vừa đi qua Spark'][i]
                        if i == 0 and view == 'report':
                            expected = '03 / Chất lượng phát hiện'
                        page.get_by_text(expected, exact=True).first.wait_for(timeout=30000)
                        page.wait_for_timeout(500)
                        if width == 390:
                            collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
                            if sidebar.count() and sidebar.get_attribute('aria-expanded') == 'true' and collapse.count() and collapse.is_visible():
                                collapse.click()
                                page.wait_for_timeout(250)
                        assert not page.locator('[data-testid="stException"]').count()
                        dom = page.evaluate('''() => ({
                            metrics:[...document.querySelectorAll('[data-testid="stMetric"]')].map(e=>({
                                label:e.querySelector('[data-testid="stMetricLabel"]')?.innerText.trim(),
                                value:e.querySelector('[data-testid="stMetricValue"]')?.innerText.trim(),
                                delta:e.querySelector('[data-testid="stMetricDelta"]')?.innerText.trim()||''
                            })),
                            overflow:document.documentElement.scrollWidth>innerWidth,
                            chartWidths:[...document.querySelectorAll('[data-testid="stVegaLiteChart"]')]
                                .map(e=>({width:e.getBoundingClientRect().width,scroll:e.scrollWidth}))
                        })''')
                        if view == 'operations':
                            assert not dom['overflow'], dom
                            assert all(c['scroll'] <= c['width'] + 1 for c in dom['chartWidths']), dom
                        prefix = f'{view}-{i+1}-{width}x{height}'
                        page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
                        page.screenshot(path=str(OUT / f'{prefix}.png'))
                        if view == 'operations' and i in (0, 3):
                            targets = {'latency': '.st-key-ops-signal-ingest_latency_p95_ms',
                                       'duration': '.st-key-ops-signal-batch_duration_seconds'} if i == 0 else {
                                       'distribution': '.st-key-ops-detail [data-testid="stVegaLiteChart"]'}
                            if i == 0 and args.stage == 'after':
                                targets['e2e-latency'] = '.st-key-ops-signal-latency_p95_ms'
                            for name, selector in targets.items():
                                target = page.locator(selector)
                                target.scroll_into_view_if_needed()
                                target.screenshot(path=str(OUT / f'{name}-{width}x{height}.png'))
                            page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=e.scrollHeight')
                            page.screenshot(path=str(OUT / f'{prefix}-details.png'))
                        assert not errors, errors
                        report.append(dict(view=view, page=i+1, viewport=[width,height], errors=list(errors), **dom))
                        (OUT / 'browser-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
                        print(f'PASS {args.stage} {view} page {i+1} {width}x{height}', flush=True)
                    page.close()
            finally:
                proc.terminate()
                proc.wait(timeout=15)
    browser.close()
final = fingerprint()
(OUT / 'database-fingerprints.json').write_text(json.dumps(dict(before=original, after=final, unchanged=original==final), indent=2))
assert original == final
