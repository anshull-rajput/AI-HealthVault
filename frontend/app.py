import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from backend.ai_service import HealthVaultAI
from backend.report_store import available_tests, compare_test, extract_lab_values, list_reports, save_report

st.set_page_config(page_title="AI HealthVault", page_icon="🏥", layout="wide")
st.title("🏥 AI HealthVault")
st.write("Understand your medical report with a simple Generative AI assistant.")
st.caption("Educational prototype — not a medical diagnosis tool.")

try:
    ai = HealthVaultAI()
except ValueError:
    ai = None
    st.warning("Groq API key not found. You can still save and compare reports; add GROQ_API_KEY to enable AI explanations.")


def extract_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


st.subheader("📄 Upload & understand")
uploaded_file = st.file_uploader("Upload a medical report (PDF)", type=["pdf"])
st.divider()
history_tab = st.container()

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

    st.subheader("Save this report to history")
    extracted_values = extract_lab_values(report_text)
    save_col1, save_col2 = st.columns(2)
    with save_col1:
        report_name = st.text_input("Report name", value=Path(uploaded_file.name).stem)
    with save_col2:
        report_date = st.date_input("Report / check-up date")
    if extracted_values:
        st.caption("Likely numeric lab values found in the PDF. Please check the PDF if a value looks incorrect.")
        st.dataframe(
            [{"Test": item["label"], "Value": item["value"], "Unit": item["unit"]} for item in extracted_values],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No clear numeric lab values were detected. You can still save the PDF and view it in your history.")
    if st.button("💾 Save report locally", use_container_width=True):
        if report_name.strip():
            try:
                save_report(uploaded_file, report_name, report_date, report_text, extracted_values)
                st.success("Saved locally on this computer. Scroll to Saved report history to compare it later.")
            except Exception as exc:
                st.error(f"Could not save this report: {exc}")
        else:
            st.error("Please enter a report name.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Generate Summary", use_container_width=True):
            if not ai:
                st.error("Add GROQ_API_KEY to .env to generate AI explanations.")
            else:
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
            if not ai:
                st.error("Add GROQ_API_KEY to .env to generate AI explanations.")
            else:
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
        if not ai:
            st.error("Add GROQ_API_KEY to .env to ask AI questions.")
        else:
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

with history_tab:
    st.subheader("Your saved reports")
    st.caption("Reports are saved locally in this app's data folder on this computer. They are not uploaded to GitHub.")
    saved_reports = list_reports()
    if not saved_reports:
        st.info("No reports saved yet. Upload a PDF above, add a name and date, then save it.")
    else:
        st.dataframe(
            [
                {"Date": report["report_date"], "Name": report["report_name"], "File": report["original_filename"], "Detected values": len(report["lab_values"])}
                for report in saved_reports
            ],
            use_container_width=True,
            hide_index=True,
        )
        tests = available_tests(saved_reports)
        if tests:
            selected_test = st.selectbox("Compare a lab value", tests, format_func=lambda value: value.title())
            comparison_rows, change = compare_test(saved_reports, selected_test)
            if comparison_rows:
                st.dataframe(comparison_rows, use_container_width=True, hide_index=True)
                if change is None:
                    st.info("Save at least two reports containing this same test to see a change.")
                else:
                    direction = "increased" if change > 0 else "decreased" if change < 0 else "did not change"
                    unit = comparison_rows[-1]["Unit"]
                    st.metric("Change from first to latest saved result", f"{change:+g} {unit}", f"It {direction}")
                    st.caption("This shows the numeric difference only. Different labs, units, methods, and reference ranges can affect interpretation.")
                    if ai and st.button("🤖 Explain this change in simple language", use_container_width=True):
                        prompt = f"""Explain this lab-value trend in simple, careful language.
Facts only: {selected_test} changed from {comparison_rows[0]['Value']:g} {unit} on {comparison_rows[0]['Date']} to {comparison_rows[-1]['Value']:g} {unit} on {comparison_rows[-1]['Date']} ({change:+g} {unit}).
Do not diagnose, say whether it is normal/abnormal without a shown reference range, or prescribe treatment. Explain that a clinician should interpret it with symptoms, history, and the report's reference range. Offer sensible questions to ask a healthcare professional."""
                        with st.spinner("Preparing explanation..."):
                            try:
                                st.markdown("### Trend explanation")
                                st.write(ai.ask(prompt))
                            except Exception as exc:
                                st.error(f"Groq request failed: {exc}")
        else:
            st.info("The saved PDFs do not contain clearly detected numeric lab values to compare yet.")
    st.info("⚠️ This history feature is educational and not a diagnosis or treatment plan. Ask a qualified healthcare professional to interpret trends, especially if results change or you have symptoms.")
