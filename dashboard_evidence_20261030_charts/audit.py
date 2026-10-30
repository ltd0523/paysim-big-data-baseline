"""Dump/compare all four views on the same real, read-only Mongo evidence snapshot."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

from bson import json_util
from pymongo import MongoClient
from streamlit import dataframe_util
from streamlit.testing.v1 import AppTest

ROOT = Path('/workspace')
EVIDENCE = ROOT / 'dashboard_evidence_20261030_charts'
OUT = Path('/tmp/paysim-charts')
parser = argparse.ArgumentParser()
parser.add_argument('stage', choices=['before', 'after', 'compare'])
args = parser.parse_args()
sys.path.insert(0, str(EVIDENCE / 'before-source' if args.stage == 'before' else ROOT / 'dashboard'))
import dashboard_core as core


def frame_json(frame):
    return json.loads(frame.to_json(orient='split', date_format='iso', date_unit='ns'))


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
        if key not in ['operations/1', 'operations/4']:
            assert old['charts'] == new['charts'], key
        if key == 'operations/4':
            assert old['charts'][0]['frames'] == new['charts'][0]['frames']
        if key == 'operations/1':
            assert len(old['charts']) == 4 and len(new['charts']) == 5
            assert old['charts'][0]['frames'] == new['charts'][0]['frames']
            assert old['charts'][1]['frames'] == new['charts'][1]['frames']
            latency = old['charts'][2]['frames'][0]
            for index, label in [(2, 'Ingest p95'), (3, 'End-to-end p95')]:
                expected = [r for r in latency['data'] if r[1] == label]
                assert expected == new['charts'][index]['frames'][0]['data']
            old_duration = old['charts'][3]['frames'][0]
            duration = new['charts'][4]['frames'][0]
            pos = duration['columns'].index('batch_duration_seconds')
            assert [r[2] for r in old_duration['data']] == [r[pos] for r in duration['data']]
        rows.append(dict(view_page=key, metrics_equal=True, tables_equal=True,
                         chart_data_preserved=True, metrics=new['metrics']))
    # The extension is the only change allowed to the shared core.
    old_ast = ast.parse((EVIDENCE / 'before-source/dashboard_core.py').read_text())
    new_ast = ast.parse((ROOT / 'dashboard/dashboard_core.py').read_text())
    render = next(n for n in new_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'render_page')
    render.args.kwonlyargs.clear()
    render.args.kw_defaults.clear()
    render.body.pop(0)  # New API docstring.
    for node in ast.walk(render):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == 'aggregates':
            node.body[:] = [n for n in node.body if not (isinstance(n, ast.If) and
                isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name) and
                n.test.left.id == 'transaction_renderer')]
    assert ast.dump(old_ast) == ast.dump(new_ast), 'Unexpected core change'
    for name in ['app.py', 'view_report.py', 'view_studio.py', 'requirements.txt']:
        assert (EVIDENCE / 'before-source' / name).read_bytes() == (ROOT / 'dashboard' / name).read_bytes()
    markers = lambda path: [s for s in path.read_text().splitlines() if s.startswith(('# BEFORE ', '# AFTER '))]
    assert markers(EVIDENCE / 'before-source/view_operations.py') == markers(ROOT / 'dashboard/view_operations.py')
    # Browser metrics match the same before/after Operations page and viewport.
    old_browser = json.loads((OUT / 'before/browser-results.json').read_text())
    new_browser = json.loads((OUT / 'after/browser-results.json').read_text())
    assert len(old_browser) == 12 and len(new_browser) == 48
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
    report = dict(snapshot=after['snapshot'], pages=rows, browser_before=12, browser_after=48,
        business_logic_ast_unchanged=True, frozen_database_unchanged=True,
        other_views_chart_specs_and_data_identical=True,
        studio_note='Existing custom transaction page uses a vertical bar, not a donut; preserved unchanged.')
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('PASS: 16 view/page pairs, all KPIs/tables, model/rule metrics, chart datasets, protected source and database')


if args.stage == 'compare': compare()
else: dump()
