import os
import sys
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import streamlit as st
import datetime
from bson import ObjectId

# Ensure the root directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import config

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="World Model Insights Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("World Model Insights Dashboard")
st.markdown("Analytics on agent performance, user queries, and data gaps.")

# --- Helper to clean MongoDB documents for JSON display ---
def clean_mongo_document(doc):
    """Recursively convert MongoDB types to JSON-serializable types."""
    if isinstance(doc, dict):
        return {k: clean_mongo_document(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [clean_mongo_document(v) for v in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime.datetime):
        return doc.isoformat()
    else:
        return doc

# --- Data Loading and Caching ---
@st.cache_data(ttl=600)
def load_metrics_data():
    client = MongoClient(config.MONGODB_URI)
    db = client[config.DATABASE_NAME]
    cursor = db.dashboard_metrics.find().sort("date", -1)
    data = list(cursor)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    # Convert 'date' to datetime and set as index
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date', ascending=False)
        df = df.set_index('date')
    return df

# Load the data
df = load_metrics_data()

# Handle the Empty State
if df.empty:
    st.warning("No metrics data found.")
    st.info("Please run the ETL script to populate the dashboard: `python scripts/etl_metrics.py`")
    st.stop()

# --- Show Latest Raw Metrics Document ---
st.subheader("Latest Raw Metrics Document")
try:
    latest_doc = df.iloc[0].to_dict()
    st.json(clean_mongo_document(latest_doc))
except Exception as e:
    st.info(f"Could not display raw metrics document: {e}")

# --- Show Recent Raw Metrics Documents (Top 5) ---
st.subheader("Recent Raw Metrics Documents")
for i, row in df.head(5).iterrows():
    st.json(clean_mongo_document(row.to_dict()))

# --- Key Performance Indicators (KPIs) ---
st.subheader("Key Performance Metrics (Last 30 Days)")
col1, col2, col3 = st.columns(3)

total_gaps = df["data_gaps"].sum()
avg_time = df["avg_exec_time"].mean()
total_queries = df['intent_counts'].apply(lambda x: sum(x.values()) if isinstance(x, dict) else 0).sum()

col1.metric("Total Data Gaps", f"{int(total_gaps)}")
col2.metric("Average Execution Time", f"{avg_time:.2f}s")
col3.metric("Total Queries Analyzed", f"{int(total_queries)}")

# --- Intent Distribution Bar Chart ---
st.subheader("Intent Distribution")
intent_counts_df = pd.DataFrame(df['intent_counts'].tolist()).fillna(0)
intent_counts_sum = intent_counts_df.sum().sort_values(ascending=False)
st.bar_chart(intent_counts_sum)

# --- Error Type Distribution Bar Chart ---
st.subheader("Error Type Distribution")
if 'error_type_counts' in df.columns:
    error_type_counts_df = pd.DataFrame(df['error_type_counts'].tolist()).fillna(0)
    error_type_counts_sum = error_type_counts_df.sum().sort_values(ascending=False)
    st.bar_chart(error_type_counts_sum)
else:
    st.info("No error type data available.")

# --- Average Execution Time Line Chart ---
st.subheader("Average Execution Time Over Time")
if df.shape[0] > 1 and 'avg_exec_time' in df.columns:
    st.line_chart(df['avg_exec_time'])
else:
    st.info("Not enough data for line chart.")

# --- Data Gaps Table ---
st.subheader("Data Gaps Table")
st.dataframe(df[['data_gaps']])