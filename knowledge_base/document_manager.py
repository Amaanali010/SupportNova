# knowledge_base/document_manager.py
# High-level coordinator for ingesting, indexing, and querying policy documents.

import os
from typing import List, Dict, Any, Tuple
from database.db import execute_query, execute_statement
from document_processing.validator import validate_file_extension, validate_metadata, evaluate_document_validity
from document_processing.parser import parse_document
from document_processing.chunker import create_document_chunks
from knowledge_base.tfidf_retriever import TFIDFRetriever

class DocumentManager:
    """
    Manages policy document ingestion, database synchronization, and TF-IDF RAG retrieval.
    """
    def __init__(self):
        self.retriever = TFIDFRetriever()
        self.reload_index_from_db()

    def reload_index_from_db(self) -> None:
        """
        Loads all chunks and document metadata from SQLite and rebuilds the TF-IDF index.
        Defensive against missing tables or database errors.
        """
        try:
            chunks_rows = execute_query("SELECT * FROM chunks")
            docs_rows = execute_query("SELECT * FROM documents")
            chunks = [dict(r) for r in chunks_rows]
            docs = [dict(r) for r in docs_rows]
        except Exception:
            chunks = []
            docs = []

        self.retriever.build_index(chunks, docs)

    def ingest_document(self, file_path: str, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Ingests a new policy document (PDF/DOCX/TXT), parses, chunks, saves to SQLite DB, and updates RAG index.
        """
        # Step 1: Validate file extension
        filename = os.path.basename(file_path)
        if not validate_file_extension(filename):
            return False, f"Unsupported file extension: {filename}"

        # Step 2: Validate metadata
        valid_meta, missing = validate_metadata(metadata)
        if not valid_meta:
            return False, f"Missing required metadata fields: {', '.join(missing)}"

        doc_id = metadata["doc_id"]
        version = metadata["version"]
        status = metadata["status"]

        # Step 3: Parse document sections
        try:
            sections = parse_document(file_path)
        except Exception as e:
            return False, f"Error parsing document: {str(e)}"

        # Step 4: Split sections into chunks
        chunks = create_document_chunks(doc_id, version, status, sections)

        # Step 5: Save to Database
        execute_statement("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        execute_statement("DELETE FROM documents WHERE doc_id = ?", (doc_id,))

        execute_statement(
            """
            INSERT INTO documents (doc_id, title, category, version, status, effective_date, expiry_date, owner, supersedes, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                metadata.get("title", ""),
                metadata.get("category", ""),
                version,
                status,
                metadata.get("effective_date", ""),
                metadata.get("expiry_date", ""),
                metadata.get("owner", ""),
                metadata.get("supersedes", ""),
                file_path
            )
        )

        for chk in chunks:
            execute_statement(
                """
                INSERT INTO chunks (chunk_id, doc_id, section, heading, page, text, version, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chk["chunk_id"], chk["doc_id"], chk["section"], chk["heading"],
                    chk["page"], chk["text"], chk["version"], chk["status"]
                )
            )

        # Step 6: Reload TF-IDF Index
        self.reload_index_from_db()
        return True, f"Successfully ingested document {doc_id} with {len(chunks)} chunks."

    def retrieve_chunks(self, complaint_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top-K policy context chunks for a complaint query using TF-IDF and precedence ranking.
        """
        return self.retriever.retrieve_top_k(complaint_text, top_k=top_k)

# Global singleton instance for easy module import
DOCUMENT_MANAGER = DocumentManager()
