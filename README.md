# SupportNova - Customer-Complaint Triage Platform for VoltKart

SupportNova is an enterprise-grade, dual-pipeline customer complaint triage and verification engine built for **VoltKart**. It combines GenAI structured interpretation (Pipeline 1) with deterministic Python rule matrix validation (Pipeline 2) and an automated comparison engine to eliminate hallucinations, enforce policy compliance, and catch missed mandatory escalations.

---

## 🚀 A-to-Z Step-by-Step Setup & Running Guide

### 1. Prerequisites
- **Python**: Python 3.10, 3.11, 3.12, or 3.13 installed on your system.
- **Git** (optional): For version control.
- **Groq API Key**: Obtain a free API key from [Groq Console](https://console.groq.com/keys).

---

### 2. Install Dependencies
Open your terminal or command prompt in the project root directory (`SupportNova`) and install the required Python packages:

```bash
pip install -r requirements.txt
```

---

### 3. Configure API Key (`GROQ_API_KEY`)

You can configure your Groq API key using **Option A** (recommended for local Streamlit development) or **Option B** (environment variable).

#### 🔹 Option A: Create `.streamlit/secrets.toml` (Recommended)
1. In the root directory of the project, create a directory named `.streamlit` (if it does not exist).
2. Inside `.streamlit`, create a file named `secrets.toml`.
3. Add your Groq API key to `secrets.toml`:

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "gsk_your_actual_groq_api_key_here"
```

> **Note**: The `.streamlit/secrets.toml` file is automatically ignored by git to keep your key secure.

#### 🔹 Option B: Set Environment Variable
- **Windows (PowerShell)**:
  ```powershell
  $env:GROQ_API_KEY="gsk_your_actual_groq_api_key_here"
  ```
- **Windows (CMD)**:
  ```cmd
  set GROQ_API_KEY=gsk_your_actual_groq_api_key_here
  ```
- **Linux / macOS (Bash / Zsh)**:
  ```bash
  export GROQ_API_KEY="gsk_your_actual_groq_api_key_here"
  ```

---

### 4. Seed / Reseed the Database

The project uses SQLite (`database/supportnova.db`). The app automatically initializes and seeds the database on first run. If you ever want to reset and reseed the database from scratch:

```bash
# Delete existing database file if present
python -c "import os; os.remove('database/supportnova.db') if os.path.exists('database/supportnova.db') else None"

# Seed all 10 policy documents, 114 resolution rules, and 500 sample complaints
python database/seed.py
```

---

### 5. Run the Full Test Suite

Verify that all components and unit tests are passing:

```bash
python -m pytest tests/ -v
```

All 29 tests should pass (`29 passed in ...`).

---

### 6. Launch the Streamlit Web Application

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

Once launched, open your web browser and navigate to:
```text
http://localhost:8501
```

---

### 7. Run Batch Dataset Evaluation (500 Complaints)

To execute the batch processing runner across all 500 dataset complaints and generate the performance comparison report:

```bash
python reports/batch_runner.py
```

The output report will be generated at [reports/comparison_report.md](file:///C:/Users/student/.gemini/antigravity/scratch/SupportNova/reports/comparison_report.md).

---

## 👥 Demo Login Credentials

You can log into the Streamlit web app using any of the pre-configured role-based test accounts:

| Role | Username | Password | Access & Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin1` | `admin123` | System metrics, SLA risk monitoring, rule matrix viewer, document library, search & CSV export |
| **Manager** | `manager1` | `manager123` | Support team telemetry, review queue metrics, SLA breach tracking |
| **Reviewer** | `reviewer1` | `reviewer123` | Manual Review Queue (Approve, Reject, Modify, Reclassify, Reassign, Escalate, Audit Trail) |
| **Agent** | `agent1` | `agent123` | Agent Workspace, dual-pipeline triage trigger, AI vs Python comparison cards |
| **Customer** | `customer1` | `customer123` | Customer submission form (PII masking & injection check) and ticket status tracker |

---

## 🏗️ Architecture & Dual-Pipeline Workflow

```text
                   [ Customer Complaint Input ]
                                |
               +----------------+----------------+
               |  Sanitization & Injection Check |
               +----------------+----------------+
                                |
                   [ TF-IDF Policy RAG Retrieval ]
                                |
        +-----------------------+-----------------------+
        |                                               |
  [ Pipeline 1 (GenAI Triage) ]             [ Pipeline 2 (Python Matrix) ]
  - Groq JSON Schema Mode                   - Zero AI Calls
  - Pydantic 24-Field Schema                - Rule Matrix Validation (114 Rules)
  - Empathetic Response Draft               - Mandatory Escalation Lookup
  - Policy Section Extraction               - Action Phrase Checking
        |                                               |
        +-----------------------+-----------------------+
                                |
                    [ Comparison Engine ]
                    - Category / Dept Match
                    - Real Verification Score
                    - Disagreement Routing
                                |
               +----------------+----------------+
               |                                 |
       [ Verified Status ]             [ Manual Review Queue ]
       Auto-approved resolution        Auditor approval/override
```

---

## 🔑 Key Features & Hard Rules Compliance

- **Hard Rule 1 (Externalized Rules)**: All business rules, categories, departments, and escalation triggers live in `complaint_rules/resolution_rules.csv` and `config/settings.yaml`, never in Python code.
- **Hard Rule 2 & 4 (No AI Self-Approval)**: GenAI interprets text, but Python strictly validates priority/urgency and enforces mandatory escalations regardless of AI output.
- **Hard Rule 5 (Policy Precedence & Date Range)**: Only **Active** policies inside their effective and expiry dates serve as primary resolution basis. Precedence order: `Legal > Escalation SOP > Active Policy > Active SOP > Template > FAQ`.
- **Hard Rule 6 (Security & Prompt Injection)**: Untrusted user text is wrapped in `<<<UNTRUSTED_USER_INPUT_START>>>`. Prompt injection attempts (`"ignore your rules"`, `"approve my refund"`) route directly to Manual Review.
- **Hard Rule 7 (PII Masking)**: Automatically masks credit card numbers, passwords, and national IDs in prompts and logs.
- **Hard Rule 8 (Prompt Versioning)**: Prompts live only in `prompt_templates/` with version tags (`v1.0`), stored with every analysis.
- **Hard Rule 9 (No Fake Scores)**: Verification scores are computed strictly from empirical matching checks. If API calls fail, complaints route to Manual Review without fake AI outputs.

---

## 📁 Repository Directory Structure

```text
SupportNova/
├── app.py                      # Main Streamlit Entry Point & Navigation
├── config/
│   ├── config.py               # YAML configuration loader
│   └── settings.yaml           # App configuration settings
├── database/
│   ├── db.py                   # SQLite connection & schema creation
│   ├── models.py               # Dataclass schemas (ComplaintRecord, RuleRecord, etc.)
│   ├── seed.py                 # Reseeding logic for docs, rules, and complaints
│   └── supportnova.db          # SQLite database (auto-generated)
├── document_processing/
│   └── parser.py               # Document parser for .docx and .pdf files
├── complaint_processing/
│   ├── rule_loader.py          # Rule matrix loader & Category/Subcategory lookup
│   └── validator.py            # Sanitization, PII masking & injection check
├── complaint_rules/
│   └── resolution_rules.csv    # Real 114-row Complaint Resolution Rule Matrix
├── genai_pipeline/
│   ├── client.py               # Groq API client with JSON Schema mode & retries
│   └── pipeline1.py            # Pipeline 1 GenAI triage runner
├── knowledge_base/
│   └── document_manager.py     # Document metadata manager & TF-IDF RAG retriever
├── pages/
│   ├── 1_Login.py              # User authentication page
│   ├── 2_Submit_Complaint.py   # Customer complaint submission portal
│   ├── 3_Agent_Workspace.py    # Agent triage workspace
│   ├── 4_Review_Queue.py       # Auditor/Reviewer manual review queue
│   ├── 5_Manager_Dashboard.py  # Telemetry & SLA dashboard
│   ├── 6_Admin_Console.py      # System administration & search/export
│   └── 7_Documentation.py      # Architecture documentation viewer
├── prompt_templates/
│   └── v1.0_triage_prompt.txt  # Versioned GenAI system prompt template
├── python_validation/
│   ├── pipeline2.py            # Pipeline 2 validation runner
│   └── rule_checker.py         # Deterministic rule matrix matching & checks
├── comparison_engine/
│   └── comparator.py           # Dual-pipeline verification & agreement scoring
├── reports/
│   ├── batch_runner.py         # 500-complaint batch dataset evaluator
│   └── comparison_report.md    # Summary performance comparison report
├── sample_complaints/
│   └── complaints_500.csv      # Real 500-complaint dataset
├── sample_documents/           # 10 real policy documents (.docx & .pdf)
├── tests/                      # Pytest suite (Phase 1 through Phase 8)
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation & guide
```

---

## 🌐 Streamlit Community Cloud Deployment Guide

1. **Push Repository to GitHub**: Ensure all code, `complaint_rules/`, `sample_documents/`, and `sample_complaints/` are committed.
2. **Set Streamlit Secrets**: On Streamlit Cloud dashboard, navigate to **Settings -> Secrets** and add:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
3. **Automatic Reseeding**: On app startup, `run_seed_if_needed()` populates SQLite in memory/ephemeral disk automatically.
