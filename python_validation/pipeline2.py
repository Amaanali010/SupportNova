# python_validation/pipeline2.py
# Main execution module for Pipeline 2 (Zero-AI Independent Python Validation Engine).
# Executes rule compliance checks, policy status enforcement, mandatory escalation overrides, and hallucination checks.

import json
from typing import Dict, Any, List
from complaint_processing.rule_loader import RULE_LOADER
from python_validation.rule_checker import get_mandatory_escalation_for_rule, check_rule_compliance
from python_validation.policy_checker import check_policy_validity
from hallucination_checks.hallucination_detector import detect_unsupported_promises, detect_unsupported_facts
from database.db import execute_statement

def run_pipeline2(
    complaint_id: str,
    complaint_text: str,
    genai_output: Dict[str, Any],
    retrieved_chunks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Executes Pipeline 2 Independent Python Validation (Zero LLM calls).
    Returns structured python_result dictionary.
    """
    all_violations = []
    all_mismatches = []

    if not genai_output:
        return {
            "is_valid": False,
            "violations": ["Pipeline 1 output is missing or failed."],
            "mismatches": ["Missing AI Output"]
        }

    category = genai_output.get("category", "")
    subcategory = genai_output.get("subcategory", "")

    # Step 1: Detect Mandatory Escalation Level from Rule Matrix (Python override rule)
    mandatory_esc_req, esc_level = get_mandatory_escalation_for_rule(category, subcategory)
    ai_esc_req = bool(genai_output.get("escalation_required", False))

    if mandatory_esc_req and not ai_esc_req:
        all_violations.append(f"MISSED MANDATORY ESCALATION: Rule matrix requires '{esc_level}' escalation missed by AI.")

    # Step 2: Match Business Rule Matrix
    matching_rule = RULE_LOADER.find_rule(category, subcategory)
    rule_res = check_rule_compliance(genai_output, matching_rule)

    all_violations.extend(rule_res.get("violations", []))
    all_mismatches.extend(rule_res.get("mismatches", []))

    # Step 3: Check Policy Document Validity & Active Status (Hard Rule 5)
    policy_id = genai_output.get("policy_id", "")
    policy_section = genai_output.get("policy_section", "")
    policy_res = check_policy_validity(policy_id, policy_section, retrieved_chunks)

    all_violations.extend(policy_res.get("violations", []))

    # Step 4: Check for Unsupported Promises & Hallucinated Facts
    unsupported_promises = detect_unsupported_promises(genai_output)
    unsupported_facts = detect_unsupported_facts(genai_output, complaint_text, retrieved_chunks)

    all_violations.extend(unsupported_promises)
    all_violations.extend(unsupported_facts)

    # Deduplicate violations while preserving order
    dedup_violations = list(dict.fromkeys(all_violations))
    dedup_mismatches = list(dict.fromkeys(all_mismatches))

    # Step 5: Aggregate Pipeline 2 Validation Result
    rule_id = (matching_rule.get("rule_id", "") or matching_rule.get("Rule ID", "R-NONE")) if matching_rule else "R-NONE"
    is_fallback = bool(matching_rule.get("is_fallback_match", False)) if matching_rule else False

    python_result = {
        "complaint_id": complaint_id,
        "matching_rule_id": rule_id,
        "is_fallback_match": is_fallback,
        "validated_category": matching_rule.get("category", matching_rule.get("Category", category)) if matching_rule else category,
        "validated_department": matching_rule.get("department", matching_rule.get("Department", genai_output.get("department"))) if matching_rule else genai_output.get("department"),
        "validated_urgency": matching_rule.get("urgency", matching_rule.get("Urgency", genai_output.get("urgency"))) if matching_rule else genai_output.get("urgency"),
        "validated_priority": matching_rule.get("priority", matching_rule.get("Priority", genai_output.get("priority"))) if matching_rule else genai_output.get("priority"),
        "mandatory_escalation_required": mandatory_esc_req,
        "mandatory_escalation_level": esc_level,
        "ai_missed_escalation": mandatory_esc_req and not ai_esc_req,
        "policy_validity": policy_res,
        "rule_compliance": rule_res,
        "unsupported_promises": unsupported_promises,
        "unsupported_facts": unsupported_facts,
        "mismatches": dedup_mismatches,
        "violations": dedup_violations,
        "passed_validation": len(dedup_violations) == 0 and len(dedup_mismatches) == 0
    }

    # Step 6: Save Python Result to Database
    execute_statement(
        "UPDATE analysis_results SET python_result = ? WHERE complaint_id = ?",
        (json.dumps(python_result), complaint_id)
    )

    return python_result
