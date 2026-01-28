from pathlib import Path

from src.search import SearchEngine


def test_search_ranks_relevant_doc(tmp_path: Path):
    d = tmp_path / "data"
    d.mkdir()

    (d / "a.txt").write_text("python fastapi api", encoding="utf-8")
    (d / "b.txt").write_text("relational database postgres sql", encoding="utf-8")

    engine = SearchEngine.from_folder(d)
    results = engine.search("fastapi api", limit=2)

    assert results
    assert results[0][0].doc_id == "a.txt"
