# document_processing/chunker.py
# Module for splitting parsed policy document sections into chunk records for RAG index.

from typing import List, Dict, Any

def create_document_chunks(doc_id: str, version: str, status: str, parsed_sections: List[Dict[str, Any]], max_chunk_words: int = 200) -> List[Dict[str, Any]]:
    """
    Takes parsed document sections and splits them into searchable chunk records.
    Preserves section numbers, headings, page numbers, doc ID, version, and status.
    """
    chunk_records = []
    chunk_index = 1

    for sec in parsed_sections:
        section_num = sec.get("section", "1.0")
        heading = sec.get("heading", "General")
        page_num = sec.get("page", 1)
        full_text = sec.get("text", "")

        words = full_text.split()
        if len(words) <= max_chunk_words:
            # Short section fits in a single chunk
            chunk_records.append({
                "chunk_id": f"{doc_id}-CHK-{chunk_index:02d}",
                "doc_id": doc_id,
                "section": section_num,
                "heading": heading,
                "page": page_num,
                "text": full_text,
                "version": version,
                "status": status
            })
            chunk_index += 1
        else:
            # Long section split into sub-chunks of max_chunk_words
            for i in range(0, len(words), max_chunk_words):
                chunk_words = words[i:i + max_chunk_words]
                chunk_text = " ".join(chunk_words)
                chunk_records.append({
                    "chunk_id": f"{doc_id}-CHK-{chunk_index:02d}",
                    "doc_id": doc_id,
                    "section": section_num,
                    "heading": f"{heading} (Part {i//max_chunk_words + 1})",
                    "page": page_num,
                    "text": chunk_text,
                    "version": version,
                    "status": status
                })
                chunk_index += 1

    return chunk_records
