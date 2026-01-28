from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.indexer import InvertedIndex, build_inverted_index
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

    def search(self, query: str, limit: int = 5) -> list[tuple[RankedResult, str]]:
        terms = self.tokenizer.tokenize(query)
        ranked = rank_query(terms, self.index)[:limit]
        return [(r, self.documents[r.doc_id]) for r in ranked]
