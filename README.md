# Fieldnotes / RAG Research Agent

A local research console inspired by [RAG-Research-Agent](https://github.com/Sagardeep1/RAG-Research-Agent). It ingests TXT, Markdown, PDF, DOCX, CSV, and JSON files, retrieves relevant passages with a persisted TF-IDF index, answers with citations, logs activity, and exports Markdown reports.

## Run locally

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
env -u ANTHROPIC_MODEL .venv/bin/python run.py
```

Open `http://127.0.0.1:8000/`. The app works offline. To enable Anthropic generation, set `ANTHROPIC_API_KEY` in `.env`.

For frontend development, use `cd frontend && npm install && npm run dev`, then set `VITE_API_BASE=http://127.0.0.1:8000` if the Vite server is on port 5173.

## Verification

```bash
env -u ANTHROPIC_MODEL .venv/bin/pytest tests -q
cd frontend && npm run build
```

The first run creates `data/uploads/`, `data/index.json`, and `data/query_log.jsonl`.
