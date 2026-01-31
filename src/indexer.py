from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class InvertedIndex:
    term_to_doc_tf: dict[str, dict[str, int]]
    term_to_doc_positions: dict[str, dict[str, list[int]]]
    doc_lengths: dict[str, int]

    @property
    def document_count(self) -> int:
        return len(self.doc_lengths)

    def document_frequency(self, term: str) -> int:
        postings = self.term_to_doc_tf.get(term)
        return 0 if not postings else len(postings)


def build_inverted_index(documents: dict[str, str], tokenize) -> InvertedIndex:
    term_to_doc_tf: dict[str, dict[str, int]] = defaultdict(dict)
    term_to_doc_positions: dict[str, dict[str, list[int]]] = defaultdict(dict)
    doc_lengths: dict[str, int] = {}

    for doc_id, text in documents.items():
        tokens = tokenize(text)
        doc_lengths[doc_id] = len(tokens)

        positions: dict[str, list[int]] = defaultdict(list)
        for pos, term in enumerate(tokens):
            positions[term].append(pos)
        for term, pos_list in positions.items():
            term_to_doc_positions[term][doc_id] = pos_list

        tf = Counter(tokens)
        for term, count in tf.items():
            term_to_doc_tf[term][doc_id] = count

    return InvertedIndex(
        term_to_doc_tf=dict(term_to_doc_tf),
        term_to_doc_positions=dict(term_to_doc_positions),
        doc_lengths=doc_lengths,
    )
