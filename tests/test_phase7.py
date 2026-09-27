# tests/test_phase7.py
# Comprehensive Pytest test suite for SupportNova Phase 7.
# Validates search and filter engine, SLA risk calculation, summary metrics, and CSV report export.

import pytest
from reports.search_filter import search_and_filter_complaints
from reports.report_generator import generate_system_summary_metrics, calculate_sla_risk, export_complaints_to_csv
from database.seed import run_seed_if_needed
from database.db import execute_statement

def test_search_and_filter_complaints():
    """Test searching and filtering complaints by status, category, and text keywords."""
    run_seed_if_needed()

    execute_statement(
        "INSERT OR REPLACE INTO complaints (complaint_id, customer_id, complaint_text, status, category, urgency) VALUES (?, ?, ?, ?, ?, ?)",
        ("CMP-SEARCH-1", "CUST-SEARCH", "Searching for refund status on damaged item.", "Verified", "Billing", "High")
    )

    # Search by text query
    results_q = search_and_filter_complaints(query_text="damaged item")
    assert len(results_q) > 0
    assert results_q[0]["complaint_id"] == "CMP-SEARCH-1"

    # Search by status filter
    results_s = search_and_filter_complaints(status_filter="Verified")
    assert len(results_s) > 0
    assert any(r["complaint_id"] == "CMP-SEARCH-1" for r in results_s)

def test_sla_risk_and_summary_metrics():
    """Test SLA risk monitoring calculation and summary metrics generation."""
    run_seed_if_needed()

    metrics = generate_system_summary_metrics()
    assert "total_complaints" in metrics
    assert metrics["total_complaints"] >= 1

    sla_risks = calculate_sla_risk()
    assert isinstance(sla_risks, list)

def test_csv_export_generator():
    """Test exporting complaint records into downloadable CSV format string."""
    complaints = [
        {
            "complaint_id": "CMP-CSV-01",
            "customer_id": "CUST-CSV",
            "channel": "Web",
            "status": "Submitted",
            "category": "Billing",
            "subcategory": "Overcharge",
            "priority": "P1",
            "urgency": "High",
            "is_repeat": 0,
            "is_duplicate": 0,
            "created_at": "2026-09-26 12:00:00"
        }
    ]

    csv_out = export_complaints_to_csv(complaints)
    assert "complaint_id,customer_id,channel,status" in csv_out
    assert "CMP-CSV-01" in csv_out
    assert "CUST-CSV" in csv_out
