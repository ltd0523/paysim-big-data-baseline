"""Read-only comparison of original 9A and the new UI on the same real snapshot."""
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

from bson import json_util
import pandas as pd
from pymongo import MongoClient
from streamlit import dataframe_util
from streamlit.testing.v1 import AppTest

ROOT = Path('/workspace')
OUT = Path('/tmp/paysim9a')
sys.path.insert(0, str(ROOT/'dashboard'))
import dashboard_core as core

db = MongoClient('mongodb://mongodb:27017', tz_aware=True).paysim_ui_evidence_20261028_194420
metadata = json_util.loads((ROOT/'dashboard_evidence_20261028_194420/snapshot.json').read_text())
collections = {}
for name, rows in metadata['collections'].items():
    normalize = lambda values: sorted(json_util.dumps(row, sort_keys=True) for row in values)
    assert normalize(list(db[name].find())) == normalize(rows), name
    collections[name] = {'documents_equal_original_snapshot': True, 'count':len(rows)}

old_source = """import importlib.util
from dashboard_core import render
spec = importlib.util.spec_from_file_location('operations_before',
    '/workspace/dashboard_evidence_20261029_9a/view_operations.before.py')
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)
render(view)
"""
new_source = 'from dashboard_core import render\nimport view_operations as view\nrender(view)'
labels = {'Nguồn đã phát', 'Spark đã xử lý', 'Fraud alerts', 'Ingest hiện tại',
          'Processing throughput', 'End-to-end latency p95'}
results = []


def charts(app):
    return [(json.loads(chart.proto.spec),
             [dataframe_util.convert_arrow_bytes_to_pandas_df(ds.data.data) for ds in chart.proto.datasets])
            for chart in app.get('arrow_vega_lite_chart')]


def normalize_frame(frame):
    frame = frame.copy().reset_index(drop=True)
    for col in frame.select_dtypes(include=['datetimetz']):
        frame[col] = pd.to_datetime(frame[col], utc=True)
    return frame


with patch.object(core, 'get_database', return_value=db):
    snapshot = core.load_snapshot()
    before = AppTest.from_string(old_source, default_timeout=30).run()
    after = AppTest.from_string(new_source, default_timeout=30).run()
    for page in core.PAGES:
        before.radio[0].set_value(page).run()
        after.radio[0].set_value(page).run()
        assert not before.exception and not after.exception
        metrics = lambda app: sorted((m.label,m.value,m.delta) for m in app.metric if m.label in labels)
        assert metrics(before) == metrics(after)
        assert {m[0] for m in metrics(after)} == labels
        assert len(before.dataframe) == len(after.dataframe)
        for old, new in zip(before.dataframe, after.dataframe):
            pd.testing.assert_frame_equal(normalize_frame(old.value), normalize_frame(new.value))
        old_charts, new_charts = charts(before), charts(after)
        assert len(old_charts) == len(new_charts)
        for (old_spec, old_frames), (new_spec, new_frames) in zip(old_charts,new_charts):
            assert len(old_frames) == len(new_frames)
            for old, new in zip(old_frames,new_frames):
                # Unit is a tooltip-only addition; all original series and values must match.
                pd.testing.assert_frame_equal(normalize_frame(old),normalize_frame(new[old.columns]))
            if page != core.PAGES[0]:
                assert old_spec == new_spec, 'Core chart payload changed'
        if page == core.PAGES[0]:
            expected_colors = [['#38BDF8','#34D399'],['#FBBF24'],['#A78BFA','#FB923C'],['#BAC8D8']]
            for (spec,_),colors in zip(new_charts,expected_colors):
                assert spec['encoding']['color']['scale']['range'] == colors
                assert len(spec['encoding']['tooltip']) == 4
            assert len(after.dataframe[0].value) == len(snapshot.metrics)
        if page == core.PAGES[2]:
            frames = [f for _,items in new_charts for f in items]
            scatter = next(f for f in frames if {'event_id','amount','risk_score'} <= set(f.columns))
            pd.testing.assert_frame_equal(normalize_frame(scatter),normalize_frame(pd.DataFrame(snapshot.recent_alerts)))
            matrix = next(f for f in frames if {'Actual','Predicted','Count'} <= set(f.columns))
            assert {(r.Actual,r.Predicted):r.Count for r in matrix.itertuples()} == {
                ('Fraud','Fraud'):snapshot.model['TP'],('Fraud','Legitimate'):snapshot.model['FN'],
                ('Legitimate','Fraud'):snapshot.model['FP'],('Legitimate','Legitimate'):snapshot.model['TN']}
        if page == core.PAGES[3]:
            expected = pd.DataFrame(snapshot.recent_transactions)[after.dataframe[0].value.columns]
            pd.testing.assert_frame_equal(normalize_frame(after.dataframe[0].value), normalize_frame(expected))
        results.append({'page':page,'six_kpis_and_deltas_equal':True,
                        'all_table_values_equal':True,'all_chart_data_values_equal':True,
                        'core_chart_specs_unchanged':page!=core.PAGES[0], 'metrics':metrics(after)})
    # Presentation edge cases use a copy in memory, never write the evidence database.
    snapshot.metrics = []
    with patch.object(core, 'load_snapshot', return_value=snapshot):
        empty = AppTest.from_string(new_source).run()
        assert not empty.exception and len(empty.info) == 4
        assert not empty.get('arrow_vega_lite_chart') and not empty.dataframe
        snapshot.latest_metric = {**snapshot.latest_metric, 'latency_p95_ms':9_876_543_210_123}
        large = AppTest.from_string(new_source).run()
        assert not large.exception
        assert next(m.value for m in large.metric if m.label=='End-to-end latency p95') == '9,876,543,210,123 ms'
    snapshot.status = '<unsafe & status>'
    snapshot.run_id = '<unsafe & run>'
    with patch.object(core, 'load_snapshot', return_value=snapshot):
        escaped = AppTest.from_string(new_source).run()
        assert not escaped.exception
        header = next(m.value for m in escaped.markdown if 'ops-header' in m.value and '<h1>' in m.value)
        assert '&lt;unsafe &amp; run&gt;' in header and '<unsafe & run>' not in header

hashes = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
          ['dashboard/dashboard_core.py','dashboard/app.py','tests/test_dashboard.py']}
initial = json.loads((ROOT/'dashboard_evidence_20261029_9a/source-before.json').read_text(encoding='utf-8-sig'))
for row in initial:
    name = row['Path'].replace('\\','/').split('/paysim-big-data-baseline/')[-1]
    if name in hashes:
        assert hashes[name] == row['Hash'].lower(), name
output = {'database':db.name, 'collections':collections, 'pages':results,
          'empty_telemetry_waits_without_fake_charts':True,'large_latency_value_preserved':True,
          'header_html_escaped':True, 'protected_source_sha256':hashes,
          'limits':{'transactions':len(snapshot.recent_transactions),'alerts':len(snapshot.recent_alerts),
                    'micro_batches_in_original_snapshot':len(metadata['collections']['pipeline_metrics'])}}
(OUT/'data-audit.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
print('PASS: four original/new 9A pages; six KPI/deltas, all tables and chart data identical; core chart specs unchanged')
print('PASS: exact 300-alert payload, 60 transactions, confusion matrix, empty telemetry, large latency, escaped metadata')
