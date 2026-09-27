# comparison_engine/comparator.py
# Module comparing GenAI (Pipeline 1) and Python (Pipeline 2) outputs.
# Calculates deterministic verification score (Hard Rule 9: No fake scores) and routes to Verified or Manual Review.

import json
from typing import Dict, Any, List, Tuple
from database.db import execute_statement

def compare_ai_and_python_results(
    complaint_id: str,
    genai_output: Dict[str, Any],
    python_result: Dict[str, Any],
    is_injection_detected: bool = False
) -> Dict[str, Any]:
    """
    Compares AI vs Python outputs across category, department, urgency, priority, and escalation.
    Computes a real deterministic verification score based on passed validation checks.
    Determines final status: 'Verified' or 'Manual_Review'.
    """
    if not genai_output or not python_result:
        return {
            "verification_status": "Manual_Review",
            "verification_score": 0.0,
            "disagreement_reasons": ["Pipeline output missing or incomplete."],
            "mismatches": ["Incomplete Pipeline Runs"]
        }

    checks = []
    mismatches = []
    disagreement_reasons = []

    # 1. Category Check
    ai_cat = str(genai_output.get("category", "")).strip().lower()
    py_cat = str(python_result.get("validated_category", "")).strip().lower()
    cat_match = (ai_cat == py_cat)
    checks.append(cat_match)
    if not cat_match:
        mismatches.append(f"Category Disagreement (AI: '{genai_output.get('category')}' vs Python: '{python_result.get('validated_category')}')")
        disagreement_reasons.append("Category classification mismatch between AI and Rule Matrix.")

    # 2. Department Check
    ai_dept = str(genai_output.get("department", "")).strip().lower()
    py_dept = str(python_result.get("validated_department", "")).strip().lower()
    dept_match = (ai_dept == py_dept)
    checks.append(dept_match)
    if not dept_match:
        mismatches.append(f"Department Disagreement (AI: '{genai_output.get('department')}' vs Python: '{python_result.get('validated_department')}')")
        disagreement_reasons.append("Handling department mismatch.")

    # 3. Urgency & Priority Check
    ai_urg = str(genai_output.get("urgency", "")).strip().lower()
    py_urg = str(python_result.get("validated_urgency", "")).strip().lower()
    urg_match = (ai_urg == py_urg)
    checks.append(urg_match)
    if not urg_match:
        mismatches.append(f"Urgency Disagreement (AI: '{genai_output.get('urgency')}' vs Python: '{python_result.get('validated_urgency')}')")
        disagreement_reasons.append("Urgency level mismatch.")

    # 4. Escalation Requirement Check
    ai_esc_req = bool(genai_output.get("escalation_required", False))
    py_esc_req = bool(python_result.get("mandatory_escalation_required", False))
    esc_match = (ai_esc_req == py_esc_req)
    checks.append(esc_match)
    if not esc_match:
        mismatches.append(f"Escalation Requirement Disagreement (AI: {ai_esc_req} vs Python: {py_esc_req})")
        disagreement_reasons.append("Escalation requirement disagreement.")

    # 5. Missed Escalation Override Check
    ai_missed_esc = python_result.get("ai_missed_escalation", False)
    checks.append(not ai_missed_esc)
    if ai_missed_esc:
        disagreement_reasons.append("GenAI missed mandatory escalation trigger(s).")

    # 6. Policy Document Validity Check (Hard Rule 5)
    pol_valid = python_result.get("policy_validity", {}).get("is_primary_valid", False)
    checks.append(pol_valid)
    if not pol_valid:
        disagreement_reasons.append("Referenced policy is non-active, expired, or superseded.")

    # 7. Prohibited Actions & Unsupported Promises Check
    rule_violations = python_result.get("violations", [])
    has_violations = (len(rule_violations) > 0)
    checks.append(not has_violations)
    if has_violations:
        disagreement_reasons.extend(rule_violations)

    # 8. Prompt Injection Check (Hard Rule 6)
    checks.append(not is_injection_detected)
    if is_injection_detected:
        disagreement_reasons.append("Security Alert: Prompt injection pattern detected in input text.")

    # Calculate real deterministic verification score (0.0 to 1.0)
    passed_count = sum(1 for c in checks if c)
    total_count = len(checks)
    verification_score = round(passed_count / total_count, 2) if total_count > 0 else 0.0

    # Determine final verification status
    if verification_score == 1.0 and not is_injection_detected and not ai_missed_esc and pol_valid and not has_violations:
        final_status = "Verified"
    else:
        final_status = "Manual_Review"

    comparison_result = {
        "complaint_id": complaint_id,
        "verification_status": final_status,
        "verification_score": verification_score,
        "category_match": cat_match,
        "department_match": dept_match,
        "urgency_match": urg_match,
        "escalation_match": esc_match,
        "ai_missed_escalation": ai_missed_esc,
        "policy_valid": pol_valid,
        "is_injection_detected": is_injection_detected,
        "mismatches": mismatches,
        "disagreement_reasons": disagreement_reasons
    }

    # Save to Database
    execute_statement(
        "UPDATE analysis_results SET verification_status = ?, mismatches = ? WHERE complaint_id = ?",
        (final_status, json.dumps(mismatches), complaint_id)
    )

    val_cat = python_result.get("validated_category") or genai_output.get("category")
    val_sub = genai_output.get("subcategory")
    val_urg = python_result.get("validated_urgency") or genai_output.get("urgency")
    val_prio = python_result.get("validated_priority") or genai_output.get("priority")

    execute_statement(
        "UPDATE complaints SET status = ?, category = ?, subcategory = ?, urgency = ?, priority = ? WHERE complaint_id = ?",
        (final_status, val_cat, val_sub, val_urg, val_prio, complaint_id)
    )

    return comparison_result
