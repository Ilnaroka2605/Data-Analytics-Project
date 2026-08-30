"""
app.py
Streamlit front end for the sales analytics pipeline.
Upload a CSV -> see the numbers -> get an AI-generated executive summary -> download the report.
This file only handles UI; all real logic still lives in src/.
"""

import streamlit as st
import pandas as pd
from src.data_loader import load_and_clean, detect_anomalies, aggregate
from src.summarizer import summarize
from src.report_generator import render_markdown

st.set_page_config(page_title="Sales Insight Pipeline", page_icon="📊", layout="wide")

st.title("📊 AI-Powered Sales Insight Pipeline")
st.caption("pandas does the math — Gemini explains it in plain English.")

# --- Input ---
uploaded_file = st.file_uploader(
    "Upload a sales CSV (columns: date, region, product, units_sold, revenue, cost)",
    type="csv",
)
use_sample = st.button("...or just use the included sample data")

if "csv_source" not in st.session_state:
    st.session_state.csv_source = None

if uploaded_file is not None:
    st.session_state.csv_source = uploaded_file
elif use_sample:
    st.session_state.csv_source = "data/sample_sales_data.csv"

csv_source = st.session_state.csv_source

if csv_source is not None:
    try:
        # --- Stage 1: pandas (fast, no API call yet) ---
        df = load_and_clean(csv_source)
        df = detect_anomalies(df)
        stats = aggregate(df)

        st.subheader("Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"${stats['totals']['revenue']:,.2f}")
        col2.metric("Total Profit", f"${stats['totals']['profit']:,.2f}")
        col3.metric("Units Sold", f"{stats['totals']['units_sold']:,}")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.write("**Revenue by Region**")
            st.bar_chart(pd.DataFrame(stats["by_region"]).T["total_revenue"])
        with chart_col2:
            st.write("**Revenue by Product**")
            st.bar_chart(pd.DataFrame(stats["by_product"]).T["total_revenue"])

        if stats["anomalies"]:
            st.subheader(f"⚠️ {len(stats['anomalies'])} Anomalies Detected")
            st.dataframe(pd.DataFrame(stats["anomalies"]), width="stretch")
        else:
            st.info("No statistical anomalies detected in this data.")

        # --- Stage 2: Gemini (only runs when the user asks for it) ---
        if st.button("🤖 Generate AI Summary", type="primary"):
            with st.spinner("Asking Gemini to analyze the numbers..."):
                report = summarize(stats)

            st.subheader("Executive Summary")
            st.write(report.executive_summary)

            st.subheader("Key Insights")
            for insight in report.key_insights:
                st.write(f"- {insight}")

            if report.anomaly_explanations:
                st.subheader("Anomaly Explanations")
                for explanation in report.anomaly_explanations:
                    st.write(f"- {explanation}")

            st.subheader("Recommendations")
            for i, rec in enumerate(report.recommendations, start=1):
                st.write(f"{i}. {rec}")

            # --- Downloads ---
            st.download_button(
                "Download report.md",
                data=render_markdown(report, stats),
                file_name="report.md",
                mime="text/markdown",
            )
            st.download_button(
                "Download insights.json",
                data=report.model_dump_json(indent=2),
                file_name="insights.json",
                mime="application/json",
            )

    except ValueError as e:
        st.error(f"There's a problem with that CSV: {e}")
    except KeyError:
        st.error("Missing GEMINI_API_KEY — check your .env file.")
    except Exception as e:
        st.error(f"Something went wrong: {e}")
else:
    st.info("Upload a CSV above, or click the sample-data button, to get started.")