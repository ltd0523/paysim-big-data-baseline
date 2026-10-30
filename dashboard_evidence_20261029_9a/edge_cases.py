"""Browser presentation checks with in-memory overrides; no Mongo writes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

OUT = Path('/tmp/paysim9a/edge-cases')
OUT.mkdir(parents=True, exist_ok=True)
entry = OUT/'entry.py'
entry.write_text('''import sys
sys.path.insert(0, '/workspace/dashboard')
import streamlit as st
import dashboard_core as core
import view_operations as view
original = core.load_snapshot
def scenario_snapshot():
    s = original()
    if st.query_params.get('case') == 'large':
        s.latest_metric = {**s.latest_metric, 'latency_p95_ms':9876543210123}
        s.display_correct = False
        s.run_id = '<unsafe & run>'
    elif st.query_params.get('case') == 'empty':
        s.metrics = []
    return s
core.load_snapshot = scenario_snapshot
core.render(view)
''')
results = []
with (OUT/'server.log').open('w') as log:
    proc = subprocess.Popen([sys.executable,'-m','streamlit','run',str(entry),'--server.port=8513',
        '--server.address=127.0.0.1','--server.headless=true','--browser.gatherUsageStats=false','--theme.base=light'],
        env={**os.environ,'MONGO_URI':'mongodb://mongodb:27017',
             'MONGO_DATABASE':'paysim_ui_evidence_20261028_194420'},stdout=log,stderr=log)
    try:
        time.sleep(2)
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            for case,width,height in [('normal',1366,768),('large',1366,768),('large',390,844),('empty',390,844)]:
                page=browser.new_page(viewport={'width':width,'height':height})
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:8513/?case={case}')
                page.get_by_text('Nguồn đã phát',exact=True).wait_for()
                if width==390:
                    page.locator('[data-testid="stSidebarCollapseButton"] button').click()
                if case=='normal':
                    radio=page.get_by_role('radio').first
                    radio.focus()
                    focused=page.locator('[data-testid="stSidebar"] label:has(input:focus-visible)')
                    assert focused.count()==1
                    assert focused.evaluate('(e) => getComputedStyle(e).outlineStyle')=='solid'
                    page.keyboard.press('ArrowDown')
                    page.get_by_text('01. Ingestion',exact=True).wait_for()
                    assert page.get_by_role('radio').nth(1).is_checked()
                    page.get_by_role('radio').nth(1).focus()
                    page.keyboard.press('ArrowUp')
                    page.get_by_text('Tốc độ ingest và xử lý',exact=True).wait_for()
                    # Real Altair point hover must expose all four tooltip fields.
                    point=page.locator('.st-key-ops-signal-ingest_throughput .mark-symbol.role-mark path').last
                    point.hover()
                    tip=page.locator('#vg-tooltip-element')
                    tip.wait_for(state='visible')
                    content=tip.inner_text()
                    assert all(k in content for k in ['Timestamp','Metric','Value','Unit','Events/s'])
                elif case=='large':
                    value=page.locator('[data-testid="stMetric"]').filter(has_text='End-to-end latency p95')
                    value.scroll_into_view_if_needed()
                    assert value.locator('[data-testid="stMetricValue"]').inner_text()=='9,876,543,210,123 ms'
                    assert value.evaluate('e => e.scrollWidth <= e.clientWidth + 1')
                    page.get_by_text('SYNCING',exact=True).wait_for(state='attached')
                    assert page.locator('.ops-run-id').inner_text()=='Run ID · <unsafe & run>'
                else:
                    assert page.get_by_text('Đang chờ micro-batch telemetry đầu tiên.',exact=True).count()==4
                    assert page.locator('[data-testid="stVegaLiteChart"]').count()==0
                # Keep the production two-second fragment active and observe another refresh.
                page.wait_for_timeout(2300)
                assert not errors and not page.locator('[data-testid="stException"]').count()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(OUT/f'{case}-{width}.png'))
                results.append({'scenario':case,'viewport':[width,height],'browser_errors':errors,
                                'streamlit_exceptions':0,'passed':True})
                page.close()
            browser.close()
    finally:
        proc.terminate();proc.wait(timeout=15)
(OUT/'results.json').write_text(json.dumps(results,indent=2))
print('PASS: keyboard navigation/focus, real tooltip, large latency at desktop/mobile, SYNCING, escaped metadata, empty telemetry, two-second refresh')
