# SupportNova - User Flow & System Architecture Diagrams

This document illustrates the role-based user workflows, capabilities, and dual-pipeline execution architecture for **SupportNova**.

---

## 👥 1. Role-Based User Responsibilities & Capabilities

```mermaid
mindmap
  root((SupportNova Platform))
    Customer
      Submit Complaint
      PII Masking & Injection Check
      Missing Information Check
      Track Complaint Status
    Support Agent
      Inspect Complaint Queue
      Trigger Dual-Pipeline Triage
      View Side-by-Side Comparison
      Send Customer Reply
      Mark Verified as Resolved
    Compliance Reviewer
      Audit Manual Review Queue
      Inspect Disagreements & Mismatches
      Override Category & Escalation
      Commit Audit Trail Records
    Support Manager
      Monitor SLA Breach Risks
      View Team Telemetry & Queue Stats
      Track Agreement Rates
      Review Operational Metrics
    System Admin
      Manage Rule Matrix Rules
      Ingest Policy Documents
      Search & Filter Dataset
      Export CSV System Reports
```

---

## 🔄 2. End-to-End User Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Customer as 👤 Customer
    actor Agent as 🎧 Support Agent
    actor Reviewer as ⚖️ Reviewer
    actor Manager as 📊 Manager / Admin
    participant System as 🚀 SupportNova System
    participant DB as 💾 SQLite Database

    %% Customer Submission
    Customer->>System: 1. Submit Complaint (Title, Type, Product, Order Ref, Text)
    System->>System: 2. Validate, Mask PII & Check Prompt Injection / Missing Info
    System->>DB: 3. Store Complaint (Status: Submitted / Awaiting_Customer / Manual_Review)
    System-->>Customer: 4. Display Submission Confirmation & Ticket ID

    %% Agent Workspace Triage
    Agent->>System: 5. Select Complaint from Queue & Click "Run Dual-Pipeline Triage"
    System->>System: 6. Execute Pipeline 1 (GenAI Triage) & Pipeline 2 (Python Matrix)
    System->>System: 7. Run Comparison Engine & Compute Verification Score
    System->>DB: 8. Update Complaints (Status: Verified / Manual_Review, Category, Urgency)
    System-->>Agent: 9. Display Side-by-Side AI vs Python Comparison

    alt Status is Verified
        Agent->>System: 10. Click "Confirm Reply Sent & Mark Resolved"
        System->>DB: 11. Update Status to Resolved & Log Audit Record
    else Status is Manual_Review
        %% Reviewer Override
        Reviewer->>System: 12. Open Manual Review Queue
        Reviewer->>System: 13. Audit Disagreements & Select Action (Approve / Modify / Escalate)
        System->>DB: 14. Commit Final Decision to Reviews & Audit Trail
    end

    %% Reporting & Telemetry
    Manager->>System: 15. Inspect Manager Dashboard & SLA Risk Telemetry
    System->>DB: 16. Query Metrics, Agreement Rates & Resolution Reports
    System-->>Manager: 17. Render Real-time Dashboard Analytics
```

---

## 🛡️ 3. Dual-Pipeline Triage & Verification Architecture

```mermaid
flowchart TD
    A[Customer Complaint Submitted] --> B{Sanitization & Injection Guardrails}
    B -->|Prompt Injection Detected| C[Route to Manual Review Queue]
    B -->|Clean Input| D[TF-IDF Policy RAG Context Retrieval]

    D --> E[Pipeline 1: GenAI Structured Triage]
    D --> F[Pipeline 2: Independent Python Matrix]

    E -->|JSON Schema Extraction| G[GenAI Result: Category, Urgency, Escalation, Reply]
    F -->|114-Row Business Rules| H[Python Result: Validated Rules, Caps, Mandatory Escalation]

    G --> I[Comparison Engine]
    H --> I

    I --> J{Check Field Agreement & Compliance}
    J -->|Score = 1.0 & No Violations| K[Status: VERIFIED]
    J -->|Disagreement or Missed Escalation| L[Status: MANUAL REVIEW]

    K --> M[Agent Workspace: One-Click Resolution]
    L --> N[Reviewer Queue: Staff Override & Audit Trail]

    M --> O[(SQLite Database Update)]
    N --> O
```
