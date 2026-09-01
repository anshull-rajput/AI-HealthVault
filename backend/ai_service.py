import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class HealthVaultAI:
    """Small backend service that sends report questions to a Groq-hosted LLM."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured")
        self.client = Groq(api_key=api_key, timeout=120.0, max_retries=2)
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def ask(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful medical-report explanation assistant. "
                        "Use only the supplied report text. Do not diagnose disease or prescribe medicine. "
                        "Explain medical terms in simple language."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return response.choices[0].message.content
