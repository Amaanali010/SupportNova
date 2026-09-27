# complaint_processing/duplicate_detector.py
# Module for detecting exact or semantic duplicate complaints and repeat customer submission history.

from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database.db import execute_query

def check_repeat_customer(customer_id: str) -> Tuple[bool, int]:
    """
    Checks if the customer has submitted complaints previously.
    Returns (is_repeat: bool, prior_complaint_count: int).
    """
    if not customer_id:
        return False, 0

    rows = execute_query(
        "SELECT COUNT(*) as count FROM complaints WHERE customer_id = ?",
        (customer_id.strip(),)
    )
    count = rows[0]["count"] if rows else 0
    return count > 0, count

def check_duplicate_complaint(new_complaint_text: str, similarity_threshold: float = 0.85) -> Tuple[bool, str, float]:
    """
    Checks if the new complaint text is a duplicate of any existing complaint in SQLite database.
    Uses TF-IDF vector cosine similarity comparison.
    Returns (is_duplicate: bool, matched_complaint_id: str, similarity_score: float).
    """
    if not new_complaint_text or not new_complaint_text.strip():
        return False, "", 0.0

    existing_rows = execute_query("SELECT complaint_id, complaint_text FROM complaints")
    if not existing_rows:
        return False, "", 0.0

    corpus = [r["complaint_text"] for r in existing_rows]
    ids = [r["complaint_id"] for r in existing_rows]

    # Combine new text with corpus for TF-IDF matrix computation
    all_texts = [new_complaint_text] + corpus

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate cosine similarity of new text (index 0) against existing texts (indices 1..)
        new_vec = tfidf_matrix[0:1]
        corpus_matrix = tfidf_matrix[1:]

        sims = cosine_similarity(new_vec, corpus_matrix).flatten()

        max_idx = int(sims.argmax())
        max_sim = float(sims[max_idx])

        if max_sim >= similarity_threshold:
            return True, ids[max_idx], max_sim
        return False, "", max_sim

    except Exception:
        return False, "", 0.0
