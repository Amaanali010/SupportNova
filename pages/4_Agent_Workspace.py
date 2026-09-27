# pages/4_Agent_Workspace.py
# Streamlit page for Support Agents to trigger dual-pipeline triage and view side-by-side AI vs Python comparisons.

import streamlit as st
import json
import pandas as pd
from database.db import execute_query, execute_statement
from knowledge_base.document_manager import DOCUMENT_MANAGER
from genai_pipeline.pipeline1 import run_pipeline1
from python_validation.pipeline2 import run_pipeline2
from comparison_engine.comparator import compare_ai_and_python_results

st.set_page_config(page_title="Agent Workspace - SupportNova", page_icon="🎧", layout="wide")

st.title("🎧 Agent Triage Workspace")
st.caption("Execute dual-pipeline complaint analysis (GenAI vs Python Rule Matrix) and inspect verification scores.")

user = st.session_state.get("user")
if not user or user['role'] not in ['agent', 'reviewer', 'manager', 'admin']:
    st.warning("🔒 Access Restricted. Support Agent or Staff privileges required.")
    st.stop()

# Queue Table of Complaints
complaints = execute_query("SELECT complaint_id, customer_id, channel, status, created_at FROM complaints ORDER BY created_at DESC")

if not complaints:
    st.info("No complaints found in system.")
else:
    df_comp = pd.DataFrame([dict(r) for r in complaints])
    st.dataframe(df_comp, use_container_width=True)

    selected_id = st.selectbox("Select Complaint ID to Analyze", df_comp['complaint_id'].tolist())

    if selected_id:
        c_rows = execute_query("SELECT * FROM complaints WHERE complaint_id = ?", (selected_id,))
        if c_rows:
            comp = dict(c_rows[0])
            st.divider()
            st.write(f"**Customer ID:** {comp['customer_id']} | **Channel:** {comp['channel']} | **Current Status:** `{comp['status']}`")
            if comp.get('is_duplicate'):
                dup_link = comp.get('duplicate_of') or comp.get('duplicate_group')
                if dup_link:
                    st.warning(f"⚠️ **Duplicate Flagged**: Matches existing complaint **{dup_link}**")
                else:
                    st.warning("⚠️ **Duplicate Flagged**")
            st.info(f"**Raw Complaint Text:**\n{comp['complaint_text']}")

            # Triage Button
            if st.button("🚀 Run Dual-Pipeline Triage & Verification", type="primary"):
                with st.spinner("Step 1/3: Retrieving relevant policy context via TF-IDF RAG..."):
                    retrieved_chunks = DOCUMENT_MANAGER.retrieve_chunks(comp['complaint_text'], top_k=3)

                with st.spinner("Step 2/3: Executing Pipeline 1 (GenAI Triage)..."):
                    ai_out, ai_success, ai_msg = run_pipeline1(
                        complaint_id=comp['complaint_id'],
                        complaint_text=comp['complaint_text'],
                        customer_id=comp['customer_id'],
                        retrieved_chunks=retrieved_chunks,
                        title=comp.get('title') or "N/A",
                        customer_type=comp.get('customer_type') or "Standard",
                        product=comp.get('product') or "N/A",
                        order_ref=comp.get('order_ref') or "N/A"
                    )

                with st.spinner("Step 3/3: Executing Pipeline 2 (Python Validation Engine)..."):
                    if ai_success and ai_out:
                        p2_out = run_pipeline2(
                            complaint_id=comp['complaint_id'],
                            complaint_text=comp['complaint_text'],
                            genai_output=ai_out,
                            retrieved_chunks=retrieved_chunks
                        )

                        comp_res = compare_ai_and_python_results(
                            complaint_id=comp['complaint_id'],
                            genai_output=ai_out,
                            python_result=p2_out,
                            is_injection_detected=False
                        )
                        st.success(f"Triage Completed! Verification Status: **{comp_res['verification_status']}**")
                    else:
                        st.error(f"Pipeline 1 Issue: {ai_msg}")

                st.rerun()

            # Display Existing Analysis Results if available
            res_rows = execute_query("SELECT * FROM analysis_results WHERE complaint_id = ?", (selected_id,))
            if res_rows:
                res_rec = dict(res_rows[0])
                ai_data = json.loads(res_rec['genai_json']) if res_rec['genai_json'] else {}
                py_data = json.loads(res_rec['python_result']) if res_rec['python_result'] else {}

                # Display Comparison Header Metrics
                st.divider()
                st.markdown("### 📊 Dual-Pipeline Comparison & Verification")
                col_m1, col_m2, col_m3 = st.columns(3)

                status_badge = "🟢 VERIFIED" if res_rec['verification_status'] == "Verified" else "🔴 MANUAL REVIEW"
                col_m1.metric("Verification Status", status_badge)
                col_m2.metric("Prompt Version", res_rec.get("prompt_version", "v1.0"))
                col_m3.metric("LLM Model", res_rec.get("model", "N/A"))

                # Side-by-Side Comparison Columns
                col_ai, col_py = st.columns(2)

                with col_ai:
                    st.markdown('<div class="css-card">', unsafe_allow_html=True)
                    st.subheader("🤖 Pipeline 1 (GenAI Output)")
                    if ai_data:
                        st.write(f"**Category:** {ai_data.get('category')}")
                        st.write(f"**Subcategory:** {ai_data.get('subcategory')}")
                        st.write(f"**Department:** {ai_data.get('department')}")
                        st.write(f"**Urgency / Priority:** {ai_data.get('urgency')} / {ai_data.get('priority')}")
                        st.write(f"**Policy Applied:** {ai_data.get('policy_id')} ({ai_data.get('policy_section')})")
                        st.write(f"**Escalation Required:** {ai_data.get('escalation_required')} (Level: {ai_data.get('escalation_level')})")
                        st.write("**Resolution Steps:**")
                        for step in ai_data.get("resolution_steps", []):
                            st.write(f"- {step}")
                    else:
                        st.caption("No GenAI output recorded.")
                    st.markdown('</div>', unsafe_allow_html=True)

                with col_py:
                    st.markdown('<div class="css-card">', unsafe_allow_html=True)
                    st.subheader("🛡️ Pipeline 2 (Python Matrix Validation)")
                    if py_data:
                        rule_id_val = py_data.get('matching_rule_id', 'R-NONE')
                        if py_data.get('is_fallback_match'):
                            st.write(f"**Rule Matrix ID:** `{rule_id_val}` *(fallback match — subcategory not found)*")
                        else:
                            st.write(f"**Rule Matrix ID:** `{rule_id_val}`")
                        st.write(f"**Validated Category:** {py_data.get('validated_category')}")
                        st.write(f"**Validated Department:** {py_data.get('validated_department')}")
                        st.write(f"**Mandatory Escalation:** {py_data.get('mandatory_escalation_required')} (Level: {py_data.get('mandatory_escalation_level')})")

                        if py_data.get("ai_missed_escalation"):
                            st.error("⚠️ Mandatory Escalation Missed by AI and Raised by Python!")

                        if py_data.get("violations"):
                            st.warning("**Validation Violations / Warnings:**")
                            for v in py_data.get("violations", []):
                                st.write(f"- ⚠️ {v}")
                        else:
                            st.success("✅ Passed all rule matrix & policy checks.")
                    else:
                        st.caption("No Python validation recorded.")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Suggested Customer Response
                if ai_data.get("customer_response"):
                    st.subheader("✉️ Suggested Customer Reply")
                    st.text_area("Draft Reply", value=ai_data.get("customer_response"), height=120)
                    if st.button("✉️ Confirm Reply Sent & Mark Resolved", type="primary"):
                        execute_statement("UPDATE complaints SET status = 'Resolved' WHERE complaint_id = ?", (selected_id,))
                        execute_statement("INSERT INTO audit_log (user_id, action, target_type, target_id, details) VALUES (?, 'MARK_RESOLVED', 'COMPLAINT', ?, 'Agent confirmed reply sent and marked complaint as Resolved')", (user['username'], selected_id))
                        st.success(f"Complaint {selected_id} status updated to **Resolved**!")
                        st.rerun()
