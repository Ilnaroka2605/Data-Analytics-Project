# AI-Powered Data Application

An end-to-end pipeline that ingests raw sales data, computes aggregate
statistics, sends them to the OpenAI API for LLM-based summarisation,
and returns clean, structured JSON — enabling fully automated report
generation with no manual postprocessing.

## Why this exists

Manually reading through spreadsheets to write an executive summary
doesn't scale. This project treats an LLM as a structured-output
component in a normal data pipeline: pandas does the arithmetic (the
source of truth), and the LLM's only job is to explain and prioritise
those numbers in plain English, returned as validated JSON rather than
free-form prose.

## Architecture

```
raw CSV data
     │
     ▼
data_loader.py     → clean, validate, detect anomalies (z-score), aggregate
     │
     ▼
summarizer.py      → OpenAI API call, forced JSON output, schema validation, 1 retry
     │
     ▼
report_generator.py → renders validated JSON into a polished Markdown report
     │
     ▼
reports/insights.json  +  reports/report.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then add your OpenAI API key to .env
```

## Usage

```bash
python -m src.pipeline --input data/sample_sales_data.csv --output reports/
```

This runs against the included synthetic sample dataset (with a few
deliberate anomalies baked in) so you can see the whole pipeline work
without needing real data. Point `--input` at any CSV with the columns
`date, region, product, units_sold, revenue, cost` to use your own data.

## Running tests

```bash
pytest
```

Tests cover the JSON schema validation logic — the part of the
pipeline responsible for catching a malformed LLM response before it
reaches the report generator. They don't call the live API, so they
run free and offline.

## Tech stack

- **Python** — pipeline orchestration
- **Pandas** — data ingestion, cleaning, aggregation, anomaly detection
- **OpenAI API** — structured JSON summarisation (`response_format: json_object`)
- **pytest** — schema validation tests

## Possible extensions

- Swap the CSV loader for a database connector or REST API source
- Add a Streamlit front end for non-technical users to upload their own files
- Extend anomaly detection beyond z-scores (e.g. isolation forest)
