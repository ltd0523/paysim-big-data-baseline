"""Capture 9A against the existing, immutable real Mongo evidence database."""
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
parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['before', 'after'])
parser.add_argument('--fresh', action='store_true')
args = parser.parse_args()
OUT = Path('/tmp/paysim9a') / args.stage
OUT.mkdir(parents=True, exist_ok=True)
DB = 'paysim_ui_evidence_20261028_194420'
db = MongoClient('mongodb://mongodb:27017', tz_aware=True)[DB]


def fingerprint():
    return {name: hashlib.sha256(json_util.dumps(list(db[name].find().sort('_id', 1)),
                sort_keys=True).encode()).hexdigest() for name in db.list_collection_names()}


before = fingerprint()
entry = OUT / 'entry.py'
source = "import sys\nsys.path.insert(0, '/workspace/dashboard')\nfrom dashboard_core import render\n"
if args.stage == 'before':
    source += ("import importlib.util\n"
               "spec = importlib.util.spec_from_file_location('operations_before', "
               "'/workspace/dashboard_evidence_20261029_9a/view_operations.before.py')\n"
               "view = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(view)\n")
else:
    source += "import view_operations as view\n"
entry.write_text(source + "render(view)\n")
report = json.loads((OUT/'browser-results.json').read_text()) if (OUT/'browser-results.json').exists() and not args.fresh else []
with (OUT / 'server.log').open('w') as log:
    proc = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(entry),
        '--server.port=8511', '--server.address=127.0.0.1', '--server.headless=true',
        '--browser.gatherUsageStats=false', '--theme.base=light'],
        env={**os.environ, 'MONGO_URI': 'mongodb://mongodb:27017', 'MONGO_DATABASE': DB},
        stdout=log, stderr=log)
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen('http://127.0.0.1:8511/_stcore/health', timeout=1)
                break
            except Exception:
                time.sleep(.2)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width, height in [(1366,768), (1440,900), (1600,900), (390,844)]:
                if len([r for r in report if r['viewport'] == [width,height]]) == 4:
                    continue
                report = [r for r in report if r['viewport'] != [width,height]]
                page = browser.new_page(viewport={'width':width, 'height':height})
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto('http://127.0.0.1:8511')
                page.get_by_text('Nguồn đã phát', exact=True).wait_for(timeout=30000)
                labels = ['📡 Live Control Room', '🎯 Metrics theo 10 tracks',
                          '🛡️ Fraud & Business', '🔎 Dòng dữ liệu mới']
                for index, label in enumerate(labels):
                    if width == 390:
                        sidebar = page.locator('[data-testid="stSidebar"]')
                        if sidebar.get_attribute('aria-expanded') != 'true':
                            page.get_by_role('button', name='keyboard_double_arrow_right').click()
                    page.get_by_text(label, exact=True).click()
                    expected = ['Spark đã xử lý', '01. Ingestion',
                                'Rule baseline vs Spark MLlib', 'Giao dịch vừa đi qua Spark'][index]
                    page.get_by_text(expected, exact=True).first.wait_for(timeout=20000)
                    if width == 390:
                        collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
                        if collapse.count() and collapse.bounding_box()['x'] >= 0:
                            collapse.click()
                    page.wait_for_timeout(800)
                    exceptions = page.locator('[data-testid="stException"]').all_text_contents()
                    assert not exceptions and not errors, (exceptions, errors)
                    # One JS task avoids tearing across the two-second fragment refresh.
                    dom = page.evaluate('''() => ({
                        metrics: [...document.querySelectorAll('[data-testid="stMetric"]')].map(e => ({
                            label: e.querySelector('[data-testid="stMetricLabel"]')?.innerText.trim(),
                            value: e.querySelector('[data-testid="stMetricValue"]')?.innerText.trim(),
                            delta: e.querySelector('[data-testid="stMetricDelta"]')?.innerText.trim() || '',
                            rect: e.getBoundingClientRect().toJSON(),
                            overflow: [...e.querySelectorAll('[data-testid="stMetricValue"] > div')]
                                .some(v => v.scrollWidth > v.clientWidth + 1)
                        })),
                        documentWidth: document.documentElement.scrollWidth,
                        viewportWidth: innerWidth,
                        sidebarWidth: document.querySelector('[data-testid="stSidebar"]').getBoundingClientRect().width,
                        captionsOpaque: [...document.querySelectorAll('[data-testid="stCaptionContainer"]')]
                            .every(e => getComputedStyle(e).opacity === '1'),
                        charts: [...document.querySelectorAll('[data-testid="stVegaLiteChart"]')]
                            .map(e => e.getBoundingClientRect().toJSON()),
                        expanderStyle: (() => {
                            const e=document.querySelector('[data-testid="stExpander"] > details > summary');
                            return e ? {color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor} : null;
                        })(),
                        body: document.querySelector('[data-testid="stMain"]').innerText
                    })''')
                    filename = f'{index+1}-{width}x{height}.png'
                    if args.stage == 'after':
                        assert dom['captionsOpaque']
                        assert dom['documentWidth'] <= width
                        assert not any(m['overflow'] for m in dom['metrics'])
                        if index == 0:
                            assert dom['expanderStyle']['background'] == 'rgb(27, 43, 64)'
                    page.screenshot(path=str(OUT/filename))
                    if index == 0:
                        if args.stage == 'after':
                            page.locator('.st-key-ops-signal-consumer_lag').scroll_into_view_if_needed()
                            page.screenshot(path=str(OUT/f'signals-{width}x{height}.png'))
                            page.locator('.st-key-ops-monitor').scroll_into_view_if_needed()
                            page.screenshot(path=str(OUT/f'monitor-{width}x{height}.png'))
                        # Streamlit scrolls its main region; a full_page screenshot is insufficient.
                        page.locator('[data-testid="stMain"]').evaluate('(e) => e.scrollTop = e.scrollHeight')
                        page.wait_for_timeout(250)
                        page.screenshot(path=str(OUT/f'history-{width}x{height}.png'))
                        page.locator('[data-testid="stMain"]').evaluate('(e) => e.scrollTop = 0')
                    else:
                        page.locator('[data-testid="stMain"]').evaluate('(e) => e.scrollTop = e.scrollHeight')
                        page.screenshot(path=str(OUT/f'details-{index+1}-{width}x{height}.png'))
                        page.locator('[data-testid="stMain"]').evaluate('(e) => e.scrollTop = 0')
                    report.append(dict(page=label, viewport=[width,height], screenshot=filename,
                                       browser_errors=list(errors), streamlit_exceptions=exceptions, **dom))
                    (OUT/'browser-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
                page.close()
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=15)
after = fingerprint()
(OUT/'database-fingerprints.json').write_text(json.dumps({'before':before,'after':after,
                                                       'unchanged':before==after}, indent=2))
assert before == after
print(f'PASS: {len(report)} pages; database unchanged; output {OUT}')
