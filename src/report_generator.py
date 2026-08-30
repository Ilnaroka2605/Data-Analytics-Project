"""
report_generator.py
Turns the structured report insights into a polished, human-readable
Markdown report
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from src.summarizer import InsightReport


def render_markdown(report: InsightReport, stats: dict) -> str:
    anomaly_lines = [f"- {explanation}" for explanation in report.anomaly_explanations] or ["- None detected."]

    lines = [
        f"# Sales Insight Report",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Executive Summary",
        report.executive_summary,
        "",
        "## Key Insights",
        *[f"- {insight}" for insight in report.key_insights],
        "",
        "## Anomalies Detected",
        *anomaly_lines,
        "",
        "## Recommendations",
        *[f"{i+1}. {rec}" for i, rec in enumerate(report.recommendations)],
        "",
        "## Raw Totals",
        f"- Revenue: ${stats['totals']['revenue']:,.2f}",
        f"- Profit: ${stats['totals']['profit']:,.2f}",
        f"- Units sold: {stats['totals']['units_sold']:,}",
    ]
    return "\n".join(lines)


def save_report(report: InsightReport, stats: dict, output_dir: str | Path = "reports") -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    md_path = output_dir / "report.md"
    md_path.write_text(render_markdown(report, stats), encoding="utf-8")

    json_path = output_dir / "insights.json"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    return md_path