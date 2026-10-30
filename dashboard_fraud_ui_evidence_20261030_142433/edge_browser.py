"""In-memory edge cases, with no writes to MongoDB."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

OUT = Path('/tmp/paysim-fraud/edges')
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
mode = st.query_params.get('mode','empty')
s.evaluation = {}
s.model = core.detector_metrics({}, 'model')
if mode == 'empty':
    s.aggregates = []
    s.recent_alerts = []
else:
    s.aggregates = [dict(type='CASH_OUT', model_alerts=0, rule_alerts=0)]
    s.recent_alerts = [dict(event_id=f'edge-{i}', type='TRANSFER', amount=amount, risk_score=.5)
        for i,amount in enumerate([0, -1, None, float('inf'), 10])]
view.render(s, core.PAGES[2])
''')
report = []
with (OUT / 'server.log').open('w') as log:
    proc = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(entry),
        '--server.port=8522','--server.address=127.0.0.1','--server.headless=true',
        '--browser.gatherUsageStats=false','--theme.base=light'],
        env={**os.environ,'MONGO_URI':'mongodb://mongodb:27017',
             'MONGO_DATABASE':'paysim_ui_evidence_20261028_194420'},stdout=log,stderr=log)
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen('http://127.0.0.1:8522/_stcore/health',timeout=1)
                break
            except Exception: time.sleep(.2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for mode in ['empty','invalid']:
                for width,height in [(1440,900),(390,844)]:
                    page = browser.new_page(viewport={'width':width,'height':height})
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
                    page.goto(f'http://127.0.0.1:8522?mode={mode}')
                    page.get_by_text('Risk Score Analysis',exact=True).wait_for(timeout=30000)
                    sidebar = page.locator('[data-testid="stSidebar"]')
                    if width == 390 and sidebar.get_attribute('aria-expanded') == 'true':
                        page.locator('[data-testid="stSidebarCollapseButton"] button').click()
                    page.wait_for_timeout(500)
                    assert not page.locator('[data-testid="stException"]').count()
                    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                    if mode == 'invalid':
                        page.get_by_text('4 alerts có Amount',exact=False).wait_for()
                    gap = page.locator('.st-key-ops-fraud-business').evaluate('e=>getComputedStyle(e).gap')
                    assert gap == '28px',gap
                    for name in ['performance','matrix','alerts','risk']:
                        target = page.locator(f'.st-key-ops-fraud-{name}')
                        target.scroll_into_view_if_needed()
                        target.screenshot(path=str(OUT / f'{mode}-{name}-{width}.png'))
                    assert not errors,errors
                    report.append(dict(mode=mode,viewport=[width,height],errors=errors,passed=True))
                    print(f'PASS edge {mode} {width}x{height}',flush=True)
                    page.close()
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=15)
(OUT/'results.json').write_text(json.dumps(report,indent=2))
