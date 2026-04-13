# WKO5 Experiments

Cycling analytics platform: power-based training, nutrition, pacing, and performance modeling for an ultra-endurance cyclist.

## Knowledge Base (qmd)

This project uses a **Karpathy-style LLM wiki** backed by qmd (local hybrid search). Before answering training science, nutrition, or coaching questions, search the knowledge base.

### Wiki Schema

**Read first:** `docs/research/wiki/SCHEMA.md` — defines page structure, naming conventions, evidence tags, and operational workflows (ingest, query, lint).

### Searching

**Retrieval flow:** Read `docs/research/wiki/index.md` first to identify relevant pages, then drill in. Use qmd when the question is ambiguous or the wiki grows beyond what the index can navigate.

- **qmd MCP tools:** `query`, `get`, `multi_get` — always scope to wiki: `-c wiki`
- **qmd CLI:** `qmd search "query" -c wiki` (lexical), `qmd query "query" -c wiki` (hybrid+rerank)
- **API:** `GET /api/knowledge?q=...&collections=wiki` via the FastAPI server

### Collections

| Collection | Default | Content |
|------------|---------|---------|
| wiki | Included | Compiled knowledge pages (concepts, entities, nutrition) |
| empirical-cycling | Included | EC podcast insights (53 episodes) |
| trainingpeaks | Excluded | 2,012 TP blog articles (opt-in with `-c trainingpeaks`) |
| nutrition | Included | 3 deep nutrition research syntheses |
| reports | Included | Generated training analysis reports |
| code | Excluded | Python source code (opt-in with `-c code`) |

### Wiki Operations

- **Ingest:** New sources get compiled into wiki pages per SCHEMA.md ingest workflow
- **Query → File back:** Valuable answers should update relevant wiki pages
- **Lint:** Periodic checks for contradictions, orphans, stale claims, missing cross-refs

### Evidence Tags

All training science claims use: **[R]** research-backed, **[E]** experience-based, **[O]** opinion.

## Stack

- **Backend:** FastAPI (`wko5/api/`), DuckDB, Stan (Bayesian models)
- **Frontend:** Vanilla JS + D3 (`frontend/`)
- **Search:** qmd v2.1.0 (`.qmd/qmd.yml`)
- **Config:** `wko5/config.py` (athlete settings in DuckDB)
