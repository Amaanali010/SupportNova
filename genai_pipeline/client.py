# genai_pipeline/client.py
# Module wrapping Groq API calls with Pydantic JSON schema mode, exponential backoff retries (429/timeout), and batch delay.
# Enforces Groq rules and Hard Rule 9: No fake AI responses; log API failures and route to Manual Review.

import os
import time
import json
from typing import Dict, Any, Tuple
from config.config import get_setting
from schemas.pydantic_models import GenAIAnalysisResult

def call_groq_api(prompt: str, model: str = None) -> Tuple[Dict[str, Any], str, str]:
    """
    Invokes Groq chat.completions with json_schema / json_object response format.
    Handles 429 rate limits and timeouts with exponential backoff (max 3 retries).
    Applies small batch delay setting so bulk runs do not exceed rate limits.
    
    Returns (response_dict, model_name, provider_name).
    """
    provider = get_setting("llm.provider", "groq")
    model_name = model or get_setting("llm.default_model", "llama-3.3-70b-versatile")
    max_retries = get_setting("llm.max_retries", 3)
    timeout = get_setting("llm.timeout_seconds", 30)
    batch_delay = get_setting("llm.batch_delay_seconds", 0.5)

    # Optional batch delay to prevent rate limits during dataset execution
    if batch_delay > 0:
        time.sleep(batch_delay)

    # Look for API key in os.environ, streamlit secrets, or .env file
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            pass

    if not api_key:
        raise RuntimeError("No LLM API key configured (GROQ_API_KEY missing). API call aborted.")

    from groq import Groq
    client = Groq(api_key=api_key)

    json_schema = GenAIAnalysisResult.get_json_schema()

    # Attempt API call with exponential backoff retries
    retry_count = 0
    backoff_delay = 1.0  # seconds

    while retry_count < max_retries:
        try:
            # Try structured json_schema mode first
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a JSON-only complaint analysis system."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "GenAIAnalysisResult",
                            "strict": True,
                            "schema": json_schema
                        }
                    },
                    timeout=timeout
                )
            except Exception as schema_err:
                # Fallback to json_object mode if model does not support json_schema
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": f"You are a JSON-only assistant. Return JSON matching schema:\n{json.dumps(json_schema)}"},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    timeout=timeout
                )

            raw_text = response.choices[0].message.content
            parsed_json = json.loads(raw_text)
            return parsed_json, model_name, provider

        except Exception as err:
            err_msg = str(err)
            retry_count += 1
            # Check for 429 Rate Limit or Timeout error
            if ("429" in err_msg or "rate_limit" in err_msg.lower() or "timeout" in err_msg.lower()) and retry_count < max_retries:
                time.sleep(backoff_delay)
                backoff_delay *= 2.0  # Exponential backoff (1s -> 2s -> 4s)
            else:
                if retry_count >= max_retries:
                    raise RuntimeError(f"Groq API call failed after {max_retries} retries: {err_msg}")
                time.sleep(backoff_delay)
                backoff_delay *= 2.0

    raise RuntimeError("Groq API call failed after maximum retries.")
