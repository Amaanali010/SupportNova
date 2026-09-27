# schemas/pydantic_models.py
# Pydantic schemas for validating Pipeline 1 GenAI outputs and system responses.

import logging
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from config.config import get_setting

class GenAIAnalysisResult(BaseModel):
    """
    Pydantic schema defining the required 24 structured output fields from Pipeline 1.
    Strictly validated against allowed categories, departments, urgency, and priority levels.
    """
    primary_issue: str = Field(description="Main root cause or issue of the customer complaint")
    secondary_issues: List[str] = Field(default_factory=list, description="Additional side issues mentioned")
    category: str = Field(description="Primary category classification")
    subcategory: str = Field(description="Subcategory classification")
    sentiment: str = Field(description="Customer sentiment (e.g. Frustrated, Neutral, Angry)")
    emotion_indicators: List[str] = Field(default_factory=list, description="Emotional indicators detected in text")
    urgency: str = Field(description="Assigned urgency level (Low, Medium, High, Critical)")
    priority: str = Field(description="Assigned priority level (P0, P1, P2, P3)")
    entities: List[str] = Field(default_factory=list, description="Extracted entity names (Order ID, Product, Amounts)")
    department: str = Field(description="Primary handling department")
    supporting_departments: List[str] = Field(default_factory=list, description="Secondary assisting departments")
    policy_id: str = Field(description="Primary policy document ID applied (e.g. REF-POL-01)")
    policy_section: str = Field(description="Specific section heading or clause (e.g. Section 4.2)")
    resolution_steps: List[str] = Field(default_factory=list, description="Actionable step-by-step resolution plan")
    escalation_required: bool = Field(description="True if mandatory or recommended escalation is triggered")
    escalation_level: str = Field(default="Not Required", description="Escalation tier (e.g. Not Required, Supervisor Review, etc.)")
    escalation_reason: str = Field(default="", description="Justification for escalation")
    escalation_notes: str = Field(default="", description="Detailed guidance notes for escalation team")
    customer_response: str = Field(description="Suggested formal empathetic email reply to the customer")
    follow_up_required: bool = Field(description="True if customer or agent follow-up task is required")
    follow_up_type: str = Field(default="None", description="Type of follow-up required (e.g. Email, Call, Refund Check, None)")
    agent_guidance: str = Field(description="Internal instructions for the support agent")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions to ask customer if information is missing")
    complaint_summary: str = Field(description="Concise 2-sentence summary of the complaint")

    @field_validator('category')
    def validate_category(cls, v: str) -> str:
        allowed = get_setting('categories', [])
        if allowed and v not in allowed:
            pass
        return v

    @field_validator('urgency')
    def validate_urgency(cls, v: str) -> str:
        allowed = get_setting('urgency_levels', ['Low', 'Medium', 'High', 'Critical'])
        if v not in allowed:
            logging.warning(f"Invalid urgency '{v}' received from LLM. Allowed: {allowed}")
            raise ValueError(f"Invalid urgency '{v}'. Must be one of {allowed}.")
        return v

    @field_validator('priority')
    def validate_priority(cls, v: str) -> str:
        allowed = get_setting('priority_levels', ['P0', 'P1', 'P2', 'P3'])
        if v not in allowed:
            logging.warning(f"Invalid priority '{v}' received from LLM. Allowed: {allowed}")
            raise ValueError(f"Invalid priority '{v}'. Must be one of {allowed}.")
        return v

    @classmethod
    def get_json_schema(cls) -> dict:
        """
        Returns the OpenAI/Groq compatible JSON schema dict.
        """
        return cls.model_json_schema()
