# tests/test_phase2.py
# Comprehensive Pytest test suite for SupportNova Phase 2.
# Validates document validation, parsing, chunking, status date evaluation, precedence ranking, and TF-IDF RAG retrieval.

import os
import pytest
from document_processing.validator import validate_file_extension, validate_metadata, evaluate_document_validity
from document_processing.parser import parse_txt_file, parse_document
from document_processing.chunker import create_document_chunks
from knowledge_base.tfidf_retriever import compute_precedence_score, TFIDFRetriever
from knowledge_base.document_manager import DocumentManager
from database.seed import run_seed_if_needed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_file_extension_and_metadata_validation():
    """Test validating file extensions and metadata dictionaries."""
    assert validate_file_extension("policy.pdf") is True
    assert validate_file_extension("guide.docx") is True
    assert validate_file_extension("notes.txt") is True
    assert validate_file_extension("script.exe") is False

    valid_meta = {
        "doc_id": "DOC-001",
        "title": "Refund Policy",
        "version": "v1.0",
        "status": "Active",
        "effective_date": "2024-01-01",
        "expiry_date": "2026-12-31"
    }
    is_valid, missing = validate_metadata(valid_meta)
    assert is_valid is True
    assert len(missing) == 0

    invalid_meta = {"doc_id": "DOC-001"}
    is_valid_inv, missing_inv = validate_metadata(invalid_meta)
    assert is_valid_inv is False
    assert "title" in missing_inv

def test_document_validity_and_date_enforcement():
    """Test Hard Rule 5: Active vs Superseded/Draft document evaluation."""
    active_eval = evaluate_document_validity("Active", "2024-01-01", "2026-12-31", reference_date_str="2025-06-01")
    assert active_eval["is_primary_valid"] is True
    assert active_eval["flag"] is None

    superseded_eval = evaluate_document_validity("Superseded", "2020-01-01", "2023-12-31", reference_date_str="2025-06-01")
    assert superseded_eval["is_primary_valid"] is False
    assert "Non-Active Status" in superseded_eval["flag"]

    expired_eval = evaluate_document_validity("Active", "2020-01-01", "2022-12-31", reference_date_str="2025-06-01")
    assert expired_eval["is_primary_valid"] is False
    assert "Invalid Date Range" in expired_eval["flag"]

def test_document_parsing_and_chunking():
    """Test parsing real DOCX document and creating text chunks."""
    doc_path = os.path.join(BASE_DIR, "sample_documents", "REF-POL-01_Refund_Policy.docx")
    sections = parse_document(doc_path)
    assert len(sections) > 0
    assert "section" in sections[0]
    assert "heading" in sections[0]

    chunks = create_document_chunks("REF-POL-01", "v2.0", "Active", sections)
    assert len(chunks) > 0
    assert chunks[0]["chunk_id"].startswith("REF-POL-01-CHK")

def test_precedence_scoring():
    """Test document precedence hierarchy ranks (Legal > Escalation SOP > Policy > Active SOP > Template > FAQ)."""
    assert compute_precedence_score("Legal & Compliance", "Legal Refund Terms") == 60
    assert compute_precedence_score("Operations", "Escalation SOP") == 50
    assert compute_precedence_score("Support", "Active SOP Guide") == 30
    assert compute_precedence_score("General", "Customer Policy") == 40

def test_tfidf_retrieval_and_rag():
    """Test TF-IDF indexing and top-K query retrieval with precedence ranking."""
    run_seed_if_needed()
    doc_mgr = DocumentManager()
    
    # Query for refund policy
    query = "unauthorized charge credit card refund limit"
    retrieved = doc_mgr.retrieve_chunks(query, top_k=3)
    assert len(retrieved) > 0
    top_match = retrieved[0]
    assert "refund" in top_match["text"].lower() or "charge" in top_match["text"].lower()
    assert "similarity_score" in top_match
    assert top_match["similarity_score"] > 0
