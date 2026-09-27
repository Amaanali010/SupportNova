# pages/5_Manual_Review.py
# Streamlit page for Manual Review Queue where reviewers/managers approve, modify, reclassify, or escalate cases.
# Maintains original AI/Python decisions and final modified decisions in audit trail.

import streamlit as st
import json
import pandas as pd
from database.db import execute_query, execute_statement

st.set_page_config(page_title="Manual Review Queue - SupportNova", page_icon="⚖️", layout="wide")

st.title("⚖️ Manual Review Queue")
st.caption("Audit and resolve cases flagged for AI/Python mismatches, security injection, or policy conflicts.")

user = st.session_state.get("user")
if not user or user['role'] not in ['reviewer', 'manager', 'admin']:
    st.warning("🔒 Access Restricted. Reviewer, Manager, or Admin privileges required.")
    st.stop()

# Query cases in Manual Review
cases = execute_query("SELECT * FROM complaints WHERE status = 'Manual_Review' ORDER BY created_at DESC")

if not cases:
    st.success("🎉 Manual Review Queue is clear! No cases currently pending review.")
else:
    df_cases = pd.DataFrame([dict(r) for r in cases])
    st.dataframe(df_cases[['complaint_id', 'customer_id', 'channel', 'status', 'category', 'urgency', 'created_at']], use_container_width=True)

    selected_id = st.selectbox("Select Complaint ID to Audit", df_cases['complaint_id'].tolist())

    if selected_id:
        c_row = dict(execute_query("SELECT * FROM complaints WHERE complaint_id = ?", (selected_id,))[0])
        st.divider()
        st.markdown(f"### Auditing Case: `{selected_id}`")
        if c_row.get('is_duplicate'):
            dup_link = c_row.get('duplicate_of') or c_row.get('duplicate_group')
            if dup_link:
                st.warning(f"⚠️ **Duplicate Flagged**: Linked to existing complaint **{dup_link}**")
            else:
                st.warning("⚠️ **Duplicate Flagged**")
        st.info(f"**Complaint Text:**\n{c_row['complaint_text']}")

        # Fetch Analysis Results
        res_rows = execute_query("SELECT * FROM analysis_results WHERE complaint_id = ?", (selected_id,))
        ai_data = {}
        py_data = {}
        mismatches = []

        if res_rows:
            res_rec = dict(res_rows[0])
            ai_data = json.loads(res_rec['genai_json']) if res_rec['genai_json'] else {}
            py_data = json.loads(res_rec['python_result']) if res_rec['python_result'] else {}
            mismatches = json.loads(res_rec['mismatches']) if res_rec['mismatches'] else []

        if mismatches:
            st.error(f"**Disagreement Mismatches:** {', '.join(mismatches)}")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🤖 Original AI Proposal")
            st.json(ai_data if ai_data else {"status": "No AI output generated"})

        with col2:
            st.subheader("🛡️ Python Rule Matrix Validation")
            st.json(py_data if py_data else {"status": "No Python result generated"})

        # Staff Action Form
        st.divider()
        st.subheader("✍️ Reviewer Action & Decision Override")

        with st.form("manual_review_form"):
            action = st.selectbox(
                "Reviewer Action",
                ["Approve", "Reject", "Modify", "Reclassify", "Reassign", "Escalate", "Regenerate"]
            )
            final_category = st.text_input("Final Category", value=ai_data.get("category", c_row.get("category", "Billing & Refunds")))
            final_dept = st.text_input("Final Department", value=ai_data.get("department", "Billing Support"))
            comments = st.text_area("Audit Notes & Justification", help="State reasons for approval, modification, or escalation.")

            submit_review = st.form_submit_button("Commit Final Decision to Audit Trail", type="primary")

            if submit_review:
                final_decision_dict = {
                    "action": action,
                    "final_category": final_category,
                    "final_department": final_dept,
                    "comments": comments,
                    "reviewer": user['username']
                }

                # Save Review Record
                execute_statement(
                    """
                    INSERT INTO reviews (complaint_id, reviewer_id, original_decision, final_decision, status, comments)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        selected_id,
                        user['username'],
                        json.dumps(ai_data),
                        json.dumps(final_decision_dict),
                        action,
                        comments
                    )
                )

                if action in ["Approve", "Modify", "Reclassify"]:
                    new_status = "Resolved"
                elif action == "Reject":
                    new_status = "Closed"
                elif action == "Escalate":
                    new_status = "Escalated"
                else:
                    new_status = "In Progress"

                # Update Complaint Status
                execute_statement(
                    "UPDATE complaints SET status = ?, category = ? WHERE complaint_id = ?",
                    (new_status, final_category, selected_id)
                )

                # Update Complaint History
                execute_statement(
                    """
                    INSERT INTO complaint_history (complaint_id, changed_by, old_status, new_status, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (selected_id, user['username'], "Manual_Review", new_status, comments)
                )

                # Write Audit Log Entry
                execute_statement(
                    "INSERT INTO audit_log (user_id, action, target_type, target_id, details) VALUES (?, ?, ?, ?, ?)",
                    (user['username'], f"MANUAL_REVIEW_{action.upper()}", "COMPLAINT", selected_id, f"Action: {action}, Notes: {comments}")
                )

                st.success(f"Case {selected_id} updated successfully to status: **{new_status}**!")
                st.rerun()
