from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import ResearchAgent
from .config import settings
from .ingest import ingest_file
from .logging_utils import append_event, read_events
from .models import ActivityEvent, IngestResponse, QueryResponse
from .reports import render_report
from .retrieval import RetrievalIndex

settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
index = RetrievalIndex.load(settings.index_path)
agent = ResearchAgent()

app = FastAPI(title="Anusha Dagar / Fieldnotes", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class ReportRequest(BaseModel):
    query: QueryResponse


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "mode": "anthropic" if settings.anthropic_api_key else "offline", "indexed_chunks": index.chunk_count}


@app.get("/api/sources")
def sources() -> dict:
    return {"sources": index.source_summaries()}


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest(files: list[UploadFile] = File(...)) -> IngestResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    indexed = 0
    total_chunks = 0
    failed: list[str] = []
    for upload in files:
        name = Path(upload.filename or "").name
        if not name:
            failed.append("unnamed upload")
            continue
        destination = settings.uploads_dir / name
        with destination.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        try:
            summary, chunks = ingest_file(destination)
            index.add_source(summary, chunks)
            indexed += 1
            total_chunks += len(chunks)
        except Exception as exc:
            failed.append(f"{name}: {exc}")
    index.save(settings.index_path)
    append_event(settings.log_path, ActivityEvent(event_type="ingest", message="Sources indexed", metadata={"indexed": indexed, "failed": len(failed), "chunks": total_chunks}))
    return IngestResponse(indexed=indexed, failed=failed, total_chunks=total_chunks)


@app.post("/api/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    try:
        response = agent.answer(request.question, index, top_k=request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    append_event(settings.log_path, ActivityEvent(event_type="query", message="Query completed", metadata={"route": response.route, "mode": response.mode, "citations": len(response.citations), "question": response.question}))
    return response


@app.post("/api/report")
def report(request: ReportRequest) -> dict:
    return {"markdown": render_report(request.query), "filename": "research-report.md"}


@app.get("/api/activity")
def activity() -> dict:
    return {"events": read_events(settings.log_path)}


frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str) -> FileResponse:
        requested = frontend_dist / path
        return FileResponse(requested if requested.is_file() else frontend_dist / "index.html")
else:

    @app.get("/")
    def development_root() -> dict:
        return {"name": "Anusha Dagar / Fieldnotes", "message": "Build frontend/dist or use the Vite dev server."}
