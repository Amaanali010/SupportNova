# pages/6_Admin.py
# Streamlit page for Administrators to view metrics, SLA risk, rule matrix, search & filter complaints, and export CSV reports.

import streamlit as st
import pandas as pd
from database.db import execute_query
from reports.report_generator import generate_system_summary_metrics, calculate_sla_risk, export_complaints_to_csv
from reports.search_filter import search_and_filter_complaints

st.set_page_config(page_title="Admin Panel & Reports - SupportNova", page_icon="⚙️", layout="wide")

st.title("⚙️ Admin Console, Analytics & Reports")
st.caption("System performance dashboard, SLA risk monitoring, rule matrix viewer, and data exports.")

user = st.session_state.get("user")
if not user or user['role'] not in ['admin', 'manager']:
    st.warning("🔒 Access Restricted. Administrator or Manager privileges required.")
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Metrics & SLA Risk",
    "🔍 Advanced Search & Filter",
    "📜 Rule Matrix",
    "📚 Document Library",
    "📑 Audit Log"
])

# TAB 1: System Metrics & SLA Risk
with tab1:
    metrics = generate_system_summary_metrics()

    st.subheader("System Overview Telemetry")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Complaints", metrics["total_complaints"])
    c2.metric("Verified Automatically", metrics["verified_count"])
    c3.metric("Manual Review Queue", metrics["manual_review_count"])
    c4.metric("Escalated Cases", metrics["escalated_count"])

    st.divider()
    st.subheader("⚠️ SLA Risk Monitoring (2h / 6h / 24h Thresholds)")
    sla_risks = calculate_sla_risk()
    if not sla_risks:
        st.success("✅ No open complaints are currently at risk of SLA breach.")
    else:
        st.warning(f"Found {len(sla_risks)} open complaint(s) approaching or exceeding SLA limits.")
        df_sla = pd.DataFrame(sla_risks)
        st.dataframe(df_sla, use_container_width=True)

    st.divider()
    col_cat, col_dept = st.columns(2)
    with col_cat:
        st.subheader("Category Breakdown")
        st.bar_chart(pd.Series(metrics["category_distribution"]))

    with col_dept:
        st.subheader("Department Rule Distribution")
        st.bar_chart(pd.Series(metrics["department_distribution"]))

# TAB 2: Advanced Search & Filter + CSV Export
with tab2:
    st.subheader("🔎 Complaint Search & Multi-Criteria Filtering")

    col_s1, col_s2, col_s3 = st.columns(3)
    query_input = col_s1.text_input("Text Search", placeholder="Order ID, Customer ID, or keyword...")
    status_select = col_s2.selectbox("Status Filter", ["All", "Submitted", "Verified", "Manual_Review", "Resolved_Approve", "Resolved_Reject"])
    urgency_select = col_s3.selectbox("Urgency Filter", ["All", "Low", "Medium", "High", "Critical"])

    esc_only = st.checkbox("Show Escalations & Manual Review Cases Only")

    # Perform Search
    filtered_results = search_and_filter_complaints(
        query_text=query_input,
        status_filter=status_select,
        urgency_filter=urgency_select,
        escalation_only=esc_only
    )

    st.write(f"**Found {len(filtered_results)} matching complaint record(s).**")
    if filtered_results:
        df_filtered = pd.DataFrame(filtered_results)
        st.dataframe(df_filtered[['complaint_id', 'customer_id', 'channel', 'status', 'category', 'priority', 'urgency', 'created_at']], use_container_width=True)

        # CSV Download Button
        csv_data = export_complaints_to_csv(filtered_results)
        st.download_button(
            label="📥 Export Search Results as CSV",
            data=csv_data,
            file_name="supportnova_complaints_export.csv",
            mime="text/csv",
            type="primary"
        )

# TAB 3: Rule Matrix Viewer
with tab3:
    st.subheader("Complaint Resolution Rule Matrix (CSV Source)")
    rules = execute_query("SELECT * FROM rules")
    if rules:
        st.dataframe(pd.DataFrame([dict(r) for r in rules]), use_container_width=True)

# TAB 4: Document Library
with tab4:
    st.subheader("Ingested Policy Document Versions & Chunks")
    docs = execute_query("SELECT * FROM documents")
    if docs:
        st.dataframe(pd.DataFrame([dict(r) for r in docs]), use_container_width=True)

# TAB 5: Audit Log
with tab5:
    st.subheader("System Action Audit Log")
    logs = execute_query("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100")
    if logs:
        st.dataframe(pd.DataFrame([dict(r) for r in logs]), use_container_width=True)
