from __future__ import annotations

import argparse
from pathlib import Path

from src.search import SearchEngine


def _preview(text: str, max_len: int = 160) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= max_len else clean[: max_len - 3] + "..."


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Algorithm Engine")
    parser.add_argument("--data", required=True, help="Folder containing .txt documents")
    parser.add_argument("--query", default=None, help="Search query")
    parser.add_argument("--limit", type=int, default=5, help="Max results")
    parser.add_argument("--offset", type=int, default=0, help="Result offset")
    args = parser.parse_args()

    engine = SearchEngine.from_folder(Path(args.data))

    if args.query is not None:
        results = engine.search(args.query, limit=args.limit, offset=args.offset)
        for i, (r, text) in enumerate(results, start=1):
            print(f"{i}. {r.doc_id}  score={r.score:.4f}")
            print(f"   {_preview(text)}")
        return 0

    while True:
        q = input("query> ").strip()
        if not q:
            continue
        if q in {":q", ":quit", "quit", "exit"}:
            return 0
        results = engine.search(q, limit=args.limit, offset=args.offset)
        for i, (r, text) in enumerate(results, start=1):
            print(f"{i}. {r.doc_id}  score={r.score:.4f}")
            print(f"   {_preview(text)}")


if __name__ == "__main__":
    raise SystemExit(main())
