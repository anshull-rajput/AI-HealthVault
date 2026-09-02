# AI HealthVault

A simple Generative AI application for understanding medical PDF reports.

## Features
- Upload a medical report in PDF format
- Extract text using PyPDF
- Generate a simple AI summary using Groq
- Show important findings and possible abnormal values
- Ask questions about the uploaded report
- Save report names, dates, and detected lab values for the current browser session
- View saved report history and compare detected numeric lab values (for example, glucose) over time
- Optional Groq-powered, non-diagnostic explanation of a numeric trend
- Includes a medical safety disclaimer

## Tech Stack
- Python
- Streamlit
- Groq API
- PyPDF
- python-dotenv

## How it works
1. User uploads a PDF medical report.
2. PyPDF extracts readable text from the report.
3. The extracted text is sent to a Groq language model with a focused prompt.
4. The AI returns a summary and findings.
5. The user can ask follow-up questions about the same report.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```text
```

Run from the project root:

```bash
streamlit run frontend/app.py
```

## Report history and comparison

When a PDF is uploaded, give it a name and its check-up date, then choose **Save to this session**. The app keeps only the report name, date, filename, and detected numeric lab values in the active Streamlit browser session. It does not save the PDF, readable report text, or history to a local folder, SQLite database, GitHub, or shared deployed-server storage. The session history clears when the browser session ends.

Open **Your saved reports** to see reports from the current session. Select a test found in two or more reports, such as *fasting blood sugar*, to see its values in date order and the numerical increase or decrease. The extractor is deliberately simple and visible in the UI; users should always confirm extracted values against the PDF. Results with different units are not compared.

## Safety
This project is an educational prototype. It does not diagnose disease, determine whether a result is normal or abnormal without its report reference range, prescribe treatment, or replace a qualified healthcare professional. AI explanations describe only the supplied report or numerical change. Users should consult a doctor or other qualified healthcare professional for medical decisions and for interpretation of changing results.
