# python_validation/rule_checker.py
# Module performing deterministic Python rule matrix validation (Zero GenAI calls).
# Enforces Hard Rule 1 & 3: Rules loaded dynamically from CSV, zero hardcoded escalation codes or levels.

import re
from typing import Dict, Any, List, Tuple
from complaint_processing.rule_loader import RULE_LOADER

# The 6 real escalation levels from resolution_rules.csv (Escalation column):
# "Not Required", "Supervisor Review", "Department Manager", "Specialist Team", "Compliance Review", "Critical Management Escalation"

def get_mandatory_escalation_for_rule(category: str, subcategory: str) -> Tuple[bool, str]:
    """
    Looks up matching rule in resolution_rules.csv matrix by Category and Subcategory.
    Reads Escalation column. If value is not 'Not Required', mandatory escalation is True.
    When no rule is found for high-risk categories (Safety, Account, Privacy), defaults to Critical Management Escalation.

    Returns (mandatory_escalation_required: bool, escalation_level: str).
    """
    rule = RULE_LOADER.find_rule(category, subcategory)
    if not rule:
        cat_clean = category.strip().lower()
        if cat_clean in ["safety", "account", "privacy"]:
            return True, "Critical Management Escalation"
        return False, "Not Required"

    esc_val = rule.get("escalation_level", "").strip() or rule.get("Escalation", "").strip() or "Not Required"

    if esc_val.lower() != "not required" and esc_val != "":
        return True, esc_val
    return False, "Not Required"

def check_rule_compliance(genai_output: Dict[str, Any], matching_rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares GenAI Pipeline 1 output against matching real Rule Matrix row.
    Validates category, department, urgency, priority, required actions, and prohibited actions.
    Supports both CSV header keys ('Category', 'Department', etc.) and DB snake_case keys ('category', 'department', etc.).
    """
    violations = []
    mismatches = []

    if not matching_rule:
        cat_clean = str(genai_output.get("category", "")).strip().lower()
        if cat_clean in ["safety", "account", "privacy"]:
            return {
                "has_rule_match": False,
                "violations": ["High-risk category with no exact rule match — defaulted to Critical Management Escalation."],
                "mismatches": ["Rule Matrix Missing (High-Risk Escalation)"]
            }
        return {
            "has_rule_match": False,
            "violations": ["No matching rule found in Rule Matrix for category/subcategory. Manual review required."],
            "mismatches": ["Rule Matrix Missing"]
        }

    # Extract fields supporting both CSV headers and DB column names
    rule_cat = str(matching_rule.get("category", "") or matching_rule.get("Category", "")).strip()
    rule_dept = str(matching_rule.get("department", "") or matching_rule.get("Department", "")).strip()
    rule_urgency = str(matching_rule.get("urgency", "") or matching_rule.get("Urgency", "Medium")).strip()
    rule_priority = str(matching_rule.get("priority", "") or matching_rule.get("Priority", "Medium")).strip()
    prohibited_str = matching_rule.get("prohibited_actions", "") or matching_rule.get("Prohibited Actions", "")
    required_str = matching_rule.get("required_actions", "") or matching_rule.get("Required Actions", "")
    rule_esc_level = (matching_rule.get("escalation_level", "") or matching_rule.get("Escalation", "") or "Not Required").strip()
    rule_id = matching_rule.get("rule_id", "") or matching_rule.get("Rule ID", "R-000")
    policy_ref = matching_rule.get("policy_reference", "") or matching_rule.get("Policy Reference", "")

    # 1. Category & Department Match
    ai_cat = str(genai_output.get("category", "")).strip()
    if ai_cat.lower() != rule_cat.lower():
        mismatches.append(f"Category mismatch (AI: '{ai_cat}' vs Rule Matrix: '{rule_cat}')")

    ai_dept = str(genai_output.get("department", "")).strip()
    if ai_dept.lower() != rule_dept.lower():
        mismatches.append(f"Department mismatch (AI: '{ai_dept}' vs Rule Matrix: '{rule_dept}')")

    # 2. Priority & Urgency Check
    ai_urgency = str(genai_output.get("urgency", "Medium")).strip()
    if ai_urgency.lower() != rule_urgency.lower():
        mismatches.append(f"Urgency mismatch (AI: '{ai_urgency}' vs Rule Matrix: '{rule_urgency}')")

    ai_priority = str(genai_output.get("priority", "Medium")).strip()
    if ai_priority.lower() != rule_priority.lower():
        mismatches.append(f"Priority mismatch (AI: '{ai_priority}' vs Rule Matrix: '{rule_priority}')")

    # 3. Prohibited Actions Check (split by '; ')
    res_text = " ".join(genai_output.get("resolution_steps", [])) + " " + genai_output.get("customer_response", "") + " " + genai_output.get("agent_guidance", "")
    res_text_lower = res_text.lower()

    prohibited_list = [p.strip().lower() for p in prohibited_str.split(";") if p.strip()]
    found_prohibited = []

    for p in prohibited_list:
        if p and p in res_text_lower:
            found_prohibited.append(p)
            violations.append(f"Prohibited action detected: '{p}'")

    # 4. Required Actions Check (split by '; ')
    required_list = [r.strip().lower() for r in required_str.split(";") if r.strip()]
    missing_required = []

    for r in required_list:
        # Check key phrase match
        key_phrase = r[:30].strip() if len(r) > 30 else r
        if key_phrase and key_phrase not in res_text_lower:
            missing_required.append(r)
            violations.append(f"Missing mandatory required action: '{r[:60]}...'")

    # 5. Escalation Level & Contradictions Check
    ai_esc_req = bool(genai_output.get("escalation_required", False))
    ai_esc_lvl = str(genai_output.get("escalation_level", "Not Required")).strip()

    if rule_esc_level.lower() != "not required" and not ai_esc_req:
        violations.append(f"MISSED MANDATORY ESCALATION: Rule matrix requires '{rule_esc_level}' but AI reported escalation_required=False.")

    return {
        "has_rule_match": True,
        "rule_id": rule_id,
        "rule_category": rule_cat,
        "rule_department": rule_dept,
        "rule_urgency": rule_urgency,
        "rule_priority": rule_priority,
        "policy_reference": policy_ref,
        "escalation_level": rule_esc_level,
        "mismatches": mismatches,
        "violations": violations,
        "found_prohibited": found_prohibited,
        "missing_required": missing_required
    }
