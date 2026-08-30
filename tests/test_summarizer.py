"""
Unit tests for the schema-validation logic in summarizer.py.

These tests do NOT call the real OpenAI API (no network, no cost) —
they test the validation function directly, which is the part of the
code most worth having tests for: it's what stops a malformed LLM
response from silently producing a broken report.
"""

import pytest

from src.summarizer import SummarizerError, _validate_schema


def test_valid_payload_passes():
    payload = {
        "headline": "Revenue grew steadily with one regional outlier.",
        "key_insights": ["Insight one", "Insight two"],
        "risks": ["Risk one"],
        "recommendations": ["Do this", "Then this"],
    }
    _validate_schema(payload)  # should not raise


def test_missing_key_raises():
    payload = {
        "headline": "Missing keys example",
        "key_insights": [],
        "risks": [],
        # "recommendations" missing
    }
    with pytest.raises(SummarizerError, match="missing required keys"):
        _validate_schema(payload)


def test_wrong_type_raises():
    payload = {
        "headline": "Wrong type example",
        "key_insights": "should be a list, not a string",
        "risks": [],
        "recommendations": [],
    }
    with pytest.raises(SummarizerError, match="Expected 'key_insights' to be a list"):
        _validate_schema(payload)
