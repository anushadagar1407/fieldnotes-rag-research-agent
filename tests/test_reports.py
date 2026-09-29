from pathlib import Path

from app.logging_utils import append_event, read_events
from app.models import ActivityEvent, Citation, QueryResponse
from app.reports import render_report


def test_report_contains_headings_and_citations():
    query = QueryResponse(
        question="Why?", answer="Because the source says so [S1].", route="documents", mode="offline",
        citations=[Citation(citation_id="S1", source_id="one", source_name="notes.md", chunk_id="one-0", score=0.8, excerpt="Source evidence.")],
    )
    report = render_report(query)
    assert "# Research report: Why?" in report
    assert "## Sources" in report
    assert "[S1]" in report


def test_jsonl_activity_round_trip(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    append_event(path, ActivityEvent(event_type="query", message="completed"))
    events = read_events(path)
    assert len(events) == 1
    assert events[0].message == "completed"
