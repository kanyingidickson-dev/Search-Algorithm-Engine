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


def test_phrase_query_matches_only_adjacent_terms(tmp_path: Path):
    d = tmp_path / "data"
    d.mkdir()

    (d / "a.txt").write_text("fast api is great", encoding="utf-8")
    (d / "b.txt").write_text("fast and reliable api", encoding="utf-8")

    engine = SearchEngine.from_folder(d)
    results = engine.search('"fast api"', limit=10)
    doc_ids = [r.doc_id for r, _ in results]

    assert "a.txt" in doc_ids
    assert "b.txt" not in doc_ids


def test_boolean_and_or_not_and_precedence(tmp_path: Path):
    d = tmp_path / "data"
    d.mkdir()

    (d / "a.txt").write_text("fast api", encoding="utf-8")
    (d / "b.txt").write_text("fast", encoding="utf-8")
    (d / "c.txt").write_text("api", encoding="utf-8")

    engine = SearchEngine.from_folder(d)

    and_docs = {r.doc_id for r, _ in engine.search("fast AND api", limit=10)}
    assert and_docs == {"a.txt"}

    or_docs = {r.doc_id for r, _ in engine.search("fast OR api", limit=10)}
    assert or_docs == {"a.txt", "b.txt", "c.txt"}

    not_docs = {r.doc_id for r, _ in engine.search("NOT fast", limit=10)}
    assert "b.txt" not in not_docs
    assert "c.txt" in not_docs

    # precedence: NOT > AND > OR
    # fast OR api AND NOT fast  => fast OR (api AND (NOT fast))
    # api AND NOT fast matches only c.txt; OR fast adds a.txt and b.txt
    prec_docs = {r.doc_id for r, _ in engine.search("fast OR api AND NOT fast", limit=10)}
    assert prec_docs == {"a.txt", "b.txt", "c.txt"}


def test_implicit_and(tmp_path: Path):
    d = tmp_path / "data"
    d.mkdir()

    (d / "a.txt").write_text("fast api", encoding="utf-8")
    (d / "b.txt").write_text("fast", encoding="utf-8")

    engine = SearchEngine.from_folder(d)
    docs = {r.doc_id for r, _ in engine.search("fast api", limit=10)}

    assert docs == {"a.txt"}


def test_offset_pagination(tmp_path: Path):
    d = tmp_path / "data"
    d.mkdir()

    (d / "a.txt").write_text("api api api", encoding="utf-8")
    (d / "b.txt").write_text("api api", encoding="utf-8")
    (d / "c.txt").write_text("api", encoding="utf-8")

    engine = SearchEngine.from_folder(d)
    all_docs = [r.doc_id for r, _ in engine.search("api", limit=10, offset=0)]
    page = [r.doc_id for r, _ in engine.search("api", limit=1, offset=1)]

    assert len(all_docs) >= 2
    assert page == [all_docs[1]]
