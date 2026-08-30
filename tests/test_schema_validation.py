"""
Tests for the JSON schema validation logic in summarizer.py.
No network calls — these test that InsightReport correctly accepts good data
and rejects bad data, using Pydantic directly.
"""

import pytest
from pydantic import ValidationError
from src.summarizer import InsightReport


def test_valid_report_parses():
    data = {
        "executive_summary": "Sales were strong this quarter.",
        "key_insights": ["Region A grew 10%"],
        "anomaly_explanations": ["Spike likely due to a bulk order"],
        "recommendations": ["Investigate the spike"],
    }
    report = InsightReport.model_validate(data)
    assert report.executive_summary == "Sales were strong this quarter."
    assert len(report.key_insights) == 1


def test_missing_field_raises():
    data = {
        "executive_summary": "Sales were strong.",
        "key_insights": ["Region A grew"],
        # missing anomaly_explanations and recommendations
    }
    with pytest.raises(ValidationError):
        InsightReport.model_validate(data)


def test_wrong_type_raises():
    data = {
        "executive_summary": "Sales were strong.",
        "key_insights": "should be a list, not a string",
        "anomaly_explanations": [],
        "recommendations": [],
    }
    with pytest.raises(ValidationError):
        InsightReport.model_validate(data)