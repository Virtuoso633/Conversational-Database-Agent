# tests/validate_etl.py
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import sys
import os
import numpy as np

# Ensure the root directory is in the Python path to find the 'config' module.
# This assumes the script is run from the project's root directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import config

# --- Database Connection ---
try:
    client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    db = client[config.DATABASE_NAME]
    print("✓ Successfully connected to MongoDB.")
except Exception as e:
    print(f"✗ Failed to connect to MongoDB: {e}")
    sys.exit(1)


# --- Rival ETL Logic ---
print("\n--- Rival ETL Validation ---")

# FIX 1: Fetch only the last 24 hours of events to prevent timeouts and match the main ETL script.
print("Fetching events from the last 24 hours...")
yesterday = datetime.utcnow() - timedelta(days=1)
events_cursor = db.events.find({"timestamp": {"$gte": yesterday}})
events_df = pd.DataFrame(list(events_cursor))

if events_df.empty:
    print("No events found in the database to validate.")
else:
    print(f"Found {len(events_df)} events to validate.")
    ai_responses = events_df[events_df['type'] == 'ai_response'].copy()
    
    # 1. Validate Intent Counts
    ai_responses.loc[:, 'intent_type'] = ai_responses['intent'].apply(
        lambda x: x.get('query_type', 'unknown') if isinstance(x, dict) else str(x)
    )
    rival_intent_counts = ai_responses['intent_type'].value_counts().to_dict()
    print("\nRival Intent Counts:")
    print(rival_intent_counts)
    
    # 2. Validate Average Execution Time
    rival_avg_exec_time = ai_responses['execution_time'].mean()
    if pd.isna(rival_avg_exec_time):
        rival_avg_exec_time = 0.0
    print(f"\nRival Average Execution Time: {rival_avg_exec_time:.4f}s")
    
    # 3. Validate Data Gaps (Failures)
    rival_gaps = ai_responses[ai_responses['response_success'] == False].shape[0]
    print(f"\nRival Data Gaps (Failures): {rival_gaps}")

    # FIX 2: Add validation for the new error breakdown metric.
    # 4. Validate Error Breakdown
    error_df = ai_responses[ai_responses['intent_type'] == 'error']
    if not error_df.empty:
        error_df.loc[:, 'error_type'] = error_df['intent'].apply(
            lambda x: x.get('error_type', 'unknown_error') if isinstance(x, dict) else 'unknown_error'
        )
        rival_error_counts = error_df['error_type'].value_counts().to_dict()
        print("\nRival Error Breakdown:")
        print(rival_error_counts)
    else:
        rival_error_counts = {}
        print("\nRival Error Breakdown: No 'error' intents found.")


# --- Comparison with Stored Metrics ---
print("\n--- Compare with Latest Dashboard Metrics Collection ---")
# Fetch the most recent metric entry from the dashboard collection
dashboard_metric = db.dashboard_metrics.find_one(sort=[('date', -1)])

if dashboard_metric:
    print("Stored Metrics:")
    print(f"  Intents: {dashboard_metric.get('intent_counts')}")
    # FIX 3: Also print the stored error counts for comparison.
    print(f"  Errors: {dashboard_metric.get('error_type_counts')}")
    print(f"  Avg Time: {dashboard_metric.get('avg_exec_time'):.4f}s")
    print(f"  Gaps: {dashboard_metric.get('data_gaps')}")
else:
    print("No metrics found in the dashboard_metrics collection to compare against.")

