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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Page background ── */
.stApp {
    background: #0d1117;
    color: #e6edf3;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stTextInput label {
    color: #8b949e !important;
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-weight: 600;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #e6edf3;
}

/* ── Header banner ── */
.hero-banner {
    background: linear-gradient(135deg, #0d1117 0%, #1a2332 50%, #0d1117 100%);
    border: 1px solid #30363d;
    border-top: 3px solid #388bfd;
    padding: 28px 32px;
    border-radius: 12px;
    margin-bottom: 24px;
}
.hero-banner h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #e6edf3;
    margin: 0 0 6px 0;
    letter-spacing: -0.02em;
}
.hero-banner p {
    color: #8b949e;
    font-size: 0.875rem;
    margin: 0;
    font-family: 'IBM Plex Mono', monospace;
}
.hero-badge {
    display: inline-block;
    background: #1f3a5f;
    color: #388bfd;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid #388bfd40;
    margin-top: 10px;
    letter-spacing: 0.06em;
}

/* ── Result banners ── */
.result-approved {
    background: linear-gradient(135deg, #0d2818, #0f3d1d);
    border: 1px solid #238636;
    border-left: 4px solid #3fb950;
    padding: 24px 28px;
    border-radius: 10px;
    margin-bottom: 20px;
    animation: pulse-green 2s ease-in-out 1;
}
.result-rejected {
    background: linear-gradient(135deg, #2d1117, #3d1219);
    border: 1px solid #da3633;
    border-left: 4px solid #f85149;
    padding: 24px 28px;
    border-radius: 10px;
    margin-bottom: 20px;
    animation: pulse-red 2s ease-in-out 1;
}
.result-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 4px;
    opacity: 0.7;
}
.result-name {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}
.result-approved .result-label { color: #3fb950; }
.result-approved .result-name  { color: #e6edf3; }
.result-rejected .result-label { color: #f85149; }
.result-rejected .result-name  { color: #e6edf3; }

@keyframes pulse-green {
    0%   { box-shadow: 0 0 0 0 #3fb95040; }
    50%  { box-shadow: 0 0 20px 6px #3fb95030; }
    100% { box-shadow: 0 0 0 0 #3fb95000; }
}
@keyframes pulse-red {
    0%   { box-shadow: 0 0 0 0 #f8514940; }
    50%  { box-shadow: 0 0 20px 6px #f8514930; }
    100% { box-shadow: 0 0 0 0 #f8514900; }
}

/* ── Metric cards ── */
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 18px 20px;
    text-align: center;
}
.metric-card .mc-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8b949e;
    margin-bottom: 8px;
}
.metric-card .mc-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: #e6edf3;
    line-height: 1;
}

/* ── Warning / info boxes ── */
.dti-warning {
    background: #2d1f00;
    border: 1px solid #9e6a03;
    border-left: 4px solid #e3b341;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #e3b341;
    font-family: 'IBM Plex Mono', monospace;
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
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 16px;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #484f58;
}
.empty-state .es-icon {
    font-size: 3rem;
    margin-bottom: 16px;
}
.empty-state p {
    font-size: 0.9rem;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── History table ── */
.history-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    font-family: 'IBM Plex Mono', monospace;
}
.history-table th {
    background: #161b22;
    color: #8b949e;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 8px 12px;
    border-bottom: 1px solid #30363d;
    text-align: left;
}
.history-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #21262d;
    color: #c9d1d9;
}
.badge-approved {
    background: #0d2818;
    color: #3fb950;
    border: 1px solid #238636;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.7rem;
}
.badge-rejected {
    background: #2d1117;
    color: #f85149;
    border: 1px solid #da3633;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.7rem;
}

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    border-radius: 8px 8px 0 0;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #8b949e;
    font-size: 0.82rem;
    font-weight: 500;
    padding: 10px 20px;
}
.stTabs [aria-selected="true"] {
    color: #e6edf3 !important;
    border-bottom: 2px solid #388bfd !important;
}

/* ── Predict button ── */
.stButton > button {
    background: #1f6feb;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.02em;
    padding: 12px;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: #388bfd;
}

/* ── Divider ── */
hr { border-color: #30363d; }

/* ── Plotly chart background ── */
.js-plotly-plot .plotly { background: transparent !important; }

/* ── Footer ── */
.footer {
    text-align: center;
    color: #484f58;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    padding: 20px 0 8px;
    border-top: 1px solid #21262d;
    margin-top: 32px;
}

/* ── Validation error ── */
.val-error {
    background: #2d1117;
    border: 1px solid #da3633;
    border-left: 4px solid #f85149;
    border-radius: 8px;
    padding: 12px 16px;
    color: #f85149;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    margin-bottom: 16px;
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
        <div style="color:#484f58;font-family:'IBM Plex Mono',monospace;font-size:0.82rem;padding:16px 0;">
            No predictions yet in this session.
        </div>
        """, unsafe_allow_html=True)
        return

    rows = ""
    for entry in reversed(st.session_state.history):
        badge = (
            '<span class="badge-approved">APPROVED</span>'
            if entry["result"] == "Approved"
            else '<span class="badge-rejected">REJECTED</span>'
        )
        rows += f"""
        <tr>
            <td>{entry['name']}</td>
            <td>₹{entry['income']:,}</td>
            <td>₹{entry['loan']}K</td>
            <td>{entry['credit']}</td>
            <td>{badge}</td>
            <td>{entry['confidence']}</td>
        </tr>"""

    st.markdown(f"""
    <table class="history-table">
        <thead>
            <tr>
                <th>Applicant</th>
                <th>Income</th>
                <th>Loan</th>
                <th>Credit</th>
                <th>Result</th>
                <th>Confidence</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# Header
# ─────────────────────────────────────────

st.markdown("""
<div class="hero-banner">
    <h1>🏦 Loan Approval Predictor</h1>
    <p>ML-powered risk assessment · FastAPI + Decision Tree</p>
    <span class="hero-badge"><strong>PREDICT YOURS</strong></span>
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
    predict_btn = st.button("Run Prediction", use_container_width=True)


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
                    <div class="result-label">✅ Decision · Approved</div>
                    <div class="result-name">{display_name}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-rejected">
                    <div class="result-label">❌ Decision · Rejected</div>
                    <div class="result-name">{display_name}</div>
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

            # ── Gauge + details ──
            gcol, dcol = st.columns([1, 1])

            with gcol:
                st.markdown(
                    "<p style='color:#8b949e;font-family:IBM Plex Mono;font-size:0.72rem;"
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
    st.markdown(
        "<p style='color:#8b949e;font-size:0.82rem;font-family:IBM Plex Mono;"
        "margin-bottom:16px;'>Last 5 predictions in this session.</p>",
        unsafe_allow_html=True,
    )
    render_history()


# ── Tab 3: About ────────────────────────

with tab3:
    a1, a2, a3 = st.columns(3)
    metrics = [
        (a1, "614",           "Dataset size"),
        (a2, "11",            "Input features"),
        (a3, "Decision Tree", "Selected model"),
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
    #### Objective
    Predict whether a bank loan application will be **Approved** or **Rejected** using supervised
    machine learning on the standard Loan Prediction dataset (614 records, binary classification).

    #### Models trained
    Logistic Regression · Decision Tree · Random Forest

    #### Why Decision Tree?
    Selected as the final model based on F1-score performance on the held-out test set.
    Decision Trees also offer inherent interpretability — important in a credit-risk context.

    #### Key insights
    - **Credit history** is the strongest predictor of approval.
    - Applicants with good credit history have significantly higher approval rates.
    - Income, loan amount, and property area are secondary influencing factors.

    #### System architecture
    ```
    Streamlit UI  →  FastAPI backend  →  Trained .pkl model  →  JSON response
    ```

    #### Tech stack
    Python · Pandas · NumPy · Scikit-learn · FastAPI · Streamlit · Plotly
    """)


# ─────────────────────────────────────────
# Footer
# ─────────────────────────────────────────

st.markdown("""
<div class="footer">
    FastAPI · Streamlit · Scikit-Learn · Plotly — by Abhik Kundu
</div>
""", unsafe_allow_html=True)