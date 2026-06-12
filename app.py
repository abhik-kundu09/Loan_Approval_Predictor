import streamlit as st
import requests
import plotly.graph_objects as go
import threading
import uvicorn

# ─────────────────────────────────────────
# Start FastAPI in background thread
# ─────────────────────────────────────────

def run_api():
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)

thread = threading.Thread(target=run_api, daemon=True)
thread.start()

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────

API_URL = "http://localhost:8000"

GENDER_OPTIONS       = ["Male", "Female"]
MARRIED_OPTIONS      = ["Yes", "No"]
DEPENDENTS_OPTIONS   = ["0", "1", "2", "3+"]
EDUCATION_OPTIONS    = ["Graduate", "Not Graduate"]
EMPLOYMENT_OPTIONS   = ["No", "Yes"]
PROPERTY_OPTIONS     = ["Urban", "Semiurban", "Rural"]
CREDIT_OPTIONS       = {1: "Good (1)", 0: "Bad (0)"}
MAX_HISTORY          = 5
DTI_WARNING_THRESHOLD = 0.43   # 43 % is a common underwriting ceiling

st.set_page_config(
    page_title="Loan Approval Predictor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# Session state
# ─────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []

# ─────────────────────────────────────────
# Styles
# ─────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Syne:wght@700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

/* ── Base ── */
.main  { background: #0D1117; }
.block-container { padding-top: 2.8rem; padding-bottom: 2rem; max-width: 1200px; }

/* ── Header ── */
.loan-header {
    background: linear-gradient(120deg, #111827 0%, #161B22 60%, #0f1e2e 100%);
    border: 1px solid #30363D;
    border-radius: 20px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.8rem;
    margin-top: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    flex-wrap: nowrap;
    min-height: 90px;
}
.loan-header-left {
    display: flex;
    align-items: center;
    gap: 1.2rem;
    flex: 1;
    min-width: 0;
}
.loan-header-icon {
    width: 52px;
    height: 52px;
    min-width: 52px;
    background: linear-gradient(135deg, #1d4ed8 0%, #0ea5e9 100%);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    box-shadow: 0 0 20px rgba(88,166,255,0.2);
}
.loan-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    font-weight: 400;
    color: #F0F6FF;
    letter-spacing: 3px;
    margin: 0;
    line-height: 1;
    white-space: nowrap;
    text-shadow: 0 0 40px rgba(88,166,255,0.15);
}
.loan-tagline {
    font-family: 'DM Sans', sans-serif;
    color: #58A6FF;
    font-size: 0.82rem;
    margin-top: 0.4rem;
    font-weight: 400;
    letter-spacing: 0.01em;
    white-space: nowrap;
}
.loan-header-badges {
    display: flex;
    gap: 0.7rem;
    flex-shrink: 0;
}
.loan-header-badge {
    background: rgba(88,166,255,0.06);
    border: 1px solid rgba(88,166,255,0.15);
    border-radius: 10px;
    padding: 0.65rem 1.2rem;
    text-align: center;
    white-space: nowrap;
}
.loan-badge-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.3rem;
    font-weight: 600;
    color: #93C5FD;
    line-height: 1;
    letter-spacing: -0.5px;
}
.loan-badge-lbl {
    font-size: 0.65rem;
    color: #484F58;
    margin-top: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    font-weight: 500;
}

/* ── KPI strip ── */
.kpi-row { display: flex; gap: 0.8rem; margin-bottom: 1.8rem; }
.kpi-card {
    flex: 1;
    background: #13181f;
    border: 1px solid #21272f;
    border-radius: 14px;
    padding: 1.3rem 1.2rem 1.1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(88,166,255,0.4), transparent);
}
.kpi-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.75rem;
    font-weight: 600;
    color: #E6EDF3;
    letter-spacing: -0.5px;
    line-height: 1;
}
.kpi-lbl {
    color: #484F58;
    font-size: 0.72rem;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 500;
}

/* ── Result banners ── */
.result-approved {
    background: linear-gradient(135deg, #0a1a12, #0f2a1a);
    border: 2px solid #00CC88;
    border-radius: 18px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1rem;
}
.result-rejected {
    background: linear-gradient(135deg, #1a0a0a, #2a0f0f);
    border: 2px solid #FF4B4B;
    border-radius: 18px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1rem;
}
.result-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.4rem;
    font-weight: 400;
    letter-spacing: 3px;
}
.result-approved .result-label { color: #00CC88; }
.result-rejected .result-label { color: #FF4B4B; }
.result-name {
    color: #F0F6FF;
    font-size: 1.3rem;
    font-weight: 500;
    margin-top: 0.3rem;
}
.result-meta {
    color: #484F58;
    font-size: 0.8rem;
    margin-top: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.03em;
}

@keyframes pulse-green {
    0%   { box-shadow: 0 0 0 0 #00CC8840; }
    50%  { box-shadow: 0 0 20px 6px #00CC8830; }
    100% { box-shadow: 0 0 0 0 #00CC8800; }
}
@keyframes pulse-red {
    0%   { box-shadow: 0 0 0 0 #FF4B4B40; }
    50%  { box-shadow: 0 0 20px 6px #FF4B4B30; }
    100% { box-shadow: 0 0 0 0 #FF4B4B00; }
}
.result-approved { animation: pulse-green 2s ease-in-out 1; }
.result-rejected { animation: pulse-red 2s ease-in-out 1; }

/* ── Metric cards ── */
.metric-card {
    background: #161B22;
    border: 1px solid #21272f;
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card .mc-label {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #484F58;
    font-weight: 600;
    margin-bottom: 4px;
}
.metric-card .mc-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 600;
    color: #E6EDF3;
    line-height: 1;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #161B22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stTextInput label {
    color: #8b949e !important;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-weight: 600;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #E6EDF3;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
}
.sidebar-section-title {
    font-family: 'Syne', sans-serif;
    color: #E6EDF3;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
    padding-top: 0.5rem;
}

/* ── DTI warnings ── */
.dti-warning {
    background: #2d1f00;
    border: 1px solid #9e6a03;
    border-left: 4px solid #e3b341;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #e3b341;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 16px;
}
.dti-ok {
    background: #0d2818;
    border: 1px solid #238636;
    border-left: 4px solid #3fb950;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #3fb950;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 16px;
}

/* ── Prob bars ── */
.prob-row { margin: 0.5rem 0; }
.prob-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #8B949E;
    margin-bottom: 0.3rem;
}
.prob-bar-bg {
    background: #21262D;
    border-radius: 6px;
    height: 10px;
    overflow: hidden;
}
.prob-bar-approved { background: #00CC88; height: 10px; border-radius: 6px; }
.prob-bar-rejected { background: #FF4B4B; height: 10px; border-radius: 6px; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #484F58;
}
.empty-state .es-icon {
    font-size: 3rem;
    margin-bottom: 16px;
}
.empty-state p {
    font-size: 0.9rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #8B949E;
}

/* ── History cards ── */
.hist-item {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.7rem;
    font-size: 0.88rem;
}
.hist-approved { border-left: 3px solid #00CC88; }
.hist-rejected { border-left: 3px solid #FF4B4B; }
.hist-meta { color: #484F58; font-size: 0.78rem; margin-top: 0.3rem; }

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
.stTabs [data-baseweb="tab"] {
    background: #161B22;
    border-radius: 10px 10px 0 0;
    border: 1px solid #30363D;
    color: #8B949E;
    font-weight: 500;
    padding: 0.5rem 1.2rem;
}
.stTabs [aria-selected="true"] {
    background: #1F2937 !important;
    color: #E6EDF3 !important;
    border-bottom-color: #1F2937 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8 0%, #0ea5e9 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.02em;
    padding: 12px 20px;
    transition: all 0.2s;
    border: 1px solid rgba(255,255,255,0.05);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(88,166,255,0.3);
}

/* ── Plotly ── */
.js-plotly-plot .plotly { background: transparent !important; }

/* ── Info box ── */
.info-box {
    background: #161B22;
    border: 1px solid #30363D;
    border-left: 3px solid #58A6FF;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    color: #8B949E;
    font-size: 0.88rem;
    margin-bottom: 1rem;
}

/* ── Validation error ── */
.val-error {
    background: #1a0a0a;
    border: 1px solid #FF4B4B;
    border-left: 4px solid #FF4B4B;
    border-radius: 8px;
    padding: 12px 16px;
    color: #FF4B4B;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    margin-bottom: 16px;
}

/* ── Footer ── */
.loan-footer {
    text-align: center;
    color: #484F58;
    font-size: 0.82rem;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #21262D;
}

/* ── Divider ── */
hr { border-color: #30363D; }

/* ── Selectbox / Input tweaks ── */
.stSelectbox > div > div { background: #0D1117 !important; border-color: #30363D !important; border-radius: 8px !important; }
.stNumberInput > div > div { background: #0D1117 !important; border-color: #30363D !important; border-radius: 8px !important; }
.stTextInput > div > div { background: #0D1117 !important; border-color: #30363D !important; border-radius: 8px !important; }

/* ── Section title ── */
.section-title {
    font-family: 'Syne', sans-serif;
    color: #E6EDF3;
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

/* ── About content ── */
.about-section {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.about-section h4 {
    font-family: 'Syne', sans-serif;
    color: #E6EDF3;
    font-weight: 600;
    margin-bottom: 0.8rem;
}
.about-section p, .about-section li {
    color: #8B949E;
    font-size: 0.88rem;
    line-height: 1.7;
}
.about-section code {
    font-family: 'JetBrains Mono', monospace;
    color: #58A6FF;
    background: #0D1117;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.82rem;
}
.about-section ul { padding-left: 1.2rem; }
.about-section li { margin-bottom: 0.3rem; }

/* ── Model perf card in sidebar ── */
.model-perf-card {
    background: #0D1117;
    border: 1px solid #21272f;
    border-radius: 12px;
    padding: 1rem 1.1rem;
    font-size: 0.82rem;
    color: #484F58;
    line-height: 2.2;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.model-perf-card b { color: #8B949E; font-weight: 600; }
.model-perf-card span { font-family: 'JetBrains Mono', monospace; color: #E6EDF3; font-size: 0.8rem; }

/* ─────────────────────────────────────────
   MOBILE RESPONSIVE (≤ 768px)
─────────────────────────────────────────*/
@media screen and (max-width: 768px) {
    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    .loan-header {
        flex-direction: column;
        align-items: flex-start;
        padding: 1.2rem;
        gap: 1rem;
        min-height: auto;
    }
    .loan-header-left { width: 100%; }
    .loan-title {
        font-size: 2rem;
        white-space: normal;
        letter-spacing: 1.5px;
    }
    .loan-tagline {
        white-space: normal;
        font-size: 0.75rem;
        line-height: 1.5;
    }
    .loan-header-badges {
        width: 100%;
        flex-wrap: wrap;
        justify-content: space-between;
    }
    .loan-header-badge {
        flex: 1 1 48%;
        padding: 0.8rem;
    }
    .loan-badge-val { font-size: 1.1rem; }

    .kpi-row { flex-wrap: wrap; gap: 0.8rem; }
    .kpi-card {
        flex: 1 1 calc(50% - 0.4rem);
        min-width: 140px;
        padding: 1rem;
    }
    .kpi-val { font-size: 1.4rem; }
    .kpi-lbl { font-size: 0.65rem; }

    .result-approved, .result-rejected {
        padding: 1.5rem 1rem;
    }
    .result-label {
        font-size: 1.8rem;
        letter-spacing: 2px;
    }
    .result-name { font-size: 1.1rem; }
    .result-meta { font-size: 0.75rem; }

    .metric-card {
        padding: 1rem 0.8rem;
    }
    .metric-card .mc-value { font-size: 1.2rem; }

    .hist-item { padding: 0.9rem; font-size: 0.8rem; }
    .hist-meta { font-size: 0.72rem; word-break: break-word; }

    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto;
        flex-wrap: nowrap;
    }
    .stTabs [data-baseweb="tab"] {
        min-width: max-content;
        padding: 0.5rem 0.8rem;
        font-size: 0.85rem;
    }

    .stDataFrame { overflow-x: auto; }
    .js-plotly-plot { width: 100% !important; }
    [data-testid="metric-container"] { padding: 0.5rem; }
    .stButton > button { width: 100%; min-height: 44px; font-size: 0.95rem; }
}

/* Extra small devices */
@media screen and (max-width: 480px) {
    .loan-title { font-size: 1.7rem; }
    .loan-header-icon { width: 45px; height: 45px; font-size: 1.4rem; }
    .loan-header-badge { flex: 1 1 100%; }
    .kpi-card { flex: 1 1 100%; }
    .result-label { font-size: 1.5rem; }
    .kpi-val { font-size: 1.25rem; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def build_payload(
    gender, married, dependents, education, self_employed,
    applicant_income, coapplicant_income, loan_amount,
    loan_term, credit_history, property_area,
):
    return {
        "Gender":            gender,
        "Married":           married,
        "Dependents":        dependents,
        "Education":         education,
        "Self_Employed":     self_employed,
        "ApplicantIncome":   applicant_income,
        "CoapplicantIncome": coapplicant_income,
        "LoanAmount":        loan_amount,
        "Loan_Amount_Term":  loan_term,
        "Credit_History":    credit_history,
        "Property_Area":     property_area,
    }


def validate_inputs(applicant_income, loan_amount, loan_term):
    errors = []
    if applicant_income <= 0:
        errors.append("Applicant income must be greater than 0.")
    if loan_amount <= 0:
        errors.append("Loan amount must be greater than 0.")
    if loan_term <= 0:
        errors.append("Loan term must be greater than 0.")
    return errors


def compute_dti(applicant_income, coapplicant_income, loan_amount, loan_term_months):
    """Monthly debt-to-income ratio (estimated monthly repayment / gross monthly income)."""
    total_income = applicant_income + coapplicant_income
    if total_income <= 0 or loan_term_months <= 0:
        return None
    # loan_amount is in thousands; term is in months
    monthly_payment = (loan_amount * 1000) / loan_term_months
    return monthly_payment / total_income


def make_gauge(approve_p, reject_p):
    """Dual-arc confidence gauge replacing a flat bar chart."""
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=round(approve_p * 100, 1),
        number={
            "font": {"size": 36, "color": "#e6edf3", "family": "IBM Plex Mono"},
            "suffix": "%",
        },
        title={
            "text": "Approval Probability",
            "font": {"size": 12, "color": "#8b949e", "family": "IBM Plex Mono"},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#30363d",
                "tickfont": {"color": "#484f58", "size": 9},
            },
            "bar": {"color": "#3fb950" if approve_p >= 0.5 else "#f85149", "thickness": 0.25},
            "bgcolor": "#161b22",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],  "color": "#2d1117"},
                {"range": [40, 60], "color": "#1c1f23"},
                {"range": [60, 100],"color": "#0d2818"},
            ],
            "threshold": {
                "line": {"color": "#388bfd", "width": 2},
                "thickness": 0.75,
                "value": 50,
            },
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))

    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e6edf3"},
    )
    return fig


def render_history():
    if not st.session_state.history:
        st.markdown("""
        <div class="info-box" style="text-align:center">
        No predictions yet in this session. Go to the <b>Prediction</b> tab and run your first analysis.
        </div>
        """, unsafe_allow_html=True)
        return

    approved = sum(1 for h in st.session_state.history if h["result"] == "Approved")
    rejected = len(st.session_state.history) - approved

    cards_html = ""
    for entry in reversed(st.session_state.history):
        cls = "hist-approved" if entry["result"] == "Approved" else "hist-rejected"
        icon = "✅" if entry["result"] == "Approved" else "❌"
        cards_html += f"""
        <div class="hist-item {cls}">
            <span style="font-weight:600;color:{'#00CC88' if entry['result']=='Approved' else '#FF4B4B'}">{icon} {entry['result']}</span>
            &nbsp;·&nbsp;
            <span style="color:#8B949E">{entry['name']}</span>
            &nbsp;·&nbsp;
            <span style="color:#8B949E">Confidence: <b style="color:#E6EDF3">{entry['confidence']}</b></span>
            <div class="hist-meta">₹{entry['income']:,} income · ₹{entry['loan']}K loan · Credit: {entry['credit']}</div>
        </div>"""

    st.markdown(f"""
    <div class="history-header">
        <div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-bottom:1rem;">
            <div class="kpi-card" style="flex:0 1 auto;min-width:100px;padding:0.8rem 1rem;">
                <div class="kpi-val" style="font-size:1.3rem;">{len(st.session_state.history)}</div>
                <div class="kpi-lbl">Total</div>
            </div>
            <div class="kpi-card" style="flex:0 1 auto;min-width:100px;padding:0.8rem 1rem;">
                <div class="kpi-val" style="font-size:1.3rem;color:#00CC88;">{approved}</div>
                <div class="kpi-lbl">✅ Approved</div>
            </div>
            <div class="kpi-card" style="flex:0 1 auto;min-width:100px;padding:0.8rem 1rem;">
                <div class="kpi-val" style="font-size:1.3rem;color:#FF4B4B;">{rejected}</div>
                <div class="kpi-lbl">❌ Rejected</div>
            </div>
        </div>
    </div>
    {cards_html}
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# Header
# ─────────────────────────────────────────

st.markdown("""
<div class="loan-header">
    <div class="loan-header-left">
        <div class="loan-header-icon">🏦</div>
        <div>
            <div class="loan-title">Loan Approval Predictor</div>
            <div class="loan-tagline">ML-Powered Risk Assessment &nbsp;·&nbsp; FastAPI + Decision Tree</div>
        </div>
    </div>
    <div class="loan-header-badges">
        <div class="loan-header-badge">
            <div class="loan-badge-val">614</div>
            <div class="loan-badge-lbl">Records</div>
        </div>
        <div class="loan-header-badge">
            <div class="loan-badge-val">11</div>
            <div class="loan-badge-lbl">Features</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── KPI strip ─────────────────────────────────────────────────────────────────

st.markdown("""
<div class="kpi-row">
    <div class="kpi-card">
        <div class="kpi-val">96.3%</div>
        <div class="kpi-lbl">Best Accuracy (LR)</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-val">95.9%</div>
        <div class="kpi-lbl">Random Forest</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-val">614</div>
        <div class="kpi-lbl">Dataset Records</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-val">11</div>
        <div class="kpi-lbl">Input Features</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────

with st.sidebar:
    st.markdown("### Applicant Information")

    applicant_name = st.text_input(
        "Applicant Name",
        placeholder="Full name"
    )

    col_g, col_m = st.columns(2)
    with col_g:
        gender = st.selectbox("Gender", GENDER_OPTIONS)
    with col_m:
        married = st.selectbox("Married", MARRIED_OPTIONS)

    col_d, col_e = st.columns(2)
    with col_d:
        dependents = st.selectbox("Dependents", DEPENDENTS_OPTIONS)
    with col_e:
        education = st.selectbox("Education", EDUCATION_OPTIONS)

    col_se, col_pa = st.columns(2)
    with col_se:
        self_employed = st.selectbox("Self-Employed", EMPLOYMENT_OPTIONS)
    with col_pa:
        property_area = st.selectbox("Property Area", PROPERTY_OPTIONS)

    credit_history = st.selectbox(
        "Credit History",
        options=list(CREDIT_OPTIONS.keys()),
        format_func=lambda x: CREDIT_OPTIONS[x],
    )

    st.divider()
    st.markdown("### Financials")

    applicant_income = st.number_input(
        "Applicant Monthly Income (₹)",
        min_value=0,
        value=5000,
        step=500,
    )
    coapplicant_income = st.number_input(
        "Co-applicant Income (₹)",
        min_value=0,
        value=0,
        step=500,
    )
    loan_amount = st.number_input(
        "Loan Amount (₹ thousands)",
        min_value=1,
        value=150,
        step=10,
    )
    loan_term = st.number_input(
        "Loan Term (months)",
        min_value=12,
        value=360,
        step=12,
    )

    st.divider()
    predict_btn = st.button("🔮 Run Prediction", use_container_width=True)

    st.markdown("---")
    st.markdown("**📊 Model Performance**")
    st.markdown("""
    <div class="model-perf-card">
        <b>Logistic Regression</b><span style="float:right">96.31%</span><br>
        <b>Decision Tree</b><span style="float:right">94.12%</span><br>
        <b>Random Forest</b><span style="float:right">95.92%</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="color:#484F58;font-size:0.78rem;line-height:1.6">
    <b style="color:#8B949E">About</b><br>
    Loan approval prediction using supervised ML trained on 614 records with 11 features.
    Decision Tree selected based on F1-score performance.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([
    "🔮 Prediction",
    "🕐 History",
    "ℹ️ About",
])

# ── Tab 1: Prediction ───────────────────

with tab1:
    if predict_btn:

        # Validation
        errors = validate_inputs(applicant_income, loan_amount, loan_term)
        if errors:
            for err in errors:
                st.markdown(f'<div class="val-error">⚠ {err}</div>', unsafe_allow_html=True)
            st.stop()

        # DTI indicator (shown regardless of API result)
        dti = compute_dti(applicant_income, coapplicant_income, loan_amount, loan_term)
        if dti is not None:
            dti_pct = dti * 100
            if dti >= DTI_WARNING_THRESHOLD:
                st.markdown(
                    f'<div class="dti-warning">⚠ DTI ratio: {dti_pct:.1f}% — above the 43% underwriting threshold. '
                    f'High repayment burden relative to income.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="dti-ok">✓ DTI ratio: {dti_pct:.1f}% — within acceptable range.</div>',
                    unsafe_allow_html=True,
                )

        payload = build_payload(
            gender, married, dependents, education, self_employed,
            applicant_income, coapplicant_income, loan_amount,
            loan_term, credit_history, property_area,
        )

        try:
            with st.spinner("Analyzing application…"):
                response = requests.post(
                    f"{API_URL}/predict",
                    json=payload,
                    timeout=10,
                )

            if response.status_code == 422:
                st.markdown(
                    '<div class="val-error">⚠ The server rejected the input. '
                    'Check that all fields are filled correctly.</div>',
                    unsafe_allow_html=True,
                )
                st.stop()

            response.raise_for_status()
            result = response.json()

            pred       = result["prediction"]
            conf       = result["confidence"]
            approve_p  = result["approve_probability"]
            reject_p   = result["reject_probability"]
            model_used = result.get("model_used", "—")

            display_name = applicant_name.strip() if applicant_name.strip() else "Applicant"

            # ── Result banner ──
            if pred == "Approved":
                st.markdown(f"""
                <div class="result-approved">
                    <div style="font-size:3rem;margin-bottom:0.3rem;">✅</div>
                    <div class="result-label">APPROVED</div>
                    <div class="result-name">{display_name}</div>
                    <div class="result-meta">Confidence: {conf*100:.1f}% · Model: {model_used}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-rejected">
                    <div style="font-size:3rem;margin-bottom:0.3rem;">❌</div>
                    <div class="result-label">REJECTED</div>
                    <div class="result-name">{display_name}</div>
                    <div class="result-meta">Confidence: {conf*100:.1f}% · Model: {model_used}</div>
                </div>
                """, unsafe_allow_html=True)

            # ── Metric cards ──
            c1, c2, c3, c4 = st.columns(4)
            cards = [
                (c1, "Confidence",    f"{conf * 100:.1f}%"),
                (c2, "Approval Prob", f"{approve_p * 100:.1f}%"),
                (c3, "Rejection Prob",f"{reject_p * 100:.1f}%"),
                (c4, "Model Used",    model_used),
            ]
            for col, label, val in cards:
                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="mc-label">{label}</div>
                        <div class="mc-value">{val}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Probability breakdown ──
            approve_pct = approve_p * 100
            reject_pct = reject_p * 100
            st.markdown(f"""
            <div class="prob-row">
                <div class="prob-label"><span>✅ Approved</span><span>{approve_pct:.1f}%</span></div>
                <div class="prob-bar-bg"><div class="prob-bar-approved" style="width:{approve_pct}%"></div></div>
            </div>
            <div class="prob-row">
                <div class="prob-label"><span>❌ Rejected</span><span>{reject_pct:.1f}%</span></div>
                <div class="prob-bar-bg"><div class="prob-bar-rejected" style="width:{reject_pct}%"></div></div>
            </div>
            """, unsafe_allow_html=True)

            # ── Gauge + details ──
            gcol, dcol = st.columns([1, 1])

            with gcol:
                st.markdown(
                    "<p style='color:#8b949e;font-family:JetBrains Mono;font-size:0.72rem;"
                    "letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;'>"
                    "Risk Gauge</p>",
                    unsafe_allow_html=True,
                )
                st.plotly_chart(make_gauge(approve_p, reject_p), use_container_width=True)

            with dcol:
                st.markdown(
                    "<p style='color:#8b949e;font-family:IBM Plex Mono;font-size:0.72rem;"
                    "letter-spacing:0.08em;text-transform:uppercase;margin-bottom:12px;'>"
                    "Submitted Details</p>",
                    unsafe_allow_html=True,
                )
                details = {
                    "Name":            display_name,
                    "Gender":          gender,
                    "Married":         married,
                    "Dependents":      dependents,
                    "Education":       education,
                    "Self-Employed":   self_employed,
                    "Property Area":   property_area,
                    "Credit History":  "Good" if credit_history == 1 else "Bad",
                    "App. Income":     f"₹{applicant_income:,}",
                    "Co-app. Income":  f"₹{coapplicant_income:,}",
                    "Loan Amount":     f"₹{loan_amount:,}K",
                    "Loan Term":       f"{loan_term} months",
                }
                for k, v in details.items():
                    st.markdown(
                        f"<span style='color:#8b949e;font-size:0.78rem;font-family:IBM Plex Mono;'>{k}: </span>"
                        f"<span style='color:#e6edf3;font-size:0.82rem;font-weight:500;'>{v}</span><br>",
                        unsafe_allow_html=True,
                    )

            # ── Save to history ──
            st.session_state.history = st.session_state.history[-(MAX_HISTORY - 1):]
            st.session_state.history.append({
                "name":       display_name,
                "income":     applicant_income,
                "loan":       loan_amount,
                "credit":     "Good" if credit_history == 1 else "Bad",
                "result":     pred,
                "confidence": f"{conf * 100:.1f}%",
            })

        except requests.exceptions.ConnectionError:
            st.markdown(
                '<div class="val-error">⚠ Cannot reach the API server at '
                f'{API_URL}. Make sure the FastAPI backend is running.</div>',
                unsafe_allow_html=True,
            )
        except requests.exceptions.Timeout:
            st.markdown(
                '<div class="val-error">⚠ Request timed out after 10 s. '
                'The server may be overloaded.</div>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.markdown(
                f'<div class="val-error">⚠ Unexpected error: {e}</div>',
                unsafe_allow_html=True,
            )

    else:
        st.markdown("""
        <div class="empty-state">
            <div class="es-icon">🏦</div>
            <p>Fill in the applicant details in the sidebar<br>and click <strong>Run Prediction</strong>.</p>
        </div>
        """, unsafe_allow_html=True)


# ── Tab 2: History ──────────────────────

with tab2:
    st.markdown("### 🕐 Prediction History")
    st.markdown('<div class="info-box">Last 5 predictions in this session.</div>', unsafe_allow_html=True)
    render_history()


# ── Tab 3: About ────────────────────────

with tab3:
    st.markdown("### ℹ️ About This Project")

    a1, a2, a3 = st.columns(3)
    metrics = [
        (a1, "614",           "Dataset Size"),
        (a2, "11",            "Input Features"),
        (a3, "Decision Tree", "Selected Model"),
    ]
    for col, val, label in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="mc-label">{label}</div>
                <div class="mc-value" style="font-size:1.4rem;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="about-section">
    <h4>🎯 Objective</h4>
    <p>Predict whether a bank loan application will be <strong style="color:#00CC88">Approved</strong> or
    <strong style="color:#FF4B4B">Rejected</strong> using supervised machine learning on the standard
    Loan Prediction dataset (614 records, binary classification).</p>
    </div>

    <div class="about-section">
    <h4>🧠 Models Trained</h4>
    <p>Logistic Regression · Decision Tree · Random Forest</p>
    <p>Decision Tree was selected as the final model based on F1-score performance on the held-out test set.
    Decision Trees also offer inherent interpretability — important in a credit-risk context.</p>
    </div>

    <div class="about-section">
    <h4>📊 Key Insights</h4>
    <ul>
    <li><strong>Credit history</strong> is the strongest predictor of approval.</li>
    <li>Applicants with good credit history have significantly higher approval rates.</li>
    <li>Income, loan amount, and property area are secondary influencing factors.</li>
    </ul>
    </div>

    <div class="about-section">
    <h4>🏗️ System Architecture</h4>
    <p><code>Streamlit UI</code> → <code>FastAPI backend</code> → <code>Trained .pkl model</code> → <code>JSON response</code></p>
    </div>

    <div class="about-section">
    <h4>🛠️ Tech Stack</h4>
    <p>Python · Pandas · NumPy · Scikit-learn · FastAPI · Streamlit · Plotly</p>
    </div>
    """)


# ─────────────────────────────────────────
# Footer
# ─────────────────────────────────────────

st.markdown("""
<div class="loan-footer">
    FastAPI · Streamlit · Scikit-Learn · Plotly &nbsp;|&nbsp; Loan Approval Predictor · Abhik Kundu
</div>
""", unsafe_allow_html=True)