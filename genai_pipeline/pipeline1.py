# genai_pipeline/pipeline1.py
# Module for executing Pipeline 1 (GenAI Triage & Structured Interpretation).
# Re-validates output against Pydantic schema and allowed values, logs API metadata, and handles API failures without fake outputs.

import json
from typing import Dict, Any, List, Tuple, Optional
from config.config import get_setting
from prompt_templates.prompt_loader import format_triage_prompt
from schemas.pydantic_models import GenAIAnalysisResult
from genai_pipeline.client import call_groq_api
from database.db import execute_statement

def run_pipeline1(
    complaint_id: str,
    complaint_text: str,
    customer_id: str,
    retrieved_chunks: List[Dict[str, Any]],
    override_model: str = None,
    title: str = "N/A",
    customer_type: str = "Standard",
    product: str = "N/A",
    order_ref: str = "N/A",
    **kwargs
) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    """
    Executes Pipeline 1 GenAI Analysis for a customer complaint.
    Returns (validated_result_dict, is_success, status_message).
    """
    prompt_version = get_setting("llm.prompt_version", "v1.0")

    # Step 1: Format Prompt with Versioning and Untrusted Text Block
    try:
        prompt_text = format_triage_prompt(
            version=prompt_version,
            complaint_id=complaint_id,
            customer_id=customer_id,
            untrusted_text=complaint_text,
            retrieved_chunks=retrieved_chunks,
            title=title,
            customer_type=customer_type,
            product=product,
            order_ref=order_ref
        )
    except Exception as e:
        return None, False, f"Prompt formatting error: {str(e)}"

    # Step 2: Call LLM API (Groq with retries and exponential backoff)
    try:
        raw_json, model_used, provider_used = call_groq_api(prompt_text, model=override_model)
    except Exception as api_err:
        # Hard Rule 9: If GenAI API fails, do NOT generate fake output!
        # Log failure, write audit log, and route complaint to Manual Review.
        err_msg = f"Pipeline 1 API Failure: {str(api_err)}"
        execute_statement(
            "UPDATE complaints SET status = 'Manual_Review' WHERE complaint_id = ?",
            (complaint_id,)
        )
        execute_statement(
            "INSERT INTO audit_log (user_id, action, target_type, target_id, details) VALUES (?, ?, ?, ?, ?)",
            ("SYSTEM", "PIPELINE_1_FAILURE", "COMPLAINT", complaint_id, err_msg)
        )
        return None, False, err_msg

    # Step 3: Re-validate LLM JSON with Pydantic Schema and Allowed-Values
    try:
        pydantic_obj = GenAIAnalysisResult(**raw_json)
        analysis_dict = pydantic_obj.model_dump()
    except Exception as val_err:
        err_msg = f"Pipeline 1 Pydantic Validation Error: {str(val_err)}"
        execute_statement(
            "UPDATE complaints SET status = 'Manual_Review' WHERE complaint_id = ?",
            (complaint_id,)
        )
        return None, False, err_msg

    # Step 4: Extract Policy Versions applied
    policy_versions_list = list(set([chk.get("version", "v1.0") for chk in retrieved_chunks if chk.get("version")]))
    policy_versions_str = ", ".join(policy_versions_list) if policy_versions_list else "None"

    # Step 5: Save Analysis Result to Database
    execute_statement(
        """
        INSERT INTO analysis_results (
            complaint_id, genai_json, verification_status, prompt_version, model, provider, policy_versions
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            complaint_id,
            json.dumps(analysis_dict),
            "Pending_Pipeline2",
            prompt_version,
            model_used,
            provider_used,
            policy_versions_str
        )
    )

    return analysis_dict, True, f"Pipeline 1 completed successfully using model {model_used} ({provider_used})."
