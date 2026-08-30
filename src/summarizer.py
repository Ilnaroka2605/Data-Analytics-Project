"""
summarizer.py
Sends the aggregated numbers to Gemini and get back a structured report
Design:
  - pandas numbers go into a prompt
  - Gemini is constrained to a JSON schema via a Pydantic model
  - if the response fails to parse/validate, retry once with a stricter prompt
  - if it still fails, raise loudly rather than pass garbage downstream
"""

from __future__ import annotations
import os
import json
from google import genai
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

load_dotenv()  # reads your .env file into environment variables

MODEL_NAME = "gemini-2.5-flash"


class InsightReport(BaseModel):
    executive_summary: str
    key_insights: list[str]
    anomaly_explanations: list[str]
    recommendations: list[str]


def _build_prompt(stats: dict) -> str:
    return f"""
You are a data analyst. Below is aggregated sales data already computed
do not recalculate anything, just interpret it.

{json.dumps(stats, indent=2, default=str)}

Write:
- executive_summary: 2-3 sentence plain-English overview
- key_insights: 3-5 observations about regions/products
- anomaly_explanations: one plain-English sentence per anomaly, explaining what likely happened
- recommendations: 2-4 concrete, actionable next steps
""".strip()


def summarize(stats: dict) -> InsightReport:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = _build_prompt(stats)

    for attempt in range(2):  # 1 try + 1 retry
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": InsightReport,
            },
        )
        try:
            return InsightReport.model_validate_json(response.text)
        except (ValidationError, ValueError) as e:
            if attempt == 0:
                print(f"[summarizer] validation failed, retrying: {e}")
                prompt += "\n\nIMPORTANT: your previous response did not match the required JSON schema. Follow it exactly."
                continue
            raise RuntimeError(f"Gemini response failed schema validation twice: {e}") from e