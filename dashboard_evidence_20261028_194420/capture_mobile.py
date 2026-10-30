"""Supplement repository captures with navigation on all 16 mobile pages."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright

OUT = Path('/evidence')
PAGES = ['📡 Live Control Room', '🎯 Metrics theo 10 tracks', '🛡️ Fraud & Business', '🔎 Dòng dữ liệu mới']
LABELS = ['Nguồn đã phát', 'Spark đã xử lý', 'Fraud alerts', 'Ingest hiện tại',
          'Processing throughput', 'End-to-end latency p95']
rows = json.loads((OUT/'mobile-results.json').read_text()) if (OUT/'mobile-results.json').exists() else []


def in_view(locator):
    if not locator.count():
        return False
    box = locator.first.bounding_box()
    return bool(box and box['x'] >= 0 and box['x'] < 390 and box['y'] >= 0 and box['y'] < 844)


with tempfile.TemporaryDirectory(prefix='track9-mobile-') as tmp, sync_playwright() as p:
    browser = p.chromium.launch()
    for view in ['baseline', 'operations', 'report', 'studio']:
        if len([r for r in rows if r['view'] == view]) == 4:
            continue
        rows = [r for r in rows if r['view'] != view]
        entry = Path(tmp)/f'{view}.py'
        entry.write_text('import sys\nsys.path.insert(0,"/workspace/dashboard")\nfrom dashboard_core import render\n' + (
            'render()\n' if view == 'baseline' else f'import view_{view} as view\nrender(view)\n'))
        with (OUT/f'mobile-{view}-server.txt').open('w') as log:
            proc = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(entry),
                '--server.port=8510', '--server.address=127.0.0.1', '--server.headless=true',
                '--browser.gatherUsageStats=false', '--theme.base=light'], stdout=log, stderr=log)
            try:
                for _ in range(100):
                    try:
                        urllib.request.urlopen('http://127.0.0.1:8510/_stcore/health', timeout=1)
                        break
                    except Exception:
                        time.sleep(.2)
                page = browser.new_page(viewport={'width':390, 'height':844}, device_scale_factor=1)
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto('http://127.0.0.1:8510')
                page.get_by_text('Nguồn đã phát', exact=True).wait_for(timeout=30000)
                for i, label in enumerate(PAGES):
                    errors.clear()
                    if view == 'operations':
                        nav = page.get_by_text(label, exact=True)
                        if not in_view(nav):
                            expand = page.locator('[data-testid="stExpandSidebarButton"] button, '
                                                  '[data-testid="stSidebarCollapsedControl"] button')
                            if expand.count():
                                expand.first.click()
                            else:
                                page.get_by_role('button', name='keyboard_double_arrow_right').click()
                        nav.click()
                        collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
                        if in_view(collapse): collapse.click()
                    elif view == 'baseline':
                        collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
                        if in_view(collapse): collapse.click()
                        page.get_by_text(label, exact=True).click()
                    elif view == 'report':
                        page.get_by_role('combobox').click()
                        page.get_by_role('option', name=label, exact=True).click()
                    else:
                        page.get_by_role('button', name=label.split(' ', 1)[1], exact=False).click()
                    expected = ['Tốc độ ingest và xử lý', '01. Ingestion',
                                'Rule baseline vs Spark MLlib', 'Giao dịch vừa đi qua Spark'][i]
                    if i == 0 and view == 'operations': expected = 'Trung tâm vận hành'
                    if i == 0 and view == 'report': expected = '03 / Chất lượng phát hiện'
                    page.get_by_text(expected, exact=True).first.wait_for(timeout=20000)
                    page.wait_for_timeout(1000)
                    # Read the DOM in one browser task: 2-second fragment refresh
                    # can otherwise remove an nth metric between locator calls.
                    for attempt in range(20):
                        metrics = page.locator('[data-testid="stMetric"]').evaluate_all('''elements =>
                            elements.map(e => ({
                                label: e.querySelector('[data-testid="stMetricLabel"]')?.innerText.trim() || '',
                                value: e.querySelector('[data-testid="stMetricValue"]')?.innerText.trim() || '',
                                delta: e.querySelector('[data-testid="stMetricDelta"]')?.innerText.trim() || ''
                            }))''')
                        metrics = [m for m in metrics if m['label'] in LABELS]
                        if set(m['label'] for m in metrics) == set(LABELS): break
                        page.wait_for_timeout(200)
                    exceptions = page.locator('[data-testid="stException"]').count()
                    assert exceptions == 0 and not errors, (view, label, exceptions, errors)
                    assert set(m['label'] for m in metrics) == set(LABELS)
                    filename = f'{view}-{i+1}-mobile.png'
                    page.screenshot(path=str(OUT/'captures'/filename), full_page=True)
                    rows.append({'view': view, 'page': label, 'viewport': {'width':390, 'height':844},
                                 'metrics': metrics, 'browser_errors': list(errors),
                                 'streamlit_exceptions': exceptions, 'screenshot': f'captures/{filename}'})
                    (OUT/'mobile-results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
                page.close()
            finally:
                proc.terminate()
                proc.wait(timeout=15)
    browser.close()
print(f'PASS: {len(rows)} mobile pages with six KPI and zero exceptions')
