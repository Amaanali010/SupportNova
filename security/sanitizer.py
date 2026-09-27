# security/sanitizer.py
# Security module for masking sensitive data (PII) and detecting prompt injection attempts.

import re
from typing import Tuple, List
from config.config import get_setting

# Regex patterns for detecting and masking sensitive data
CREDIT_CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
PASSWORD_KEYWORD_REGEX = re.compile(r'(?i)\b(password|passwd|pwd|pass)\s*[:=]\s*(\S+)')
NATIONAL_ID_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b')

def mask_sensitive_data(text: str) -> str:
    """
    Masks credit card numbers, passwords, and national IDs in untrusted text.
    Replaces them with [MASKED_CREDIT_CARD], [MASKED_PASSWORD], [MASKED_ID].
    """
    if not text:
        return ""
    
    masked_text = text
    # Mask credit cards
    if get_setting("security.mask_credit_cards", True):
        masked_text = CREDIT_CARD_REGEX.sub("[MASKED_CREDIT_CARD]", masked_text)
    
    # Mask passwords
    if get_setting("security.mask_passwords", True):
        masked_text = PASSWORD_KEYWORD_REGEX.sub(r'\1: [MASKED_PASSWORD]', masked_text)
        
    # Mask national IDs / SSNs
    if get_setting("security.mask_national_ids", True):
        masked_text = NATIONAL_ID_REGEX.sub("[MASKED_NATIONAL_ID]", masked_text)
        
    return masked_text

def detect_prompt_injection(text: str) -> Tuple[bool, List[str]]:
    """
    Scans untrusted input for malicious prompt injection phrases.
    Returns (is_injection_detected: bool, matched_keywords: List[str])
    """
    if not text:
        return False, []
    
    keywords = get_setting("security.injection_keywords", [
        "ignore your rules",
        "ignore previous instructions",
        "approve my refund",
        "i am the admin",
        "override policy",
        "bypass validation"
    ])
    
    text_lower = text.lower()
    detected_patterns = []
    
    for kw in keywords:
        if kw.lower() in text_lower:
            detected_patterns.append(kw)
            
    return len(detected_patterns) > 0, detected_patterns

def sanitize_and_wrap_input(text: str) -> Tuple[str, bool, List[str]]:
    """
    Sanitizes untrusted text by masking PII, checks for prompt injection,
    and wraps the text in clear XML/delimiter tags for LLM safety.
    
    Returns (safe_delimited_text, is_injection, injection_flags)
    """
    masked = mask_sensitive_data(text)
    is_injection, flags = detect_prompt_injection(masked)
    
    delimited = (
        "<<<UNTRUSTED_USER_INPUT_START>>>\n"
        f"{masked}\n"
        "<<<UNTRUSTED_USER_INPUT_END>>>"
    )
    
    return delimited, is_injection, flags
