# pages/2_Submit_Complaint.py
# Streamlit page for customer complaint submission with input validation, prompt injection check, and duplicate detection.

import streamlit as st
from complaint_processing.validator import validate_and_sanitize_complaint
from complaint_processing.duplicate_detector import check_repeat_customer, check_duplicate_complaint
from database.db import execute_statement, execute_query

st.set_page_config(page_title="Submit Complaint - SupportNova", page_icon="📝", layout="wide")

st.title("📝 Submit a Complaint")
st.caption("Submit your issue or inquiry for VoltKart automated triage.")

# Check user role authorization
user = st.session_state.get("user")
if not user:
    st.warning("Please log in to submit a complaint.")
    st.stop()

with st.form("complaint_submission_form"):
    col1, col2 = st.columns(2)
    with col1:
        customer_id = st.text_input("Customer ID", value=user.get("username", "CUST-001"), disabled=True)
        title = st.text_input("Complaint Title *", help="Brief summary title of your complaint")
        customer_type = st.selectbox("Customer Type", ["Standard", "VIP", "New Customer"])
    with col2:
        channel = st.selectbox("Channel", ["Web", "Email", "Mobile App", "Phone Transcription"])
        product = st.text_input("Product / Service Name (Optional)", help="e.g. VoltKart Phone Charger 30W")
        order_ref = st.text_input("Order Reference / ID (Optional)", help="e.g. VK-552310")

    complaint_text = st.text_area("Describe your complaint in detail *", height=180, help="Provide full description of the issue.")

    submit_btn = st.form_submit_button("Submit Complaint for Triage", type="primary")

    if submit_btn:
        # Step 1: Validate and sanitize complaint
        result = validate_and_sanitize_complaint(complaint_text, customer_id, channel, title=title)

        if not result["is_valid"]:
            for err in result["errors"]:
                st.error(err)
        else:
            # Step 2: Check for repeat customer history
            is_repeat, prior_count = check_repeat_customer(customer_id)

            # Step 3: Check for duplicate complaints
            is_duplicate, matched_id, sim_score = check_duplicate_complaint(result["sanitized_text"])

            # Step 4: Check for missing information (CMP-SOP-01 2.2)
            is_missing_info, missing_fields = check_missing_information(order_ref, result["sanitized_text"])

            # Determine initial complaint status (Hard Rule 6: Injection triggers Manual Review)
            is_injection = result["is_injection_detected"]
            if is_injection:
                status = "Manual_Review"
            elif is_missing_info:
                status = "Awaiting_Customer"
            else:
                status = "Submitted"

            # Generate new complaint ID
            existing_count = execute_query("SELECT COUNT(*) as count FROM complaints")[0]['count']
            complaint_id = f"CMP-{existing_count + 1001}"

            # Step 5: Save complaint to Database
            execute_statement(
                """
                INSERT INTO complaints (
                    complaint_id, title, customer_id, customer_type, product, order_ref,
                    complaint_text, channel, status, is_repeat, is_duplicate, duplicate_of
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    complaint_id, title.strip(), customer_id, customer_type,
                    product.strip() if product else None,
                    order_ref.strip() if order_ref else None,
                    result["sanitized_text"], channel, status,
                    1 if is_repeat else 0, 1 if is_duplicate else 0, matched_id if is_duplicate else None
                )
            )

            # Step 6: Log action to Audit Log
            dup_detail = f" (Duplicate of {matched_id})" if is_duplicate and matched_id else ""
            missing_detail = f" (Missing: {', '.join(missing_fields)})" if is_missing_info else ""
            execute_statement(
                "INSERT INTO audit_log (user_id, action, target_type, target_id, details) VALUES (?, ?, ?, ?, ?)",
                (customer_id, "SUBMIT_COMPLAINT", "COMPLAINT", complaint_id, f"Status: {status}, Repeat: {is_repeat}, Duplicate: {is_duplicate}{dup_detail}{missing_detail}, Injection: {is_injection}")
            )

            # Step 7: Render User Feedback Messages
            if is_injection:
                st.error(f"🚨 Security Alert: Prompt injection phrase detected ({', '.join(result['injection_flags'])}). Case routed immediately to Manual Review Queue!")
            elif is_missing_info:
                st.warning(f"⚠️ Missing Information Note: Order Reference is missing for this complaint. Status set to **Awaiting_Customer**. Please provide your Order Reference ID so we can proceed with resolution. (Submitted as {complaint_id})")
            elif is_duplicate:
                st.warning(f"⚠️ Duplicate Warning: Similar complaint previously submitted ({matched_id}, {sim_score*100:.1f}% similarity). Submitted as {complaint_id}.")
            elif is_repeat:
                st.info(f"ℹ️ Repeat Customer Note: You have {prior_count} previous complaint submission(s). Submitted as {complaint_id}.")
            else:
                st.success(f"✅ Complaint {complaint_id} submitted successfully! Status: **{status}**")
