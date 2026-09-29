from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models import (
    ActivityEvent,
    Citation,
    DocumentChunk,
    IngestResponse,
    QueryResponse,
    SourceSummary,
)
from app.config import PROJECT_DIR, Settings


def test_source_summary_requires_identity_and_counts_chunks():
    with pytest.raises(ValidationError):
        SourceSummary()

    source = SourceSummary(source_id="source-1", name="notes.md", chunk_count=2)

    assert source.source_id == "source-1"
    assert source.name == "notes.md"
    assert source.chunk_count == 2
    assert source.file_type == ""


def test_citation_requires_source_and_supporting_excerpt():
    citation = Citation(
        citation_id="S1",
        source_id="source-1",
        source_name="notes.md",
        chunk_id="source-1-0",
        score=0.75,
        excerpt="A supporting passage.",
    )

    assert citation.citation_id == "S1"
    assert citation.score == pytest.approx(0.75)


def test_query_response_defaults_are_deterministic_and_serializable():
    response = QueryResponse(question="What is this about?", answer="It is about testing.")

    assert response.route == "direct"
    assert response.mode == "offline"
    assert response.citations == []
    assert response.warnings == []
    assert isinstance(response.created_at, datetime)


def test_ingest_response_defaults_and_activity_event_timestamp():
    ingest = IngestResponse(indexed=1, failed=[])
    assert ingest.total_chunks == 0
    assert ingest.failed == []

    event = ActivityEvent(event_type="query", message="Query completed")
    assert event.metadata == {}
    assert isinstance(event.timestamp, datetime)


def test_document_chunk_requires_stable_source_metadata():
    chunk = DocumentChunk(
        chunk_id="source-1-0",
        source_id="source-1",
        source_name="notes.md",
        chunk_index=0,
        text="A normalized passage.",
    )

    assert chunk.chunk_id == "source-1-0"
    assert chunk.chunk_index == 0
    assert chunk.text == "A normalized passage."


def test_settings_defaults_are_project_anchored(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    configured = Settings()

    assert configured.data_dir == PROJECT_DIR / "data"
    assert configured.uploads_dir == PROJECT_DIR / "data" / "uploads"
    assert configured.index_path == PROJECT_DIR / "data" / "index.json"
    assert configured.log_path == PROJECT_DIR / "data" / "query_log.jsonl"
    assert configured.anthropic_model == "claude-3-5-sonnet-latest"
    assert configured.top_k == 5
