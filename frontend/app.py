import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from backend.ai_service import HealthVaultAI

st.set_page_config(page_title="AI HealthVault", page_icon="🏥", layout="wide")
st.title("🏥 AI HealthVault")
st.write("Understand your medical report with a simple Generative AI assistant.")
st.caption("Educational prototype — not a medical diagnosis tool.")

try:
    ai = HealthVaultAI()
except ValueError:
    st.warning("Groq API key not found. Add GROQ_API_KEY to your .env file and restart the app.")
    st.stop()


def extract_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


uploaded_file = st.file_uploader("📄 Upload a medical report (PDF)", type=["pdf"])

if uploaded_file:
    try:
        report_text = extract_text(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read this PDF: {exc}")
        st.stop()

    if not report_text:
        st.error("No readable text was found in this PDF. Please upload a text-based medical report.")
        st.stop()

    st.success(f"Report loaded: {uploaded_file.name}")
    report = report_text[:9000]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Generate Summary", use_container_width=True):
            prompt = f"""Create a simple patient-friendly summary of this medical report.
Use these sections: Report overview, Key findings, Values outside reference range (only if explicitly shown), Questions for the doctor.
Do not invent values or diagnose.

REPORT:\n{report}"""
            with st.spinner("Generating summary..."):
                try:
                    st.session_state.summary = ai.ask(prompt)
                except Exception as exc:
                    st.error(f"Groq request failed: {exc}")

    with col2:
        if st.button("🔎 Find Important Points", use_container_width=True):
            prompt = f"""List the most important points from this medical report in simple language.
Mention values and reference ranges only when explicitly present. Do not diagnose or prescribe treatment.

REPORT:\n{report}"""
            with st.spinner("Finding important points..."):
                try:
                    st.session_state.findings = ai.ask(prompt)
                except Exception as exc:
                    st.error(f"Groq request failed: {exc}")

    if st.session_state.get("summary"):
        st.subheader("📋 AI Summary")
        st.markdown(st.session_state.summary)
    if st.session_state.get("findings"):
        st.subheader("⭐ Important Findings")
        st.markdown(st.session_state.findings)

    st.divider()
    st.subheader("💬 Ask AI About Your Report")
    question = st.text_input("Example: What does my hemoglobin result mean?")
    if st.button("Ask Question", use_container_width=True) and question.strip():
        prompt = f"""Answer the user's question using only this medical report. Explain simply. If information is missing, say so. Do not diagnose or prescribe medicine.

QUESTION:\n{question}

REPORT:\n{report}"""
        with st.spinner("Thinking..."):
            try:
                st.markdown("### 💡 Answer")
                st.write(ai.ask(prompt))
            except Exception as exc:
                st.error(f"Groq request failed: {exc}")

    st.info("⚠️ Educational information only. Discuss medical results and treatment decisions with a qualified healthcare professional.")
