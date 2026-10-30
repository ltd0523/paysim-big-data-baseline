import sys
sys.path.insert(0, '/workspace/dashboard')
import copy
import streamlit as st
import dashboard_core as core
import view_operations as view
st.set_page_config(**view.PAGE_CONFIG)
view.setup()
s = copy.deepcopy(core.load_snapshot())
mode = st.query_params.get('mode','empty')
s.evaluation = {}
s.model = core.detector_metrics({}, 'model')
if mode == 'empty':
    s.aggregates = []
    s.recent_alerts = []
else:
    s.aggregates = [dict(type='CASH_OUT', model_alerts=0, rule_alerts=0)]
    s.recent_alerts = [dict(event_id=f'edge-{i}', type='TRANSFER', amount=amount, risk_score=.5)
        for i,amount in enumerate([0, -1, None, float('inf'), 10])]
view.render(s, core.PAGES[2])
