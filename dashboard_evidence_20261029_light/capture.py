"""Read-only browser evidence against the existing frozen Mongo snapshot."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from bson import json_util
import pandas as pd
from playwright.sync_api import sync_playwright
from pymongo import MongoClient

ROOT = Path('/workspace')
EVIDENCE = ROOT / 'dashboard_evidence_20261029_light'
parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['before', 'after'])
args = parser.parse_args()
OUT = Path('/tmp/paysim-light') / args.stage
OUT.mkdir(parents=True, exist_ok=True)
db = MongoClient('mongodb://mongodb:27017', tz_aware=True).paysim_ui_evidence_20261028_194420


def fingerprint():
    return {name: hashlib.sha256(json_util.dumps(list(db[name].find().sort('_id', 1)),
            sort_keys=True).encode()).hexdigest() for name in db.list_collection_names()}


original = fingerprint()
entry = OUT / 'entry.py'
source = "import sys\nsys.path.insert(0, '/workspace/dashboard')\nfrom dashboard_core import render\n"
if args.stage == 'before':
    source += ("import importlib.util\n"
               "spec = importlib.util.spec_from_file_location('operations_before', "
               f"'{EVIDENCE}/view_operations.before.py')\n"
               "view = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(view)\n")
else:
    source += "import view_operations as view\n"
entry.write_text(source + 'render(view)\n')
report = []
with (OUT / 'server.log').open('w') as log:
    proc = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(entry),
        '--server.port=8518', '--server.address=127.0.0.1', '--server.headless=true',
        '--browser.gatherUsageStats=false', '--theme.base=light'],
        env={**os.environ, 'MONGO_URI': 'mongodb://mongodb:27017',
             'MONGO_DATABASE': 'paysim_ui_evidence_20261028_194420'}, stdout=log, stderr=log)
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen('http://127.0.0.1:8518/_stcore/health', timeout=1)
                break
            except Exception:
                time.sleep(.2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width, height in [(1366, 768), (1440, 900), (1600, 900), (390, 844)]:
                page = browser.new_page(viewport={'width': width, 'height': height}, accept_downloads=True)
                page.add_init_script("window.showSaveFilePicker = async () => { throw new DOMException('Headless CSV test', 'NotSupportedError'); };")
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto('http://127.0.0.1:8518')
                page.locator('[data-testid="stMetricValue"]').first.wait_for()
                for index in range(4):
                    sidebar = page.locator('[data-testid="stSidebar"]')
                    if width == 390 and sidebar.get_attribute('aria-expanded') != 'true':
                        page.get_by_role('button', name='keyboard_double_arrow_right').click()
                    if args.stage == 'before':
                        sidebar.locator('[role="radiogroup"] label').nth(index).click()
                    else:
                        menu = page.locator('.st-key-dashboard_page button')
                        menu.nth(3).wait_for()
                        assert menu.count() == 4
                        menu.nth(index).click()
                        # Clicking the current option must keep that page selected.
                        menu.nth(index).click()
                    expected = ['Spark đã xử lý', '01. Ingestion',
                                'Rule baseline vs Spark MLlib', 'Giao dịch vừa đi qua Spark'][index]
                    page.get_by_text(expected, exact=True).first.wait_for()
                    page.wait_for_timeout(350)
                    if width == 390:
                        if index == 0:
                            page.screenshot(path=str(OUT / 'sidebar-390x844.png'))
                        page.locator('[data-testid="stSidebarCollapseButton"] button').click()
                        page.wait_for_timeout(350)
                    page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
                    assert not page.locator('[data-testid="stException"]').count()
                    dom = page.evaluate('''() => ({
                        background:getComputedStyle(document.querySelector('[data-testid="stAppViewContainer"]')).backgroundColor,
                        sidebar:getComputedStyle(document.querySelector('[data-testid="stSidebar"]')).backgroundColor,
                        metrics:[...document.querySelectorAll('[data-testid="stMetric"]')].map(e=>({
                            label:e.querySelector('[data-testid="stMetricLabel"]')?.innerText.trim(),
                            value:e.querySelector('[data-testid="stMetricValue"]')?.innerText.trim(),
                            delta:e.querySelector('[data-testid="stMetricDelta"]')?.innerText.trim()||'',
                            overflow:[...e.querySelectorAll('[data-testid="stMetricValue"] > div')]
                                .some(v=>v.scrollWidth>v.clientWidth+1)
                        })),
                        menu:[...document.querySelectorAll('.st-key-dashboard_page button')].map(e=>({
                            label:e.innerText,selected:e.dataset.testid==='stBaseButton-pillsActive',
                            font:getComputedStyle(e.querySelector('p')).fontSize,
                            leftBorder:getComputedStyle(e).borderLeftWidth,
                            icons:[...e.querySelectorAll('[data-testid="stIconMaterial"]')].map(i=>i.innerText)
                        })),
                        help:[...document.querySelectorAll('[data-testid="stTooltipIcon"] svg')].map(e=>getComputedStyle(e).color),
                        rounded:[...document.querySelectorAll('.st-key-ops-detail [data-testid="stVegaLiteChart"] > .chart-wrapper')]
                            .map(e=>getComputedStyle(e).borderRadius),
                        pageOverflow:document.documentElement.scrollWidth>innerWidth
                    })''')
                    assert not dom['pageOverflow']
                    assert not any(m['overflow'] for m in dom['metrics'])
                    if args.stage == 'after':
                        assert dom['background'] == 'rgb(245, 247, 251)'
                        assert dom['sidebar'] == 'rgb(237, 242, 248)'
                        assert all(c == 'rgb(255, 255, 255)' for c in dom['help'])
                        assert all(m['font'] == '16px' and len(m['icons']) == 1 for m in dom['menu'])
                        assert sum(m['selected'] for m in dom['menu']) == 1
                        assert dom['menu'][index]['selected']
                        assert all(radius == '15px' for radius in dom['rounded'])
                        if index == 0:
                            icon = page.locator('[data-testid="stTooltipIcon"]').first
                            icon.hover()
                            page.get_by_role('tooltip').wait_for(timeout=5000)
                            assert page.get_by_role('tooltip').inner_text().strip()
                            page.mouse.move(width-5, 50)
                            page.get_by_role('tooltip').wait_for(state='hidden')
                    page.screenshot(path=str(OUT / f'{index+1}-{width}x{height}.png'))
                    page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=e.scrollHeight')
                    page.wait_for_timeout(200)
                    page.screenshot(path=str(OUT / f'details-{index+1}-{width}x{height}.png'))
                    if args.stage == 'after' and width in [1366, 390] and index in [0, 2, 3]:
                        table = page.locator('[data-testid="stDataFrame"]').first
                        # Keep the toolbar above the table clear of Streamlit's sticky header.
                        table.evaluate("(e)=>e.scrollIntoView({block:'center'})")
                        table.hover()
                        page.wait_for_timeout(250)
                        button = table.get_by_role('button', name='Download as CSV')
                        # Native toolbar floats outside its table. Use a real pointer click
                        # without Playwright scrolling it back into that table's bounds.
                        assert button.evaluate('''e=>{
                            const r=e.getBoundingClientRect();
                            return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest('button')===e;
                        }'''), 'CSV button is occluded'
                        bounds = button.bounding_box()
                        with page.expect_download() as task:
                            page.mouse.click(bounds['x']+bounds['width']/2, bounds['y']+bounds['height']/2)
                        download = task.value
                        target = OUT / f'page-{index+1}-{width}.csv'
                        download.save_as(target)
                        frame = pd.read_csv(target)
                        assert len(frame) == {0: 13, 2: 2, 3: 60}[index]
                        dom['csv'] = {'rows': len(frame), 'columns': list(frame.columns)}
                    assert not errors
                    report.append({'page': index+1, 'viewport': [width, height], 'errors': list(errors), **dom})
                    (OUT / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
                    print(f'PASS {args.stage}: page {index+1}, {width}x{height}', flush=True)
                page.close()
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=15)
final = fingerprint()
(OUT / 'database-fingerprints.json').write_text(json.dumps({'before': original, 'after': final,
                                                          'unchanged': original == final}, indent=2))
assert original == final
print(f'PASS {args.stage}: 16 page/viewport combinations; frozen database unchanged')
