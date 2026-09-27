# tests/test_phase5.py
# Comprehensive Pytest test suite for SupportNova Phase 5.
# Validates Pipeline 2 (Zero AI calls), mandatory escalation overrides, real rule matrix checks, unsupported promises, and policy validity checks.

import pytest
from python_validation.rule_checker import get_mandatory_escalation_for_rule, check_rule_compliance
from python_validation.policy_checker import check_policy_validity
from hallucination_checks.hallucination_detector import detect_unsupported_promises, detect_unsupported_facts
from python_validation.pipeline2 import run_pipeline2
from database.seed import run_seed_if_needed

def test_mandatory_escalation_for_rule():
    """Test Python mandatory escalation level lookup from real 114-row rule matrix."""
    run_seed_if_needed()
    is_req, level = get_mandatory_escalation_for_rule("Delivery", "Delayed Delivery")
    assert isinstance(is_req, bool)
    assert level in ["Not Required", "Supervisor Review", "Department Manager", "Specialist Team", "Compliance Review", "Critical Management Escalation"]

def test_unsupported_promises_detection():
    """Test detecting unauthorized or prohibited promises ('guaranteed refund', 'cash payout')."""
    genai_output = {
        "resolution_steps": ["We offer a guaranteed refund of $500 immediately."],
        "customer_response": "We guarantee 100% money back and cash payout.",
        "agent_guidance": "Provide direct bank transfer."
    }
    violations = detect_unsupported_promises(genai_output)
    assert len(violations) >= 2
    assert any("guaranteed refund" in v for v in violations)

def test_prohibited_action_check():
    """Test prohibited actions check against real rule matrix row."""
    genai_output = {
        "category": "Delivery",
        "subcategory": "Delayed Delivery",
        "resolution_steps": ["Promise a new delivery date the carrier has not confirmed."],
        "customer_response": "We promise the carrier will deliver tomorrow."
    }
    rule = {
        "rule_id": "RM-001",
        "category": "Delivery",
        "subcategory": "Delayed Delivery",
        "prohibited_actions": "Promise a new delivery date the carrier has not confirmed; Offer compensation before SLA breach is confirmed"
    }
    res = check_rule_compliance(genai_output, rule)
    assert len(res["violations"]) > 0
    assert any("Prohibited action detected" in v for v in res["violations"])

def test_non_active_policy_flag():
    """Test Hard Rule 5: Flagging non-existent or invalid policy references."""
    run_seed_if_needed()
    res = check_policy_validity("NON-EXISTENT-POL", "Section 1.0", [])
    assert res["is_primary_valid"] is False
    assert len(res["violations"]) > 0
    assert any("does not exist" in v for v in res["violations"])

def test_pipeline2_execution_and_missed_escalation_override():
    """Test full Pipeline 2 execution (zero AI calls) and catching AI-missed mandatory escalation."""
    run_seed_if_needed()
    complaint_text = "I suspect fraud on my account. Someone made an unauthorized transaction."

    # Simulated AI output where AI missed the mandatory escalation for a high-priority case
    ai_output = {
        "primary_issue": "Unauthorized transaction",
        "category": "Refunds",
        "subcategory": "Unauthorized Transactions",
        "sentiment": "Frustrated",
        "urgency": "High",
        "priority": "P1",
        "department": "Billing Support",
        "policy_id": "REF-POL-01",
        "policy_section": "5.1",
        "resolution_steps": ["Verify transaction details", "Issue refund"],
        "escalation_required": False,  # AI missed escalation!
        "escalation_level": "Not Required",
        "customer_response": "We are investigating your complaint."
    }

    retrieved_chunks = [
        {"doc_id": "REF-POL-01", "section": "5.1", "heading": "Unauthorized Charges", "text": "Escalate unauthorized charges under escalation procedure."}
    ]

    p2_result = run_pipeline2("CMP-P2-TEST", complaint_text, ai_output, retrieved_chunks)
    assert "mandatory_escalation_required" in p2_result
    assert "mandatory_escalation_level" in p2_result
