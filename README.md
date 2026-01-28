# Search Algorithm Engine

![CI](https://github.com/kanyingidickson-dev/Search-Algorithm-Engine/actions/workflows/ci.yml/badge.svg)

A small, handwritten text search engine that indexes local documents and returns ranked results.

This project focuses on core information retrieval fundamentals:
- tokenization + normalization
- inverted index construction
- TF-IDF scoring
- cosine similarity ranking

No external search libraries are used.

## Tech stack

- Python 3 (standard library)
- pytest (tests)

## How to run locally

```bash
pip install -r requirements.txt
python -m src.cli --data data/raw --query "fast api database"
```

Interactive mode:

```bash
python -m src.cli --data data/raw
```

## Example usage

```bash
python -m src.cli --data data/raw --query "python api"
```

## Design decisions

- Inverted index maps `term -> {doc_id: term_frequency}`.
- TF-IDF uses `idf = log((N + 1) / (df + 1)) + 1` to avoid division-by-zero and to smooth rare terms.
- Ranking uses cosine similarity between the query TF-IDF vector and each candidate document vector.

## Future improvements

- Phrase queries / positional index
- Stopword lists and stemming options
- Field weighting (title vs body)
- Persisting the index to disk
