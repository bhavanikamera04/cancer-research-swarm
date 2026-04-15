"""
CancerResearchSwarm — Main Dashboard
Professional UI with bug-fixed parallel agent execution.
Run: streamlit run main.py
"""

import streamlit as st
import threading
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CANCER_TYPES, RISK_FACTORS, MEDICAL_DISCLAIMER, GROQ_API_KEY
from agents.literature_scout  import run_literature_scout
from agents.patient_analyst   import run_patient_analyst, PatientProfile
from agents.treatment_advisor import run_treatment_advisor


st.set_page_config(
    page_title = "CancerResearchSwarm",
    page_icon  = "🔬",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #050A14; color: #E8EDF5; }
[data-testid="stSidebar"] { background: #080F1E !important; border-right: 1px solid rgba(99,179,237,0.12); }
[data-testid="stSidebar"] * { color: #CBD5E0 !important; }
[data-testid="stSidebar"] label { font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.08em; color: #718096 !important; font-weight: 500 !important; }
[data-testid="stSelectbox"] > div > div, [data-testid="stTextArea"] textarea, [data-testid="stNumberInput"] input { background: #0D1829 !important; border: 1px solid rgba(99,179,237,0.18) !important; border-radius: 8px !important; color: #E2E8F0 !important; }
[data-testid="stMultiSelect"] > div > div { background: #0D1829 !important; border: 1px solid rgba(99,179,237,0.18) !important; border-radius: 8px !important; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #1E6FEB 0%, #7C3AED 100%) !important; color: white !important; border: none !important; border-radius: 10px !important; padding: 0.65rem 1.5rem !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important; font-size: 0.95rem !important; letter-spacing: 0.04em !important; }
[data-testid="metric-container"] { background: #0D1829; border: 1px solid rgba(99,179,237,0.14); border-radius: 12px; padding: 1rem 1.2rem; }
[data-testid="stMetricValue"] { color: #63B3ED !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important; }
[data-testid="stExpander"] { background: #0D1829 !important; border: 1px solid rgba(99,179,237,0.14) !important; border-radius: 10px !important; }
hr { border-color: rgba(99,179,237,0.1) !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #050A14; }
::-webkit-scrollbar-thumb { background: #1E6FEB44; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def section_header(text, icon=""):
    st.markdown(f"""
    <div style="font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:700;
    color:#E2E8F0;letter-spacing:-0.01em;margin:2rem 0 1rem 0;
    padding-bottom:0.6rem;border-bottom:1px solid rgba(99,179,237,0.1);">
    {icon}&nbsp; {text}</div>
    """, unsafe_allow_html=True)

def agent_card(icon, title, subtitle, color="#1E6FEB"):
    return f"""
    <div style="background:#0D1829;border:1px solid rgba(99,179,237,0.14);
    border-top:3px solid {color};border-radius:12px;padding:1.2rem;height:100%;">
        <div style="font-size:1.5rem;margin-bottom:0.4rem;">{icon}</div>
        <div style="font-family:'Syne',sans-serif;font-weight:700;
        color:#E2E8F0;font-size:0.95rem;">{title}</div>
        <div style="color:#718096;font-size:0.8rem;margin-top:0.2rem;">{subtitle}</div>
    </div>"""

def risk_badge(level, score):
    colors = {"High":"#FC8181","Moderate":"#F6AD55","Low":"#68D391","Unknown":"#A0AEC0"}
    c = colors.get(level, "#A0AEC0")
    return f"""<span style="background:{c}22;color:{c};border:1px solid {c}55;
    border-radius:8px;padding:4px 14px;font-family:'Syne',sans-serif;
    font-weight:700;font-size:1rem;">{level} Risk — {score}/100</span>"""

def info_row(label, value, highlight=False):
    vc = "#63B3ED" if highlight else "#CBD5E0"
    return f"""<div style="display:flex;justify-content:space-between;padding:0.5rem 0;
    border-bottom:1px solid rgba(99,179,237,0.07);font-size:0.87rem;">
    <span style="color:#718096;">{label}</span>
    <span style="color:{vc};font-weight:500;">{value}</span></div>"""

def bullet_list(items, color="#63B3ED", icon="▸"):
    if not items:
        return '<p style="color:#4A5568;font-size:0.85rem;font-style:italic;">None identified</p>'
    return "".join(
        f'<div style="display:flex;gap:8px;margin-bottom:0.5rem;">'
        f'<span style="color:{color};margin-top:1px;flex-shrink:0;">{icon}</span>'
        f'<span style="color:#CBD5E0;font-size:0.88rem;line-height:1.5;">{item}</span>'
        f'</div>'
        for item in items
    )


# ── Hero Header ───────────────────────────────────────────────────────────────

st.markdown("""
<div style="padding:2.5rem 0 1.5rem 0;border-bottom:1px solid rgba(99,179,237,0.1);margin-bottom:2rem;">
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:0.5rem;">
        <div style="width:42px;height:42px;border-radius:10px;
        background:linear-gradient(135deg,#1E6FEB,#7C3AED);
        display:flex;align-items:center;justify-content:center;font-size:1.3rem;">🔬</div>
        <span style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
        color:#E8EDF5;letter-spacing:-0.02em;">
        CancerResearch<span style="color:#1E6FEB;">Swarm</span></span>
    </div>
    <p style="color:#718096;font-size:0.9rem;margin:0;font-weight:300;letter-spacing:0.02em;">
        3-Agent Parallel AI System &nbsp;·&nbsp;
        Literature Scout &nbsp;+&nbsp; Patient Analyst &nbsp;+&nbsp; Treatment Advisor
    </p>
</div>
""", unsafe_allow_html=True)

if not GROQ_API_KEY:
    st.markdown("""
    <div style="background:#1A0A00;border:1px solid #F6AD55;border-left:4px solid #ED8936;
    border-radius:10px;padding:1rem 1.2rem;margin-bottom:1.5rem;
    color:#FBD38D;font-size:0.88rem;">
        ⚠️ <strong>Groq API key missing.</strong>
        Set: <code style="background:#2D1A00;padding:2px 6px;border-radius:4px;">
        export GROQ_API_KEY=your_key</code> &nbsp;
        Get free at <a href="https://console.groq.com" style="color:#63B3ED;">console.groq.com</a>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
    color:#E2E8F0;padding:1rem 0 0.5rem 0;
    border-bottom:1px solid rgba(99,179,237,0.1);margin-bottom:1rem;">
    Patient Information</div>
    """, unsafe_allow_html=True)

    cancer_type     = st.selectbox("Cancer Type", CANCER_TYPES)
    age             = st.number_input("Patient Age", min_value=1, max_value=120, value=55)
    gender          = st.selectbox("Gender", ["Female", "Male", "Other"])
    symptoms        = st.text_area("Symptoms (comma-separated)",
                        placeholder="persistent cough, weight loss, chest pain", height=90)
    duration_weeks  = st.slider("Symptom Duration (weeks)", 1, 52, 6)
    risk_factors    = st.multiselect("Risk Factors", RISK_FACTORS)
    medical_history = st.text_area("Medical History",
                        placeholder="diabetes, hypertension...", height=70)
    family_history  = st.text_area("Family History of Cancer",
                        placeholder="father: lung cancer...", height=60)
    current_meds    = st.text_area("Current Medications",
                        placeholder="metformin, lisinopril...", height=60)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    run_button = st.button("🚀  Run All 3 Agents", type="primary", use_container_width=True)

    st.markdown("""
    <div style="margin-top:1.2rem;padding:0.8rem;background:#100500;
    border:1px solid rgba(246,173,85,0.2);border-radius:8px;
    color:#A0AEC0;font-size:0.72rem;line-height:1.5;">
        ⚠️ Research tool only. All output must be reviewed by a licensed oncologist.
    </div>
    """, unsafe_allow_html=True)


# ── Run Workflow ──────────────────────────────────────────────────────────────

if run_button:

    if not symptoms.strip():
        st.error("Please enter patient symptoms before running.")
        st.stop()

    profile = PatientProfile(
        age             = age,
        gender          = gender,
        cancer_type     = cancer_type,
        symptoms        = symptoms,
        duration_weeks  = duration_weeks,
        risk_factors    = risk_factors,
        medical_history = medical_history,
        current_meds    = current_meds,
        family_history  = family_history,
    )

    section_header("Agent Execution", "🤖")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(agent_card("📚", "Agent 1 — Literature Scout",
                               "Searching PubMed live...", "#1E6FEB"), unsafe_allow_html=True)
        a1_status = st.empty()
        a1_status.info("⏳ Running in parallel...")
    with col2:
        st.markdown(agent_card("🏥", "Agent 2 — Patient Analyst",
                               "Calculating risk score...", "#7C3AED"), unsafe_allow_html=True)
        a2_status = st.empty()
        a2_status.info("⏳ Running in parallel...")
    with col3:
        st.markdown(agent_card("💊", "Agent 3 — Treatment Advisor",
                               "Awaiting Agents 1 & 2...", "#0BC5EA"), unsafe_allow_html=True)
        a3_status = st.empty()
        a3_status.info("⏳ Waiting...")

    # ── BUG FIX: Threads capture exceptions — never return None silently ──────
    literature_result = [None]
    patient_result    = [None]
    agent1_error      = [None]
    agent2_error      = [None]

    def run_agent1():
        try:
            literature_result[0] = run_literature_scout(
                cancer_type = cancer_type,
                symptoms    = symptoms,
            )
        except Exception as e:
            agent1_error[0] = str(e)

    def run_agent2():
        try:
            patient_result[0] = run_patient_analyst(profile)
        except Exception as e:
            agent2_error[0] = str(e)

    # Launch both threads simultaneously — true parallel execution
    start_time = time.time()
    t1 = threading.Thread(target=run_agent1)
    t2 = threading.Thread(target=run_agent2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    parallel_time = round(time.time() - start_time, 1)

    literature = literature_result[0]
    patient    = patient_result[0]

    # Safe status — check None before accessing any attribute
    if agent1_error[0]:
        a1_status.error(f"❌ {agent1_error[0][:100]}")
    elif literature is None:
        a1_status.error("❌ Agent 1 returned no data")
    else:
        a1_status.success(f"✅ {literature.papers_found} papers found ({parallel_time}s)")

    if agent2_error[0]:
        a2_status.error(f"❌ {agent2_error[0][:100]}")
    elif patient is None:
        a2_status.error("❌ Agent 2 returned no data")
    else:
        a2_status.success(f"✅ Risk: {patient.risk_level} ({patient.risk_score}/100)")

    # Agent 3 only runs if both succeeded
    treatment = None
    if literature is not None and patient is not None:
        a3_status.info("⏳ Synthesizing...")
        try:
            treatment = run_treatment_advisor(literature, patient)
            a3_status.success("✅ Recommendations ready")
        except Exception as e:
            a3_status.error(f"❌ {str(e)[:100]}")
    else:
        a3_status.warning("⏠ Skipped — upstream agents failed")

    total_time = round(time.time() - start_time, 1)

    st.markdown(f"""
    <div style="background:#0D1829;border:1px solid rgba(99,179,237,0.14);
    border-radius:10px;padding:1rem 1.4rem;margin:1.2rem 0;
    display:flex;gap:2rem;align-items:center;flex-wrap:wrap;">
        <span style="color:#68D391;font-size:0.9rem;">
            ✅ Agents 1 &amp; 2 ran <strong>in parallel</strong>
        </span>
        <span style="color:#63B3ED;font-size:0.9rem;">
            ⚡ Parallel time: <strong>{parallel_time}s</strong>
        </span>
        <span style="color:#A0AEC0;font-size:0.9rem;">
            🕐 Total: <strong>{total_time}s</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── AGENT 1 RESULTS ────────────────────────────────────────────────────────
    if literature is not None:
        section_header("Agent 1: Literature Scout", "📚")

        if getattr(literature, 'error', None):
            st.error(f"Error: {literature.error}")
        else:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                <div style="background:#0D1829;border:1px solid rgba(99,179,237,0.12);
                border-radius:12px;padding:1.4rem;margin-bottom:1rem;">
                    <div style="font-size:0.72rem;color:#1E6FEB;text-transform:uppercase;
                    letter-spacing:0.1em;font-weight:600;margin-bottom:0.6rem;">AI SYNTHESIS</div>
                    <div style="color:#CBD5E0;font-size:0.92rem;line-height:1.7;">
                        {literature.ai_summary or "Groq API key required for AI analysis."}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if literature.key_findings:
                    st.markdown("""<div style="font-size:0.78rem;color:#1E6FEB;text-transform:uppercase;
                    letter-spacing:0.1em;font-weight:600;margin-bottom:0.6rem;">Key Findings</div>
                    """, unsafe_allow_html=True)
                    st.markdown(bullet_list(literature.key_findings, "#68D391", "◆"),
                                unsafe_allow_html=True)

                if literature.research_gaps:
                    st.markdown("""<div style="font-size:0.78rem;color:#ED8936;text-transform:uppercase;
                    letter-spacing:0.1em;font-weight:600;margin:1rem 0 0.6rem 0;">Research Gaps</div>
                    """, unsafe_allow_html=True)
                    st.markdown(bullet_list(literature.research_gaps, "#F6AD55", "◇"),
                                unsafe_allow_html=True)

            with c2:
                st.metric("Papers Found", literature.papers_found)
                st.metric("Evidence Level", literature.evidence_level)

                if literature.papers:
                    st.markdown("""<div style="font-size:0.72rem;color:#718096;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin:1rem 0 0.4rem 0;">PubMed Sources</div>""",
                    unsafe_allow_html=True)
                    for p in literature.papers:
                        st.markdown(f"""
                        <div style="background:#081018;border:1px solid rgba(99,179,237,0.1);
                        border-radius:8px;padding:0.7rem;margin-bottom:0.5rem;">
                            <a href="{p.url}" target="_blank" style="color:#63B3ED;
                            font-size:0.8rem;font-weight:500;text-decoration:none;">
                            {p.title[:65]}{"..." if len(p.title) > 65 else ""}</a>
                            <div style="color:#4A5568;font-size:0.73rem;margin-top:3px;">
                            {p.journal[:35]} · {p.year}</div>
                        </div>
                        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── AGENT 2 RESULTS ────────────────────────────────────────────────────────
    if patient is not None:
        section_header("Agent 2: Patient Analyst", "🏥")

        if getattr(patient, 'error', None):
            st.error(f"Error: {patient.error}")
        else:
            if patient.red_flags:
                for flag in patient.red_flags:
                    st.markdown(f"""
                    <div style="background:#1A0000;border:1px solid #F56565;
                    border-left:4px solid #FC8181;border-radius:10px;
                    padding:0.9rem 1.2rem;color:#FEB2B2;font-size:0.9rem;
                    margin-bottom:0.6rem;">🚨 {flag}</div>
                    """, unsafe_allow_html=True)

            c3, c4 = st.columns([1, 2])
            with c3:
                st.markdown(f"""
                <div style="background:#0D1829;border:1px solid rgba(99,179,237,0.14);
                border-radius:12px;padding:1.4rem;">
                    <div style="margin-bottom:1rem;">{risk_badge(patient.risk_level, patient.risk_score)}</div>
                    {info_row("Urgency", patient.urgency, highlight=patient.urgency=="Immediate")}
                    {info_row("Age", str(patient.patient_profile.age))}
                    {info_row("Duration", f"{patient.patient_profile.duration_weeks} weeks")}
                    {info_row("Risk Factors", str(len(patient.patient_profile.risk_factors)))}
                </div>
                """, unsafe_allow_html=True)

            with c4:
                st.markdown(f"""
                <div style="background:#0D1829;border:1px solid rgba(99,179,237,0.12);
                border-radius:12px;padding:1.4rem;margin-bottom:1rem;">
                    <div style="font-size:0.72rem;color:#7C3AED;text-transform:uppercase;
                    letter-spacing:0.1em;font-weight:600;margin-bottom:0.6rem;">Clinical Summary</div>
                    <div style="color:#CBD5E0;font-size:0.9rem;line-height:1.7;">
                        {patient.clinical_summary or "Summary unavailable — check Groq API key."}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c4a, c4b = st.columns(2)
                with c4a:
                    st.markdown("""<div style="font-size:0.72rem;color:#718096;text-transform:uppercase;
                    letter-spacing:0.08em;margin-bottom:0.5rem;">Patterns</div>""",
                    unsafe_allow_html=True)
                    st.markdown(bullet_list(patient.identified_patterns, "#B794F4", "◆"),
                                unsafe_allow_html=True)
                with c4b:
                    st.markdown("""<div style="font-size:0.72rem;color:#718096;text-transform:uppercase;
                    letter-spacing:0.08em;margin-bottom:0.5rem;">Ask Doctor</div>""",
                    unsafe_allow_html=True)
                    st.markdown(bullet_list(patient.questions_for_doctor, "#76E4F7", "?"),
                                unsafe_allow_html=True)

    st.markdown("---")

    # ── AGENT 3 RESULTS ────────────────────────────────────────────────────────
    if treatment is not None:
        section_header("Agent 3: Treatment Advisor", "💊")

        st.markdown("""
        <div style="background:#0A0F00;border:1px solid rgba(246,173,85,0.2);
        border-radius:8px;padding:0.6rem 1rem;color:#F6AD55;
        font-size:0.78rem;margin-bottom:1rem;">
            ⚠️ For qualified oncologist review only — not direct medical advice
        </div>
        """, unsafe_allow_html=True)

        if getattr(treatment, 'error', None):
            st.error(f"Error: {treatment.error}")
        else:
            if treatment.urgent_actions:
                st.markdown("""<div style="font-size:0.78rem;color:#FC8181;text-transform:uppercase;
                letter-spacing:0.1em;font-weight:600;margin-bottom:0.6rem;">⚡ Urgent Actions</div>""",
                unsafe_allow_html=True)
                for action in treatment.urgent_actions:
                    st.markdown(f"""
                    <div style="background:#1A0000;border:1px solid rgba(252,129,129,0.3);
                    border-radius:8px;padding:0.7rem 1rem;color:#FEB2B2;
                    font-size:0.88rem;margin-bottom:0.4rem;">🔴 {action}</div>
                    """, unsafe_allow_html=True)

            if treatment.full_synthesis:
                st.markdown(f"""
                <div style="background:#0D1829;border:1px solid rgba(11,197,234,0.14);
                border-top:3px solid #0BC5EA;border-radius:12px;
                padding:1.4rem;margin-bottom:1.2rem;">
                    <div style="font-size:0.72rem;color:#0BC5EA;text-transform:uppercase;
                    letter-spacing:0.1em;font-weight:600;margin-bottom:0.6rem;">Clinical Synthesis</div>
                    <div style="color:#CBD5E0;font-size:0.9rem;line-height:1.7;">
                        {treatment.full_synthesis}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if treatment.first_line_priority:
                st.markdown(f"""
                <div style="background:#081808;border:1px solid rgba(104,211,145,0.3);
                border-radius:10px;padding:0.9rem 1.2rem;color:#9AE6B4;
                font-size:0.9rem;margin-bottom:1.2rem;">
                    <strong style="color:#68D391;">First-Line Priority:</strong>
                    &nbsp;{treatment.first_line_priority}
                </div>
                """, unsafe_allow_html=True)

            if treatment.treatment_options:
                st.markdown("""<div style="font-size:0.78rem;color:#0BC5EA;text-transform:uppercase;
                letter-spacing:0.1em;font-weight:600;margin-bottom:0.8rem;">Treatment Options</div>""",
                unsafe_allow_html=True)

                ev_colors = {"Strong":"#68D391","Moderate":"#F6AD55","Emerging":"#63B3ED"}
                for opt in treatment.treatment_options:
                    ev_color = ev_colors.get(opt.evidence_strength, "#A0AEC0")
                    with st.expander(
                        f"{opt.name}  ·  {opt.category}  ·  Evidence: {opt.evidence_strength}"
                    ):
                        st.markdown(f"""
                        <div style="padding:0.3rem 0;">
                            <div style="color:#718096;font-size:0.78rem;text-transform:uppercase;
                            letter-spacing:0.08em;margin-bottom:0.3rem;">Description</div>
                            <div style="color:#CBD5E0;font-size:0.88rem;line-height:1.6;
                            margin-bottom:0.8rem;">{opt.description}</div>
                            <div style="color:#718096;font-size:0.78rem;text-transform:uppercase;
                            letter-spacing:0.08em;margin-bottom:0.3rem;">Relevant for this patient</div>
                            <div style="color:{ev_color};font-size:0.88rem;line-height:1.6;">
                            {opt.relevant_for}</div>
                        </div>
                        """, unsafe_allow_html=True)

            cm, cl = st.columns(2)
            with cm:
                st.markdown("""<div style="font-size:0.72rem;color:#718096;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:0.5rem;">Monitoring Plan</div>""",
                unsafe_allow_html=True)
                st.markdown(bullet_list(treatment.monitoring_plan, "#63B3ED", "◆"),
                            unsafe_allow_html=True)
            with cl:
                st.markdown("""<div style="font-size:0.72rem;color:#718096;text-transform:uppercase;
                letter-spacing:0.08em;margin-bottom:0.5rem;">Lifestyle Recommendations</div>""",
                unsafe_allow_html=True)
                st.markdown(bullet_list(treatment.lifestyle_recommendations, "#68D391", "◆"),
                            unsafe_allow_html=True)

            if treatment.confidence_note:
                st.markdown(f"""
                <div style="color:#4A5568;font-size:0.8rem;font-style:italic;
                margin-top:1rem;padding-top:0.8rem;
                border-top:1px solid rgba(99,179,237,0.08);">
                    📝 {treatment.confidence_note}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style="background:#0D0A00;border:1px solid rgba(246,173,85,0.15);
    border-radius:10px;padding:1rem 1.2rem;color:#D69E2E;
    font-size:0.8rem;line-height:1.6;">{MEDICAL_DISCLAIMER}</div>
    """, unsafe_allow_html=True)


# ── Empty State ───────────────────────────────────────────────────────────────

else:
    c1, c2, c3 = st.columns(3)
    cards = [
        ("📚", "Literature Scout", "Agent 1", "#1E6FEB",
         "Searches <strong style='color:#CBD5E0;'>real PubMed papers</strong> live. Returns peer-reviewed abstracts with AI summaries, key findings, and research gaps."),
        ("🏥", "Patient Analyst", "Agent 2", "#7C3AED",
         "Calculates <strong style='color:#CBD5E0;'>evidence-based risk score</strong> from age, symptoms, and history. Flags urgent red flags."),
        ("💊", "Treatment Advisor", "Agent 3", "#0BC5EA",
         "Synthesizes research + patient data into <strong style='color:#CBD5E0;'>NCCN/ESMO-aligned recommendations</strong> for doctor review."),
    ]
    for col, (icon, title, sub, color, desc) in zip([c1, c2, c3], cards):
        with col:
            st.markdown(f"""
            {agent_card(icon, title, sub, color)}
            <div style="padding:1rem 0 0 0;color:#718096;font-size:0.85rem;line-height:1.7;">
                {desc}
            </div>
            """, unsafe_allow_html=True)

    section_header("DevSwarm Parallel Architecture", "⚡")
    st.markdown("""
    <div style="background:#0D1829;border:1px solid rgba(99,179,237,0.12);
    border-radius:12px;padding:1.4rem;">
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;">
            <div>
                <div style="color:#1E6FEB;font-size:0.72rem;text-transform:uppercase;
                letter-spacing:0.1em;font-weight:600;margin-bottom:0.5rem;">Branch</div>
                <div style="color:#CBD5E0;font-size:0.85rem;line-height:2.2;">
                    agent-literature-scout<br>agent-patient-analyst<br>
                    agent-treatment-advisor<br>main
                </div>
            </div>
            <div>
                <div style="color:#7C3AED;font-size:0.72rem;text-transform:uppercase;
                letter-spacing:0.1em;font-weight:600;margin-bottom:0.5rem;">Execution</div>
                <div style="color:#CBD5E0;font-size:0.85rem;line-height:2.2;">
                    Parallel (thread 1)<br>Parallel (thread 2)<br>
                    Sequential (after 1+2)<br>Merge all
                </div>
            </div>
            <div>
                <div style="color:#0BC5EA;font-size:0.72rem;text-transform:uppercase;
                letter-spacing:0.1em;font-weight:600;margin-bottom:0.5rem;">Dependency</div>
                <div style="color:#CBD5E0;font-size:0.85rem;line-height:2.2;">
                    Independent ✓<br>Independent ✓<br>
                    Requires 1 + 2 ✓<br>—
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:2rem 0;color:#4A5568;font-size:0.9rem;">
        👈 Fill in patient information and click
        <strong style="color:#1E6FEB;">Run All 3 Agents</strong>
    </div>
    """, unsafe_allow_html=True)