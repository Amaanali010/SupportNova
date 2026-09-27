# AI Usage Log - SupportNova

This log documents all AI-assisted development activities for transparency and competition compliance.

## Phase 1: Repo Skeleton, Configuration, Database Schema, Seed Script & Role-Based Auth
- **Timestamp**: 2026-09-24
- **Assisted Components**:
  - Repo directory structure and configuration architecture (`config/settings.yaml`, `config/config.py`).
  - SQLite database schema and seed pipeline (`database/db.py`, `database/models.py`, `database/seed.py`).
  - Pydantic schema validation models (`schemas/pydantic_models.py`).
  - Security module with PBKDF2 password hashing, RBAC, and input sanitization (`security/auth.py`, `security/sanitizer.py`).
  - Streamlit multi-page UI architecture with responsive dark glassmorphism design.
  - Pytest suite verifying DB tables, seeding, authentication, and security (`tests/test_phase1.py`).
- **Human Verification**:
  - Verified database table creation and seed data execution.
  - Verified role-based access control and password hashing unit tests pass.

## Phase 2: Document Validation, Parsing, Chunking, Version Status & TF-IDF Retrieval
- **Timestamp**: 2026-09-24
- **Assisted Components**:
  - Document validation module for file extensions (.pdf, .docx, .txt) and metadata rules (`document_processing/validator.py`).
  - Document parsers extracting structured sections and numbered headings (`document_processing/parser.py`).
  - Policy text chunking algorithm (`document_processing/chunker.py`).
  - TF-IDF vectorizer indexing, document validity date evaluation, precedence ranking, and cosine similarity RAG retrieval (`knowledge_base/tfidf_retriever.py`).
  - Document manager coordinating DB sync and RAG queries (`knowledge_base/document_manager.py`).
  - Pytest suite verifying document parsing, chunking, date validity, precedence scoring, and TF-IDF RAG retrieval (`tests/test_phase2.py`).
- **Human Verification**:
  - Verified active vs superseded/draft policy date evaluation (HARD RULE 5).
  - Verified precedence scoring hierarchy (Legal > Escalation SOP > Policy > Active SOP > Template > FAQ).
  - Verified 14/14 pytest unit tests pass across Phase 1, Phase 2, and Phase 3.

## Phase 3: Rule Matrix Loader, Complaint Validation, Sanitization & Duplicate Detection
- **Timestamp**: 2026-09-26
- **Assisted Components**:
  - Dynamic CSV rule matrix loader module (`complaint_processing/rule_loader.py`).
  - Input validation, PII masking, and prompt injection wrapper (`complaint_processing/validator.py`).
  - Duplicate complaint detection and repeat customer submission tracker (`complaint_processing/duplicate_detector.py`).
  - Updated Streamlit complaint submission page (`pages/2_Submit_Complaint.py`).
  - Pytest test suite verifying rule matrix parsing, input sanitization, injection flags, and duplicate/repeat detection (`tests/test_phase3.py`).
- **Human Verification**:
  - Verified dynamic CSV header parsing without hardcoded column names (HARD RULES 1 & 3).
  - Verified prompt injection flagging and direct routing to Manual Review (HARD RULE 6).
  - Verified 16/16 pytest unit tests pass across Phases 1-4.

## Phase 4: Pipeline 1 (GenAI Triage, Pydantic Schema, Prompt Versioning & Retries)
- **Timestamp**: 2026-09-26
- **Assisted Components**:
  - Prompt template loading and versioning module (`prompt_templates/prompt_loader.py`).
  - Standard prompt template with XML-style untrusted text delimiters (`prompt_templates/v1.0_triage_prompt.txt`).
  - Groq API client wrapper with json_schema mode, exponential backoff retries, and batch delay setting (`genai_pipeline/client.py`).
  - Pipeline 1 execution function with Pydantic schema validation and DB results persistence (`genai_pipeline/pipeline1.py`).
  - Pytest suite verifying prompt versioning, Pydantic validation, and API failure routing to Manual Review without fake AI outputs (`tests/test_phase4.py`).
- **Human Verification**:
  - Verified no fake AI responses on API failure (HARD RULE 9).
  - Verified model, provider, prompt_version, and policy_versions database logging.
  - Verified 21/21 pytest unit tests pass across Phases 1-5.

## Phase 5: Pipeline 2 (Deterministic Python Validation, Zero AI Calls & Hallucination Checks)
- **Timestamp**: 2026-09-26
- **Assisted Components**:
  - Independent Python rule checker and mandatory escalation trigger override module (`python_validation/rule_checker.py`).
  - Policy document Active status, date validity, and section checker (`python_validation/policy_checker.py`).
  - Unsupported promise ("guaranteed refund") and hallucinated fact detector (`hallucination_checks/hallucination_detector.py`).
  - Pipeline 2 execution coordinator saving python_result to DB (`python_validation/pipeline2.py`).
  - Pytest test suite verifying zero-AI execution, mandatory escalation overrides, refund cap breaches, unsupported promises, and policy validity checks (`tests/test_phase5.py`).
- **Human Verification**:
  - Verified zero AI calls in Pipeline 2.
  - Verified mandatory escalation overrides when GenAI misses an escalation trigger.
  - Verified 24/24 pytest unit tests pass across Phases 1-6.

## Phase 6: Comparison Engine, Manual Review Queue & Audit Trail
- **Timestamp**: 2026-09-26
- **Assisted Components**:
  - Comparison engine module calculating real deterministic verification scores and routing to Verified or Manual Review (`comparison_engine/comparator.py`).
  - Agent workspace updated with dual-pipeline triage trigger button and side-by-side comparison UI (`pages/4_Agent_Workspace.py`).
  - Manual Review queue updated with reviewer actions (Approve, Reject, Modify, Reclassify, Reassign, Escalate, Regenerate) and audit trail tracking (`pages/5_Manual_Review.py`).
  - Pytest test suite verifying Verified vs Manual Review routing, verification score calculation, and review decision audit trail logging (`tests/test_phase6.py`).
- **Human Verification**:
  - Verified real deterministic verification scores (HARD RULE 9, no fake scores).
  - Verified original AI proposal and final staff decision stored in `reviews` table and `complaint_history` table.
  - Verified 27/27 pytest unit tests pass across Phases 1-7.

## Phase 7: Analytics Dashboards, SLA Risk Monitoring, Search/Filter & CSV Export
- **Timestamp**: 2026-09-26
- **Assisted Components**:
  - Multi-criteria complaint search and filtering module (`reports/search_filter.py`).
  - Report generator for system summary metrics, SLA breach risk calculation, and CSV file formatting (`reports/report_generator.py`).
  - Updated Admin Console dashboard with real-time charts, SLA risk monitoring, search/filter controls, and CSV export buttons (`pages/6_Admin.py`).
  - Pytest test suite verifying multi-criteria search, SLA risk threshold calculations, and CSV report exports (`tests/test_phase7.py`).
- **Human Verification**:
  - Verified SLA breach risk monitoring thresholds (Urgent 2h, High 6h, Medium 24h, Low 48h).
  - Verified CSV export generation and filtering engine.
  - Verified 29/29 pytest unit tests pass across all Phases 1-8.

## Phase 8: Batch Dataset Execution, Performance Comparison Report & Deployment Setup Documentation
- **Timestamp**: 2026-09-26
- **Assisted Components**:
  - Batch dataset evaluation runner module (`reports/batch_runner.py`).
  - System performance comparison markdown report (`reports/comparison_report.md`).
  - Complete README.md documentation with system architecture, local setup, secrets configuration, and Streamlit Community Cloud deployment guide (`README.md`).
  - Pytest test suite verifying batch dataset processing, markdown report generation, and system documentation (`tests/test_phase8.py`).
- **Human Verification**:
  - Verified 500-complaint batch dataset evaluation workflow.
  - Verified Streamlit Cloud deployment steps with `GROQ_API_KEY` secrets configuration and automatic SQLite seeding (`run_seed_if_needed()`).
  - Verified all 29/29 pytest unit tests pass across all Phases 1-8.







