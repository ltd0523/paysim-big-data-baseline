"""Synthetic edge cases are in memory only; never write test records to MongoDB."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

OUT = Path('/tmp/paysim-charts/edges')
OUT.mkdir(parents=True, exist_ok=True)
entry = OUT / 'entry.py'
entry.write_text('''import sys
sys.path.insert(0, '/workspace/dashboard')
import copy
import streamlit as st
import dashboard_core as core
import view_operations as view
st.set_page_config(**view.PAGE_CONFIG)
view.setup()
s = copy.deepcopy(core.load_snapshot())
mode = st.query_params.get('mode', 'one')
if mode == 'empty':
    s.metrics = []
    s.aggregates = []
else:
    s.metrics = s.metrics[:1]
    s.metrics[0]['latency_p95_ms'] = 1e12
    s.metrics[0]['ingest_latency_p95_ms'] = .125
    s.metrics[0]['batch_duration_seconds'] = .001
view.render(s, core.PAGES[0])
st.subheader('Edge distribution')
import pandas as pd
view.transaction_distribution(pd.DataFrame(s.aggregates))
''')
report = []
with (OUT / 'server.log').open('w') as log:
    proc = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(entry),
        '--server.port=8521', '--server.address=127.0.0.1', '--server.headless=true',
        '--browser.gatherUsageStats=false', '--theme.base=light'],
        env={**os.environ, 'MONGO_URI':'mongodb://mongodb:27017',
             'MONGO_DATABASE':'paysim_ui_evidence_20261028_194420'}, stdout=log, stderr=log)
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen('http://127.0.0.1:8521/_stcore/health', timeout=1)
                break
            except Exception: time.sleep(.2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for mode in ['empty', 'one']:
                for width, height in [(1440,900), (390,844)]:
                    page = browser.new_page(viewport={'width':width,'height':height})
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
                    page.goto(f'http://127.0.0.1:8521?mode={mode}')
                    page.get_by_text('Edge distribution', exact=True).wait_for(timeout=30000)
                    collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
                    if width == 390 and page.locator('[data-testid="stSidebar"]').get_attribute('aria-expanded') == 'true': collapse.click()
                    page.wait_for_timeout(500)
                    assert not page.locator('[data-testid="stException"]').count()
                    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                    assert not errors, errors
                    for selector, name in [('.st-key-ops-signal-ingest_latency_p95_ms','ingest'),
                                           ('.st-key-ops-signal-latency_p95_ms','e2e'),
                                           ('.st-key-ops-signal-batch_duration_seconds','duration')]:
                        target = page.locator(selector)
                        target.scroll_into_view_if_needed()
                        target.screenshot(path=str(OUT / f'{mode}-{name}-{width}.png'))
                    report.append(dict(mode=mode, viewport=[width,height], exceptions=[], errors=[], passed=True))
                    print(f'PASS edge {mode} {width}x{height}', flush=True)
                    page.close()
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=15)
(OUT / 'results.json').write_text(json.dumps(report, indent=2))
