# python_validation/policy_checker.py
# Module for verifying policy document existence, Active status, date validity, and section presence in DB.
# Enforces Hard Rule 5: Only Active documents inside effective and expiry dates may be primary basis of resolution.

from typing import Dict, Any, List
from database.db import execute_query
from document_processing.validator import evaluate_document_validity

def check_policy_validity(policy_id: str, policy_section: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates whether the policy specified by Pipeline 1 exists, is Active, within date validity, and section exists.
    """
    violations = []
    flags = []

    if not policy_id or policy_id == "None":
        return {
            "policy_exists": False,
            "is_active": False,
            "is_primary_valid": False,
            "section_found": False,
            "violations": ["No policy ID specified by GenAI analysis."],
            "flags": ["Missing Policy ID"]
        }

    # Query DB for policy document
    rows = execute_query("SELECT * FROM documents WHERE doc_id = ?", (policy_id.strip(),))
    if not rows:
        violations.append(f"Referenced policy ID '{policy_id}' does not exist in document database.")
        return {
            "policy_exists": False,
            "is_active": False,
            "is_primary_valid": False,
            "section_found": False,
            "violations": violations,
            "flags": ["Non-Existent Policy ID"]
        }

    doc = dict(rows[0])
    status = doc.get("status", "Draft")
    eff_date = doc.get("effective_date", "")
    exp_date = doc.get("expiry_date", "")

    # Evaluate HARD RULE 5 Active & Date Range validity
    val_eval = evaluate_document_validity(status, eff_date, exp_date)

    if not val_eval["is_primary_valid"]:
        flag_msg = val_eval["flag"]
        violations.append(f"Policy '{policy_id}' cannot be primary resolution basis: {flag_msg}")
        flags.append(flag_msg)

    # Check if section exists in retrieved policy chunks
    section_found = False
    if policy_section:
        sec_clean = policy_section.lower().replace("section", "").strip()
        for chk in retrieved_chunks:
            chk_sec = chk.get("section", "").lower().strip()
            chk_heading = chk.get("heading", "").lower().strip()
            if sec_clean in chk_sec or sec_clean in chk_heading or chk_sec in sec_clean:
                section_found = True
                break

    if not section_found and policy_section and policy_section != "None":
        violations.append(f"Specified policy section '{policy_section}' was not found in retrieved policy context.")

    return {
        "policy_exists": True,
        "doc_title": doc.get("title", ""),
        "status": status,
        "is_primary_valid": val_eval["is_primary_valid"],
        "section_found": section_found,
        "violations": violations,
        "flags": flags
    }
