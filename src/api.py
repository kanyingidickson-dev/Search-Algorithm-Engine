from fastapi import FastAPI, Query as FastAPIQuery
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import List
from src.search import SearchEngine

app = FastAPI(title="Search Algorithm Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchResult(BaseModel):
    doc_id: str
    title: str
    snippet: str
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int

class SuggestResponse(BaseModel):
    suggestions: List[str]

# Load documents and build index at startup
DATA_PATH = Path("data/raw")
engine = SearchEngine.from_folder(DATA_PATH)

@app.get("/search", response_model=SearchResponse)
def search(
    q: str = FastAPIQuery(..., description="Search query"),
    limit: int = 10,
    offset: int = 0,
):
    results = engine.search(q, limit=limit, offset=offset)
    out = []
    for ranked, content in results:
        snippet = content[:200].replace("\n", " ") + ("..." if len(content) > 200 else "")
        out.append(SearchResult(
            doc_id=ranked.doc_id,
            title=ranked.doc_id,
            snippet=snippet,
            score=ranked.score,
        ))
    return SearchResponse(results=out, total=len(engine.documents))

@app.get("/suggest", response_model=SuggestResponse)
def suggest(q: str = FastAPIQuery(..., description="Partial query")):
    # Simple suggestion: match doc_ids containing substring
    suggestions = [doc_id for doc_id in engine.documents.keys() if q.lower() in doc_id.lower()]
    # Fallback: just return the query with suffix if nothing found
    if not suggestions:
        suggestions = [q + " example", q + " test"]
    return SuggestResponse(suggestions=suggestions[:10])
