"""
summarizer.py

The "prompt layer" referenced on the CV: turns the aggregate stats
produced by data_loader.py into a single OpenAI API call that returns
STRUCTURED, machine-parseable JSON — no manual copy-pasting of prose
into a report ever again.

Design choices worth knowing (and worth being able to explain in an
interview):
- We use `response_format={"type": "json_object"}` so the API itself
  enforces valid JSON, rather than hoping the model behaves.
- We validate the returned JSON against an expected schema before
  it's allowed anywhere near the report generator. Bad output fails
  loudly instead of silently producing a broken report.
- We retry once on a schema-validation failure, since LLMs occasionally
  drop a key or return the wrong type on the first try.
"""

from __future__ import annotations

import json
import os

from openai import OpenAI, OpenAIError

REQUIRED_KEYS = {"headline", "key_insights", "risks", "recommendations"}

SYSTEM_PROMPT = """You are a data analyst producing an executive summary \
for non-technical stakeholders. You will be given aggregate sales \
statistics as JSON. Respond ONLY with a JSON object with exactly these \
keys:

- "headline": a one-sentence summary of overall performance (string)
- "key_insights": 3-5 short bullet-point observations (array of strings)
- "risks": 1-3 concerns or anomalies worth flagging (array of strings)
- "recommendations": 2-4 concrete, prioritised next actions (array of strings)

Do not include any text outside the JSON object. Do not invent numbers \
that are not implied by the data provided."""


class SummarizerError(Exception):
    """Raised when the LLM call fails or returns data that doesn't match the schema."""


def _validate_schema(payload: dict) -> None:
    missing = REQUIRED_KEYS - payload.keys()
    if missing:
        raise SummarizerError(f"LLM response missing required keys: {sorted(missing)}")
    for key in ("key_insights", "risks", "recommendations"):
        if not isinstance(payload[key], list):
            raise SummarizerError(f"Expected '{key}' to be a list, got {type(payload[key])}")


def summarise_stats(stats: dict, model: str = "gpt-4o-mini") -> dict:
    """Send aggregate stats to the OpenAI API and return validated,
    structured insights. Retries once if the first response fails
    schema validation.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SummarizerError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    client = OpenAI(api_key=api_key)
    user_content = json.dumps(stats, indent=2)

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                temperature=0.2,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
            raw = response.choices[0].message.content
            payload = json.loads(raw)
            _validate_schema(payload)
            return payload
        except (OpenAIError, json.JSONDecodeError, SummarizerError) as exc:
            last_error = exc
            continue

    raise SummarizerError(f"LLM call failed after retry: {last_error}")
