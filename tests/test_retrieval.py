from pathlib import Path

from app.models import DocumentChunk, SourceSummary
from app.retrieval import RetrievalIndex


def _source(source_id: str, name: str) -> SourceSummary:
    return SourceSummary(source_id=source_id, name=name, chunk_count=1)


def _chunk(source_id: str, text: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"{source_id}-0",
        source_id=source_id,
        source_name=f"{source_id}.md",
        chunk_index=0,
        text=text,
    )


def test_relevant_chunk_ranks_first_and_empty_queries_are_safe():
    index = RetrievalIndex()
    index.add_source(_source("plants", "plants.md"), [_chunk("plants", "Plants convert sunlight into chemical energy through photosynthesis.")])
    index.add_source(_source("weather", "weather.md"), [_chunk("weather", "Rainfall patterns vary across the Pacific Northwest.")])

    results = index.search("How do plants use sunlight?", top_k=2)

    assert results[0].chunk.source_id == "plants"
    assert results[0].score > 0
    assert index.search("", top_k=2) == []


def test_save_and_load_preserves_search_results(tmp_path: Path):
    index = RetrievalIndex()
    index.add_source(_source("notes", "notes.md"), [_chunk("notes", "Reliable systems use audit trails and evaluation records.")])
    path = tmp_path / "index.json"
    index.save(path)

    loaded = RetrievalIndex.load(path)

    assert loaded.chunk_count == 1
    assert loaded.source_summaries()[0].name == "notes.md"
    assert loaded.search("audit trails")[0].chunk.chunk_id == "notes-0"
