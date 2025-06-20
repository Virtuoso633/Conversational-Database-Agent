# scripts/etl_metrics.py
from dotenv import load_dotenv
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import sys
import os
import numpy as np

# Ensure the root directory is in the Python path to find the 'config' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import config

# Load environment variables from .env file
load_dotenv()

# --- Database Connection ---
try:
    client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    db = client[config.DATABASE_NAME]
    events = db.events
    metrics = db.dashboard_metrics
    print("✓ Successfully connected to MongoDB.")
except Exception as e:
    print(f"✗ Failed to connect to MongoDB: {e}")
    sys.exit(1)


# --- Data Loading ---
# Load events from the last 24 hours
print("\nFetching events from the last 24 hours...")
yesterday = datetime.utcnow() - timedelta(days=1)
events_cursor = events.find({"timestamp": {"$gte": yesterday}})
df = pd.DataFrame(list(events_cursor))

if df.empty:
    print("No events found in the last 24 hours. Exiting.")
    sys.exit(0)

print(f"Found {len(df)} total events.")

# Filter for only AI responses for metric calculation
ai_responses_df = df[df['type'] == 'ai_response'].copy()

if ai_responses_df.empty:
    print("No AI responses found in the last 24 hours. Exiting.")
    sys.exit(0)

print(f"Found {len(ai_responses_df)} AI responses to analyze.")


# --- Metrics Calculation ---
print("\nCalculating metrics...")

# 1. Compute Top-Level Intent Counts
ai_responses_df['intent_type'] = ai_responses_df['intent'].apply(
    lambda x: x.get('query_type', 'unknown') if isinstance(x, dict) else str(x)
)
intent_counts = ai_responses_df['intent_type'].value_counts().to_dict()
print(f"Computed Intent Counts: {intent_counts}")

# 2. Compute Average Execution Time
avg_exec_time = ai_responses_df['execution_time'].mean()
if pd.isna(avg_exec_time):
    avg_exec_time = 0.0
print(f"Computed Average Execution Time: {avg_exec_time:.4f}s")

# 3. Compute Total Data Gaps (Failures)
gaps = ai_responses_df[ai_responses_df['response_success'] == False].shape[0]
print(f"Computed Total Data Gaps (Failures): {gaps}")

# 4. **NEW**: Compute Error Type Breakdown
# Filter for only the error intents to get more detail
error_df = ai_responses_df[ai_responses_df['intent_type'] == 'error']
if not error_df.empty:
    error_df['error_type'] = error_df['intent'].apply(
        lambda x: x.get('error_type', 'unknown_error') if isinstance(x, dict) else 'unknown_error'
    )
    error_type_counts = error_df['error_type'].value_counts().to_dict()
    print(f"Computed Error Breakdown: {error_type_counts}")
else:
    error_type_counts = {}
    print("No 'error' intents found to break down.")


# --- Persist Metrics to Database ---
print("\nUpdating metrics in the database...")
# Use today's date for the metric record to represent "metrics for the past day"
today_date = datetime.utcnow().date().isoformat()

metrics.update_one(
    {"date": today_date},
    {
        "$set": {
            "intent_counts": intent_counts,
            "error_type_counts": error_type_counts,  # Add the new metric
            "avg_exec_time": float(avg_exec_time),
            "data_gaps": int(gaps),
            "last_updated": datetime.utcnow()
        }
    },
    upsert=True
)

print(f"✓ Successfully updated metrics for date: {today_date}")
