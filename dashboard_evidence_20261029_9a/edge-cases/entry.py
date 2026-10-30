import sys
sys.path.insert(0, '/workspace/dashboard')
import streamlit as st
import dashboard_core as core
import view_operations as view
original = core.load_snapshot
def scenario_snapshot():
    s = original()
    if st.query_params.get('case') == 'large':
        s.latest_metric = {**s.latest_metric, 'latency_p95_ms':9876543210123}
        s.display_correct = False
        s.run_id = '<unsafe & run>'
    elif st.query_params.get('case') == 'empty':
        s.metrics = []
    return s
core.load_snapshot = scenario_snapshot
core.render(view)
