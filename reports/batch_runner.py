# reports/batch_runner.py
# Module for running the 500-complaint dataset through Pipeline 1, Pipeline 2, and the Comparison Engine.
# Respects LLM rate limit batch delays and generates the final comparison report.

import os
import csv
import json
import time
from typing import Dict, Any, List
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db import execute_query, execute_statement
from knowledge_base.document_manager import DOCUMENT_MANAGER
from complaint_processing.validator import validate_and_sanitize_complaint
from genai_pipeline.pipeline1 import run_pipeline1
from python_validation.pipeline2 import run_pipeline2
from comparison_engine.comparator import compare_ai_and_python_results

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_batch_dataset_evaluation(limit: int = None, csv_path: str = None) -> Dict[str, Any]:
    """
    Executes the batch evaluation pipeline over the dataset CSV.
    Processes each complaint through RAG, Pipeline 1, Pipeline 2, and Comparison Engine.
    Returns aggregate summary statistics.
    """
    target_csv = csv_path or os.path.join(BASE_DIR, "sample_complaints", "complaints_500.csv")
    if not os.path.exists(target_csv):
        raise FileNotFoundError(f"Batch dataset CSV not found at: {target_csv}")

    rows_to_process = []
    with open(target_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows_to_process.append(r)

    if limit and limit > 0:
        rows_to_process = rows_to_process[:limit]

    total_count = len(rows_to_process)
    verified_count = 0
    manual_review_count = 0
    cat_matches = 0
    dept_matches = 0
    urg_matches = 0
    esc_matches = 0
    missed_esc_raised_by_python = 0
    injections_flagged = 0

    results_detail = []

    for idx, row in enumerate(rows_to_process, start=1):
        complaint_id = row.get("id", "").strip() or f"CMP-BATCH-{idx:04d}"
        customer_id = row.get("order_ref", "").strip() or row.get("customer_type", "").strip() or f"CUST-{idx:04d}"
        raw_text = row.get("description", "").strip()

        # Step 1: Validate, sanitize & check prompt injection
        val_res = validate_and_sanitize_complaint(raw_text, customer_id)
        is_inj = val_res["is_injection_detected"]
        sanitized_text = val_res["sanitized_text"]

        if is_inj:
            injections_flagged += 1

        # Step 2: Retrieve RAG policy context
        retrieved_chunks = DOCUMENT_MANAGER.retrieve_chunks(sanitized_text, top_k=3)

        # Step 3: Execute Pipeline 1 (GenAI Triage)
        ai_out, ai_success, ai_msg = run_pipeline1(
            complaint_id=complaint_id,
            complaint_text=sanitized_text,
            customer_id=customer_id,
            retrieved_chunks=retrieved_chunks
        )

        # Step 4: Execute Pipeline 2 (Python Rule Matrix Validation)
        p2_out = {}
        comp_res = {}

        if ai_success and ai_out:
            p2_out = run_pipeline2(
                complaint_id=complaint_id,
                complaint_text=sanitized_text,
                genai_output=ai_out,
                retrieved_chunks=retrieved_chunks
            )

            # Step 5: Comparison Engine Evaluation
            comp_res = compare_ai_and_python_results(
                complaint_id=complaint_id,
                genai_output=ai_out,
                python_result=p2_out,
                is_injection_detected=is_inj
            )

            if comp_res["verification_status"] == "Verified":
                verified_count += 1
            else:
                manual_review_count += 1

            if comp_res.get("category_match"): cat_matches += 1
            if comp_res.get("department_match"): dept_matches += 1
            if comp_res.get("urgency_match"): urg_matches += 1
            if comp_res.get("escalation_match"): esc_matches += 1
            if comp_res.get("ai_missed_escalation"): missed_esc_raised_by_python += 1
        else:
            manual_review_count += 1

        results_detail.append({
            "complaint_id": complaint_id,
            "status": comp_res.get("verification_status", "Manual_Review"),
            "score": comp_res.get("verification_score", 0.0),
            "is_injection": is_inj
        })

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_processed": total_count,
        "verified_count": verified_count,
        "manual_review_count": manual_review_count,
        "verification_rate_pct": round((verified_count / total_count) * 100, 1) if total_count > 0 else 0.0,
        "category_agreement_pct": round((cat_matches / total_count) * 100, 1) if total_count > 0 else 0.0,
        "department_agreement_pct": round((dept_matches / total_count) * 100, 1) if total_count > 0 else 0.0,
        "urgency_agreement_pct": round((urg_matches / total_count) * 100, 1) if total_count > 0 else 0.0,
        "escalation_agreement_pct": round((esc_matches / total_count) * 100, 1) if total_count > 0 else 0.0,
        "missed_escalations_raised_by_python": missed_esc_raised_by_python,
        "prompt_injections_flagged": injections_flagged
    }

    # Write summary report markdown file
    write_comparison_report_markdown(summary)
    return summary

def write_comparison_report_markdown(summary: Dict[str, Any]) -> str:
    """
    Generates reports/comparison_report.md containing dataset analysis and dual-pipeline performance metrics.
    """
    report_md = f"""# SupportNova - Dual-Pipeline Triage & Verification Comparison Report

**Generated Date**: {summary.get('timestamp')}  
**Target Dataset**: `sample_complaints/complaints_500.csv`  

---

## 📊 Summary Performance Metrics

| Metric | Value |
| :--- | :--- |
| **Total Complaints Processed** | {summary.get('total_processed')} |
| **Verified Automatically** | {summary.get('verified_count')} ({summary.get('verification_rate_pct')}%) |
| **Routed to Manual Review** | {summary.get('manual_review_count')} |
| **Category Agreement Rate** | {summary.get('category_agreement_pct')}% |
| **Department Agreement Rate** | {summary.get('department_agreement_pct')}% |
| **Urgency/Priority Agreement Rate** | {summary.get('urgency_agreement_pct')}% |
| **Escalation Agreement Rate** | {summary.get('escalation_agreement_pct')}% |
| **Missed Escalations Raised by Python** | {summary.get('missed_escalations_raised_by_python')} |
| **Security Prompt Injections Flagged** | {summary.get('prompt_injections_flagged')} |

---

## 🛡️ Key Architectural Guardrails Demonstrated

1. **Zero-AI Mandatory Escalation Enforcement**:
   - Python Pipeline 2 independently evaluates mandatory escalation triggers from the Complaint Resolution Rule Matrix.
   - Caught **{summary.get('missed_escalations_raised_by_python')}** case(s) where GenAI failed to escalate, automatically escalating them to staff review.

2. **Security & Prompt Injection Protection**:
   - Flagged **{summary.get('prompt_injections_flagged')}** prompt injection attempt(s) (e.g., `"ignore your rules"`, `"approve my refund"`).
   - Wrapped untrusted user input inside XML delimiters `<<<UNTRUSTED_USER_INPUT_START>>>` to prevent prompt hijacking.

3. **Deterministic Verification Scoring**:
   - Enforced Hard Rule 9: Verification scores are computed strictly from empirical matching checks, eliminating arbitrary AI confidence ratings.

---
*Report generated automatically by SupportNova Batch Processing Engine.*
"""
    report_path = os.path.join(BASE_DIR, "reports", "comparison_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    return report_path

if __name__ == "__main__":
    summary = run_batch_dataset_evaluation()
    print("Batch Processing Summary:", json.dumps(summary, indent=2))
