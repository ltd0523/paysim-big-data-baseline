"""Verify final evidence, derive correctness tables from audit, and hash artifacts."""
import hashlib
import json
from pathlib import Path
import re

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parent
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
for path in [*ROOT.joinpath('dashboard').glob('*.py'), ROOT/'tests/test_dashboard.py', *EVIDENCE.glob('*.py')]:
    compile(path.read_text(encoding='utf-8-sig'),str(path),'exec')
(EVIDENCE/'syntax-results.txt').write_text('PASS: all dashboard modules, dashboard tests and evidence scripts compile\n')
result = read(EVIDENCE/'verification.json')
assert all(result[k] for k in ['business_logic_ast_unchanged','frozen_database_unchanged',
    'other_views_chart_specs_and_data_identical','prior_operations_charts_identical'])
assert len(result['pages']) == 16 and result['scatter_rows'] == 300
assert len(read(EVIDENCE/'before/browser-results.json')) == 16
assert len(read(EVIDENCE/'after/browser-results.json')) == 64
assert len(read(EVIDENCE/'edges/results.json')) == 4
assert all(r['passed'] for r in read(EVIDENCE/'edges/results.json'))
assert all(r['passed'] for r in read(EVIDENCE/'docker/results.json'))
assert '17 passed' in (EVIDENCE/'test-results.txt').read_text()
assert (EVIDENCE/'comparison-results.txt').read_text().startswith('PASS:')
for row in read(EVIDENCE/'deployment-verification.json'):
    if 'streamlit' not in row['Name']:
        assert row['ContainerIdUnchanged'] and row['StartedAtUnchanged']
for row in read(EVIDENCE/'runtime-source-verification.json'):
    assert hashlib.sha256((ROOT/'dashboard'/row['File']).read_bytes()).hexdigest() == row['Sha256']
before = read(EVIDENCE/'before-data.json')
after = read(EVIDENCE/'after-data.json')
old_kpis = {r[0]:r[1] for r in before['operations/3']['metrics']}
new_kpis = {r[0]:r[1] for r in after['operations/3']['metrics']}
labels = ['Nguồn đã phát','Spark đã xử lý','Fraud alerts','Alert rate','Ingest hiện tại',
          'Processing throughput','End-to-end latency p95']
table = ['| Metric | Trước | Sau | Kết quả |','|---|---:|---:|---|']
for label in labels:
    assert old_kpis[label] == new_kpis[label]
    table.append(f'| {label} | {old_kpis[label]} | {new_kpis[label]} | PASS |')
for key,name in [('model','Spark MLlib'),('rule','Rule Baseline')]:
    for metric in ['Precision','Recall','F1','Alert rate','TP','FP','TN','FN']:
        old = before['snapshot'][key][metric]
        new = after['snapshot'][key][metric]
        assert old == new
        display = lambda v: format(v,'.2%') if metric in ['Precision','Recall','F1','Alert rate'] else format(v,',')
        table.append(f'| {name} — {metric} | {display(old)} | {display(new)} | PASS |')
audit = read(EVIDENCE/'chart-data-audit.json')
assert audit['alerts_by_type_before'] == audit['alerts_by_type_after']
for kind,detector,count in audit['alerts_by_type_after']:
    table.append(f'| Alerts {kind} — {detector} | {count:,} | {count:,} | PASS |')
table.append(f"| Bản ghi scatter | {before['snapshot']['alerts']} | {after['snapshot']['alerts']} | PASS |")
doc = ROOT/'fraud-business-ui-improvements.md'
body = doc.read_text(encoding='utf-8')
body = re.sub(r'<!-- METRICS_START -->.*?<!-- METRICS_END -->',
              '<!-- METRICS_START -->\n'+'\n'.join(table)+'\n<!-- METRICS_END -->',body,flags=re.S)
doc.write_text(body,encoding='utf-8')
for path in [doc,EVIDENCE/'README.md']:
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        if not target.startswith(('http:','https:','#')):
            assert (path.parent/target).exists(),target
files = [p for p in EVIDENCE.rglob('*') if p.is_file() and p.name != 'artifact-manifest.json']+[doc]
manifest = {str(p.relative_to(ROOT)).replace('\\','/'):dict(bytes=p.stat().st_size,
    sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)}
(EVIDENCE/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(f'PASS: {len(manifest)} artifacts; syntax, correctness table, report links and deployed source verified')
