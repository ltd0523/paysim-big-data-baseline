"""Dump/compare all four views on the same real, read-only Mongo evidence snapshot."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
from unittest.mock import patch

from bson import json_util
from pymongo import MongoClient
from streamlit import dataframe_util
from streamlit.testing.v1 import AppTest

ROOT = Path('/workspace')
EVIDENCE = ROOT / 'dashboard_fraud_ui_evidence_20261030_142433'
OUT = Path('/tmp/paysim-fraud')
parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['before', 'after', 'compare'])
args = parser.parse_args()
sys.path.insert(0, str(EVIDENCE / 'before-source' if args.stage == 'before' else ROOT / 'dashboard'))
import dashboard_core as core


def frame_json(frame):
    return json.loads(frame.to_json(orient='split', date_format='iso', date_unit='ns', double_precision=15))


def dump():
    db = MongoClient('mongodb://mongodb:27017', tz_aware=True).paysim_ui_evidence_20261028_194420
    original = json_util.loads((ROOT / 'dashboard_evidence_20261028_194420/snapshot.json').read_text())
    normalize = lambda rows: sorted(json_util.dumps(r, sort_keys=True) for r in rows)
    for name, rows in original['collections'].items():
        assert normalize(list(db[name].find())) == normalize(rows), name
    result = {}
    with patch.object(core, 'get_database', return_value=db):
        snapshot = core.load_snapshot()
        result['snapshot'] = dict(run_id=snapshot.run_id, model=snapshot.model,
            rule=core.detector_metrics(snapshot.evaluation, 'rule'),
            metrics=len(snapshot.metrics), transactions=len(snapshot.recent_transactions),
            alerts=len(snapshot.recent_alerts), display_correct=snapshot.display_correct)
        for view in ['baseline', 'operations', 'report', 'studio']:
            source = 'from dashboard_core import render\n' + ('render()' if view == 'baseline'
                else f'import view_{view} as view\nrender(view)')
            app = AppTest.from_string(source, default_timeout=30).run()
            for i, page in enumerate(core.PAGES):
                if view == 'baseline': app.radio[0].set_value(page).run()
                elif view == 'report': app.selectbox[0].set_value(page).run()
                else: app.button_group[0].set_value([page]).run()
                assert not app.exception, app.exception
                metrics = sorted((m.label, m.value, m.delta) for m in app.metric
                                 if m.label not in {'Query latency', 'Snapshot response', 'Dashboard freshness'})
                charts = []
                for chart in app.get('arrow_vega_lite_chart'):
                    charts.append(dict(spec=json.loads(chart.proto.spec), frames=[
                        frame_json(dataframe_util.convert_arrow_bytes_to_pandas_df(ds.data.data))
                        for ds in chart.proto.datasets]))
                result[f'{view}/{i+1}'] = dict(metrics=metrics,
                    tables=[frame_json(t.value) for t in app.dataframe], charts=charts)
    (OUT / f'{args.stage}-data.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f'PASS {args.stage}: 16 view/page combinations; collections match original snapshot')


def compare():
    before = json.loads((OUT / 'before-data.json').read_text())
    after = json.loads((OUT / 'after-data.json').read_text())
    assert before['snapshot'] == after['snapshot']
    rows = []
    for key, old in before.items():
        if key == 'snapshot': continue
        new = after[key]
        assert old['metrics'] == new['metrics'], key
        assert old['tables'] == new['tables'], key
        if key != 'operations/3':
            assert old['charts'] == new['charts'], key
        rows.append(dict(view_page=key, metrics_equal=True, tables_equal=True,
                         chart_data_preserved=True, metrics=new['metrics']))
    old_fraud = before['operations/3']['charts']
    new_fraud = after['operations/3']['charts']
    assert len(old_fraud) == 3 and len(new_fraud) == 4
    records = lambda chart: [dict(zip(chart['frames'][0]['columns'], r)) for r in chart['frames'][0]['data']]
    matrix = lambda chart: sorted((r['Actual'],r['Predicted'],r['Count']) for r in records(chart))
    assert matrix(old_fraud[0]) == matrix(new_fraud[1])
    detector_names = {'model_alerts':'Spark MLlib', 'rule_alerts':'Rule Baseline'}
    old_alerts = sorted((r['type'],detector_names[r['Detector']],r['Alerts']) for r in records(old_fraud[1]))
    new_alerts = sorted((r['type'],r['Detector'],r['Alerts']) for r in records(new_fraud[2]))
    assert old_alerts == new_alerts
    assert old_fraud[2]['frames'] == new_fraud[3]['frames']
    assert len(records(new_fraud[3])) == after['snapshot']['alerts'] == 300
    assert new_fraud[3]['spec']['encoding']['x']['scale']['type'] == 'log'
    assert new_fraud[3]['spec']['encoding']['y']['scale']['domain'] == [0,1]
    expected_performance = sorted((name,metric,after['snapshot'][key][metric])
        for key,name in [('model','Spark MLlib'),('rule','Rule Baseline')]
        for metric in ['Precision','Recall','F1'])
    actual_performance = sorted((r['Detector'],r['Metric'],r['Value']) for r in records(new_fraud[0]))
    assert all(a[:2] == b[:2] and math.isclose(a[2],b[2],rel_tol=0,abs_tol=1e-14)
               for a,b in zip(actual_performance,expected_performance))
    assert len(actual_performance) == len(expected_performance) == 6
    invalid_amounts = [r['event_id'] for r in records(new_fraud[3])
        if not isinstance(r['amount'], (int,float)) or not math.isfinite(r['amount']) or r['amount'] <= 0]
    # Strip only the new hook, then compare the entire shared core AST.
    old_ast = ast.parse((EVIDENCE / 'before-source/dashboard_core.py').read_text())
    new_ast = ast.parse((ROOT / 'dashboard/dashboard_core.py').read_text())
    render = next(n for n in new_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'render_page')
    original_render = next(n for n in old_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'render_page')
    render.args.kwonlyargs.pop()
    render.args.kw_defaults.pop()
    render.body[0] = original_render.body[0]
    for node in ast.walk(render):
        if isinstance(node, ast.If):
            node.body[:] = [n for n in node.body if not (isinstance(n, ast.If) and
                isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name) and
                n.test.left.id == 'fraud_renderer')]
    assert ast.dump(old_ast) == ast.dump(new_ast), 'Unexpected core change'
    for name in ['app.py', 'view_report.py', 'view_studio.py', 'requirements.txt', 'Dockerfile', 'Banner.png']:
        assert (EVIDENCE / 'before-source' / name).read_bytes() == (ROOT / 'dashboard' / name).read_bytes()
    old_ops = ast.parse((EVIDENCE / 'before-source/view_operations.py').read_text())
    new_ops = ast.parse((ROOT / 'dashboard/view_operations.py').read_text())
    functions = lambda tree: {n.name:n for n in tree.body if isinstance(n, ast.FunctionDef)}
    old_funcs, new_funcs = functions(old_ops), functions(new_ops)
    for name, old_func in old_funcs.items():
        if name not in ['setup','render']:
            assert ast.dump(old_func) == ast.dump(new_funcs[name]), name
    for node in ast.walk(new_funcs['render']):
        if isinstance(node, ast.Call):
            node.keywords[:] = [k for k in node.keywords if k.arg != 'fraud_renderer']
    assert ast.dump(old_funcs['render']) == ast.dump(new_funcs['render'])
    markers = lambda path: [s for s in path.read_text().splitlines() if s.startswith(('# BEFORE ', '# AFTER '))]
    assert markers(EVIDENCE / 'before-source/view_operations.py') == markers(ROOT / 'dashboard/view_operations.py')
    # Browser metrics match the same before/after Operations page and viewport.
    old_browser = json.loads((OUT / 'before/browser-results.json').read_text())
    new_browser = json.loads((OUT / 'after/browser-results.json').read_text())
    assert len(old_browser) == 16 and len(new_browser) == 64
    labels = {'Nguồn đã phát', 'Spark đã xử lý', 'Fraud alerts', 'Alert rate',
              'Ingest hiện tại', 'Processing throughput', 'End-to-end latency p95'}
    for old in old_browser:
        new = next(r for r in new_browser if r['view'] == 'operations' and
                   r['page'] == old['page'] and r['viewport'] == old['viewport'])
        metrics = lambda r: sorted((m['label'], m['value'], m['delta']) for m in r['metrics'] if m['label'] in labels)
        assert metrics(old) == metrics(new)
        # Tracks repeats the canonical latency as a track metric as well.
        assert {m[0] for m in metrics(new)} == labels
    fingerprints = [json.loads((OUT / stage / 'database-fingerprints.json').read_text()) for stage in ['before', 'after']]
    assert all(f['unchanged'] for f in fingerprints) and fingerprints[0]['before'] == fingerprints[1]['after']
    report = dict(snapshot=after['snapshot'], pages=rows, browser_before=16, browser_after=64,
        business_logic_ast_unchanged=True, frozen_database_unchanged=True,
        other_views_chart_specs_and_data_identical=True,
        prior_operations_charts_identical=True, scatter_rows=300,
        invalid_log_amount_event_ids=invalid_amounts)
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (OUT / 'kpi-comparison.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    (OUT / 'confusion-matrix-comparison.json').write_text(json.dumps(dict(
        before=matrix(old_fraud[0]), after=matrix(new_fraud[1]), equal=True), indent=2))
    (OUT / 'chart-data-audit.json').write_text(json.dumps(dict(
        detector_metrics=expected_performance, alerts_by_type_before=old_alerts, alerts_by_type_after=new_alerts,
        scatter_input_equal=True, scatter_rows=300, invalid_log_amount_event_ids=invalid_amounts,
        prior_charts_and_other_views_identical=True), ensure_ascii=False, indent=2))
    print('PASS: 16 view/page pairs, all KPIs/tables, detector metrics, confusion counts, alerts, 300 scatter records, protected source/database')


if args.stage == 'compare': compare()
else: dump()
