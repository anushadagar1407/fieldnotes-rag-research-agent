"""Append-only activity logging helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ActivityEvent


def append_event(path: Path, event: ActivityEvent) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(event.model_dump_json() + "\n")


def read_events(path: Path, limit: int = 50) -> list[ActivityEvent]:
    path = Path(path)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    events = []
    for line in reversed(lines):
        try:
            events.append(ActivityEvent.model_validate(json.loads(line)))
        except (ValueError, TypeError):
            continue
    return events
