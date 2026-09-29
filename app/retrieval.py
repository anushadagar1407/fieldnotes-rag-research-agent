from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from .models import DocumentChunk, SourceSummary


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float
    rank: int


class RetrievalIndex:
    def __init__(self, chunks: list[DocumentChunk] | None = None, sources: list[SourceSummary] | None = None):
        self._chunks = list(chunks or [])
        self._sources = {source.source_id: source for source in (sources or [])}
        self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._matrix = None
        self._rebuild()

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def source_summaries(self) -> list[SourceSummary]:
        return list(self._sources.values())

    def _rebuild(self) -> None:
        if not self._chunks:
            self._matrix = None
            return
        self._matrix = self._vectorizer.fit_transform([chunk.text for chunk in self._chunks])

    def add_source(self, summary: SourceSummary, chunks: list[DocumentChunk]) -> None:
        self._chunks = [chunk for chunk in self._chunks if chunk.source_id != summary.source_id]
        self._chunks.extend(chunks)
        self._sources[summary.source_id] = summary
        self._rebuild()

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not query.strip() or not self._chunks or self._matrix is None:
            return []
        query_vector = self._vectorizer.transform([query])
        scores = (self._matrix @ query_vector.T).toarray().ravel()
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        results = []
        for rank, (index, score) in enumerate(ranked[: max(0, top_k)], start=1):
            if score <= 0:
                continue
            results.append(SearchResult(chunk=self._chunks[index], score=float(score), rank=rank))
        return results

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sources": [source.model_dump(mode="json") for source in self._sources.values()],
            "chunks": [chunk.model_dump(mode="json") for chunk in self._chunks],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "RetrievalIndex":
        path = Path(path)
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources = [SourceSummary.model_validate(value) for value in payload.get("sources", [])]
        chunks = [DocumentChunk.model_validate(value) for value in payload.get("chunks", [])]
        return cls(chunks=chunks, sources=sources)
