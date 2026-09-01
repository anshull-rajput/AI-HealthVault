import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader

load_dotenv()

st.set_page_config(page_title="AI HealthVault", page_icon="🏥", layout="wide")

st.title("🏥 AI HealthVault")
st.write("Understand your medical report with a simple Generative AI assistant.")
st.caption("Educational prototype — not a medical diagnosis tool.")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.warning("Groq API key not found. Add GROQ_API_KEY to your .env file and restart the app.")
    st.stop()

# Groq API client. The longer timeout helps with larger medical reports.
client = Groq(api_key=api_key, timeout=120.0, max_retries=2)
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def extract_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n".join(pages).strip()


def ask_ai(prompt):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful medical-report explanation assistant. "
                    "Use only the supplied report text. Do not diagnose disease or prescribe medicine. "
                    "Clearly say when information is missing. Explain medical terms in simple language."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    return response.choices[0].message.content


uploaded_file = st.file_uploader("📄 Upload a medical report (PDF)", type=["pdf"])

if uploaded_file:
    with st.spinner("Reading your report..."):
        try:
            report_text = extract_text(uploaded_file)
        except Exception as exc:
            st.error(f"Could not read this PDF: {exc}")
            st.stop()

    if not report_text:
        st.error("No readable text was found in this PDF. Please upload a text-based medical report.")
        st.stop()

    st.success(f"Report loaded: {uploaded_file.name}")
    # Keep prompts compact so Groq responds faster and reliably.
    report_for_ai = report_text[:9000]

    if "summary" not in st.session_state:
        st.session_state.summary = ""
    if "findings" not in st.session_state:
        st.session_state.findings = ""

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🤖 Generate Summary", use_container_width=True):
            prompt = f"""
Read the following medical report and create a simple patient-friendly summary.

Return exactly these sections:
1. Report overview
2. Key findings
3. Values outside the provided reference range (only if explicitly shown)
4. Questions the patient may ask their doctor

Do not invent values or diagnoses.

REPORT:
{report_for_ai}
"""
            with st.spinner("Generating summary..."):
                try:
                    st.session_state.summary = ask_ai(prompt)
                except Exception as exc:
                    st.error(f"Groq request failed: {exc}")

    with col2:
        if st.button("🔎 Find Important Points", use_container_width=True):
            prompt = f"""
Review this medical report and list the most important points in simple language.
For each point, mention the test/value only when it is explicitly present in the report.
If a reference range is present, say whether the value is within or outside that range.
Do not diagnose or recommend treatment.

REPORT:
{report_for_ai}
"""
            with st.spinner("Finding important points..."):
                try:
                    st.session_state.findings = ask_ai(prompt)
                except Exception as exc:
                    st.error(f"Groq request failed: {exc}")

    if st.session_state.summary:
        st.subheader("📋 AI Summary")
        st.markdown(st.session_state.summary)

    if st.session_state.findings:
        st.subheader("⭐ Important Findings")
        st.markdown(st.session_state.findings)

    st.divider()
    st.subheader("💬 Ask AI About Your Report")
    question = st.text_input("Example: What does my hemoglobin result mean?")

    if st.button("Ask Question", use_container_width=True) and question.strip():
        prompt = f"""
Answer the user's question using only the medical report below.
Explain the answer in simple language. If the report does not contain enough information,
say so. Do not diagnose disease or prescribe medicine.

USER QUESTION:
{question}

REPORT:
{report_for_ai}
"""
        with st.spinner("Thinking..."):
            try:
                answer = ask_ai(prompt)
                st.markdown("### 💡 Answer")
                st.write(answer)
            except Exception as exc:
                st.error(f"Groq request failed: {exc}")

    st.info("⚠️ Medical disclaimer: AI HealthVault is for educational information only. Always discuss medical results and treatment decisions with a qualified healthcare professional.")
