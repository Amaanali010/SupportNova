# hallucination_checks/hallucination_detector.py
# Module for checking unsupported promises ("guaranteed refund") and hallucinated facts against raw complaint & chunks.

import re
from typing import Dict, Any, List, Tuple

PROHIBITED_UNSUPPORTED_PROMISES = [
    "guaranteed refund",
    "guarantee refund",
    "100% money back guarantee",
    "cash payout",
    "direct bank transfer",
    "promise agent termination",
    "fire the agent",
    "instant wire transfer"
]

def detect_unsupported_promises(genai_output: Dict[str, Any]) -> List[str]:
    """
    Scans AI resolution steps, agent guidance, and customer response for unauthorized or prohibited promises.
    Returns list of detected unsupported promise violation strings.
    """
    violations = []
    res_steps = genai_output.get("resolution_steps", [])
    cust_resp = genai_output.get("customer_response", "")
    guidance = genai_output.get("agent_guidance", "")

    full_text = (" ".join(res_steps) + " " + cust_resp + " " + guidance).lower()

    for promise in PROHIBITED_UNSUPPORTED_PROMISES:
        if promise in full_text:
            violations.append(f"Unsupported promise detected: '{promise}' in GenAI output.")

    return violations

def detect_unsupported_facts(
    genai_output: Dict[str, Any],
    raw_complaint_text: str,
    retrieved_chunks: List[Dict[str, Any]]
) -> List[str]:
    """
    Cross-checks extracted entities and facts against raw complaint text and policy chunks.
    Flags facts or entity identifiers invented by GenAI that do not exist in input sources.
    """
    unsupported = []
    source_corpus = (raw_complaint_text + " " + " ".join([c.get("text", "") for c in retrieved_chunks])).lower()

    entities = genai_output.get("entities", [])
    for ent in entities:
        ent_clean = str(ent).strip().lower()
        # Skip trivial short words
        if len(ent_clean) > 3 and ent_clean not in source_corpus:
            unsupported.append(f"Unsupported fact/entity: '{ent}' mentioned by AI was not found in complaint or policies.")

    return unsupported
