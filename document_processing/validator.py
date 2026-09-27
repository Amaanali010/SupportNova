# document_processing/validator.py
# Module for validating uploaded policy documents and verifying document status/validity dates.

import os
from datetime import datetime
from typing import Tuple, List, Dict, Any

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
REQUIRED_METADATA_FIELDS = ["doc_id", "title", "version", "status", "effective_date", "expiry_date"]

def validate_file_extension(filename: str) -> bool:
    """
    Validates if an uploaded file has a supported extension (.pdf, .docx, .txt).
    """
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that policy document metadata contains all required fields.
    Returns (is_valid, missing_fields).
    """
    missing = [field for field in REQUIRED_METADATA_FIELDS if not metadata.get(field)]
    return len(missing) == 0, missing

def check_date_validity(effective_date_str: str, expiry_date_str: str, reference_date_str: str = None) -> Tuple[bool, str]:
    """
    Checks if a reference date (defaults to today) falls within effective_date and expiry_date.
    Returns (is_within_dates, status_message).
    """
    try:
        ref_date = datetime.strptime(reference_date_str, "%Y-%m-%d").date() if reference_date_str else datetime.now().date()
        eff_date = datetime.strptime(effective_date_str, "%Y-%m-%d").date()
        exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        if ref_date < eff_date:
            return False, "Not Yet Effective"
        if ref_date > exp_date:
            return False, "Expired"
        return True, "Valid Date Range"
    except Exception as e:
        return False, f"Date Parse Error: {str(e)}"

def evaluate_document_validity(status: str, effective_date_str: str, expiry_date_str: str, reference_date_str: str = None) -> Dict[str, Any]:
    """
    Hard Rule 5 Enforcement: Evaluates whether a document can be the primary basis of resolution.
    Only Active status documents inside their effective and expiry dates are valid for primary resolution.
    Superseded and Draft ones get flagged as reference-only.
    """
    date_valid, date_msg = check_date_validity(effective_date_str, expiry_date_str, reference_date_str)
    
    is_active = status.strip().capitalize() == "Active"
    is_primary_valid = is_active and date_valid

    flag = None
    if not is_active:
        flag = f"Non-Active Status ({status})"
    elif not date_valid:
        flag = f"Invalid Date Range ({date_msg})"

    return {
        "is_primary_valid": is_primary_valid,
        "status": status,
        "date_status": date_msg,
        "flag": flag
    }
