"""Inspect rendered chart payloads and Studio record selection on real evidence."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pymongo import MongoClient
from streamlit import dataframe_util
from streamlit.testing.v1 import AppTest

sys.path.insert(0, '/workspace/dashboard')
import dashboard_core as core

out = Path('/evidence')
db = MongoClient(os.environ['MONGO_URI'], tz_aware=True)[os.environ['MONGO_DATABASE']]
results = []
with patch.object(core, 'get_database', return_value=db):
    s = core.load_snapshot()
    for view in ['baseline', 'operations', 'report', 'studio']:
        source = 'from dashboard_core import render\n' + ('render()' if view == 'baseline'
                  else f'import view_{view} as view\nrender(view)')
        app = AppTest.from_string(source).run()
        if view in ['baseline', 'operations']:
            app.radio[0].set_value(core.PAGES[2]).run()
        elif view == 'report':
            app.selectbox[0].set_value(core.PAGES[2]).run()
        else:
            app.button_group[0].set_value([core.PAGES[2]]).run()
        assert not app.exception
        frames = []
        for chart in app.get('arrow_vega_lite_chart'):
            for dataset in chart.proto.datasets:
                frames.append(dataframe_util.convert_arrow_bytes_to_pandas_df(dataset.data.data))
        scatter = next(f for f in frames if {'event_id','risk_score','amount'}.issubset(f.columns))
        expected = pd.DataFrame(s.recent_alerts)
        pd.testing.assert_frame_equal(scatter[['event_id','risk_score','amount','type']].reset_index(drop=True),
                                      expected[['event_id','risk_score','amount','type']].reset_index(drop=True))
        matrix = next(f for f in frames if {'Actual','Predicted','Count'}.issubset(f.columns))
        observed = {(r.Actual, r.Predicted): int(r.Count) for r in matrix.itertuples()}
        assert observed == {('Fraud','Fraud'): s.model['TP'], ('Fraud','Legitimate'): s.model['FN'],
                            ('Legitimate','Fraud'): s.model['FP'], ('Legitimate','Legitimate'): s.model['TN']}
        results.append({'view':view, 'all_300_alert_scatter_values_equal_snapshot':True,
                        'confusion_matrix_rendered_values_equal_snapshot':True})
    app = AppTest.from_string('from dashboard_core import render\nimport view_studio as view\nrender(view)').run()
    selections = []
    for index in [0, 59]:
        # AppTest 1.50 needs explicit segmented selection before serializing
        # another widget; otherwise the default icon proto is treated as value.
        app.button_group[0].set_value([core.PAGES[3]])
        app.selectbox[0].set_value(index).run()
        assert not app.exception and app.selectbox[0].value == index
        expected = s.recent_transactions[index]
        assert f"## {core.fmt_float(expected.get('amount'),2)}" in [m.value for m in app.markdown]
        assert f"Scored at: {expected.get('scored_at','—')}" in [c.value for c in app.caption]
        selections.append({'index': index, 'event_id': expected['event_id'], 'amount_and_scored_at_equal_snapshot':True})
    (out/'visual-data-audit.json').write_text(json.dumps({'fraud_pages':results, 'studio_selections':selections},
                                                        ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS: exact 300-alert scatter and four-cell confusion payloads in all 4 UIs; Studio first/last selection')
