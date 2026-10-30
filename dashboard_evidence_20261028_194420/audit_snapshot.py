"""Audit actual frozen inputs and all four AppTest views; no fixture data."""
import hashlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from bson import json_util
from pymongo import MongoClient
from streamlit.testing.v1 import AppTest

ROOT = Path('/workspace')
OUT = Path('/evidence')
sys.path.insert(0, str(ROOT/'dashboard'))
import dashboard_core as core

client = MongoClient(os.environ['MONGO_URI'], tz_aware=True)
db = client[os.environ['MONGO_DATABASE']]
metadata = json_util.loads((OUT/'snapshot.json').read_text())
checks = {}
for name, rows in metadata['collections'].items():
    actual = list(db[name].find())
    normalize = lambda values: sorted(json_util.dumps(row, sort_keys=True) for row in values)
    checks[name] = {'expected': len(rows), 'actual': len(actual), 'documents_equal': normalize(rows) == normalize(actual)}
    assert checks[name]['documents_equal'], name

with patch.object(core, 'get_database', return_value=db):
    s = core.load_snapshot()
    assert s.display_correct
    assert s.aggregate_count == s.processed == s.latest_metric['processed_total']
    assert s.alerts_count == s.model['TP'] + s.model['FP']
    assert len(s.recent_transactions) == min(60, metadata['counts']['recent_transactions'])
    assert len(s.recent_alerts) == min(300, s.alerts_count)
    assert len(s.metrics) == min(60, metadata['counts']['pipeline_metrics'])
    labels = {'Nguồn đã phát', 'Spark đã xử lý', 'Fraud alerts', 'Ingest hiện tại',
              'Processing throughput', 'End-to-end latency p95'}
    results = []
    baseline = {}
    for view in ['baseline', 'operations', 'report', 'studio']:
        source = 'from dashboard_core import render\n' + (
            'render()' if view == 'baseline' else f'import view_{view} as view\nrender(view)')
        app = AppTest.from_string(source, default_timeout=30).run()
        assert not app.exception, str(app.exception)
        for page in core.PAGES:
            if view in ['baseline', 'operations']:
                app.radio[0].set_value(page).run()
            elif view == 'report':
                app.selectbox[0].set_value(page).run()
            else:
                app.button_group[0].set_value([page]).run()
            assert not app.exception, (view, page, str(app.exception))
            metrics = sorted((m.label, m.value, m.delta) for m in app.metric if m.label in labels)
            if view == 'baseline':
                baseline[page] = metrics
            assert metrics == baseline[page], (view, page, metrics)
            detail = {'view': view, 'page': page, 'six_kpis_equal_before': True,
                      'metrics': metrics, 'streamlit_exceptions': len(app.exception),
                      'tables': [{'rows': len(f.value), 'columns': list(f.value.columns)} for f in app.dataframe]}
            if page == core.PAGES[3]:
                table = next(f.value for f in app.dataframe if 'risk_score' in f.value.columns)
                expected = pd.DataFrame(s.recent_transactions)[table.columns]
                # Arrow uses UTC; PyMongo uses an equivalent BSON FixedOffset(0).
                expected['scored_at'] = pd.to_datetime(expected['scored_at'], utc=True)
                pd.testing.assert_frame_equal(table.reset_index(drop=True), expected.reset_index(drop=True))
                detail['all_60_transaction_values_equal_snapshot'] = True
            if page == core.PAGES[2]:
                table = next(f.value for f in app.dataframe if 'Detector' in f.value.columns)
                expected = []
                for key, name in [('rule', 'Spark SQL rule'), ('model', 'Spark MLlib')]:
                    values = core.detector_metrics(s.evaluation, key)
                    expected.append({'Detector': name, **{k: core.fmt_pct(v) if k in
                        ['Precision', 'Recall', 'F1', 'Alert rate'] else v for k, v in values.items()}})
                pd.testing.assert_frame_equal(table.reset_index(drop=True), pd.DataFrame(expected))
                detail['model_rule_metrics_and_confusion_totals_equal_snapshot'] = True
            results.append(detail)
    output = {'database': db.name, 'run_id': s.run_id, 'collections': checks,
              'display_correct': s.display_correct, 'canonical': {
                  'emitted': s.emitted, 'processed': s.processed, 'lag': s.lag, 'alerts': s.alerts_count,
                  'ingest_events_per_second': s.run['instant_emission_rate'],
                  'processing_events_per_second': s.latest_metric['processing_throughput'],
                  'latency_p95_ms': s.latest_metric['latency_p95_ms'],
                  'model': s.model, 'rule': core.detector_metrics(s.evaluation, 'rule'),
                  'transactions_loaded': len(s.recent_transactions), 'alerts_loaded': len(s.recent_alerts),
                  'micro_batches_loaded': len(s.metrics)}, 'pages': results,
              'source_hash_checks': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest
                  for name, digest in json.loads((OUT/'environment.json').read_text())['source_sha256'].items()}}
    # The user selected BEFORE in app.py concurrently. Capture imports each view
    # directly; preserve that selection and require every other source to match.
    output['routing_note'] = 'app.py changed externally from Operations to BEFORE during this session; preserved'
    output['data_logic_and_views_unchanged'] = all(ok for name, ok in output['source_hash_checks'].items()
                                                 if name != 'dashboard/app.py')
    assert output['data_logic_and_views_unchanged']
    (OUT/'snapshot-audit.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(output['canonical'], ensure_ascii=False, indent=2))
    print('PASS: 16 real-snapshot AppTest pages; 12/12 AFTER comparisons; exact transaction tables and detector totals')
