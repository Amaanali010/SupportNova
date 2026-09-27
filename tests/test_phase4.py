# tests/test_phase4.py
# Comprehensive Pytest test suite for SupportNova Phase 4.
# Validates prompt versioning, Pydantic schema re-validation, Groq API call wrapping, and Hard Rule 9 failure handling.

import json
import pytest
from prompt_templates.prompt_loader import load_prompt_template, format_triage_prompt
from genai_pipeline.pipeline1 import run_pipeline1
from database.seed import run_seed_if_needed
from database.db import execute_query, execute_statement

def test_prompt_template_loader():
    """Test loading prompt templates by version and formatting context blocks."""
    raw_template = load_prompt_template("v1.1")
    assert "System Prompt" in raw_template
    assert "<<<UNTRUSTED_USER_INPUT_START>>>" in raw_template

    retrieved = [
        {"doc_id": "REF-POL-01", "section": "4.1", "heading": "Refund Policy", "text": "Escalate high-value refund claims to Supervisor Review."}
    ]

    formatted = format_triage_prompt(
        version="v1.1",
        complaint_id="CMP-TEST-100",
        customer_id="CUST-100",
        untrusted_text="I was charged $450 fraudulently.",
        retrieved_chunks=retrieved
    )

    assert "CMP-TEST-100" in formatted
    assert "CUST-100" in formatted
    assert "REF-POL-01" in formatted
    assert "I was charged $450 fraudulently." in formatted

def test_pipeline1_api_failure_fallback():
    """Test Hard Rule 9: If GenAI API fails (e.g. invalid model / network failure), route case to Manual Review without fake data."""
    run_seed_if_needed()

    # Insert test complaint
    execute_statement(
        "INSERT OR REPLACE INTO complaints (complaint_id, customer_id, complaint_text, status) VALUES (?, ?, ?, ?)",
        ("CMP-FAIL-TEST", "CUST-001", "Test complaint text requiring triage.", "Submitted")
    )

    # Calling run_pipeline1 with an invalid model will trigger failure fallback
    result_dict, is_success, status_msg = run_pipeline1(
        complaint_id="CMP-FAIL-TEST",
        complaint_text="Test complaint text requiring triage.",
        customer_id="CUST-001",
        retrieved_chunks=[],
        override_model="invalid-nonexistent-model-xyz"
    )

    assert is_success is False
    assert result_dict is None
    assert "Pipeline 1 API Failure" in status_msg

    # Verify complaint status was routed to Manual_Review in database
    comp_row = execute_query("SELECT status FROM complaints WHERE complaint_id = ?", ("CMP-FAIL-TEST",))[0]
    assert comp_row["status"] == "Manual_Review"
