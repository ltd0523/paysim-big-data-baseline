"""UI equivalence on a deterministic Mongo fixture (not a pipeline E2E test)."""
import sys
import copy
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

import mongomock
import pytest
from streamlit.testing.v1 import AppTest
from streamlit import dataframe_util

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dashboard'))
import dashboard_core


def fixture_database():
    db = mongomock.MongoClient(tz_aware=True).paysim
    now = datetime(2026, 10, 23, tzinfo=timezone.utc)
    db.runs.insert_one(dict(run_id='ui-test', started_at=now, status='completed', events_emitted=100,
                            instant_emission_rate=50, source_progress_pct=.5, source_row=100, dataset_rows=200))
    db.evaluation_totals.insert_one(dict(_id='ui-test', processed=100, updated_at=now,
        model=dict(tp=1, fp=1, tn=97, fn=1), rule=dict(tp=1, fp=0, tn=98, fn=1)))
    for i in range(3):
        db.pipeline_metrics.insert_one(dict(run_id='ui-test', batch_id=i, created_at=now,
            processing_throughput=25+i, ingest_throughput=50, consumer_lag=0,
            ingest_latency_p95_ms=10, latency_p95_ms=500+i, batch_duration_seconds=2+i,
            processed_rows=100, input_rows=100, aggregate_correctness=True, transformation_correctness=True))
    db.live_aggregates.insert_one(dict(run_id='ui-test', type='TRANSFER', transactions=100,
                                     model_alerts=2, rule_alerts=1, total_amount=15000))
    for i in range(2):
        row=dict(run_id='ui-test', event_id=f'e{i}', scored_at=now, type='TRANSFER', amount=100+i,
                 risk_score=.8, prediction=1, source_cycle=1, source_row=i, end_to_end_latency_ms=500)
        db.fraud_alerts.insert_one(row.copy()); db.recent_transactions.insert_one(row.copy())
    return db


def app_source(view):
    return ('from dashboard_core import render\n' +
            ('render()' if view == 'baseline' else f'import view_{view} as view\nrender(view)'))


def metrics(at):
    # Timing of the UI query and wall-clock freshness are not business results.
    exclude = {'Query latency', 'Snapshot response', 'Dashboard freshness'}
    # Operations shows alert rate as a peer KPI instead of the Fraud alerts delta.
    alert_rate = next((m.value for m in at.metric if m.label == 'Alert rate'), None)
    return sorted((m.label, m.value,
                   alert_rate if m.label == 'Fraud alerts' and alert_rate is not None else m.delta)
                  for m in at.metric if m.label not in exclude)


@pytest.mark.parametrize('view', ['operations', 'report', 'studio'])
def test_all_four_pages_preserve_six_run_metrics(view):
    db = fixture_database()
    with patch.object(dashboard_core, 'get_database', return_value=db):
        before = AppTest.from_string(app_source('baseline')).run()
        after = AppTest.from_string(app_source(view)).run()
        assert not before.exception and not after.exception
        pages = before.radio[0].options
        for page in pages:
            before.radio[0].set_value(page).run()
            # The view switch stays active on the same fragment rerun path.
            if view == 'report': after.selectbox[0].set_value(page).run()
            else: after.button_group[0].set_value([page]).run()
            assert not before.exception and not after.exception
            labels = {'Nguồn đã phát','Spark đã xử lý','Fraud alerts','Ingest hiện tại',
                      'Processing throughput','End-to-end latency p95'}
            expected = [m for m in metrics(before) if m[0] in labels]
            actual = [m for m in metrics(after) if m[0] in labels]
            assert expected == actual
            # Core pages can be rearranged or enriched; six canonical run values stay identical.
            assert {m[0] for m in actual} == labels



@pytest.mark.parametrize('view', ['baseline', 'operations', 'report', 'studio'])
def test_empty_database_displays_waiting_message(view):
    db = mongomock.MongoClient().paysim
    with patch.object(dashboard_core, 'get_database', return_value=db):
        app = AppTest.from_string(app_source(view)).run()
        assert not app.exception
        assert 'Pipeline đang chuẩn bị' in app.info[0].value


def chart_payloads(app):
    return [(json.loads(c.proto.spec),
             [dataframe_util.convert_arrow_bytes_to_pandas_df(ds.data.data) for ds in c.proto.datasets])
            for c in app.get('arrow_vega_lite_chart')]


@pytest.mark.parametrize('batch_count', [0, 1, 60])
def test_operations_telemetry_charts_preserve_values_and_handle_backlog(batch_count):
    from datetime import timedelta
    db = fixture_database()
    with patch.object(dashboard_core, 'get_database', return_value=db):
        snapshot = dashboard_core.load_snapshot()
    # Deliberately reverse IDs and separate timestamps: ordinal sorting must be numeric.
    template = snapshot.metrics[0]
    snapshot.metrics = [dict(template, batch_id=i,
        created_at=template['created_at'] + timedelta(seconds=i),
        batch_duration_seconds=i + .125, ingest_latency_p95_ms=i + .5,
        latency_p95_ms=1e12 + i) for i in reversed(range(batch_count))]
    # Keep an incomplete telemetry row; the shared time domain must still include it.
    if batch_count > 1:
        snapshot.metrics[0]['ingest_latency_p95_ms'] = None
    original = copy.deepcopy(snapshot.metrics)
    with patch.object(dashboard_core, 'load_snapshot', return_value=snapshot):
        app = AppTest.from_string(app_source('operations')).run()
    assert not app.exception
    assert snapshot.metrics == original
    charts = chart_payloads(app)
    if not batch_count:
        assert not charts
        assert len(app.info) >= 4
        return
    assert len(charts) == 5
    ingest, e2e, duration = charts[2:]
    for (spec, frames), field, color in [
        (ingest, 'ingest_latency_p95_ms', '#0284C7'),
        (e2e, 'latency_p95_ms', '#E11D48'),
    ]:
        assert spec['mark']['type'] == 'line'
        assert spec['height'] == 220
        assert spec['encoding']['color']['scale']['range'] == [color]
        assert 'domain' not in spec['encoding']['y'].get('scale', {})
        assert frames[0]['Value'].dropna().tolist() == [r[field] for r in original if r[field] is not None]
        assert set(frames[0]['Unit']) == {'ms'}
    assert ingest[0]['encoding']['x']['scale'] == e2e[0]['encoding']['x']['scale']
    spec, frames = duration
    assert spec['mark'] == {'type': 'bar', 'color': '#2563EB'}
    assert spec['encoding']['x']['field'] == 'batch_id'
    assert spec['encoding']['x']['sort'] == 'ascending'
    assert spec['encoding']['y']['scale']['zero'] is True
    assert frames[0]['batch_duration_seconds'].tolist() == [r['batch_duration_seconds'] for r in original]
    assert {t['field'] for t in spec['encoding']['tooltip']} == {'batch_id', 'created_at', 'batch_duration_seconds'}
    # History retains the original descending order and all rows.
    assert app.dataframe[0].value['batch_id'].tolist() == sorted((r['batch_id'] for r in original), reverse=True)


@pytest.mark.parametrize('view', ['baseline', 'operations', 'report', 'studio'])
def test_transaction_renderer_is_scoped_to_operations_and_ranks_by_count(view):
    db = fixture_database()
    db.live_aggregates.delete_many({})
    for kind, count, amount in [('CASH_OUT', 30, 1), ('PAYMENT', 5, 999999), ('DEBIT', 0, 0)]:
        db.live_aggregates.insert_one(dict(run_id='ui-test', type=kind, transactions=count,
            total_amount=amount, model_alerts=0, rule_alerts=0))
    with patch.object(dashboard_core, 'get_database', return_value=db):
        app = AppTest.from_string(app_source(view)).run()
        if view == 'baseline': app.radio[0].set_value(dashboard_core.PAGES[3]).run()
        elif view == 'report': app.selectbox[0].set_value(dashboard_core.PAGES[3]).run()
        else: app.button_group[0].set_value([dashboard_core.PAGES[3]]).run()
    assert not app.exception
    spec, frames = next((spec, frames) for spec, frames in chart_payloads(app)
                        if frames and 'transactions' in frames[0])
    counts_by_type = dict(zip(frames[0]['type'], frames[0]['transactions']))
    assert counts_by_type == {'CASH_OUT': 30, 'PAYMENT': 5, 'DEBIT': 0}
    if view == 'operations':
        assert frames[0]['type'].tolist() == ['CASH_OUT', 'PAYMENT', 'DEBIT']
        assert frames[0]['total_amount'].tolist() == [1, 999999, 0]
        bars, counts = spec['layer']
        assert bars['mark'] == {'type': 'bar', 'color': '#2563EB'}
        assert bars['encoding']['y']['sort'] == {'field': 'transactions', 'order': 'descending'}
        assert bars['encoding']['x']['field'] == 'transactions'
        assert counts['encoding']['text']['field'] == 'transactions'
        assert {t['field'] for t in bars['encoding']['tooltip']} == {'type', 'transactions', 'total_amount'}
    elif view == 'studio':
        # Studio already owns this page and uses a vertical bar (no core Donut).
        assert spec['mark']['type'] == 'bar'
        assert spec['encoding']['y']['field'] == 'transactions'
    else:
        assert spec['mark']['type'] == 'arc'


def test_fraud_renderer_preserves_snapshot_and_all_chart_values():
    import pandas as pd
    db = fixture_database()
    db.evaluation_totals.update_one({'_id':'ui-test'}, {'$set': {
        'model':dict(tp=1, fp=9999, tn=20000, fn=3),
        'rule':dict(tp=0, fp=0, tn=30000, fn=3)}})
    db.live_aggregates.insert_one(dict(run_id='ui-test', type='PAYMENT', transactions=20,
                                     model_alerts=10, rule_alerts=0, total_amount=1))
    with patch.object(dashboard_core, 'get_database', return_value=db):
        snapshot = dashboard_core.load_snapshot()
    original = copy.deepcopy(vars(snapshot))
    with patch.object(dashboard_core, 'load_snapshot', return_value=snapshot):
        app = AppTest.from_string(app_source('operations')).run()
        app.button_group[0].set_value([dashboard_core.PAGES[2]]).run()
    assert not app.exception
    assert vars(snapshot) == original
    performance, matrix, alerts, scatter = chart_payloads(app)
    spec, frames = performance
    expected = {(name, metric): dashboard_core.detector_metrics(snapshot.evaluation, key)[metric]
        for key, name in [('model','Spark MLlib'), ('rule','Rule Baseline')]
        for metric in ['Precision','Recall','F1']}
    assert {(r.Detector,r.Metric):r.Value for r in frames[0].itertuples()} == expected
    bars, labels = spec['layer']
    assert bars['encoding']['x']['scale']['domain'] == [0,1]
    assert bars['encoding']['y']['sort'] == ['Precision','Recall','F1']
    assert labels['encoding']['text']['format'] == '.2%'
    assert bars['encoding']['color']['scale'] == {
        'domain':['Spark MLlib','Rule Baseline'], 'range':['#2563EB','#0F766E']}
    table = app.dataframe[0].value
    for key, name in [('rule','Spark SQL rule'), ('model','Spark MLlib')]:
        values = dashboard_core.detector_metrics(snapshot.evaluation, key)
        row = table[table['Detector'] == name].iloc[0]
        for metric, value in values.items():
            assert row[metric] == (dashboard_core.fmt_pct(value) if metric in
                ['Precision','Recall','F1','Alert rate'] else value)
    spec, frames = matrix
    assert {(r.Actual,r.Predicted):r.Count for r in frames[0].itertuples()} == {
        ('Fraud','Fraud'):snapshot.model['TP'], ('Fraud','Legitimate'):snapshot.model['FN'],
        ('Legitimate','Fraud'):snapshot.model['FP'], ('Legitimate','Legitimate'):snapshot.model['TN']}
    assert set(frames[0]['Cell']) == {'TP','FN','FP','TN'}
    assert spec['layer'][1]['encoding']['color']['value'] == '#0F172A'
    assert spec['layer'][1]['encoding']['color']['condition']['value'] == '#FFFFFF'
    spec, frames = alerts
    assert {(r.type,r.Detector):r.Alerts for r in frames[0].itertuples()} == {
        (r['type'],name):r[field] for r in snapshot.aggregates
        for field,name in [('model_alerts','Spark MLlib'),('rule_alerts','Rule Baseline')]}
    assert spec['layer'][0]['encoding']['y']['sort'] == ['PAYMENT','TRANSFER']
    assert spec['layer'][0]['encoding']['x']['scale']['zero'] is True
    spec, frames = scatter
    # Arrow normalizes equivalent UTC timezone implementations during transport.
    pd.testing.assert_frame_equal(frames[0], pd.DataFrame(snapshot.recent_alerts), check_dtype=False)
    assert spec['encoding']['x']['scale']['type'] == 'log'
    assert spec['encoding']['y']['scale']['domain'] == [0,1]
    assert spec['mark']['opacity'] == .65
    assert {t['field'] for t in spec['encoding']['tooltip']} == {'event_id','type','amount','risk_score'}
    assert spec['encoding']['color']['scale']['domain'] == ['CASH_OUT','PAYMENT','CASH_IN','TRANSFER','DEBIT']


@pytest.mark.parametrize('amounts', [[], [0, -1, None, float('inf'), 10]])
def test_fraud_empty_counts_and_invalid_log_amounts_are_reported_without_filtering(amounts):
    db = fixture_database()
    with patch.object(dashboard_core, 'get_database', return_value=db):
        snapshot = dashboard_core.load_snapshot()
    snapshot.evaluation = {}
    snapshot.model = dashboard_core.detector_metrics({}, 'model')
    snapshot.aggregates = []
    snapshot.recent_alerts = [dict(event_id=f'edge-{i}', type='TRANSFER', amount=amount, risk_score=.5)
                              for i, amount in enumerate(amounts)]
    original = copy.deepcopy(vars(snapshot))
    with patch.object(dashboard_core, 'load_snapshot', return_value=snapshot):
        app = AppTest.from_string(app_source('operations')).run()
        app.button_group[0].set_value([dashboard_core.PAGES[2]]).run()
    assert not app.exception and vars(snapshot) == original
    charts = chart_payloads(app)
    assert len(charts) == (3 if amounts else 2)
    if amounts:
        assert '4 alerts' in app.warning[0].value
        assert len(charts[-1][1][0]) == len(amounts)
    else:
        assert not app.warning
    assert set(charts[0][1][0]['Value']) == {0}
    assert set(charts[1][1][0]['Count']) == {0}
