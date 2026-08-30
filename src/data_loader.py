"""
data_loader.py
Responsibilities:
  - load & validate the raw CSV
  - clean it (types, missing values, duplicates)
  - detect statistical anomalies so the AI has something concrete to flag
  - aggregate into the summary stats the AI will explain in plain English
"""

from __future__ import annotations
import pandas as pd
from pathlib import Path

REQUIRED_COLUMNS = {"date", "region", "product", "units_sold", "revenue", "cost"}
ZSCORE_THRESHOLD = 2.5 

def load_and_clean(csv_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"CSV is missing required columns: {missing_cols}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ("units_sold", "revenue", "cost"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=list(REQUIRED_COLUMNS)).drop_duplicates()
    dropped = before - len(df)
    if dropped:
        print(f"[data_loader] dropped {dropped} invalid/duplicate rows")

    df["profit"] = df["revenue"] - df["cost"]
    return df.reset_index(drop=True)


def detect_anomalies(df: pd.DataFrame, value_col: str = "revenue") -> pd.DataFrame:
    def zscore(group: pd.Series) -> pd.Series:
        std = group.std(ddof=0)
        if std == 0 or pd.isna(std):
            return pd.Series(0, index=group.index)
        return (group - group.mean()) / std

    df = df.copy()
    df["zscore"] = df.groupby("product")[value_col].transform(zscore)
    df["is_anomaly"] = df["zscore"].abs() > ZSCORE_THRESHOLD
    return df


def aggregate(df: pd.DataFrame) -> dict:
    by_region = (
        df.groupby("region")
        .agg(total_revenue=("revenue", "sum"), total_profit=("profit", "sum"), units_sold=("units_sold", "sum"))
        .round(2).to_dict(orient="index")
    )
    by_product = (
        df.groupby("product")
        .agg(total_revenue=("revenue", "sum"), total_profit=("profit", "sum"), units_sold=("units_sold", "sum"))
        .round(2).to_dict(orient="index")
    )
    anomalies = (
        df[df["is_anomaly"]][["date", "region", "product", "revenue", "zscore"]]
        .assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d"))
        .round(2).to_dict(orient="records")
    )
    return {
        "totals": {
            "revenue": round(df["revenue"].sum(), 2),
            "profit": round(df["profit"].sum(), 2),
            "units_sold": int(df["units_sold"].sum()),
        },
        "by_region": by_region,
        "by_product": by_product,
        "anomalies": anomalies,
    }


def load_and_summarize(csv_path: str | Path) -> dict:
    """The one function pipeline.py will actually call."""
    df = load_and_clean(csv_path)
    df = detect_anomalies(df)
    return aggregate(df)