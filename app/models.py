"""Pydantic contracts shared across backend services and the frontend."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_id: str
    name: str
    chunk_count: int = Field(default=0, ge=0)
    file_type: str = ""
    path: str | None = None
    size_bytes: int = Field(default=0, ge=0)
    ingested_at: datetime = Field(default_factory=utc_now)


class DocumentChunk(BaseModel):
    """A normalized passage in a source document."""

    model_config = ConfigDict(extra="ignore")

    chunk_id: str
    source_id: str
    source_name: str
    chunk_index: int = Field(ge=0)
    text: str


class Citation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    citation_id: str = Field(description="Stable display identifier such as S1")
    source_id: str
    source_name: str
    chunk_id: str
    score: float = Field(ge=0)
    excerpt: str


class QueryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question: str
    answer: str
    route: str = "direct"
    mode: str = "offline"
    citations: list[Citation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    retrieval_trace: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class IngestResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    indexed: int = Field(ge=0)
    failed: list[str] = Field(default_factory=list)
    total_chunks: int = Field(default=0, ge=0)


class ActivityEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_type: str
    message: str
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
