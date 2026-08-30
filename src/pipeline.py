"""
pipeline.py
The single entry point: CSV in -> Markdown report out.
Chains data_loader -> summarizer -> report_generator.
"""

from __future__ import annotations
import argparse
from src.data_loader import load_and_summarize
from src.summarizer import summarize
from src.report_generator import save_report


def run(input_csv: str, output_dir: str = "reports") -> None:
    print(f"[pipeline] loading and aggregating {input_csv}...")
    stats = load_and_summarize(input_csv)

    print("[pipeline] sending to Gemini for summarization...")
    report = summarize(stats)

    print("[pipeline] rendering report...")
    path = save_report(report, stats, output_dir)

    print(f"[pipeline] done -> {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-powered sales data pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", default="reports", help="Output directory")
    args = parser.parse_args()
    run(args.input, args.output)