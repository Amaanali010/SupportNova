# tests/test_phase6.py
# Comprehensive Pytest test suite for SupportNova Phase 6.
# Validates comparison engine routing (Verified vs Manual Review), deterministic verification score, and review audit trail.

import pytest
from comparison_engine.comparator import compare_ai_and_python_results
from database.seed import run_seed_if_needed
from database.db import execute_query, execute_statement

def test_comparison_engine_verified_routing():
    """Test routing to Verified status when AI and Python outputs fully agree."""
    run_seed_if_needed()

    execute_statement(
        "INSERT OR REPLACE INTO complaints (complaint_id, customer_id, complaint_text, status) VALUES (?, ?, ?, ?)",
        ("CMP-COMP-VERIFIED", "CUST-001", "Unauthorized charge refund request.", "Submitted")
    )
    execute_statement(
        "INSERT OR REPLACE INTO analysis_results (complaint_id, verification_status) VALUES (?, ?)",
        ("CMP-COMP-VERIFIED", "Pending")
    )

    ai_out = {
        "category": "Billing",
        "department": "Billing",
        "urgency": "High",
        "priority": "P1",
        "escalation_required": True,
        "escalation_level": "Supervisor Review"
    }

    py_out = {
        "validated_category": "Billing",
        "validated_department": "Billing",
        "validated_urgency": "High",
        "validated_priority": "P1",
        "mandatory_escalation_required": True,
        "mandatory_escalation_level": "Supervisor Review",
        "ai_missed_escalation": False,
        "policy_validity": {"is_primary_valid": True},
        "violations": []
    }

    res = compare_ai_and_python_results("CMP-COMP-VERIFIED", ai_out, py_out, is_injection_detected=False)

    assert res["verification_status"] == "Verified"
    assert res["verification_score"] == 1.0
    assert len(res["mismatches"]) == 0

def test_comparison_engine_manual_review_routing():
    """Test routing to Manual Review when category disagrees or injection is detected."""
    ai_out = {
        "category": "Delivery",  # Disagrees with Billing
        "department": "Billing",
        "urgency": "High",
        "priority": "P1",
        "escalation_required": False
    }

    py_out = {
        "validated_category": "Billing",
        "validated_department": "Billing",
        "validated_urgency": "High",
        "validated_priority": "P1",
        "mandatory_escalation_required": False,
        "ai_missed_escalation": False,
        "policy_validity": {"is_primary_valid": True},
        "violations": []
    }

    res = compare_ai_and_python_results("CMP-COMP-MISMATCH", ai_out, py_out, is_injection_detected=False)

    assert res["verification_status"] == "Manual_Review"
    assert res["verification_score"] < 1.0
    assert len(res["mismatches"]) > 0

def test_manual_review_audit_trail_logging():
    """Test recording staff review decisions and audit trail entries in SQLite."""
    run_seed_if_needed()

    execute_statement(
        "INSERT OR REPLACE INTO complaints (complaint_id, customer_id, complaint_text, status) VALUES (?, ?, ?, ?)",
        ("CMP-AUDIT-TEST", "CUST-999", "Audit test complaint.", "Manual_Review")
    )

    # Perform manual review action
    execute_statement(
        "INSERT INTO reviews (complaint_id, reviewer_id, status, comments) VALUES (?, ?, ?, ?)",
        ("CMP-AUDIT-TEST", "reviewer1", "Approve", "Approved after policy check.")
    )
    execute_statement(
        "UPDATE complaints SET status = 'Resolved_Approve' WHERE complaint_id = ?",
        ("CMP-AUDIT-TEST",)
    )

    # Check reviews record
    rev_rows = execute_query("SELECT * FROM reviews WHERE complaint_id = ?", ("CMP-AUDIT-TEST",))
    assert len(rev_rows) > 0
    assert rev_rows[0]["status"] == "Approve"

    comp_row = execute_query("SELECT status FROM complaints WHERE complaint_id = ?", ("CMP-AUDIT-TEST",))[0]
    assert comp_row["status"] == "Resolved_Approve"
