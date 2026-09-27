# pages/3_Customer_Status.py
# Streamlit page allowing customers to view the status and resolution history of their complaints.

import streamlit as st
import pandas as pd
from database.db import execute_query

st.set_page_config(page_title="Customer Status - SupportNova", page_icon="📋", layout="wide")

st.title("📋 Customer Complaint Tracker")
st.caption("View the real-time status and resolution details of your submitted complaints.")

user = st.session_state.get("user")
if not user:
    st.warning("Please log in as a customer or staff member to view complaint status.")
    st.stop()

# Query complaints for the current customer (or all if agent/admin)
if user['role'] in ['admin', 'manager', 'reviewer', 'agent']:
    complaints = execute_query("SELECT complaint_id, customer_id, channel, status, category, urgency, created_at FROM complaints ORDER BY created_at DESC")
else:
    complaints = execute_query("SELECT complaint_id, customer_id, channel, status, category, urgency, created_at FROM complaints WHERE customer_id = ? ORDER BY created_at DESC", (user['username'],))

if not complaints:
    st.info("No complaint records found.")
else:
    df = pd.DataFrame([dict(r) for r in complaints])
    st.dataframe(df, use_container_width=True)
