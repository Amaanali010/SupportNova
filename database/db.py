# database/db.py
# SQLite Database connection and schema initialization helper for SupportNova.
# Provides helper functions to connect, execute queries, and initialize tables.

import os
import sqlite3
from typing import List, Dict, Any, Optional
from config.config import get_setting

# Get absolute path to the database file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_db_path() -> str:
    """
    Returns the absolute path to the SQLite database file.
    Ensures the parent directory exists.
    """
    relative_path = get_setting("app.db_path", "database/supportnova.db")
    db_path = os.path.join(BASE_DIR, relative_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path

_db_initialized = False

def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a SQLite database connection with row factory enabled
    so query results can be accessed as dictionary-like objects.
    Ensures database schema and seed data exist before returning connection.
    """
    global _db_initialized
    db_path = get_db_path()
    if not _db_initialized or not os.path.exists(db_path):
        _db_initialized = True
        try:
            from database.seed import run_seed_if_needed
            run_seed_if_needed()
        except Exception:
            pass
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable Foreign Keys enforcement in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def execute_query(sql: str, params: tuple = ()) -> List[sqlite3.Row]:
    """
    Executes a SELECT SQL query and returns all matching rows.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

def execute_statement(sql: str, params: tuple = ()) -> int:
    """
    Executes an INSERT, UPDATE, or DELETE statement and commits changes.
    Returns the last inserted row ID or affected row count.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid

def init_db() -> None:
    """
    Creates all SQLite tables required by SupportNova if they do not already exist.
    Updated for real Rule Matrix and 500-complaints dataset schemas.
    """
    schema_statements = [
        # Table 1: Users
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,

        # Table 2: Documents
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT,
            version TEXT NOT NULL,
            status TEXT NOT NULL,
            effective_date TEXT,
            expiry_date TEXT,
            owner TEXT,
            supersedes TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,

        # Table 3: Chunks
        """
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            section TEXT,
            heading TEXT,
            page INTEGER,
            text TEXT NOT NULL,
            version TEXT,
            status TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents (doc_id) ON DELETE CASCADE
        );
        """,

        # Table 4: Rules (Matching real 114-row Complaint Resolution Rule Matrix CSV)
        """
        CREATE TABLE IF NOT EXISTS rules (
            rule_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            case_variant TEXT,
            conditions TEXT,
            department TEXT,
            urgency TEXT,
            priority TEXT,
            policy_reference TEXT,
            escalation_level TEXT,
            required_actions TEXT,
            prohibited_actions TEXT,
            follow_up_required TEXT
        );
        """,

        # Table 5: Complaints (Matching real 500-complaints dataset CSV)
        """
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id TEXT PRIMARY KEY,
            title TEXT,
            customer_id TEXT,
            customer_type TEXT,
            product TEXT,
            order_ref TEXT,
            complaint_text TEXT NOT NULL,
            channel TEXT DEFAULT 'Web',
            status TEXT DEFAULT 'Submitted',
            category TEXT,
            subcategory TEXT,
            priority TEXT,
            urgency TEXT,
            special_case TEXT,
            duplicate_group TEXT,
            duplicate_of TEXT,
            exp_category TEXT,
            exp_subcategory TEXT,
            exp_department TEXT,
            exp_urgency TEXT,
            exp_priority TEXT,
            exp_escalation TEXT,
            notes TEXT,
            is_repeat INTEGER DEFAULT 0,
            is_duplicate INTEGER DEFAULT 0,
            created_at TEXT
        );
        """,

        # Table 6: Analysis Results
        """
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            genai_json TEXT,
            python_result TEXT,
            verification_status TEXT NOT NULL,
            prompt_version TEXT,
            model TEXT,
            provider TEXT,
            policy_versions TEXT,
            mismatches TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints (complaint_id) ON DELETE CASCADE
        );
        """,

        # Table 7: Reviews
        """
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            reviewer_id TEXT NOT NULL,
            original_decision TEXT,
            final_decision TEXT,
            status TEXT NOT NULL,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints (complaint_id) ON DELETE CASCADE
        );
        """,

        # Table 8: Audit Log
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id TEXT,
            details TEXT
        );
        """,

        # Table 9: Complaint History
        """
        CREATE TABLE IF NOT EXISTS complaint_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            changed_by TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            notes TEXT,
            FOREIGN KEY (complaint_id) REFERENCES complaints (complaint_id) ON DELETE CASCADE
        );
        """
    ]

    with get_connection() as conn:
        cursor = conn.cursor()
        for statement in schema_statements:
            cursor.execute(statement)
        try:
            cursor.execute("ALTER TABLE complaints ADD COLUMN duplicate_of TEXT;")
        except sqlite3.OperationalError:
            pass
        conn.commit()
