"""
data_loader.py

Handles ingestion of raw tabular data and computes the statistical
summary that gets handed to the LLM layer. Keeping this separate from
the summarisation logic means the pipeline can support new data
sources (CSV today, a database or API tomorrow) without touching the
prompt or JSON-parsing code.
"""

from __future__ import annotations

import pandas as pd


class DataLoadError(Exception):
    """Raised when the input file can't be read or is missing required columns."""


REQUIRED_COLUMNS = {"date", "region", "product", "units_sold", "revenue", "cost"}


def load_raw_data(path: str) -> pd.DataFrame:
    """Read a CSV file into a DataFrame and do basic cleaning.

    Raises DataLoadError if the file is missing, empty, or missing
    required columns, so the pipeline can fail fast with a clear
    message instead of crashing deep inside pandas.
    """
    try:
        df = pd.read_csv(path, parse_dates=["date"])
    except FileNotFoundError as exc:
        raise DataLoadError(f"Could not find input file: {path}") from exc
    except pd.errors.EmptyDataError as exc:
        raise DataLoadError(f"Input file is empty: {path}") from exc

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise DataLoadError(f"Input file is missing required columns: {sorted(missing)}")

    # Drop fully-empty rows, coerce numerics defensively.
    df = df.dropna(how="all")
    for col in ("units_sold", "revenue", "cost"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["units_sold", "revenue", "cost"])

    df["profit"] = df["revenue"] - df["cost"]
    df["margin_pct"] = (df["profit"] / df["revenue"]).round(4) * 100

    return df


def detect_anomalies(df: pd.DataFrame, z_threshold: float = 2.0) -> pd.DataFrame:
    """Flag rows whose units_sold is more than `z_threshold` standard
    deviations from the mean for that product. This is a simple
    z-score check, not a substitute for a real anomaly-detection model,
    but it's enough to surface rows worth a human's attention.
    """
    df = df.copy()
    group = df.groupby("product")["units_sold"]
    mean = group.transform("mean")
    std = group.transform(lambda s: s.std(ddof=0))

    df["z_score"] = ((df["units_sold"] - mean) / std.replace(0, pd.NA)).fillna(0.0)
    df["is_anomaly"] = df["z_score"].abs() > z_threshold
    return df


def summarise_for_llm(df: pd.DataFrame) -> dict:
    """Reduce the raw DataFrame to compact aggregate statistics.

    We deliberately do NOT send the whole raw dataset to the LLM —
    that's slow, expensive, and unnecessary. Instead we compute the
    numbers ourselves (source of truth = pandas, not the model) and
    ask the LLM to explain and prioritise them in plain English.
    """
    by_region = (
        df.groupby("region")[["units_sold", "revenue", "profit"]]
        .sum()
        .round(2)
        .to_dict(orient="index")
    )
    by_product = (
        df.groupby("product")[["units_sold", "revenue", "profit"]]
        .sum()
        .round(2)
        .to_dict(orient="index")
    )
    anomalies = df[df["is_anomaly"]][
        ["date", "region", "product", "units_sold", "z_score"]
    ].copy()
    anomalies["date"] = anomalies["date"].astype(str)
    anomalies["z_score"] = anomalies["z_score"].round(2)

    return {
        "period_start": str(df["date"].min().date()),
        "period_end": str(df["date"].max().date()),
        "total_revenue": round(df["revenue"].sum(), 2),
        "total_profit": round(df["profit"].sum(), 2),
        "avg_margin_pct": round(df["margin_pct"].mean(), 2),
        "by_region": by_region,
        "by_product": by_product,
        "anomalies": anomalies.to_dict(orient="records"),
    }
