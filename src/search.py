from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.indexer import InvertedIndex, build_inverted_index
from src.query import evaluate_query, iter_positive_terms, parse_query
from src.ranker import RankedResult, rank_query
from src.tokenizer import Tokenizer


def load_documents_from_folder(folder: Path) -> dict[str, str]:
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Data folder not found: {folder}")

    documents: dict[str, str] = {}
    for p in sorted(folder.glob("*.txt")):
        documents[p.name] = p.read_text(encoding="utf-8")

    if not documents:
        raise RuntimeError(f"No .txt documents found in: {folder}")

    return documents


@dataclass
class SearchEngine:
    tokenizer: Tokenizer
    documents: dict[str, str]
    index: InvertedIndex

    @classmethod
    def from_folder(cls, folder: Path) -> "SearchEngine":
        tokenizer = Tokenizer()
        documents = load_documents_from_folder(folder)
        index = build_inverted_index(documents, tokenize=tokenizer.tokenize)
        return cls(tokenizer=tokenizer, documents=documents, index=index)

    def search(
        self, query: str, *, limit: int = 5, offset: int = 0
    ) -> list[tuple[RankedResult, str]]:
        if offset < 0:
            raise ValueError("offset must be >= 0")

        ast = parse_query(query, tokenize=self.tokenizer.tokenize)
        candidate_docs = evaluate_query(ast, self.index)
        terms = list(iter_positive_terms(ast))

        if not terms:
            doc_ids = sorted(candidate_docs)
            doc_ids = doc_ids[offset : offset + limit]
            ranked = [RankedResult(doc_id=doc_id, score=0.0) for doc_id in doc_ids]
            return [(r, self.documents[r.doc_id]) for r in ranked]

        ranked = rank_query(terms, self.index, candidate_docs=candidate_docs)
        ranked = ranked[offset : offset + limit]
        return [(r, self.documents[r.doc_id]) for r in ranked]
