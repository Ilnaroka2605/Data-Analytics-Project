"""
pipeline.py

End-to-end orchestration, runnable from the command line:

    python -m src.pipeline --input data/sample_sales_data.csv --output reports/

Steps:
  1. Ingest raw CSV data (data_loader)
  2. Detect anomalies and compute aggregate stats
  3. Send stats to the OpenAI API for LLM-based summarisation (summarizer)
  4. Save both the raw structured JSON and a polished Markdown report (report_generator)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.data_loader import DataLoadError, detect_anomalies, load_raw_data, summarise_for_llm
from src.report_generator import build_markdown_report
from src.summarizer import SummarizerError, summarise_stats


def run_pipeline(input_path: str, output_dir: str, model: str = "gpt-4o-mini") -> None:
    load_dotenv()

    print(f"[1/4] Loading data from {input_path} ...")
    try:
        df = load_raw_data(input_path)
    except DataLoadError as exc:
        print(f"Error loading data: {exc}", file=sys.stderr)
        sys.exit(1)

    print("[2/4] Detecting anomalies and computing aggregate stats ...")
    df = detect_anomalies(df)
    stats = summarise_for_llm(df)

    print(f"[3/4] Requesting LLM summarisation ({model}) ...")
    try:
        insights = summarise_stats(stats, model=model)
    except SummarizerError as exc:
        print(f"Error during summarisation: {exc}", file=sys.stderr)
        sys.exit(1)

    print("[4/4] Writing report and structured JSON ...")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "insights.json"
    json_path.write_text(json.dumps({"stats": stats, "insights": insights}, indent=2, default=str))

    report_path = out_dir / "report.md"
    report_path.write_text(build_markdown_report(stats, insights))

    print(f"Done. Wrote {json_path} and {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-powered data summarisation pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--output", default="reports", help="Directory to write outputs to")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use")
    args = parser.parse_args()

    run_pipeline(args.input, args.output, args.model)


if __name__ == "__main__":
    main()
