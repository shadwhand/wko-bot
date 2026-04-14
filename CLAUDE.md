# WKO5 Experiments

Cycling analytics platform: power-based training, nutrition, pacing, and performance modeling for an ultra-endurance cyclist.

## MANDATORY: Wiki-First Workflow

**Before answering ANY question about training, nutrition, pacing, physiology, coaching, race planning, or ride analysis, you MUST follow this retrieval flow:**

1. **Route via local LLM** — run `tools/wiki-route.sh "your question"` to get 2-3 relevant page paths from Qwen3-4B (~5s, free). This replaces reading index.md manually.
2. **Read those wiki pages** — extract specific evidence with [R]/[E]/[O] tags and source citations
3. **Answer using wiki content as primary source** — cite the page and evidence tags in your response
4. **File back** — if your answer reveals connections not captured in the wiki, update the relevant pages
5. **Re-index** — `qmd update && qmd embed` after any wiki changes

**Fallback if omlx is down:** Read `docs/research/wiki/index.md` manually and identify pages yourself.

**Do NOT answer from general knowledge when the wiki has relevant content.** The wiki contains curated, evidence-tagged knowledge compiled from 2,012 TrainingPeaks articles, 55 EC podcast episodes, and the athlete's personal ride history. General knowledge is a fallback, not the default.

**Do NOT skip straight to pages you "already know about."** Use the router. It may point to pages you'd miss.

**After every valuable answer, ask:** "Did this reveal connections worth filing back to the wiki?" If yes, update pages and re-index.

## Knowledge Base (qmd)

Karpathy-style LLM wiki backed by qmd (local hybrid search). Schema: `docs/research/wiki/SCHEMA.md`.

### Searching

**Retrieval flow:** index.md → relevant pages → answer → file back → re-index.

- **qmd MCP tools:** `query`, `get`, `multi_get` — always scope to wiki: `-c wiki`
- **qmd CLI:** `qmd search "query" -c wiki` (lexical), `qmd query "query" -c wiki` (hybrid+rerank)
- **API:** `GET /api/knowledge?q=...&collections=wiki` via the FastAPI server

Use qmd search when the question is ambiguous or you're not sure which pages are relevant.

### Collections

| Collection | Default | Content |
|------------|---------|---------|
| wiki | Included | Compiled knowledge pages (concepts, entities, nutrition) |
| empirical-cycling | Included | EC podcast insights (55 episodes) |
| trainingpeaks | Excluded | 2,012 TP blog articles (opt-in with `-c trainingpeaks`) |
| nutrition | Included | 3 deep nutrition research syntheses |
| reports | Included | Generated training analysis reports |
| code | Excluded | Python source code (opt-in with `-c code`) |

### Wiki Operations

- **Ingest:** New sources → transcribe → extract insights → update wiki pages → re-index. See `tools/wiki-ingest.md`.
- **Query → File back:** Every valuable answer should check if wiki pages need updating. See SCHEMA.md §2.
- **Lint:** After re-indexing, check cross-references, index.md coverage, contradictions. See `tools/wiki-lint.md`.
- **Re-index:** `qmd update && qmd embed` after ANY wiki change. Non-negotiable. Automated via PostToolUse hook.

### Evidence Tags

All training science claims use: **[R]** research-backed, **[E]** experience-based, **[O]** opinion.

### Personal Data

The athlete's personal ride log (`entities/personal-ride-log.md`) and race plans (`docs/reports/`) are gitignored — local only. Other athletes using this repo build their own data via `setup.sh`.

## Race Plans

Race plans follow the template at `docs/reports/TEMPLATE-race-plan.md`. Use this format for all new plans.

## Local LLM (omlx)

Local MLX models available at `http://127.0.0.1:8000` for wiki-grounded Q&A. See `wko5/local_llm.py`. Use Qwen3-4B for fast prefetch, Qwen3.5-122B for full synthesis.

## Stack

- **Backend:** FastAPI (`wko5/api/`), DuckDB, Stan (Bayesian models)
- **Frontend:** Vanilla JS + D3 (`frontend/`)
- **Search:** qmd v2.1.0 (`.qmd/qmd.yml`)
- **Config:** `wko5/config.py` (athlete settings in DuckDB)
- **Local LLM:** omlx server (`wko5/local_llm.py`)
