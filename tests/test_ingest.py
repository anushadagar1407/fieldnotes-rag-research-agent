import json
from pathlib import Path

import pytest

from app.ingest import chunk_text, extract_text, ingest_file


def test_extract_text_reads_txt_and_markdown(tmp_path: Path):
    txt = tmp_path / "notes.txt"
    txt.write_text("  Alpha\n\nBeta  ", encoding="utf-8")
    md = tmp_path / "readme.md"
    md.write_text("# Heading\n\nBody", encoding="utf-8")

    assert extract_text(txt) == "Alpha\n\nBeta"
    assert extract_text(md) == "# Heading\n\nBody"


def test_extract_text_serializes_csv_and_json_readably(tmp_path: Path):
    csv_path = tmp_path / "rows.csv"
    csv_path.write_text("name,score\nAda,10\nGrace,9\n", encoding="utf-8")
    json_path = tmp_path / "record.json"
    json_path.write_text(json.dumps({"name": "Ada", "tags": ["math", "logic"]}), encoding="utf-8")

    assert extract_text(csv_path) == "name | score\nAda | 10\nGrace | 9"
    assert extract_text(json_path) == '{\n  "name": "Ada",\n  "tags": [\n    "math",\n    "logic"\n  ]\n}'


def test_chunk_text_has_requested_overlap():
    chunks = chunk_text("0123456789", chunk_size=6, overlap=2)

    assert chunks == ["012345", "456789"]


def test_chunk_text_rejects_invalid_sizes():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=0)
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=4, overlap=4)


def test_ingest_file_returns_stable_source_and_chunk_metadata(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("A useful passage for indexing.", encoding="utf-8")

    summary, chunks = ingest_file(path, chunk_size=10, overlap=2)

    assert summary.name == "notes.txt"
    assert summary.file_type == ".txt"
    assert summary.path == str(path)
    assert summary.chunk_count == len(chunks)
    assert chunks[0].source_id == summary.source_id
    assert chunks[0].source_name == summary.name
    assert chunks[0].chunk_id == f"{summary.source_id}-0"
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_extract_text_rejects_unsupported_extensions(tmp_path: Path):
    path = tmp_path / "archive.bin"
    path.write_bytes(b"binary")

    with pytest.raises(ValueError, match="Unsupported file extension"):
        extract_text(path)
