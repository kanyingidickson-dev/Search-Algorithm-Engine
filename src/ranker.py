from __future__ import annotations

import math
from dataclasses import dataclass

from src.indexer import InvertedIndex


def _idf(n_docs: int, df: int) -> float:
    return math.log((n_docs + 1) / (df + 1)) + 1.0


def _l2_norm(vec: dict[str, float]) -> float:
    return math.sqrt(sum(v * v for v in vec.values()))


@dataclass(frozen=True)
class RankedResult:
    doc_id: str
    score: float


def rank_query(
    query_terms: list[str],
    index: InvertedIndex,
    *,
    candidate_docs: set[str] | None = None,
) -> list[RankedResult]:
    n_docs = index.document_count
    if n_docs == 0:
        return []

    query_tf: dict[str, int] = {}
    for t in query_terms:
        query_tf[t] = query_tf.get(t, 0) + 1

    query_vec: dict[str, float] = {}
    for term, tf in query_tf.items():
        df = index.document_frequency(term)
        if df == 0:
            continue
        query_vec[term] = float(tf) * _idf(n_docs, df)

    q_norm = _l2_norm(query_vec)
    if q_norm == 0.0:
        return []

    term_candidates: set[str] = set()
    for term in query_vec.keys():
        term_candidates.update(index.term_to_doc_tf.get(term, {}).keys())

    if candidate_docs is None:
        candidate_docs = term_candidates
    else:
        candidate_docs = candidate_docs & term_candidates

    results: list[RankedResult] = []

    for doc_id in candidate_docs:
        doc_vec: dict[str, float] = {}
        for term in query_vec.keys():
            tf = index.term_to_doc_tf.get(term, {}).get(doc_id)
            if not tf:
                continue
            df = index.document_frequency(term)
            doc_vec[term] = float(tf) * _idf(n_docs, df)

        d_norm = _l2_norm(doc_vec)
        if d_norm == 0.0:
            continue

        dot = sum(query_vec[t] * doc_vec.get(t, 0.0) for t in query_vec.keys())
        score = dot / (q_norm * d_norm)
        results.append(RankedResult(doc_id=doc_id, score=score))

    results.sort(key=lambda r: (-r.score, r.doc_id))
    return results
