# Ingest Log

## 2026-04-12 — Initial compilation

- **Sources:** 2,012 TP articles, 53 EC episodes (master ref + 7 batch extracts), 3 nutrition research docs
- **Pages created:** 21 (12 concepts, 4 entities, 5 nutrition)
- **Compiled by:** Claude Code parallel agent pipeline (10 agents)
- **Method:** Each agent read relevant source articles + EC master reference, compiled evidence-tagged wiki pages

## 2026-04-12 — Infrastructure setup

- **qmd v2.1.0** installed, 6 collections configured (`.qmd/qmd.yml`)
- **Indexed:** 2,203 documents, 7,834 vector embeddings, 68.8 MB index
- **MCP server:** configured in `~/.claude/settings.json` (stdio transport)
- **HTTP daemon:** `qmd mcp --http --daemon` on localhost:8181
- **Python client:** `wko5/knowledge.py` (KnowledgeClient with MCP session handling)
- **API endpoint:** `GET /api/knowledge` added to `wko5/api/routes.py`
- **Tests:** 6/6 passing in `tests/test_knowledge.py`

## 2026-04-12 — TP article conversion

- **Converted:** 1,292 new articles from JSON to markdown (tools/convert_tp_articles.py)
- **Total:** 2,012 markdown articles in `docs/research/trainingpeaks/`
- **Nutrition cleanup:** 3 files extracted from JSON conversation wrappers to clean markdown

## 2026-04-12 — Eval: baseline vs augmented

- **Method:** 5 question pairs (FTP plateau, VO2max-FTP, 200km fueling, VO2max block, durability)
- **Baseline:** answer from general knowledge only (avg 13,661 tokens, 36.9s)
- **Augmented:** answer after reading relevant wiki pages (avg 40,490 tokens, 56.5s)
- **Results:** Overall +1.3/5, evidence quality +2.6/5, correctness +1.0/5
- **One regression:** Q3 actionability (baseline hour-by-hour format beat augmented's 2-hr groupings)
- **Full report:** `docs/research/wiki/eval/results.md`

## 2026-04-12 — Ingest: TMT #75 — The Art of Autoregulation (Training To Vibes)

- **Source:** `/tmp/ec-episodes/tmt-75.txt` (transcript, March 26 2026, 1:20 duration)
- **Episode insights:** `docs/research/empirical-cycling/ep-tmt75-autoregulation.md`
- **Pages updated:**
  - `concepts/training-periodization.md` — priority ranking in microcycles, flexible workout prescriptions, prefab plan forecast analogy
  - `concepts/training-load-recovery.md` — low-fatigue readiness gauges (FTP check, sprint), rest inertia, anticipated recovery environment, suggestion bias, fatigue security blanket, common mistakes 8-10
  - `concepts/interval-design.md` — flexible threshold prescription, RPE management per workout type, substitution rule, outdoor precision tolerance, vibes-based VO2max
  - `concepts/endurance-base-training.md` — group rides as valid training, long ride frequency for ultra, diminishing returns on ultra-long rides
  - `concepts/ultra-endurance.md` — 6+ hr/month ride frequency, diminishing returns on extreme duration, training camp autoregulation
- **Pages created:** none
- **Key findings:** Autoregulation is a 25-75% spectrum, not binary; short FTP checks and sprints are near-zero-fatigue-cost readiness gauges; "anticipated recovery environment" should inform workout deployment; undercooking by 5-20% beats overcooking by 10%; 100% plan compliance is explicitly undesirable

## 2026-04-12 — Karpathy pattern completion

- **SCHEMA.md** created — defines page structure, evidence tags, cross-reference format, and 4 operations (ingest, query, lint, maintenance)
- **CLAUDE.md** created — project-level config referencing schema
- **Skills updated:** wko5-training, wko5-science, wko5-nutrition, wko5-analyzer — each points to SCHEMA.md (one-liner, not duplicated content)
- **Cross-reference pass:** 3 parallel agents adding `## Cross-References` sections to all 21 pages
- **Ingest pipeline:** `tools/wiki-ingest.md` — prompt template for new source ingestion
- **Lint workflow:** `tools/wiki-lint.md` — prompt template for periodic health checks
