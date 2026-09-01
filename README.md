# AI HealthVault

A simple Generative AI application for understanding medical PDF reports.

## Features
- Upload a medical report in PDF format
- Extract text using PyPDF
- Generate a simple AI summary using Groq
- Show important findings and possible abnormal values
- Ask questions about the uploaded report
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
GROQ_API_KEY=your_api_key_here
```

Run:

```bash
streamlit run app.py
```

## Safety
This project is an educational prototype. It does not diagnose disease, prescribe treatment, or replace a qualified healthcare professional. Users should consult a doctor for medical decisions.
