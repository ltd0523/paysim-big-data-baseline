import sys
sys.path.insert(0, '/workspace/dashboard')
import copy
import streamlit as st
import dashboard_core as core
import view_operations as view
st.set_page_config(**view.PAGE_CONFIG)
view.setup()
s = copy.deepcopy(core.load_snapshot())
mode = st.query_params.get('mode', 'one')
if mode == 'empty':
    s.metrics = []
    s.aggregates = []
else:
    s.metrics = s.metrics[:1]
    s.metrics[0]['latency_p95_ms'] = 1e12
    s.metrics[0]['ingest_latency_p95_ms'] = .125
    s.metrics[0]['batch_duration_seconds'] = .001
view.render(s, core.PAGES[0])
st.subheader('Edge distribution')
import pandas as pd
view.transaction_distribution(pd.DataFrame(s.aggregates))
