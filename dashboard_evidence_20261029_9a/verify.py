"""Final read-only verification and hashes; run inside the existing test container."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path('/workspace')
OUT=Path('/tmp/paysim9a')
evidence=ROOT/'dashboard_evidence_20261029_9a'
for name,command in [
    ('test-results.txt',[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',str(ROOT/'tests/test_dashboard.py')]),
    ('audit-results.txt',[sys.executable,str(evidence/'audit.py')]),
]:
    result=subprocess.run(command,capture_output=True,text=True)
    (OUT/name).write_text(result.stdout+result.stderr)
    assert result.returncode==0,(name,result.stdout,result.stderr)
    print(name, 'PASS')

before=json.loads((OUT/'before/browser-results.json').read_text())
after=json.loads((OUT/'after/browser-results.json').read_text())
assert len(before)==len(after)==16
labels={'Nguồn đã phát','Spark đã xử lý','Fraud alerts','Ingest hiện tại',
        'Processing throughput','End-to-end latency p95'}
for old,new in zip(before,after):
    assert old['page']==new['page'] and old['viewport']==new['viewport']
    metrics=lambda row: sorted((m['label'],m['value'],m['delta']) for m in row['metrics'] if m['label'] in labels)
    assert metrics(old)==metrics(new)
    assert {m['label'] for m in new['metrics'] if m['label'] in labels}==labels
    assert not new['browser_errors'] and not new['streamlit_exceptions']
    assert new['documentWidth']<=new['viewport'][0] and new['sidebarWidth']==252
    assert not any(m['overflow'] for m in new['metrics']) and new['captionsOpaque']
    if new['page'].startswith('📡'):
        assert new['expanderStyle']=={'color':'rgb(241, 245, 249)','background':'rgb(27, 43, 64)'}
original=(evidence/'view_operations.before.py').read_text()
modified=(ROOT/'dashboard/view_operations.py').read_text()
markers=lambda text:re.findall(r'^# (?:BEFORE|AFTER) (?:Start|END).*$',text,re.M)
assert markers(original)==markers(modified)
assert len(markers(modified))==20
assert '@st.fragment(run_every=2.0)' in (ROOT/'dashboard/dashboard_core.py').read_text()
for stage in ['before','after']:
    assert json.loads((OUT/stage/'database-fingerprints.json').read_text())['unchanged']
assert json.loads((OUT/'before/database-fingerprints.json').read_text())['before']==json.loads(
    (OUT/'after/database-fingerprints.json').read_text())['after']
edges=json.loads((OUT/'edge-cases/results.json').read_text())
assert len(edges)==4 and all(r['passed'] for r in edges)
output={'original_tests':'7 passed','browser_before':16,'browser_after':16,
        'six_kpis_and_deltas_equal_in_all_browser_pairs':True,'all_20_markers_preserved':True,
        'snapshot_fingerprints_equal_across_before_after':True,'responsive_assertions_passed':True,
        'edge_cases':edges,'streamlit':'1.50.0','altair':'5.5.0',
        'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in
            ['dashboard/view_operations.py','dashboard/dashboard_core.py','dashboard/app.py']}}
(OUT/'verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
print('PASS: 16 browser pairs, unchanged evidence, no KPI clipping or document overflow, 20 markers, four edge scenarios')
