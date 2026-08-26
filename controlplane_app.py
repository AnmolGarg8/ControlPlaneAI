"""
ControlPlane.ai — AIRAVAT for AI
Round 2 Prototype: Accenture Innovation Challenge 2026
Same detection philosophy as AIRAVAT XDR (Round 1 pitch), re-pointed from
network telemetry to enterprise AI response monitoring.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

from ai_response_simulator import (
    generate_normal_traffic,
    inject_hallucination,
    inject_cost_spike,
    inject_responsibility_violation,
    USE_CASES,
    GEOGRAPHIES,
)
from performance_detector import PerformanceDetector
from cost_monitor import CostMonitor
from responsibility_detector import ResponsibilityDetector
from policy_engine import compute_policy_decisions
from audit_trail import process_flags, record_feedback, feedback_summary
from metrics import compute_detector_accuracy, compute_latency_overhead

st.set_page_config(
    page_title="ControlPlane.ai — AIRAVAT for AI",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    with open("cyber-theme.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown("""
<style>
    header, [data-testid="stHeader"], [data-testid="stToolbar"], footer, #MainMenu {
        display: none !important; visibility: hidden !important;
    }
    .stApp { top: -70px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="cyber-navbar">
    <div class="nav-left">
        <div style="font-size:1.5rem; color:#00D4FF; margin-right:1rem;">☰</div>
        <div class="nav-logo">CONTROLPLANE.AI // AIRAVAT FOR AI</div>
    </div>
    <div class="nav-right">
        <div class="status-indicator"><div class="pulse-dot"></div> OVERSIGHT_LIVE</div>
    </div>
</div>
<div style="margin-top: 55px;"></div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="padding: 0 0 1rem 0;">
    <div style="font-size:0.85rem; color:#94A3B8; letter-spacing:0.5px;">
        A real-time trust layer for enterprise AI — the same anomaly-detection engine behind
        AIRAVAT XDR, re-pointed from network packets to AI response streams.
        Watches every response for <b style="color:#00D4FF;">Performance</b>,
        <b style="color:#00D4FF;">Cost</b>, and <b style="color:#00D4FF;">Responsibility</b> risk — live.
    </div>
</div>
""", unsafe_allow_html=True)


# ── Cached model init ────────────────────────────────────────────────────────
@st.cache_resource
def load_models():
    perf = PerformanceDetector()
    cost = CostMonitor()
    resp = ResponsibilityDetector()
    resp.train()
    baseline = generate_normal_traffic(200)
    perf.fit(baseline)
    cost.fit(baseline)
    return perf, cost, resp


performance_detector, cost_monitor, responsibility_detector = load_models()


def run_pipeline(df):
    df = performance_detector.predict(df)
    df = cost_monitor.predict(df)
    df = responsibility_detector.predict(df)
    df = compute_policy_decisions(df, sensitivity=st.session_state.get("sensitivity", 1.0))
    return df


# ── Session state ────────────────────────────────────────────────────────────
if "sensitivity" not in st.session_state:
    st.session_state.sensitivity = 1.0

if "response_log" not in st.session_state:
    baseline = generate_normal_traffic(90)
    baseline = run_pipeline(baseline)
    st.session_state.response_log = baseline
    st.session_state.flags = process_flags(baseline)
    st.session_state.sim_history = []

df = st.session_state.response_log

# ── Governance panel ─────────────────────────────────────────────────────────
st.markdown('<div class="section-header">⚙️ Governance Panel</div>', unsafe_allow_html=True)
gcol1, gcol2, gcol3 = st.columns([1, 1, 2])
with gcol1:
    st.selectbox("Use case (view only)", ["All"] + USE_CASES, key="uc_filter")
with gcol2:
    st.selectbox("Geography (view only)", ["All"] + GEOGRAPHIES, key="geo_filter")
with gcol3:
    new_sensitivity = st.slider(
        "Flagging sensitivity — over-flagging (alert fatigue) vs under-flagging (liability)",
        0.5, 2.0, st.session_state.sensitivity, 0.1,
    )
    if new_sensitivity != st.session_state.sensitivity:
        st.session_state.sensitivity = new_sensitivity
        st.session_state.response_log = run_pipeline(st.session_state.response_log.drop(
            columns=[c for c in ["performance_risk_score", "performance_flag", "cost_risk_score",
                                  "cost_flag", "responsibility_risk_score", "responsibility_flag",
                                  "pii_rule_hit", "composite_risk_score", "decision", "decision_confidence"]
                     if c in st.session_state.response_log.columns]
        ))
        st.session_state.flags = process_flags(st.session_state.response_log)
        st.rerun()

filtered = df.copy()
if st.session_state.get("uc_filter", "All") != "All":
    filtered = filtered[filtered["use_case"] == st.session_state.uc_filter]
if st.session_state.get("geo_filter", "All") != "All":
    filtered = filtered[filtered["geography"] == st.session_state.geo_filter]

# ── KPI Row ──────────────────────────────────────────────────────────────────
acc = compute_detector_accuracy(df)
latency = compute_latency_overhead(df)
flag_rate = round(100 * (df["decision"] != "ALLOW").mean(), 1)

kcol1, kcol2, kcol3, kcol4, kcol5 = st.columns(5)
kpis = [
    ("RESPONSES MONITORED", f"{len(df)}"),
    ("FLAG RATE", f"{flag_rate}%"),
    ("EST. FALSE POSITIVE RATE", f"{acc['overall']['false_positive_rate_pct']}%"),
    ("EST. FALSE NEGATIVE RATE", f"{acc['overall']['false_negative_rate_pct']}%"),
    ("ADDED LATENCY / RESPONSE", f"~{latency['assumed_ms_per_response']}ms"),
]
for col, (label, val) in zip([kcol1, kcol2, kcol3, kcol4, kcol5], kpis):
    with col:
        st.markdown(f"""<div class="cyber-card fade-in">
            <div class="kpi-wrapper">
                <div class="kpi-title">{label}</div>
                <div class="kpi-val monospace">{val}</div>
            </div>
        </div>""", unsafe_allow_html=True)

st.caption(
    "False positive/negative rates are measured against hidden ground-truth labels in the "
    "synthetic traffic generator — used only for scoring, never fed to the detectors themselves."
)

# ── Per-dimension risk + trend ───────────────────────────────────────────────
chart_left, chart_right = st.columns([1, 2])
with chart_left:
    st.markdown('<div class="section-header">Per-Dimension Avg Risk</div>', unsafe_allow_html=True)
    dims = ["performance_risk_score", "cost_risk_score", "responsibility_risk_score"]
    dim_labels = ["Performance", "Cost", "Responsibility"]
    avgs = [filtered[d].mean() if len(filtered) else 0 for d in dims]
    fig_bar = go.Figure(go.Bar(
        x=avgs, y=dim_labels, orientation="h",
        marker=dict(color=["#00D4FF", "#6C63FF", "#FF2D55"]),
    ))
    fig_bar.update_layout(
        height=220, margin=dict(t=10, b=30, l=100, r=20),
        paper_bgcolor="#000000", plot_bgcolor="#000000",
        xaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.05)", tickfont={"color": "#64748b"}),
        yaxis=dict(tickfont={"color": "#94a3b8"}),
        font={"color": "#e2e8f0"},
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_right:
    st.markdown('<div class="section-header">Composite Risk Trend</div>', unsafe_allow_html=True)
    trend_df = filtered.copy()
    if len(trend_df):
        trend_df["timestamp"] = pd.to_datetime(trend_df["timestamp"])
        trend_df = trend_df.sort_values("timestamp")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_df["timestamp"], y=trend_df["composite_risk_score"],
            mode="markers",
            marker=dict(size=6, color=trend_df["composite_risk_score"],
                        colorscale=[[0, "#10b981"], [0.4, "#f59e0b"], [0.7, "#fb923c"], [1, "#ef4444"]],
                        opacity=0.7),
            name="Composite Risk",
        ))
        fig_trend.update_layout(
            height=220, margin=dict(t=10, b=30, l=40, r=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont={"color": "#64748b"}),
            yaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.05)", tickfont={"color": "#64748b"}),
            font={"color": "#e2e8f0"},
        )
        st.plotly_chart(fig_trend, use_container_width=True)

# ── Simulation console ───────────────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:2rem;">📡 Inject Test Responses</div>
<div style="font-size:0.7rem; color:var(--text-secondary); margin-bottom:1rem; letter-spacing:1px; text-transform:uppercase;">
    Watch each dimension catch its target risk live
</div>
""", unsafe_allow_html=True)

sc1, sc2, sc3 = st.columns(3)


def run_injection(fn, label):
    new = fn()
    new = run_pipeline(new)
    st.session_state.response_log = pd.concat([st.session_state.response_log, new], ignore_index=True)
    new_flags = process_flags(new)
    st.session_state.flags.extend(new_flags)
    st.session_state.sim_history.append({
        "type": label, "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "count": len(new), "flagged": int((new["decision"] != "ALLOW").sum()),
    })


with sc1:
    if st.button("🧠 Inject Confidently-Wrong Response", use_container_width=True):
        run_injection(inject_hallucination, "Hallucination")
        st.rerun()
with sc2:
    if st.button("💸 Inject Cost Spike", use_container_width=True):
        run_injection(inject_cost_spike, "Cost Spike")
        st.rerun()
with sc3:
    if st.button("⚠️ Inject Bias / PII Leak", use_container_width=True):
        run_injection(inject_responsibility_violation, "Responsibility Violation")
        st.rerun()

if st.session_state.sim_history:
    st.markdown("<div style='background:rgba(0,212,255,0.05); border:1px solid rgba(0,212,255,0.1); border-radius:8px; padding:1rem; margin-top:1rem;'>", unsafe_allow_html=True)
    for s in reversed(st.session_state.sim_history[-5:]):
        st.markdown(
            f"<div style='font-size:0.8rem; margin-bottom:4px;'>"
            f"<span style='color:var(--text-muted); font-family:monospace;'>[{s['time']}]</span> "
            f"<span style='color:var(--accent-cyan); font-weight:700;'>{s['type'].upper()}</span> "
            f"<span style='color:var(--text-secondary);'>— {s['count']} responses injected, {s['flagged']} caught non-ALLOW</span>"
            f"</div>", unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ── Decision ledger ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header" style="margin-top:2.5rem;">📋 Live Decision Ledger</div>', unsafe_allow_html=True)
ledger = df.sort_values("timestamp", ascending=False).head(25)[
    ["timestamp", "use_case", "geography", "performance_risk_score", "cost_risk_score",
     "responsibility_risk_score", "composite_risk_score", "decision", "decision_confidence"]
].copy()
ledger.columns = ["Timestamp", "Use Case", "Geo", "Performance", "Cost", "Responsibility",
                   "Composite", "Decision", "Confidence %"]


def color_decision(val):
    colors = {"BLOCK": "#ff2d55", "FLAG_FOR_REVIEW": "#ff6b35", "AUTO_EDIT": "#ffaa00", "ALLOW": "#00e676"}
    return f"color: {colors.get(val, '#e0e6ed')}"


st.dataframe(
    ledger.style.applymap(color_decision, subset=["Decision"]),
    use_container_width=True, height=350,
)

# ── Audit trail + feedback loop ─────────────────────────────────────────────
st.markdown('<div class="section-header" style="margin-top:2.5rem;">📂 Audit Trail & Reviewer Feedback</div>', unsafe_allow_html=True)

fb = feedback_summary(st.session_state.flags)
if fb["reviewed"] > 0:
    st.caption(f"Reviewer feedback so far: {fb['reviewed']} reviewed — "
               f"{fb['confirmed']} confirmed, {fb['false_positive']} marked false positive "
               f"(running FP rate from feedback: {fb['fp_rate_pct']}%)")
else:
    st.caption("No reviewer feedback logged yet — confirm or override a flag below.")

if st.session_state.flags:
    for flag in reversed(st.session_state.flags[-12:]):
        badge = {"BLOCK": "🔴", "FLAG_FOR_REVIEW": "🟠", "AUTO_EDIT": "🟡"}.get(flag["decision"], "⚪")
        verdict_note = f" — reviewer: {flag['reviewer_verdict']}" if flag["reviewer_verdict"] else ""
        with st.expander(f"{badge} {flag['decision']} — {flag['use_case']} — risk {flag['composite_risk_score']:.0f}{verdict_note}"):
            st.code(flag["report"], language=None)
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                if st.button("✅ Confirm flag", key=f"confirm_{flag['flag_id']}"):
                    record_feedback(st.session_state.flags, flag["flag_id"], "confirmed")
                    st.rerun()
            with fcol2:
                if st.button("❌ Mark false positive", key=f"fp_{flag['flag_id']}"):
                    record_feedback(st.session_state.flags, flag["flag_id"], "false_positive")
                    st.rerun()
else:
    st.info("No flags raised yet.")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#3a4a5a; font-size:0.8rem;'>"
    "ControlPlane.ai — AIRAVAT for AI • Same detection engine as AIRAVAT XDR, re-pointed at AI response streams • "
    f"Responses Processed: {len(df)} • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    "</div>",
    unsafe_allow_html=True,
)
