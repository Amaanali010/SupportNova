# prompt_templates/prompt_loader.py
# Module for loading and formatting prompt templates from prompt_templates/ by version number.
# Enforces Hard Rule 8: Prompts live only in prompt_templates/ with version numbers.

import os
from typing import List, Dict, Any

TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_prompt_template(version: str = "v1.0") -> str:
    """
    Loads raw prompt template file matching version string (e.g. v1.0 -> v1.0_triage_prompt.txt).
    """
    filename = f"{version}_triage_prompt.txt"
    filepath = os.path.join(TEMPLATE_DIR, filename)

    if not os.path.exists(filepath):
        # Fallback to default v1.0 if requested version file does not exist
        filepath = os.path.join(TEMPLATE_DIR, "v1.0_triage_prompt.txt")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prompt template file not found at: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def format_triage_prompt(
    version: str,
    complaint_id: str,
    customer_id: str,
    untrusted_text: str,
    retrieved_chunks: List[Dict[str, Any]],
    title: str = "N/A",
    customer_type: str = "Standard",
    product: str = "N/A",
    order_ref: str = "N/A"
) -> str:
    """
    Formats the loaded prompt template with policy chunks, customer context, and untrusted user input.
    """
    template_raw = load_prompt_template(version)

    # Format policy chunks into readable text blocks
    chunk_blocks = []
    for idx, chk in enumerate(retrieved_chunks, start=1):
        doc_id = chk.get("doc_id", "DOC-UNKNOWN")
        section = chk.get("section", "N/A")
        heading = chk.get("heading", "General")
        text = chk.get("text", "")
        flag = chk.get("warning_flag")
        flag_str = f" [WARNING: {flag}]" if flag else ""

        chunk_blocks.append(f"Chunk {idx} (Doc: {doc_id}, Section: {section}, Heading: {heading}){flag_str}:\n{text}")

    chunks_text = "\n\n".join(chunk_blocks) if chunk_blocks else "No relevant policy chunks retrieved."

    formatted_prompt = template_raw.format(
        retrieved_policy_chunks=chunks_text,
        customer_id=customer_id,
        complaint_id=complaint_id,
        title=title or "N/A",
        customer_type=customer_type or "Standard",
        product=product or "N/A",
        order_ref=order_ref or "N/A",
        untrusted_complaint_text=untrusted_text
    )

    return formatted_prompt
