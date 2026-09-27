# knowledge_base/tfidf_retriever.py
# Module implementing TF-IDF vectorizer indexing, document precedence scoring, and top-K policy RAG retrieval.

import re
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from document_processing.validator import evaluate_document_validity
from config.config import get_setting

# Precedence hierarchy scoring matrix based on HARD RULE 5:
# Legal > Escalation SOP > Active Policies (latest date) > Active SOPs > Templates > FAQs
PRECEDENCE_RANKS = {
    "legal": 60,
    "escalation_sop": 50,
    "policy": 40,
    "active_sop": 30,
    "template": 20,
    "faq": 10
}

def compute_precedence_score(doc_category: str, doc_title: str) -> int:
    """
    Computes numerical precedence rank based on document title and category.
    Higher rank means higher precedence in policy conflicts.
    """
    text_lower = f"{doc_category} {doc_title}".lower()
    if "legal" in text_lower or "compliance" in text_lower:
        return PRECEDENCE_RANKS["legal"]
    elif "escalation" in text_lower and "sop" in text_lower:
        return PRECEDENCE_RANKS["escalation_sop"]
    elif "sop" in text_lower:
        return PRECEDENCE_RANKS["active_sop"]
    elif "template" in text_lower:
        return PRECEDENCE_RANKS["template"]
    elif "faq" in text_lower:
        return PRECEDENCE_RANKS["faq"]
    else:
        return PRECEDENCE_RANKS["policy"]

class TFIDFRetriever:
    """
    RAG Retriever using scikit-learn TF-IDF vectorizer and cosine similarity.
    Integrates HARD RULE 5: Document validity check and policy precedence ranking.
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        self.chunks_data: List[Dict[str, Any]] = []
        self.tfidf_matrix = None
        self.is_indexed = False

    def build_index(self, chunks: List[Dict[str, Any]], documents_metadata: List[Dict[str, Any]] = None) -> None:
        """
        Builds or rebuilds the TF-IDF matrix index from list of chunk records and document metadata.
        """
        if not chunks:
            self.is_indexed = False
            self.chunks_data = []
            return

        doc_meta_map = {}
        if documents_metadata:
            doc_meta_map = {d['doc_id']: d for d in documents_metadata}

        enriched_chunks = []
        corpus = []

        for chk in chunks:
            doc_id = chk.get('doc_id')
            meta = doc_meta_map.get(doc_id, {})

            status = chk.get('status') or meta.get('status', 'Active')
            version = chk.get('version') or meta.get('version', 'v1.0')
            eff_date = meta.get('effective_date', '2024-01-01')
            exp_date = meta.get('expiry_date', '2026-12-31')
            category = meta.get('category', 'General')
            title = meta.get('title', 'Policy Document')

            # Evaluate HARD RULE 5 document validity
            validity_eval = evaluate_document_validity(status, eff_date, exp_date)
            prec_score = compute_precedence_score(category, title)

            chk_copy = dict(chk)
            chk_copy.update({
                'title': title,
                'category': category,
                'effective_date': eff_date,
                'expiry_date': exp_date,
                'is_primary_valid': validity_eval['is_primary_valid'],
                'warning_flag': validity_eval['flag'],
                'precedence_score': prec_score
            })
            enriched_chunks.append(chk_copy)
            # Corpus text combines section heading, title, and chunk text for high-relevance matching
            corpus.append(f"{title} {category} {chk.get('heading', '')} {chk.get('text', '')}")

        self.chunks_data = enriched_chunks
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_indexed = True

    def retrieve_top_k(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the index using cosine similarity on TF-IDF vectors.
        Ranks results by similarity score and policy precedence.
        """
        if not self.is_indexed or self.tfidf_matrix is None or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        results = []
        for idx, sim in enumerate(similarities):
            if sim > 0.01: # Filter zero-relevance matches
                item = dict(self.chunks_data[idx])
                item['similarity_score'] = float(sim)
                results.append(item)

        # Sort primarily by validity, then precedence_score, then similarity_score
        results.sort(
            key=lambda x: (
                1 if x['is_primary_valid'] else 0,
                x['precedence_score'],
                x['similarity_score']
            ),
            reverse=True
        )

        return results[:top_k]
