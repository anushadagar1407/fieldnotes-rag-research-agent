import io

from fastapi.testclient import TestClient

from app.main import app, index, settings


client = TestClient(app)


def test_health_and_empty_sources():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "indexed_chunks" in response.json()
    assert client.get("/api/sources").status_code == 200


def test_ingest_query_and_report(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "uploads_dir", tmp_path / "uploads")
    monkeypatch.setattr(settings, "index_path", tmp_path / "index.json")
    monkeypatch.setattr(settings, "log_path", tmp_path / "events.jsonl")
    settings.uploads_dir.mkdir()
    index._chunks.clear()
    index._sources.clear()
    index._rebuild()

    upload = client.post("/api/ingest", files={"files": ("notes.md", io.BytesIO(b"Audit trails make research systems easier to trust."), "text/markdown")})
    assert upload.status_code == 200
    assert upload.json()["indexed"] == 1

    response = client.post("/api/query", json={"question": "Why do audit trails matter?"})
    assert response.status_code == 200
    body = response.json()
    assert body["citations"][0]["citation_id"] == "S1"

    report = client.post("/api/report", json={"query": body})
    assert report.status_code == 200
    assert "# Research report" in report.json()["markdown"]
