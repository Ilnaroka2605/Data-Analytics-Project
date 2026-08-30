"""
report_generator.py

Turns the structured JSON insights into a polished, human-readable
Markdown report — the "automated report generation without manual
postprocessing" step. Because the input is already clean, validated
JSON, this is pure formatting: no parsing of messy LLM prose required.
"""

from __future__ import annotations

from datetime import datetime


def build_markdown_report(stats: dict, insights: dict) -> str:
    lines = [
        f"# Sales Analytics Report",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
        f"Period {stats['period_start']} to {stats['period_end']}*",
        "",
        f"## Headline",
        insights["headline"],
        "",
        f"## Key Metrics",
        f"- Total revenue: £{stats['total_revenue']:,.2f}",
        f"- Total profit: £{stats['total_profit']:,.2f}",
        f"- Average margin: {stats['avg_margin_pct']:.1f}%",
        "",
        "## Key Insights",
    ]
    lines += [f"- {item}" for item in insights["key_insights"]]

    lines += ["", "## Risks & Anomalies"]
    lines += [f"- {item}" for item in insights["risks"]]

    lines += ["", "## Recommendations"]
    lines += [f"- {item}" for item in insights["recommendations"]]

    if stats.get("anomalies"):
        lines += ["", "## Flagged Data Points", "", "| Date | Region | Product | Units Sold | Z-score |",
                   "|---|---|---|---|---|"]
        for a in stats["anomalies"]:
            lines.append(
                f"| {a['date']} | {a['region']} | {a['product']} | "
                f"{a['units_sold']} | {a['z_score']} |"
            )

    return "\n".join(lines) + "\n"
