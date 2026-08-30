# Data Analytics Project

An end-to-end pipeline that ingests raw sales data, computes aggregate
statistics with pandas, sends them to the Google Gemini API for
LLM-based summarisation, and returns a validated, structured report
enabling automated report generation with no manual postprocessing.

## Why this exists

Manually reading through spreadsheets to write an executive summary
doesn't scale. This project treats an LLM as a structured-output
component in a normal data pipeline: pandas does the arithmetic, and the LLM's only job is to explain and prioritise
those numbers in plain English, returned as schema-validated JSON
rather than free-form prose.

## Architecture

```
raw CSV data
│
▼
data_loader.py → clean, validate, detect anomalies aggregate
│
▼
summarizer.py → Gemini API call, forced JSON output, 1 retry
│
▼
report_generator.py → renders validated JSON into a polished Markdown report
│
▼
reports/insights.json + reports/report.md

```

## Setup

```bash
git clone https://github.com/<your-username>/Data-Analytics-Project.git
cd Data-Analytics-Project

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then add your Gemini API key to .env
```

Get a Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## Usage

```bash
python -m src.pipeline --input data/sample_sales_data.csv --output reports
```

This runs against the included synthetic sample dataset so you can see the whole pipeline work
without needing real data. Point `--input` at any CSV with the columns
`date, region, product, units_sold, revenue, cost` to use your own data.

## Running tests

```bash
pytest
```

Tests cover the JSON schema validation logic the part of the
pipeline responsible for catching a malformed Gemini response before
it reaches the report generator. They don't call the live API, so
they run free and offline.

## Project structure

```
Data-Analytics-Project/
├── .env # your real API key
├── .env.example
├── requirements.txt
├── data/
│ └── sample_sales_data.csv
├── src/
│ ├── data_loader.py # pandas: clean, validate, z-score anomalies, aggregate
│ ├── summarizer.py # Gemini API call, forced JSON, schema validation, retry
│ ├── report_generator.py # renders validated JSON -> Markdown
│ └── pipeline.py # CLI entry point, orchestrates the three stages
├── tests/
│ └── test_schema_validation.py
└── reports/ # generated output
```

## Tech stack

- **Python** — pipeline orchestration
- **Pandas** — data ingestion, cleaning, aggregation, z-score anomaly detection
- **Google Gemini API** (`google-genai`) — structured JSON summarisation via `response_schema`
- **Pydantic** — defines and validates the JSON schema returned by Gemini
- **pytest** — schema validation tests

## Possible extensions

- Swap the CSV loader for a database connector or REST API source
- Add a Streamlit front end for non-technical users to upload their own files
- Extend anomaly detection beyond z-scores (e.g. isolation forest)
- Cache Gemini responses for identical inputs to save on API calls

## About me

I'm a Computer Science student at the University of Essex, graduated in July 2026, with practical data analytics experience from an internship in the oil and gas sector. I'm currently looking for data analyst roles in the UK.

- [LinkedIn](https://www.linkedin.com/in/ilnara-temerbulatova/)
- [Email](mailto:ilnara.temerbulatova2605@gmail.com)
