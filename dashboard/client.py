import streamlit as st
import requests

st.set_page_config(page_title="Conversational DB Agent UI", page_icon="🤖", layout="wide")
st.title("Conversational DB Agent UI")
st.markdown("Ask questions about your data. Select a collection and enter your query, or pick a demo query below.")

# --- Demo Queries with Collection Mapping ---
demo_queries = [
    {"label": "Show all customers from California", "collection": "customers", "query": "Show all customers from California"},
    {"label": "Find accounts with a limit of 10000", "collection": "accounts", "query": "Find accounts with a limit of 10000"},
    {"label": "How many transactions happened last month?", "collection": "transactions", "query": "How many transactions happened last month?"},
    {"label": "What are the most common errors?", "collection": "dashboard_metrics", "query": "What are the most common errors?"},
    {"label": "List customers with active accounts", "collection": "customers", "query": "List customers with active accounts"},
    {"label": "Show dashboard metrics for the last 5 days", "collection": "dashboard_metrics", "query": "Show dashboard metrics for the last 5 days"},
]

demo_labels = [""] + [d["label"] for d in demo_queries]
selected_demo_label = st.selectbox("Choose a demo query (optional)", demo_labels)

# --- Session and Collection Selection ---
session_id = st.text_input("Session ID (optional)")

# Set collection and query_text based on demo query selection
if selected_demo_label:
    selected_demo = next(d for d in demo_queries if d["label"] == selected_demo_label)
    collection = selected_demo["collection"]
    query_text = selected_demo["query"]
else:
    collection = st.selectbox("Collection", ["customers", "accounts", "transactions", "dashboard_metrics", "events"])
    query_text = st.text_area("Your query", height=80, key="query_text_area")

# --- Send Query Button ---
if st.button("Send"):
    if not query_text.strip():
        st.warning("Please enter a query before sending.")
    else:
        payload = {
            "session_id": session_id or None,
            "collection": collection,
            "query_text": query_text
        }
        try:
            response = requests.post("http://localhost:8000/query", json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            st.subheader("Agent Response")

            # Show error if present
            if result.get("error"):
                st.error(f"Error: {result.get('error')} (type: {result.get('error_type')})")
            else:
                data = result.get("data", [])
                if isinstance(data, list) and len(data) == 1 and "count" in data[0]:
                    st.success(f"Count: {data[0]['count']}")
                elif data:
                    st.json(data)
                else:
                    st.info("No data returned.")

            st.caption(f"Session ID: {result.get('session_id')}")
            st.caption(f"Execution Time: {result.get('execution_time', 0):.4f} seconds")

            with st.expander("Show Raw Response"):
                st.json(result)

        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
