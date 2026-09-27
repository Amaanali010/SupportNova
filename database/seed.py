# database/seed.py
# Database seeding script for SupportNova.
# Populates default users, 10 real policy documents, 114 real rule matrix rows, and 500 sample complaints
# so the application works out-of-the-box on Streamlit Community Cloud.

import os
import csv
import re
from typing import List, Dict, Any
from database.db import init_db, execute_query, execute_statement
from security.auth import hash_password
from document_processing.parser import parse_document
from document_processing.chunker import create_document_chunks

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def seed_demo_users() -> int:
    """
    Creates default demo users for each RBAC role if users table is empty.
    """
    rows = execute_query("SELECT COUNT(*) as count FROM users")
    if rows and rows[0]['count'] > 0:
        return 0

    demo_users = [
        ("admin1", "admin123", "admin", "System Administrator", "admin@voltkart.com"),
        ("manager1", "manager123", "manager", "Senior Support Manager", "manager@voltkart.com"),
        ("reviewer1", "reviewer123", "reviewer", "Compliance Reviewer", "reviewer@voltkart.com"),
        ("agent1", "agent123", "agent", "Tier 1 Support Agent", "agent@voltkart.com"),
        ("customer1", "customer123", "customer", "Demo Customer", "customer1@gmail.com")
    ]

    count = 0
    for username, password, role, name, email in demo_users:
        pass_hash = hash_password(password)
        execute_statement(
            "INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, ?, ?, ?)",
            (username, pass_hash, role, name, email)
        )
        count += 1
    return count

def seed_rule_matrix() -> int:
    """
    Loads resolution rules from complaint_rules/resolution_rules.csv into rules table.
    Matches real 114-row rule matrix schema.
    """
    rows = execute_query("SELECT COUNT(*) as count FROM rules")
    if rows and rows[0]['count'] > 0:
        return 0

    csv_path = os.path.join(BASE_DIR, "complaint_rules", "resolution_rules.csv")
    if not os.path.exists(csv_path):
        return 0

    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            execute_statement(
                """
                INSERT INTO rules (
                    rule_id, category, subcategory, case_variant, conditions,
                    department, urgency, priority, policy_reference, escalation_level,
                    required_actions, prohibited_actions, follow_up_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get('Rule ID', '').strip() or f'RM-{count+1:03d}',
                    row.get('Category', '').strip(),
                    row.get('Subcategory', '').strip(),
                    row.get('Case Variant', '').strip(),
                    row.get('Conditions', '').strip(),
                    row.get('Department', '').strip(),
                    row.get('Urgency', '').strip(),
                    row.get('Priority', '').strip(),
                    row.get('Policy Reference', '').strip(),
                    row.get('Escalation', '').strip(),
                    row.get('Required Actions', '').strip(),
                    row.get('Prohibited Actions', '').strip(),
                    row.get('Follow-Up', '').strip()
                )
            )
            count += 1
    return count

def seed_documents_and_chunks() -> int:
    """
    Loads real 10 policy documents metadata and text chunks into documents and chunks tables.
    """
    rows = execute_query("SELECT COUNT(*) as count FROM documents")
    if rows and rows[0]['count'] > 0:
        return 0

    meta_csv = os.path.join(BASE_DIR, "sample_documents", "policies_metadata.csv")
    if not os.path.exists(meta_csv):
        return 0

    doc_count = 0
    with open(meta_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get('doc_id', '').strip() or f'DOC-{doc_count+1:03d}'
            file_path = row.get('file_path', '').strip()
            version = row.get('version', 'v1.0').strip()
            status = row.get('status', 'Active').strip()

            execute_statement(
                """
                INSERT INTO documents (
                    doc_id, title, category, version, status, effective_date, expiry_date, owner, supersedes, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    row.get('title', '').strip(),
                    row.get('category', '').strip(),
                    version,
                    status,
                    row.get('effective_date', '').strip(),
                    row.get('expiry_date', '').strip(),
                    row.get('owner', '').strip(),
                    row.get('supersedes', '').strip(),
                    file_path
                )
            )
            doc_count += 1

            # Parse document into structured sections and chunks using parser.py
            if file_path:
                abs_path = os.path.join(BASE_DIR, file_path) if not os.path.isabs(file_path) else file_path
                if os.path.exists(abs_path):
                    try:
                        parsed_sections = parse_document(abs_path)
                        chunks = create_document_chunks(doc_id, version, status, parsed_sections)
                        for chk in chunks:
                            execute_statement(
                                """
                                INSERT INTO chunks (chunk_id, doc_id, section, heading, page, text, version, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    chk['chunk_id'], chk['doc_id'], chk['section'], chk['heading'],
                                    chk['page'], chk['text'], chk['version'], chk['status']
                                )
                            )
                    except BaseException as e:
                        print(f"Warning: Failed to parse document {doc_id} at {abs_path}: {e}")

    return doc_count

def seed_sample_complaints() -> int:
    """
    Loads real 500-complaints dataset into complaints table.
    """
    rows = execute_query("SELECT COUNT(*) as count FROM complaints")
    if rows and rows[0]['count'] > 0:
        return 0

    csv_path = os.path.join(BASE_DIR, "sample_complaints", "complaints_500.csv")
    if not os.path.exists(csv_path):
        return 0

    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get('id', '').strip() or f'CMP-{count+1:04d}'
            desc = row.get('description', '').strip()
            title = row.get('title', '').strip()
            cust_type = row.get('customer_type', '').strip()
            product = row.get('product', '').strip()
            order_ref = row.get('order_ref', '').strip()
            channel = row.get('channel', 'Web').strip()
            date_str = row.get('date', '').strip()
            special_case = row.get('special_case', '').strip()
            dup_group = row.get('duplicate_group', '').strip()
            exp_cat = row.get('exp_category', '').strip()
            exp_sub = row.get('exp_subcategory', '').strip()
            exp_dept = row.get('exp_department', '').strip()
            exp_urg = row.get('exp_urgency', '').strip()
            exp_prio = row.get('exp_priority', '').strip()
            exp_esc = row.get('exp_escalation', '').strip()
            notes = row.get('notes', '').strip()

            execute_statement(
                """
                INSERT INTO complaints (
                    complaint_id, title, customer_id, customer_type, product, order_ref,
                    complaint_text, channel, status, category, subcategory, priority, urgency,
                    special_case, duplicate_group, exp_category, exp_subcategory, exp_department,
                    exp_urgency, exp_priority, exp_escalation, notes, is_repeat, is_duplicate, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid, title, order_ref or cust_type or "CUST-001", cust_type, product, order_ref,
                    desc, channel, "Submitted", exp_cat, exp_sub, exp_prio, exp_urg,
                    special_case, dup_group, exp_cat, exp_sub, exp_dept,
                    exp_urg, exp_prio, exp_esc, notes, 0, 0, date_str
                )
            )
            count += 1
    return count

def run_seed_if_needed() -> None:
    """
    Checks database health and seeds missing tables. Safe to call on every app start.
    """
    init_db()
    users_seeded = seed_demo_users()
    rules_seeded = seed_rule_matrix()
    docs_seeded = seed_documents_and_chunks()
    complaints_seeded = seed_sample_complaints()

    if any([users_seeded, rules_seeded, docs_seeded, complaints_seeded]):
        execute_statement(
            "INSERT INTO audit_log (user_id, action, target_type, details) VALUES (?, ?, ?, ?)",
            ("SYSTEM", "SEED_DATABASE", "SYSTEM_INIT", f"Seeded users:{users_seeded}, rules:{rules_seeded}, docs:{docs_seeded}, complaints:{complaints_seeded}")
        )

if __name__ == "__main__":
    run_seed_if_needed()
    print("Database seeding completed successfully.")
