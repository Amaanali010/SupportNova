# database/models.py
# Dataclasses representing entity records in the database.
# Updated to match the real VoltKart Rule Matrix and 500-complaints dataset schemas.

from dataclasses import dataclass
from typing import Optional

@dataclass
class UserRecord:
    """Represents a registered user in the system."""
    id: int
    username: str
    password_hash: str
    role: str # customer, agent, reviewer, manager, admin
    full_name: str
    email: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class DocumentRecord:
    """Represents a policy document metadata record."""
    doc_id: str
    title: str
    category: str
    version: str
    status: str # Active, Superseded, Draft
    effective_date: str
    expiry_date: str
    owner: str
    supersedes: Optional[str] = None
    file_path: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class ChunkRecord:
    """Represents a searchable policy text chunk for RAG."""
    chunk_id: str
    doc_id: str
    section: str
    heading: str
    page: int
    text: str
    version: str
    status: str

@dataclass
class RuleRecord:
    """Represents a deterministic complaint resolution rule matching real 114-row matrix."""
    rule_id: str
    category: str
    subcategory: str
    case_variant: str
    conditions: str
    department: str
    urgency: str
    priority: str
    policy_reference: str
    escalation_level: str
    required_actions: str
    prohibited_actions: str
    follow_up_required: str

@dataclass
class ComplaintRecord:
    """Represents a customer complaint submission matching real 500-row dataset."""
    complaint_id: str
    title: Optional[str] = None
    customer_id: Optional[str] = None
    customer_type: Optional[str] = None
    product: Optional[str] = None
    order_ref: Optional[str] = None
    complaint_text: str = ""
    channel: str = "Web"
    status: str = "Submitted"
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[str] = None
    urgency: Optional[str] = None
    special_case: Optional[str] = None
    duplicate_group: Optional[str] = None
    duplicate_of: Optional[str] = None
    exp_category: Optional[str] = None
    exp_subcategory: Optional[str] = None
    exp_department: Optional[str] = None
    exp_urgency: Optional[str] = None
    exp_priority: Optional[str] = None
    exp_escalation: Optional[str] = None
    notes: Optional[str] = None
    is_repeat: int = 0
    is_duplicate: int = 0
    created_at: Optional[str] = None
