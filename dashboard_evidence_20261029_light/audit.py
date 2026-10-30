"""Compare every table/chart dataset and run KPI before/after on frozen evidence."""
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
OUT = Path('/tmp/paysim-light')
sys.path.insert(0, str(ROOT / 'dashboard'))
import dashboard_core as core

db = MongoClient('mongodb://mongodb:27017', tz_aware=True).paysim_ui_evidence_20261028_194420
metadata = json_util.loads((ROOT / 'dashboard_evidence_20261028_194420/snapshot.json').read_text())
normalize = lambda rows: sorted(json_util.dumps(r, sort_keys=True) for r in rows)
collections = {}
for name, rows in metadata['collections'].items():
    assert normalize(list(db[name].find())) == normalize(rows), name
    collections[name] = {'equal_original_snapshot': True, 'count': len(rows)}

old_source = '''import importlib.util
from dashboard_core import render
spec = importlib.util.spec_from_file_location('operations_before',
    '/workspace/dashboard_evidence_20261029_light/view_operations.before.py')
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)
render(view)
'''
new_source = 'from dashboard_core import render\nimport view_operations as view\nrender(view)'
labels = {'Nguồn đã phát', 'Spark đã xử lý', 'Fraud alerts', 'Alert rate',
          'Ingest hiện tại', 'Processing throughput', 'End-to-end latency p95'}


def charts(app):
    return [(json.loads(c.proto.spec),
        [dataframe_util.convert_arrow_bytes_to_pandas_df(ds.data.data) for ds in c.proto.datasets])
        for c in app.get('arrow_vega_lite_chart')]


results = []
with patch.object(core, 'get_database', return_value=db):
    snapshot = core.load_snapshot()
    before = AppTest.from_string(old_source, default_timeout=30).run()
    after = AppTest.from_string(new_source, default_timeout=30).run()
    for page in core.PAGES:
        before.radio[0].set_value(page).run()
        after.button_group[0].set_value([page]).run()
        assert not before.exception and not after.exception
        assert after.session_state['dashboard_page'] == page
        metrics = lambda app: sorted((m.label, m.value, m.delta) for m in app.metric if m.label in labels)
        assert metrics(before) == metrics(after)
        assert {m[0] for m in metrics(after)} == labels
        assert len(before.dataframe) == len(after.dataframe)
        for old, new in zip(before.dataframe, after.dataframe):
            pd.testing.assert_frame_equal(old.value, new.value)
        old_charts, new_charts = charts(before), charts(after)
        assert len(old_charts) == len(new_charts)
        for (old_spec, old_frames), (new_spec, new_frames) in zip(old_charts, new_charts):
            assert len(old_frames) == len(new_frames)
            for old, new in zip(old_frames, new_frames):
                pd.testing.assert_frame_equal(old, new)
            if page == core.PAGES[0]:
                # Only chart palette, background, fonts and axis/grid styling may differ.
                old_spec.pop('config', None)
                new_spec.pop('config', None)
                old_spec['encoding']['color']['scale'].pop('range')
                new_spec['encoding']['color']['scale'].pop('range')
            assert old_spec == new_spec, 'Chart semantics changed'
        # Deselecting a native pill must preserve the selected page and data.
        after.button_group[0].set_value([]).run()
        assert after.session_state['dashboard_page'] == page
        assert metrics(before) == metrics(after)
        assert not after.exception
        results.append({'page': page, 'seven_kpis_and_deltas_equal': True,
                        'all_tables_equal': True, 'all_chart_datasets_equal': True,
                        'chart_semantics_equal': True, 'selection_retained_on_deselect': True,
                        'metrics': metrics(after)})

    colors = [['#2563EB', '#0F766E'], ['#B45309'], ['#7C3AED', '#C2410C'], ['#475569']]
    after.button_group[0].set_value([core.PAGES[0]]).run()
    for (spec, _), expected in zip(charts(after), colors):
        assert spec['config']['background'] == '#FFFFFF'
        assert spec['encoding']['color']['scale']['range'] == expected
    assert len(after.dataframe[0].value) == len(snapshot.metrics) == 13
    assert len(snapshot.recent_alerts) == 300
    assert len(snapshot.recent_transactions) == 60

report = {'run_id': snapshot.run_id, 'status': snapshot.status, 'pages': results,
          'collections': collections, 'refresh_seconds': 2.0,
          'protected_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [ROOT / 'dashboard' / n for n in
                        ['dashboard_core.py', 'app.py', 'view_report.py', 'view_studio.py', 'requirements.txt']]}}
(OUT / 'data-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print('PASS: original frozen collections, 7 KPIs on all 4 pages, every table/chart dataset, '
      'chart semantics, 300 alerts, 60 transactions, 13 batches, option menu state')
