"""9A — Trung tâm vận hành. Năm vùng AFTER chỉ thay cách trình bày."""
import altair as alt
import pandas as pd
import streamlit as st
from html import escape
from dashboard_core import PAGES, fmt_int, fmt_float, fmt_pct, render_page

PAGE_CONFIG = dict(page_title="PaySim | Operations", layout="wide", initial_sidebar_state="expanded")

# BEFORE Start — 9A.1
# Tiêu đề lớn + sidebar System UIs của dashboard gốc.
# BEFORE END — 9A.1
# AFTER Start — 9A.1: khung điều hành tối, thanh điều hướng dọc.
def setup():
    st.markdown('''<style>
    [data-testid="stAppViewContainer"] {
        --ops-bg:#0B1220; --ops-sidebar:#142237; --ops-surface:#1B2B40;
        --ops-border:#304258; --ops-accent:#38BDF8; --ops-success:#34D399;
        --ops-warning:#FBBF24; --ops-danger:#FB7185; --ops-text:#F1F5F9;
        --ops-secondary:#BAC8D8; --ops-muted:#94A3B8;
        --ops-font:Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background:var(--ops-bg); color:var(--ops-text);
        font-family:Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size:14px;
    }
    [data-testid="stAppViewContainer"] :is(h1,h2,h3,h4,p,label,button,a,input,summary,
        [data-testid="stMetricValue"],[data-testid="stMetricDelta"]) {font-family:var(--ops-font);}
    [data-testid="stHeader"] {background:#0B1220; color:#F1F5F9;}
    [data-testid="stHeader"] button {color:#BAC8D8;}
    [data-testid="stHeader"] [data-testid="stIconMaterial"] {color:#BAC8D8;}
    [data-testid="stMainBlockContainer"] {
        max-width:1520px; padding:4.5rem 28px 32px;
    }
    [data-testid="stVerticalBlock"] {gap:18px;}
    [data-testid="stHorizontalBlock"] {gap:20px;}
    [data-testid="stColumn"] {min-width:0;}
    [data-testid="stMain"] :is(h1,h2,h3,h4),
    [data-testid="stSidebar"] :is(h1,h2,h3,p) {color:var(--ops-text);}
    [data-testid="stMain"] h1 {font-size:32px; font-weight:700; letter-spacing:-.8px; padding:0;}
    [data-testid="stMain"] :is(h2,h3) {font-size:21px; font-weight:650; padding:0;}
    [data-testid="stMain"] h4 {font-size:18px;}
    [data-testid="stMarkdownContainer"] p {color:var(--ops-secondary); font-size:14px;}
    [data-testid="stCaptionContainer"] {opacity:1;}
    [data-testid="stCaptionContainer"] p {color:var(--ops-muted); font-size:12px; line-height:1.6;}
    [data-testid="stMetric"] {
        background:var(--ops-surface); border:1px solid var(--ops-border);
        border-radius:15px; padding:20px; min-height:136px; box-sizing:border-box;
        box-shadow:0 3px 12px rgb(0 0 0 / 8%); font-variant-numeric:tabular-nums;
    }
    [data-testid="stMetricLabel"] p {color:var(--ops-secondary); font-size:13px; font-weight:500;}
    [data-testid="stMetricValue"] {color:var(--ops-text); font-size:34px; font-weight:650; line-height:1.25;}
    [data-testid="stMetricValue"] > div {
        white-space:normal; overflow:visible; overflow-wrap:anywhere; text-overflow:clip;
    }
    [data-testid="stMetricDelta"] {
        color:var(--ops-warning); background:transparent; font-size:12px;
    }
    /* Lag and alert rate are context, not an improvement over a previous value. */
    [data-testid="stMetricDelta"] svg {display:none;}
    [data-testid="stMetricDelta"] > div {white-space:normal;}
    .st-key-ops-kpis [data-testid="stColumn"]:nth-child(2) [data-testid="stMetricValue"] {color:var(--ops-accent);}
    .st-key-ops-kpis [data-testid="stColumn"]:nth-child(3) [data-testid="stMetricValue"] {color:var(--ops-success);}
    .st-key-ops-kpis {margin-bottom:12px;}
    [data-testid="stSidebar"] {
        background:var(--ops-sidebar); border-right:1px solid var(--ops-border);
        min-width:252px; max-width:252px;
    }
    [data-testid="stSidebarContent"] {padding:12px 0 0;}
    [data-testid="stSidebarUserContent"] {padding:20px 14px;}
    [data-testid="stSidebar"] .st-key-dashboard_page,
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(> [data-testid="stLinkButton"]) {width:100%;}
    .ops-brand {font-size:23px; font-weight:750; letter-spacing:3px; color:var(--ops-text);}
    .ops-brand span {color:var(--ops-accent);}
    .ops-brand-sub {color:var(--ops-secondary); font-size:12px; margin:6px 0 24px;}
    .ops-nav-label {font-size:11px; letter-spacing:1.4px; color:var(--ops-muted); font-weight:600;}
    [data-testid="stSidebar"] [role="radiogroup"] {gap:8px;}
    [data-testid="stSidebar"] [role="radiogroup"] label {
        border:1px solid transparent;
        border-radius:9px; padding:11px 9px; margin:0; width:100%; min-height:48px;
        box-sizing:border-box; transition:background .15s;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#1B2B40;}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background:#1C364D; border-color:#304258;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {display:none;}
    [data-testid="stSidebar"] [role="radiogroup"] label p {font-size:13px; line-height:1.5;}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {color:var(--ops-accent);}
    [data-testid="stSidebar"] [data-testid="stLinkButton"] a {
        background:var(--ops-surface); color:var(--ops-secondary); border-color:var(--ops-border);
        width:100%; justify-content:space-between; font-size:13px; border-radius:9px;
    }
    [data-testid="stSidebar"] [data-testid="stIconMaterial"] {color:var(--ops-secondary);}
    [data-testid="stAppViewContainer"] :is(button,a,input,summary):focus-visible,
    [data-testid="stSidebar"] label:has(input:focus-visible) {
        outline:2px solid var(--ops-accent); outline-offset:3px;
    }
    [data-testid="stAppViewContainer"] hr {border-color:var(--ops-border);}
    .ops-header {display:flex; align-items:flex-start; justify-content:space-between; gap:20px; margin-bottom:6px;}
    .ops-eyebrow {color:var(--ops-accent); font-size:11px; letter-spacing:1.8px; font-weight:650; margin-bottom:7px;}
    .ops-subtitle {color:var(--ops-secondary); font-size:14px; margin-top:9px;}
    .ops-run {display:flex; flex-direction:column; align-items:flex-end; gap:8px; max-width:48%; padding-top:3px;}
    .ops-badge {display:inline-flex; align-items:center; gap:7px; border-radius:6px; padding:5px 9px;
        border:1px solid var(--ops-border); background:var(--ops-sidebar); color:var(--ops-secondary);
        font-size:11px; font-weight:650; letter-spacing:.4px;}
    .ops-badge::before {content:''; width:6px; height:6px; border-radius:50%; background:currentColor; flex-shrink:0;}
    .ops-run-id {color:var(--ops-secondary); font:12px ui-monospace,Consolas,monospace;
        overflow-wrap:anywhere; text-align:right;}
    .ops-refresh {color:var(--ops-muted); font-size:12px;}
    .ops-workspace {color:var(--ops-muted); font-size:12px;}
    .st-key-ops-workspace > [data-testid="stHorizontalBlock"] {gap:24px;}
    [class*="st-key-ops-signal-"] {
        background:var(--ops-surface); border:1px solid var(--ops-border);
        border-radius:15px; padding:20px; box-shadow:0 3px 12px rgb(0 0 0 / 8%);
    }
    [class*="st-key-ops-signal-"] h3 {font-size:18px;}
    .st-key-ops-monitor [data-testid="stMetricValue"] {font-size:28px;}
    .st-key-ops-monitor [data-testid="stMetric"] {min-height:126px;}
    .st-key-ops-fraud {
        padding:20px; background:var(--ops-surface); border:1px solid var(--ops-border); border-radius:15px;
        min-height:126px; box-sizing:border-box;
    }
    .st-key-ops-fraud [data-testid="stHorizontalBlock"] {flex-wrap:nowrap; gap:12px;}
    .st-key-ops-fraud [data-testid="stColumn"] {flex:1 1 0; width:0; min-width:0;}
    .st-key-ops-fraud [data-testid="stMetric"] {
        padding:0; min-height:0; border:0; border-radius:0; background:transparent; box-shadow:none;
    }
    .st-key-ops-fraud [data-testid="stMetricValue"] {font-size:24px; color:var(--ops-warning);}
    .st-key-ops-source, .st-key-ops-reconciliation {
        padding:20px; background:var(--ops-surface); border:1px solid var(--ops-border); border-radius:15px;
    }
    [data-testid="stProgressBar"] [role="progressbar"] {accent-color:var(--ops-accent);}
    .ops-check {font-weight:650; font-size:14px; color:var(--ops-warning);}
    .ops-check-pass {color:var(--ops-success);}
    .ops-check-note {font-size:12px; color:var(--ops-muted); margin-top:8px; line-height:1.6;}
    [data-testid="stExpander"] {border:1px solid var(--ops-border); border-radius:15px; background:var(--ops-surface);}
    [data-testid="stExpander"] > details {border:0;}
    [data-testid="stExpander"] > details > summary {
        background:var(--ops-surface); color:var(--ops-text); padding:16px 20px; border-radius:15px;
    }
    [data-testid="stExpander"] > details > summary p {color:var(--ops-text); font-size:16px; font-weight:600;}
    [data-testid="stTooltipIcon"] {color:#FFFFFF;}
    [data-testid="stTooltipIcon"] svg {color:#FFFFFF;}
    [data-testid="stExpanderDetails"] {padding:4px 20px 20px;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--ops-border); border-radius:15px;}
    [data-testid="stAlert"] {background:#142C41; border:1px solid #2B4C65; color:var(--ops-secondary); border-radius:10px;}
    [data-testid="stAlert"] p {color:var(--ops-secondary);}
    .st-key-ops-detail .metric-code,
    .st-key-ops-detail [data-testid="stElementContainer"]:has(.metric-code) {display:none;}
    /* Keep the native table toolbar (including CSV download) outside the table bounds. */
    [data-testid="stDataFrame"] {border-radius:10px; overflow:visible; border:1px solid var(--ops-border);}
    [data-testid="stVegaLiteChart"] {min-width:0;}
    .st-key-ops-detail [data-testid="stVegaLiteChart"] > .chart-wrapper {
        border-radius:15px; overflow:hidden;
    }
    #vg-tooltip-element {background:#142237; color:#F1F5F9; border-color:#304258; font-size:12px;}
    #vg-tooltip-element td.key {color:#BAC8D8;}
    @media (max-width:1100px) {
        .st-key-ops-workspace > [data-testid="stHorizontalBlock"] {flex-wrap:wrap;}
        .st-key-ops-workspace > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            flex:1 1 100%; width:100%;
        }
    }
    @media (max-width:767px) {
        [data-testid="stMainBlockContainer"] {padding:4.2rem 20px 28px;}
        [data-testid="stHorizontalBlock"] {flex-wrap:wrap; gap:16px;}
        [data-testid="stColumn"] {flex:1 1 100%; width:100%;}
        .ops-header {flex-direction:column; gap:16px;}
        .ops-run {align-items:flex-start; max-width:100%;}
        .ops-run-id {text-align:left;}
        [data-testid="stMain"] h1 {font-size:30px;}
        [class*="st-key-ops-signal-"] {padding:16px;}
    }
    </style>''', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="ops-brand">PAY<span>SIM</span></div>'
                    '<div class="ops-brand-sub">Operations Console</div>'
                    '<div class="ops-nav-label">WORKSPACE</div>', unsafe_allow_html=True)
        page = st.radio("Không gian vận hành", PAGES, key="dashboard_page", label_visibility="collapsed")
        st.divider()
        st.markdown('<div class="ops-nav-label">SYSTEM UIs</div>', unsafe_allow_html=True)
        st.link_button("HDFS ↗", "http://127.0.0.1:9870")
        st.link_button("Spark Web UI ↗", "http://127.0.0.1:4040")
        st.caption("PaySim Big Data · Capstone 2026")
    return page
# AFTER END — 9A.1

# BEFORE Start — 9A.2
# Sáu KPI nằm trong lưới 3 × 2 trước tất cả biểu đồ.
# BEFORE END — 9A.2
# AFTER Start — 9A.2: dải tốc độ trên cùng, số liệu rủi ro ở cột giám sát.
def summary(s):
    st.markdown(
        '<div class="ops-header"><div><div class="ops-eyebrow">PAYSIM / OPERATIONS</div>'
        '<h1>Operations Center</h1><div class="ops-subtitle">PaySim Big Data / Stream Monitoring</div>'
        '</div><div class="ops-run">'
        f'<span class="ops-badge">RUN · {escape(str(s.status).upper())}</span>'
        f'<span class="ops-run-id">Run ID · {escape(str(s.run_id))}</span>'
        '<span class="ops-refresh">Chu kỳ cập nhật · 2 giây</span></div></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="ops-kpis"):
        a, b, c = st.columns(3)
        a.metric("Spark đã xử lý", fmt_int(s.processed), delta=f"{fmt_int(s.lag)} đang chờ",
                 delta_color="off", help="Tổng giao dịch Spark đã xử lý; lag là số events đã phát còn đang chờ.")
        b.metric("Ingest hiện tại", f"{fmt_float(s.run.get('instant_emission_rate'))} ev/s",
                 help="Events/s tại thời điểm run được ghi nhận; snapshot lịch sử giữ nguyên giá trị này.")
        c.metric("Processing throughput", f"{fmt_float(s.latest_metric.get('processing_throughput'))} ev/s",
                 help="Events/s của micro-batch gần nhất trong snapshot.")
# AFTER END — 9A.2

# BEFORE Start — 9A.3
# Bốn biểu đồ đường cùng kích thước trên nền trắng.
# BEFORE END — 9A.3
# AFTER Start — 9A.3: biểu đồ tốc độ lớn, hai biểu đồ phụ trên nền tối.
def signal(s, fields, title, unit, height=250):
    frame=pd.DataFrame(s.metrics)
    available=[f for f in fields if f in frame]
    with st.container(key=f"ops-signal-{fields[0]}"):
        st.markdown(f"### {title}")
        if frame.empty or not available:
            # Reserve the plot's space while waiting, without inventing data.
            with st.container(height=height, border=False):
                st.info("Đang chờ micro-batch telemetry đầu tiên.")
            return
        series = {
            'ingest_throughput': ('Ingest', '#38BDF8'),
            'processing_throughput': ('Processing', '#34D399'),
            'consumer_lag': ('Events đang chờ', '#FBBF24'),
            'ingest_latency_p95_ms': ('Ingest p95', '#A78BFA'),
            'latency_p95_ms': ('End-to-end p95', '#FB923C'),
            'batch_duration_seconds': ('Batch duration', '#BAC8D8'),
        }
        data=frame[['created_at',*available]].melt('created_at',var_name='Metric',value_name='Value')
        data['Metric']=data['Metric'].replace({field: label for field, (label, _) in series.items()})
        data['Unit'] = unit
        chart=alt.Chart(data).mark_line(point=alt.OverlayMarkDef(size=18, filled=True),strokeWidth=2.5).encode(
            x=alt.X('created_at:T',title=None, axis=alt.Axis(format='%H:%M', tickCount=4)),
            y=alt.Y('Value:Q',title=unit, axis=alt.Axis(tickCount=4)),
            color=alt.Color('Metric:N', scale=alt.Scale(
                domain=[series[field][0] for field in available],
                range=[series[field][1] for field in available]),
                legend=alt.Legend(orient='top', title=None, labelLimit=180, columns=1 if len(available)==1 else 2)),
            tooltip=[alt.Tooltip('created_at:T', title='Timestamp', format='%Y-%m-%d %H:%M:%S'),
                     alt.Tooltip('Metric:N', title='Metric'),
                     alt.Tooltip('Value:Q', title='Value', format=',.2f'),
                     alt.Tooltip('Unit:N', title='Unit')],
        ).properties(height=height).configure(
            background='#1B2B40', view={'stroke':None}, font='Inter, sans-serif',
            axis={'labelColor':'#BAC8D8','titleColor':'#BAC8D8','gridColor':'#304258',
                  'gridOpacity':.5,'domainColor':'#304258','tickColor':'#304258',
                  'labelFontSize':12,'titleFontSize':12,'titleFontWeight':500,'labelPadding':8},
            legend={'labelColor':'#BAC8D8','labelFontSize':12,'symbolStrokeWidth':2.5,'padding':0},
        )
        st.altair_chart(chart, theme=None, use_container_width=True)
# AFTER END — 9A.3

# BEFORE Start — 9A.4
# Pipeline dạng sơ đồ ngang luôn chiếm phần đầu trang.
# BEFORE END — 9A.4
# AFTER Start — 9A.4: cột giám sát và tiến độ nằm cạnh biểu đồ chính.
def watch(s):
    with st.container(key="ops-monitor"):
        st.markdown("### Giám sát")
        with st.container(key="ops-fraud"):
            alerts, rate = st.columns(2)
            alerts.metric("Fraud alerts", fmt_int(s.alerts_count))
            rate.metric("Alert rate", fmt_pct(s.model['Alert rate']))
        st.metric("End-to-end latency p95", f"{fmt_float(s.latest_metric.get('latency_p95_ms'),0)} ms")
        st.metric("Nguồn đã phát", fmt_int(s.emitted))
        with st.container(key="ops-source"):
            st.markdown("**Tiến độ vòng dữ liệu**")
            st.caption(f"Vòng dữ liệu {s.run.get('source_cycle',1)}")
            progress = min(float(s.run.get('source_progress_pct',0)),1.0)
            st.progress(progress, text=f"{progress:.2%}")
            st.caption(f"Dòng {fmt_int(s.run.get('source_row'))}/{fmt_int(s.run.get('dataset_rows'))}")
        with st.container(key="ops-reconciliation"):
            st.markdown("**Đối soát dữ liệu**")
            label = "PASS" if s.display_correct else "SYNCING"
            style = "ops-check-pass" if s.display_correct else ""
            st.markdown(f'<div class="ops-check {style}">{label}</div>'
                        '<div class="ops-check-note">Kiểm tra tổng aggregate và số alerts với evaluation của run.</div>',
                        unsafe_allow_html=True)
# AFTER END — 9A.4

# BEFORE Start — 9A.5
# Một khung nội dung tuyến tính dùng chung cho mọi phiên bản.
# BEFORE END — 9A.5
# AFTER Start — 9A.5: workspace biểu đồ + cột giám sát, nhật ký batch ở cuối.
def render(s,page):
    summary(s)
    with st.container(key="ops-workspace"):
        main, aside = st.columns([3,1])
        with main:
            if page==PAGES[0]:
                signal(s,['ingest_throughput','processing_throughput'],'Tốc độ ingest và xử lý','Events/s',340)
                left,right=st.columns(2)
                with left: signal(s,['consumer_lag'],'Kafka consumer lag','Events',220)
                with right: signal(s,['ingest_latency_p95_ms','latency_p95_ms'],'Latency p95','ms',220)
            else:
                with st.container(key="ops-detail"):
                    render_page(s,page)
        with aside:
            watch(s)
    if page==PAGES[0]:
        with st.container(key="ops-history"):
            st.markdown("### Micro-batch History")
            st.caption("60 micro-batch gần nhất · Giữ nguyên đơn vị và dữ liệu telemetry.")
            with st.expander("Batch Duration và nhật ký",expanded=True):
                signal(s,['batch_duration_seconds'],'Thời gian mỗi micro-batch','Seconds',150)
                if s.metrics:
                    frame=pd.DataFrame(s.metrics).sort_values('batch_id',ascending=False)
                    columns=[c for c in ['batch_id','created_at','input_rows','processed_rows','consumer_lag','processing_throughput','latency_p95_ms','invalid_rows','duplicate_removed','alerts'] if c in frame]
                    st.dataframe(frame[columns],hide_index=True,height=240, width="stretch")
# AFTER END — 9A.5
