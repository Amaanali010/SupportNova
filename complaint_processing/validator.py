# complaint_processing/validator.py
# Module for validating complaint input fields, performing security sanitization, and checking prompt injection.

from typing import Dict, Any, List, Tuple, Optional
from security.sanitizer import mask_sensitive_data, detect_prompt_injection, sanitize_and_wrap_input

def check_missing_information(order_ref: str, complaint_text: str) -> Tuple[bool, List[str]]:
    """
    Checks if mandatory order_ref is missing for order-related complaints per CMP-SOP-01 2.2.
    Non-order categories (Account, Privacy, App/Website bugs) do not require order_ref.
    Returns (is_missing_info: bool, missing_fields: List[str]).
    """
    if order_ref and order_ref.strip():
        return False, []

    text_lower = complaint_text.lower() if complaint_text else ""
    non_order_keywords = ["account", "password", "login", "privacy", "data breach", "personal data", "consent", "app crash", "website bug", "bug report"]
    if any(k in text_lower for k in non_order_keywords):
        return False, []

    return True, ["order_ref"]

def validate_and_sanitize_complaint(complaint_text: str, customer_id: str, channel: str = "Web", title: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates complaint inputs, masks sensitive PII, detects prompt injection, and formats untrusted text.
    """
    errors = []

    # Validate Customer ID
    if not customer_id or not customer_id.strip():
        errors.append("Customer ID is required.")

    # Validate Title if title is explicitly passed as a string
    if title is not None and not title.strip():
        errors.append("Complaint Title is required.")

    # Validate Complaint Text
    text_clean = complaint_text.strip() if complaint_text else ""
    if not text_clean:
        errors.append("Complaint text cannot be empty.")
    elif len(text_clean) < 10:
        errors.append("Complaint text must be at least 10 characters long.")

    if errors:
        return {
            "is_valid": False,
            "errors": errors,
            "sanitized_text": text_clean,
            "delimited_text": "",
            "is_injection_detected": False,
            "injection_flags": []
        }

    # Step 1: Mask PII (credit cards, passwords, national IDs)
    sanitized = mask_sensitive_data(text_clean)

    # Step 2: Detect Prompt Injection (Hard Rule 6)
    is_injection, flags = detect_prompt_injection(sanitized)

    # Step 3: Wrap untrusted text in XML/delimiter tags
    delimited, _, _ = sanitize_and_wrap_input(sanitized)

    return {
        "is_valid": True,
        "errors": [],
        "sanitized_text": sanitized,
        "delimited_text": delimited,
        "is_injection_detected": is_injection,
        "injection_flags": flags
    }
