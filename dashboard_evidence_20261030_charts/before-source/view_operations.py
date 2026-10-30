"""9A — Trung tâm vận hành. Năm vùng AFTER chỉ thay cách trình bày."""
import base64
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from html import escape
from dashboard_core import PAGES, fmt_int, fmt_float, fmt_pct, render_page

PAGE_CONFIG = dict(page_title="PaySim | Operations", layout="wide", initial_sidebar_state="expanded")


@st.cache_data(show_spinner=False)
def banner_image_uri():
    # Resolve from this module so local runs and the Docker image share the asset.
    image = Path(__file__).with_name("Banner.png")
    if not image.is_file():
        return ""
    return "data:image/png;base64," + base64.b64encode(image.read_bytes()).decode("ascii")

# BEFORE Start — 9A.1
# Tiêu đề lớn + sidebar System UIs của dashboard gốc.
# BEFORE END — 9A.1
# AFTER Start — 9A.1: Light Enterprise, option menu dọc với Material Icons.
def setup():
    st.markdown('''<style>
    [data-testid="stAppViewContainer"] {
        --ops-bg:#F5F7FB; --ops-sidebar:#EDF2F8; --ops-surface:#FFFFFF;
        --ops-border:#DCE5EF; --ops-accent:#2563EB; --ops-success:#0F766E;
        --ops-warning:#B45309; --ops-danger:#B91C1C; --ops-text:#0F172A;
        --ops-secondary:#475569; --ops-muted:#64748B;
        --ops-font:Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background:var(--ops-bg); color:var(--ops-text);
        font-family:Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size:14px;
    }
    [data-testid="stAppViewContainer"] :is(h1,h2,h3,h4,p,label,button,a,input,summary,
        [data-testid="stMetricValue"],[data-testid="stMetricDelta"]) {font-family:var(--ops-font);}
    [data-testid="stHeader"] {background:#F5F7FB; color:#0F172A;}
    [data-testid="stHeader"] button {color:#475569;}
    [data-testid="stHeader"] [data-testid="stIconMaterial"] {color:#475569;}
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
        box-shadow:0 3px 12px rgb(15 23 42 / 4%); font-variant-numeric:tabular-nums;
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
    .st-key-ops-kpis [data-testid="stColumn"]:first-child [data-testid="stMetricDelta"] {color:#475569;}
    .st-key-ops-kpis [data-testid="stColumn"]:nth-child(2) [data-testid="stMetricValue"] {color:var(--ops-accent);}
    .st-key-ops-kpis [data-testid="stColumn"]:nth-child(3) [data-testid="stMetricValue"] {color:var(--ops-success);}
    .st-key-ops-kpis {margin-bottom:12px;}
    [data-testid="stSidebar"] {
        background:var(--ops-sidebar); border-right:1px solid var(--ops-border);
        min-width:260px; max-width:260px;
    }
    [data-testid="stSidebarContent"] {padding:12px 0 0;}
    [data-testid="stSidebarUserContent"] {padding:20px 14px;}
    [data-testid="stSidebar"] .st-key-dashboard_page,
    [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(> [data-testid="stLinkButton"]) {width:100%;}
    .ops-brand {font-size:23px; font-weight:750; letter-spacing:3px; color:var(--ops-text);}
    .ops-brand span {color:var(--ops-accent);}
    .ops-brand-sub {color:var(--ops-secondary); font-size:12px; margin:6px 0 24px;}
    .ops-nav-label {font-size:11px; letter-spacing:1.4px; color:var(--ops-muted); font-weight:600;}
    .st-key-dashboard_page [role="radiogroup"] {
        display:flex; flex-direction:column; align-items:stretch; gap:8px; width:100%;
    }
    [data-testid="stSidebar"] .st-key-dashboard_page button {
        background:transparent; color:var(--ops-secondary); border:1px solid transparent;
        border-radius:9px; padding:12px 8px; margin:0; width:100%; min-height:52px;
        justify-content:flex-start; gap:8px; text-align:left; box-sizing:border-box;
        transition:background .15s;
    }
    [data-testid="stSidebar"] .st-key-dashboard_page button:hover {background:#E3EAF4;}
    [data-testid="stSidebar"] .st-key-dashboard_page [data-testid="stBaseButton-pillsActive"] {
        background:#E3EDFF; border-color:#C7D9FC; color:var(--ops-accent);
    }
    [data-testid="stSidebar"] .st-key-dashboard_page button p {
        color:inherit; font-size:16px; font-weight:500; line-height:1.5; white-space:normal;
        display:flex; align-items:center; gap:10px;
    }
    [data-testid="stSidebar"] .st-key-dashboard_page [data-testid="stIconMaterial"] {
        color:inherit; font-size:22px; flex-shrink:0;
    }
    [data-testid="stSidebar"] [data-testid="stLinkButton"] a {
        background:var(--ops-surface); color:var(--ops-secondary); border-color:var(--ops-border);
        width:100%; justify-content:flex-start; font-size:14px; border-radius:9px;
    }
    [data-testid="stSidebar"] [data-testid="stIconMaterial"] {color:var(--ops-secondary);}
    [data-testid="stAppViewContainer"] :is(button,a,input,summary):focus-visible {
        outline:2px solid var(--ops-accent); outline-offset:3px;
    }
    [data-testid="stAppViewContainer"] hr {border-color:var(--ops-border);}
    .ops-team-row {display:flex; justify-content:flex-start; margin-bottom:12px;}
    .ops-team-badge {
        display:inline-flex; align-items:center; justify-content:center; padding:10px 18px;
        border:1px solid #C99B35; border-radius:12px; color:#4C3209;
        background:linear-gradient(120deg, #C59635 0%, #F7E4A3 48%, #D9AE4A 100%);
        box-shadow:0 3px 12px rgb(153 112 29 / 14%);
        font:700 14px var(--ops-font); letter-spacing:.8px; white-space:nowrap;
    }
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
    .ops-hero {
        position:relative; isolation:isolate; display:flex; align-items:flex-end;
        min-height:240px; padding:30px; margin-bottom:10px; box-sizing:border-box;
        overflow:hidden; border-radius:20px; border:1px solid #35415A;
        background:#080D19;
        box-shadow:0 16px 36px rgb(15 23 42 / 18%), 0 0 24px rgb(185 28 28 / 10%);
    }
    .ops-hero-image {
        position:absolute; inset:0; z-index:-2; display:block; width:100%; max-width:100%; height:100%;
        object-fit:cover; object-position:center 28%; transition:transform .6s ease;
    }
    .ops-hero:hover .ops-hero-image {transform:scale(1.015);}
    .ops-hero::after {
        content:''; position:absolute; inset:0; z-index:-1; pointer-events:none;
        background:linear-gradient(90deg, rgb(4 8 18 / 94%) 0%, rgb(4 8 18 / 65%) 26%, transparent 55%),
                   linear-gradient(0deg, rgb(4 8 18 / 85%), transparent 65%);
    }
    .ops-hero .ops-header {align-items:flex-end; width:100%; margin:0;}
    .ops-hero-copy {max-width:440px;}
    [data-testid="stMain"] .ops-hero h1 {
        color:#FFFFFF; font-size:clamp(30px, 2.8vw, 42px); line-height:1.15;
        text-shadow:0 2px 16px rgb(0 0 0 / 55%);
    }
    .ops-hero .ops-eyebrow {color:#60A5FA;}
    .ops-hero .ops-subtitle {color:#E2E8F0; line-height:1.6;}
    .ops-hero .ops-team-badge {box-shadow:0 0 22px rgb(217 174 74 / 35%);}
    .ops-hero .ops-run {
        flex-shrink:0; padding:12px 14px; border:1px solid rgb(148 163 184 / 25%);
        border-radius:12px; background:rgb(8 15 30 / 65%); backdrop-filter:blur(10px);
    }
    .ops-hero .ops-badge {color:#DBEAFE; border-color:#475569; background:rgb(30 41 59 / 90%);}
    .ops-hero .ops-badge-live {color:#A7F3D0; border-color:rgb(52 211 153 / 40%);}
    .ops-hero .ops-badge-live::before {box-shadow:0 0 8px #34D399;}
    .ops-hero .ops-run-id {color:#F1F5F9;}
    .ops-hero .ops-refresh {color:#CBD5E1;}
    .ops-workspace {color:var(--ops-muted); font-size:12px;}
    .st-key-ops-workspace > [data-testid="stHorizontalBlock"] {gap:24px;}
    [class*="st-key-ops-signal-"] {
        background:var(--ops-surface); border:1px solid var(--ops-border);
        border-radius:15px; padding:20px; box-shadow:0 3px 12px rgb(15 23 42 / 4%);
    }
    [class*="st-key-ops-signal-"] h3 {font-size:18px;}
    .st-key-ops-monitor {
        padding:20px; background:var(--ops-surface); border:1px solid var(--ops-border);
        border-radius:15px; box-shadow:0 3px 12px rgb(15 23 42 / 4%);
    }
    .st-key-ops-monitor [data-testid="stMetricValue"] {font-size:28px;}
    .st-key-ops-monitor [data-testid="stMetric"] {
        padding:0; min-height:0; border:0; border-radius:0; background:transparent; box-shadow:none;
    }
    .st-key-ops-fraud {
        padding:0; min-height:0; box-sizing:border-box;
    }
    .st-key-ops-fraud [data-testid="stHorizontalBlock"] {flex-wrap:nowrap; gap:12px;}
    .st-key-ops-fraud [data-testid="stColumn"] {flex:1 1 0; width:0; min-width:0;}
    .st-key-ops-fraud [data-testid="stMetricValue"] {font-size:24px; color:#0F172A;}
    .st-key-ops-fraud [data-testid="stColumn"]:nth-child(2) [data-testid="stMetricValue"] {color:#BE123C;}
    .st-key-ops-source, .st-key-ops-reconciliation {
        padding:16px 0 0; border-top:1px solid var(--ops-border);
    }
    [data-testid="stProgressBar"] [role="progressbar"] {accent-color:var(--ops-accent); background:#E3EDFF;}
    [data-testid="stProgressBar"] [role="progressbar"] > div {background:var(--ops-accent);}
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
    [data-testid="stTooltipIcon"] svg {color:#FFFFFF; border-radius:50%;}
    [data-testid="stExpanderDetails"] {padding:4px 20px 20px;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--ops-border); border-radius:15px;}
    [data-testid="stAlert"] {background:#EFF6FF; border:1px solid #BFDBFE; color:var(--ops-secondary); border-radius:10px;}
    [data-testid="stAlert"] p {color:var(--ops-secondary);}
    .st-key-ops-detail .metric-code,
    .st-key-ops-detail [data-testid="stElementContainer"]:has(.metric-code) {display:none;}
    /* Keep the native table toolbar (including CSV download) outside the table bounds. */
    [data-testid="stDataFrame"] {border-radius:10px; overflow:visible; border:1px solid var(--ops-border);}
    [data-testid="stVegaLiteChart"] {min-width:0;}
    .st-key-ops-detail [data-testid="stVegaLiteChart"] > .chart-wrapper {
        border-radius:15px; overflow:hidden;
    }
    #vg-tooltip-element {background:#FFFFFF; color:#0F172A; border-color:#DCE5EF; font-size:12px;}
    #vg-tooltip-element td.key {color:#475569;}
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
        .ops-hero {display:block; min-height:0; padding:0; border-radius:16px;}
        .ops-hero-image {
            position:relative; display:block; height:auto; aspect-ratio:1914 / 822;
            object-fit:contain; border-bottom:1px solid #35415A;
        }
        .ops-hero:hover .ops-hero-image {transform:none;}
        .ops-hero::after {display:none;}
        .ops-hero .ops-header {padding:22px; box-sizing:border-box; align-items:stretch;}
        .ops-hero .ops-run {max-width:100%; align-items:flex-start; flex-shrink:1;}
        .ops-hero .ops-run-id {text-align:left;}
        [data-testid="stMain"] .ops-hero h1 {font-size:30px;}
        [data-testid="stMain"] h1 {font-size:30px;}
        [class*="st-key-ops-signal-"] {padding:16px;}
    }
    @media (prefers-reduced-motion:reduce) {
        .ops-hero-image {transition:none;}
        .ops-hero:hover .ops-hero-image {transform:none;}
    }
    </style>''', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="ops-brand">PAY<span>SIM</span></div>'
                    '<div class="ops-brand-sub">Operations Console</div>'
                    '<div class="ops-nav-label">WORKSPACE</div>', unsafe_allow_html=True)
        icons = dict(zip(PAGES, ("sensors", "analytics", "shield", "receipt_long")))
        st.session_state.setdefault("_ops_active_page", PAGES[0])

        def remember_page():
            # Keep one page selected even when the current option is clicked again.
            if st.session_state.dashboard_page is None:
                st.session_state.dashboard_page = st.session_state._ops_active_page
            else:
                st.session_state._ops_active_page = st.session_state.dashboard_page

        page = st.pills(
            "Không gian vận hành", PAGES, default=PAGES[0], key="dashboard_page",
            format_func=lambda item: f":material/{icons[item]}: {item.split(' ', 1)[1]}",
            selection_mode="single", label_visibility="collapsed", width="stretch",
            on_change=remember_page,
        )
        st.divider()
        st.markdown('<div class="ops-nav-label">SYSTEM UIs</div>', unsafe_allow_html=True)
        st.link_button("HDFS", "http://127.0.0.1:9870", icon=":material/storage:")
        st.link_button("Spark Web UI", "http://127.0.0.1:4040", icon=":material/open_in_new:")
        st.caption("PaySim Big Data · Capstone 2026")
    return page or st.session_state._ops_active_page
# AFTER END — 9A.1

# BEFORE Start — 9A.2
# Sáu KPI nằm trong lưới 3 × 2 trước tất cả biểu đồ.
# BEFORE END — 9A.2
# AFTER Start — 9A.2: dải tốc độ trên cùng, số liệu rủi ro ở cột giám sát.
def summary(s):
    banner_uri = banner_image_uri()
    banner = f'<img class="ops-hero-image" src="{banner_uri}" alt="" aria-hidden="true">' if banner_uri else ""
    badge_class = "ops-badge ops-badge-live" if s.is_live else "ops-badge"
    st.markdown(
        '<section class="ops-hero" aria-label="PaySim Operations Center">'
        f'{banner}<div class="ops-header"><div class="ops-hero-copy">'
        '<div class="ops-team-row"><div class="ops-team-badge">NHÓM 4 AOF-BD</div></div>'
        '<div class="ops-eyebrow">PAYSIM / OPERATIONS</div>'
        '<h1>Operations Center</h1><div class="ops-subtitle">PaySim Big Data / Stream Monitoring</div></div>',
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
# AFTER Start — 9A.3: biểu đồ tốc độ lớn, hai biểu đồ phụ trên nền sáng.
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
            'ingest_throughput': ('Ingest', '#2563EB'),
            'processing_throughput': ('Processing', '#0F766E'),
            'consumer_lag': ('Events đang chờ', '#64748B'),
            'ingest_latency_p95_ms': ('Ingest p95', '#0284C7'),
            'latency_p95_ms': ('End-to-end p95', '#E11D48'),
            'batch_duration_seconds': ('Batch duration', '#334155'),
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
            background='#FFFFFF', view={'stroke':None}, font='Inter, Segoe UI, sans-serif',
            axis={'labelColor':'#475569','titleColor':'#475569','gridColor':'#DCE5EF',
                  'gridOpacity':.5,'domainColor':'#DCE5EF','tickColor':'#DCE5EF',
                  'labelFontSize':12,'titleFontSize':12,'titleFontWeight':500,'labelPadding':8},
            legend={'labelColor':'#475569','labelFontSize':12,'symbolStrokeWidth':2.5,'padding':0},
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
