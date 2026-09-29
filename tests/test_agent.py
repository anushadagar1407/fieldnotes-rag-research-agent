from app.agent import Calculator, ResearchAgent
from app.models import DocumentChunk, SourceSummary
from app.retrieval import RetrievalIndex


def _index() -> RetrievalIndex:
    index = RetrievalIndex()
    source = SourceSummary(source_id="notes", name="notes.md", chunk_count=1)
    chunk = DocumentChunk(
        chunk_id="notes-0", source_id="notes", source_name="notes.md", chunk_index=0,
        text="Audit trails make AI systems easier to inspect and trust.",
    )
    index.add_source(source, [chunk])
    return index


def test_calculator_rejects_non_numeric_code():
    assert Calculator().evaluate("1000 * 1.05 ** 10") > 1600
    try:
        Calculator().evaluate("__import__('os').system('whoami')")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe expression was accepted")


def test_document_question_has_offline_citations():
    response = ResearchAgent().answer("Why do audit trails matter?", _index())

    assert response.route == "documents"
    assert response.mode == "offline"
    assert response.citations[0].citation_id == "S1"
    assert "[S1]" in response.answer


def test_calculator_and_no_match_routes():
    calc = ResearchAgent().answer("what is 100 + 25", _index())
    missing = ResearchAgent().answer("What is the weather?", _index())

    assert calc.route == "calculator"
    assert "125" in calc.answer
    assert missing.warnings
