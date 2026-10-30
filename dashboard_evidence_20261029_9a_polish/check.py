"""Verify peer fraud KPIs, track-code visibility and native CSV downloads."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pandas as pd
from playwright.sync_api import sync_playwright

OUT=Path('/tmp/paysim9a-polish')
OUT.mkdir(exist_ok=True)
entry=OUT/'entry.py'
entry.write_text("import sys\nsys.path.insert(0,'/workspace/dashboard')\n"
                 "from dashboard_core import render\nimport view_operations as view\nrender(view)\n")
results=[]
with (OUT/'server.log').open('w') as log:
    proc=subprocess.Popen([sys.executable,'-m','streamlit','run',str(entry),
        '--server.port=8514','--server.address=127.0.0.1','--server.headless=true',
        '--browser.gatherUsageStats=false','--theme.base=light'],
        env={**os.environ,'MONGO_URI':'mongodb://mongodb:27017',
             'MONGO_DATABASE':'paysim_ui_evidence_20261028_194420'},stdout=log,stderr=log)
    try:
        time.sleep(2)
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            for width,height in [(1366,768),(390,844)]:
                page=browser.new_page(viewport={'width':width,'height':height},accept_downloads=True)
                # Native Chromium opens an OS save picker, which emits no download event.
                # Exercise Streamlit's supported Blob download fallback in headless tests.
                page.add_init_script("window.showSaveFilePicker = async () => { throw new DOMException('Headless CSV test', 'NotSupportedError'); };")
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto('http://127.0.0.1:8514')
                page.get_by_text('Nguồn đã phát',exact=True).wait_for()
                if width==390:
                    page.locator('[data-testid="stSidebarCollapseButton"] button').click()
                fraud=page.locator('.st-key-ops-fraud')
                fraud.scroll_into_view_if_needed()
                values=fraud.locator('[data-testid="stMetricValue"]')
                page.wait_for_timeout(500)
                actual=[text.strip() for text in values.all_text_contents()]
                assert actual==['1,238','19.97%'], actual
                geometry=values.evaluate_all('''es => es.map(e => ({
                    x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,
                    font:getComputedStyle(e).fontSize,width:e.getBoundingClientRect().width,
                    overflow:e.firstElementChild.scrollWidth > e.firstElementChild.clientWidth+1
                }))''')
                assert geometry[0]['font']==geometry[1]['font']=='24px'
                assert abs(geometry[0]['y']-geometry[1]['y'])<1
                assert abs(geometry[0]['width']-geometry[1]['width'])<1
                assert not any(g['overflow'] for g in geometry)
                assert not page.get_by_text('Alert rate · Cảnh báo cần xem xét, chưa phải gian lận đã xác nhận.',exact=True).count()
                page.screenshot(path=str(OUT/f'fraud-{width}.png'))
                scenarios=[('📡 Live Control Room','history',13),
                           ('🛡️ Fraud & Business','detectors',2),
                           ('🔎 Dòng dữ liệu mới','transactions',60),
                           ('🎯 Metrics theo 10 tracks','tracks',None)]
                exports=[]
                for label,name,count in scenarios:
                    if width==390:
                        page.get_by_role('button',name='keyboard_double_arrow_right').click()
                    page.get_by_text(label,exact=True).click()
                    expected={'history':'Micro-batch History','detectors':'Rule baseline vs Spark MLlib',
                              'transactions':'Giao dịch vừa đi qua Spark','tracks':'01. Ingestion'}[name]
                    page.get_by_text(expected,exact=True).wait_for()
                    page.wait_for_timeout(500)
                    if width==390:
                        page.locator('[data-testid="stSidebarCollapseButton"] button').click()
                    if name=='tracks':
                        codes=page.locator('.metric-code')
                        assert codes.count()>30
                        assert codes.evaluate_all("es=>es.every(e=>getComputedStyle(e).display==='none')")
                        assert page.get_by_text('Ingest throughput',exact=True).count()==1
                        assert page.get_by_text('Replayer → Kafka → Spark consumer',exact=True).is_visible()
                        assert page.get_by_text('Guardrail:',exact=False).count()==10
                        page.screenshot(path=str(OUT/f'tracks-{width}.png'))
                        continue
                    table=page.locator('[data-testid="stDataFrame"]').first
                    table.scroll_into_view_if_needed()
                    table.hover()
                    download=table.get_by_role('button',name='Download as CSV')
                    download.wait_for(state='visible')
                    with page.expect_download() as task:
                        download.click()
                    item=task.value
                    file=OUT/f'{name}-{width}.csv'
                    item.save_as(file)
                    assert item.failure() is None
                    csv=pd.read_csv(file)
                    assert len(csv)==count,(name,len(csv),count)
                    assert len(csv.columns)=={'history':10,'detectors':9,'transactions':9}[name]
                    if name=='history':
                        assert int(csv.iloc[0,0])==198
                        assert float(csv['latency_p95_ms'].iloc[0])==29763813
                    elif name=='detectors':
                        assert csv['Detector'].tolist()==['Spark SQL rule','Spark MLlib']
                        assert csv['TP'].tolist()==[8,52]
                        assert csv['FP'].tolist()==[64,1186]
                    else:
                        assert csv['prediction'].isin([0,1]).all()
                    exports.append({'table':name,'rows':len(csv),'columns':list(csv.columns),'file':file.name})
                    page.screenshot(path=str(OUT/f'{name}-{width}.png'))
                assert not errors and not page.locator('[data-testid="stException"]').count()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                results.append({'viewport':[width,height],'fraud':geometry,'exports':exports,
                                'codes_hidden_other_text_retained':True,'browser_errors':errors})
                (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
                page.close()
            browser.close()
    finally:
        proc.terminate();proc.wait(timeout=15)
print('PASS: equal peer KPI sizes on desktop/mobile; all six CSV downloads; track codes hidden, other text retained')
