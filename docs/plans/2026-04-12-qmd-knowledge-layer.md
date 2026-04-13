# QMD Knowledge Layer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate qmd as the platform's knowledge retrieval service — a compiled wiki over all research content, searchable via both MCP (Claude Code sessions) and HTTP API (Flask endpoints).

**Architecture:** Three-layer Karpathy-style knowledge system. Layer 1: raw sources (2,013 TP JSONs, EC transcripts, nutrition docs). Layer 2: LLM-compiled wiki with concept/entity pages, cross-references, and an index. Layer 3: qmd hybrid search (BM25 + vector + rerank) over both wiki and converted sources. The Flask API gains a `/api/knowledge` endpoint that queries qmd's HTTP daemon for contextual retrieval.

**Tech Stack:** qmd (Node.js, @tobilu/qmd), Python (conversion scripts, Flask integration), SQLite (qmd index), GGUF models (EmbeddingGemma 300M, Qwen3-Reranker 0.6B)

---

## Current State

| Asset | Location | Count | Format | Status |
|-------|----------|-------|--------|--------|
| Raw TP articles | `docs/research/raw/trainingpeaks/` | 2,013 | JSON (`url`, `title`, `author`, `real_author`, `content`, `content_clean`, `slug`) | Unconverted |
| Converted TP articles | `docs/research/trainingpeaks/` | 720 | Markdown with YAML frontmatter (`title`, `author`, `source`, `score`, `skills`, `relevance`) | Ready to index |
| EC master reference | `docs/research/empirical-cycling/ec-master-reference.md` | 1 | Compiled wiki (2,200+ lines, 8 sections, evidence-tagged) | Ready to index |
| EC episode insights | `docs/research/empirical-cycling/ep-*.md` | 7 | Episode batch extracts with claims, tables, platform hints | Ready to index |
| Nutrition research | `docs/research/nutrition-*.md` | 3 | Mixed (1 clean markdown, 2 JSON-wrapped) | Needs cleanup |
| Reports | `docs/reports/` | 4 | Generated analysis markdown | Ready to index |
| Flask API | `wko5/api/routes.py` | 41 endpoints | FastAPI with bearer auth, in-memory cache | No search capability |

## Target Architecture

```
docs/research/
├── raw/trainingpeaks/          # Layer 1: immutable raw sources (2,013 JSON)
├── trainingpeaks/              # Layer 1.5: converted markdown (720 existing + 1,293 new)
├── empirical-cycling/          # Layer 1.5: existing compiled content
├── nutrition-*.md              # Layer 1.5: existing research
├── wiki/                       # Layer 2: LLM-compiled knowledge (NEW)
│   ├── index.md                # Master catalog of all wiki pages
│   ├── log.md                  # Ingest log (append-only)
│   ├── concepts/               # Concept pages (FTP, durability, pacing, VO2max, etc.)
│   ├── entities/               # Entity pages (athletes, races, methods, tools)
│   └── nutrition/              # Nutrition knowledge pages
└── reports/                    # Existing generated reports

.qmd/                           # Layer 3: qmd index (NEW)
├── index.sqlite                # FTS5 + vector index
└── qmd.yml                     # Collection config

wko5/api/
├── routes.py                   # Existing endpoints + new /api/knowledge
└── knowledge.py                # NEW: qmd HTTP client wrapper
```

---

### Task 1: Install qmd and verify

**Files:**
- None (global install)

**Step 1: Install qmd globally**

```bash
npm install -g @tobilu/qmd
```

**Step 2: Verify installation**

```bash
qmd --version
qmd status
```

Expected: version number, empty index status.

**Step 3: Verify model download works**

```bash
qmd search "test" 2>&1 | head -5
```

Expected: empty results or model download progress (models auto-download on first use).

---

### Task 2: Convert remaining 1,293 TP articles (JSON -> Markdown)

**Files:**
- Create: `tools/convert_tp_articles.py`
- Read: `docs/research/raw/trainingpeaks/*.json`
- Write to: `docs/research/trainingpeaks/*.md`

**Step 1: Write the conversion script**

The script must:
1. Read each JSON from `raw/trainingpeaks/`
2. Check if corresponding `.md` already exists in `trainingpeaks/` — skip if so
3. Extract fields: `title`, `author` (prefer `real_author` over `author`), `url`, `content_clean` (fallback to `content`)
4. Strip HTML boilerplate from content (nav elements, category breadcrumbs, related articles)
5. Write markdown with YAML frontmatter matching existing format:

```markdown
---
title: "Article Title"
author: "Author Name"
source: "https://www.trainingpeaks.com/blog/slug/"
slug: "slug-name"
---

Article body content...
```

Note: existing converted articles have additional fields (`score`, `skills`, `relevance`, `trusted_author`) that were added by a triage pass. New conversions should omit these — they can be added by a later triage step if needed.

**Step 2: Run the conversion**

```bash
cd /Users/jshin/Documents/wko5-experiments
python tools/convert_tp_articles.py
```

Expected: ~1,293 new `.md` files created, ~720 skipped (already exist). Print summary.

**Step 3: Verify conversion count**

```bash
ls docs/research/trainingpeaks/*.md | wc -l
```

Expected: ~2,013 files.

**Step 4: Spot-check a converted file**

Read 2-3 newly converted files and verify frontmatter + content quality.

---

### Task 3: Clean up nutrition docs

**Files:**
- Modify: `docs/research/nutrition-racing.md`
- Modify: `docs/research/nutrition-ultra.md`

**Step 1: Inspect and fix nutrition-racing.md**

This file is JSON-wrapped (Claude conversation history). Extract the actual research content and rewrite as clean markdown.

**Step 2: Inspect and fix nutrition-ultra.md**

Same treatment — extract research content from JSON wrapper.

**Step 3: Verify all three nutrition files are clean markdown**

```bash
head -5 docs/research/nutrition-*.md
```

Expected: all three start with markdown headers or YAML frontmatter, no JSON.

---

### Task 4: Configure qmd collections and context

**Files:**
- Create: `.qmd/qmd.yml`

**Step 1: Create qmd config**

```yaml
global_context: >
  Cycling training science knowledge base for a coach+athlete analytics platform.
  Content covers power-based training, nutrition, pacing, durability, race strategy,
  and performance modeling. The athlete is an ultra-endurance cyclist.

collections:
  wiki:
    path: ./docs/research/wiki
    pattern: "**/*.md"
    context:
      "/": "LLM-compiled knowledge pages — synthesized concepts, entities, and cross-references"
      "/concepts": "Training science concepts: FTP, durability, pacing, VO2max, power-duration modeling"
      "/entities": "Athletes, races, methods, tools referenced across the research"
      "/nutrition": "Nutrition science: fueling, glycogen, hydration, race-day protocols"
    includeByDefault: true

  empirical-cycling:
    path: ./docs/research/empirical-cycling
    pattern: "**/*.md"
    ignore:
      - "eval/**"
    context:
      "/": "Empirical Cycling podcast insights — evidence-tagged claims from 53 episodes"
      "/ec-master-reference.md": "Master consolidated reference across all episodes"
    includeByDefault: true

  trainingpeaks:
    path: ./docs/research/trainingpeaks
    pattern: "**/*.md"
    context:
      "/": "TrainingPeaks blog articles on power analysis, training methodology, nutrition, and race strategy"
    includeByDefault: false

  nutrition:
    path: ./docs/research
    pattern: "nutrition-*.md"
    context:
      "/": "Deep research syntheses on cycling nutrition — modeling, racing, and ultra-endurance"
    includeByDefault: true

  reports:
    path: ./docs/reports
    pattern: "**/*.md"
    context:
      "/": "Generated training analysis reports — fitness status, race plans, training recommendations"
    includeByDefault: true

  code:
    path: ./wko5
    pattern: "**/*.py"
    ignore:
      - "**/__pycache__/**"
      - "mmp_cache/**"
    context:
      "/": "Python source code for the cycling analytics platform"
      "/api": "FastAPI endpoints and route handlers"
      "/stan": "Stan statistical models for Bayesian power-duration fitting"
    includeByDefault: false
```

Key design decisions:
- `wiki` and `empirical-cycling` are `includeByDefault: true` — these are the compiled knowledge, highest signal
- `trainingpeaks` is `includeByDefault: false` — 2,013 articles create noise; searched only when explicitly requested
- `code` is `includeByDefault: false` — useful for architecture questions but not training science queries
- `reports` is `includeByDefault: true` — recent analyses are highly relevant context

**Step 2: Initialize qmd with this config**

```bash
cd /Users/jshin/Documents/wko5-experiments
qmd --index .qmd/qmd.yml collection list
```

Expected: all 6 collections listed.

---

### Task 5: Compile the wiki (Layer 2)

This is the heaviest task. We compile 2,013 TP articles + EC insights + nutrition research into ~30-50 structured wiki pages.

**Files:**
- Create: `docs/research/wiki/index.md`
- Create: `docs/research/wiki/log.md`
- Create: `docs/research/wiki/concepts/*.md` (~15-20 pages)
- Create: `docs/research/wiki/entities/*.md` (~10-15 pages)
- Create: `docs/research/wiki/nutrition/*.md` (~5-8 pages)

**Step 1: Build article manifest**

Create a manifest of all 2,013+ articles: title, author, first 150 chars. This feeds the topic clustering step.

```bash
python -c "
import json, glob, os
manifest = []
for f in sorted(glob.glob('docs/research/trainingpeaks/*.md')):
    with open(f) as fh:
        lines = fh.readlines()
    title = next((l.split(':', 1)[1].strip().strip('\"') for l in lines if l.startswith('title:')), os.path.basename(f))
    # Get first non-frontmatter line
    body_start = next((i for i, l in enumerate(lines) if l.strip() == '---' and i > 0), 0) + 1
    body = ''.join(lines[body_start:body_start+3]).strip()[:150]
    manifest.append(f'{title} | {body}')
for m in manifest[:10]:
    print(m)
print(f'... {len(manifest)} total')
"
```

**Step 2: Topic clustering via parallel agents**

Dispatch agents to cluster articles into concept groups. Proposed wiki page structure:

**Concepts (docs/research/wiki/concepts/):**
- `ftp-threshold-testing.md` — FTP definitions, testing protocols, threshold training
- `power-duration-modeling.md` — PD curves, phenotyping, strengths/limiters
- `vo2max-training.md` — VO2max intervals, protocols, ceiling effects
- `durability-fatigue.md` — Durability science, degradation modeling, long-ride capacity
- `pacing-strategy.md` — Race pacing, negative splits, time trial strategy
- `training-periodization.md` — Base/build/peak/race phases, block periodization
- `training-load-recovery.md` — TSS/CTL/ATL/TSB, recovery protocols, overtraining
- `interval-design.md` — Interval structures, work/rest ratios, progression
- `endurance-base-training.md` — Zone 2 science, volume vs intensity, LT1
- `strength-conditioning.md` — Off-bike training, power-to-weight, injury prevention
- `heat-altitude-environment.md` — Environmental factors, acclimatization
- `mental-performance.md` — Psychology, motivation, race-day mindset
- `indoor-training.md` — Trainer protocols, ERG mode, virtual racing
- `ultra-endurance.md` — Ultra-distance specifics, pacing, sleep deprivation
- `equipment-technology.md` — Power meters, bike fit, aero testing

**Entities (docs/research/wiki/entities/):**
- `pro-race-analyses.md` — Tour de France, Vuelta, Giro power analyses compiled
- `ironman-triathlon.md` — IM power/pacing analyses
- `notable-coaches-methods.md` — Hunter Allen, Tim Cusick, Kolie Moore approaches
- `key-research-papers.md` — Cited studies and their findings
- `tools-platforms.md` — WKO, TrainingPeaks, Best Bike Split, Garmin integration

**Nutrition (docs/research/wiki/nutrition/):**
- `fueling-fundamentals.md` — CHO oxidation rates, glycogen, caloric needs
- `race-day-nutrition.md` — Pre/during/post nutrition, gut training
- `hydration-electrolytes.md` — Fluid intake, sodium, temperature effects
- `supplements-ergogenic.md` — Caffeine, creatine, beetroot, evidence base
- `ultra-nutrition.md` — Multi-hour fueling, real food vs gels, stomach issues

**Step 3: Compile wiki pages using parallel agents**

For each concept group, dispatch an agent that:
1. Reads the relevant TP articles (filtered by title/relevance match)
2. Reads relevant EC master reference sections
3. Reads relevant nutrition docs
4. Writes a compiled wiki page in the EC master reference style:
   - Evidence tags: [R] research, [E] experience, [O] opinion
   - Specific numbers in tables
   - Cross-references to source articles and episodes
   - "Platform Module" hints where applicable
   - Conflicts/caveats section

Each agent produces 1-3 wiki pages. Target: 8-12 parallel agents covering all topics.

**Step 4: Write index.md**

After all pages are compiled, generate the master index:

```markdown
# Wiki Index

Knowledge base compiled from 2,013 TrainingPeaks articles, 53 Empirical Cycling
podcast episodes, and nutrition research. Last compiled: 2026-04-12.

## Concepts
- [FTP & Threshold Testing](concepts/ftp-threshold-testing.md) — FTP definitions, protocols, threshold training
- [Power-Duration Modeling](concepts/power-duration-modeling.md) — PD curves, phenotyping, strengths/limiters
...

## Entities
- [Pro Race Analyses](entities/pro-race-analyses.md) — Compiled power data from grand tours and classics
...

## Nutrition
- [Fueling Fundamentals](nutrition/fueling-fundamentals.md) — CHO oxidation, glycogen, caloric needs
...
```

**Step 5: Write log.md**

```markdown
# Ingest Log

## 2026-04-12 — Initial compilation
- Sources: 2,013 TP articles, 53 EC episodes (master ref + 7 batch extracts), 3 nutrition docs
- Pages created: ~30-50
- Compiled by: Claude Code parallel agent pipeline
```

**Step 6: Commit the wiki**

```bash
git add docs/research/wiki/
git commit -m "feat: compile knowledge wiki from 2,013 TP articles + EC + nutrition research"
```

---

### Task 6: Index and embed with qmd

**Files:**
- Uses: `.qmd/qmd.yml`
- Creates: `.qmd/index.sqlite`

**Step 1: Run initial index**

```bash
cd /Users/jshin/Documents/wko5-experiments
qmd --index .qmd/qmd.yml index
```

Expected: all collections indexed, document count reported.

**Step 2: Generate embeddings**

```bash
qmd --index .qmd/qmd.yml embed
```

Expected: model download (~2GB total for EmbeddingGemma + Qwen3-Reranker), then embedding generation. This will take several minutes for 2,000+ documents.

**Step 3: Verify search works**

```bash
# Lexical
qmd --index .qmd/qmd.yml search "FTP threshold testing"

# Semantic
qmd --index .qmd/qmd.yml vsearch "how to pace a 5 hour ride"

# Hybrid (best quality)
qmd --index .qmd/qmd.yml query "What interval protocol best develops VO2max for a cyclist with high FTP but low ceiling?"
```

Expected: relevant results from wiki (top) and source collections.

**Step 4: Add .qmd/index.sqlite to .gitignore**

```bash
echo ".qmd/index.sqlite" >> .gitignore
```

The SQLite index is derived data — regenerable from `qmd index && qmd embed`. The config `.qmd/qmd.yml` IS tracked.

---

### Task 7: Configure MCP server for Claude Code

**Files:**
- Modify: `~/.claude/settings.json` (or project-level `.claude/settings.json`)

**Step 1: Add qmd MCP server config**

Add to the project's Claude Code MCP settings:

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp", "--index", "/Users/jshin/Documents/wko5-experiments/.qmd/qmd.yml"]
    }
  }
}
```

**Step 2: Verify MCP tools appear in Claude Code**

Restart Claude Code session and verify `qmd` MCP tools are available (query, get, multi_get, status).

**Step 3: Test a query through MCP**

Use the qmd query tool to search "durability fatigue modeling" — should return wiki and EC pages.

---

### Task 8: Build Python HTTP client for Flask integration

**Files:**
- Create: `wko5/knowledge.py`
- Test: `tests/test_knowledge.py`

**Step 1: Write failing test for knowledge client**

```python
# tests/test_knowledge.py
import pytest
from unittest.mock import patch, MagicMock
from wko5.knowledge import KnowledgeClient

def test_search_returns_results():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"content": [{"text": "...results..."}]}}

    with patch("httpx.post", return_value=mock_response) as mock_post:
        client = KnowledgeClient(base_url="http://localhost:8181")
        results = client.search("FTP testing protocols")
        assert results is not None
        mock_post.assert_called_once()

def test_search_with_collection_filter():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"content": [{"text": "..."}]}}

    with patch("httpx.post", return_value=mock_response) as mock_post:
        client = KnowledgeClient(base_url="http://localhost:8181")
        results = client.search("glycogen depletion", collections=["nutrition", "wiki"])
        assert results is not None

def test_search_handles_unavailable_service():
    with patch("httpx.post", side_effect=Exception("Connection refused")):
        client = KnowledgeClient(base_url="http://localhost:8181")
        results = client.search("anything")
        assert results is None  # Graceful degradation, not crash
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_knowledge.py -v
```

Expected: ImportError (module doesn't exist yet).

**Step 3: Implement knowledge client**

```python
# wko5/knowledge.py
"""Thin HTTP client for qmd knowledge service."""

import httpx
import json
import logging

log = logging.getLogger(__name__)

class KnowledgeClient:
    """Queries qmd's MCP-over-HTTP endpoint."""

    def __init__(self, base_url: str = "http://localhost:8181"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"

    def _call(self, method: str, params: dict) -> dict | None:
        """Send an MCP tools/call request."""
        try:
            resp = httpx.post(self.mcp_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": method,
                    "arguments": params,
                },
            }, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            log.warning("qmd unavailable: %s", e)
            return None

    def search(self, query: str, collections: list[str] | None = None,
               limit: int = 10, min_score: float = 0.3) -> dict | None:
        """Hybrid search across knowledge base."""
        params = {
            "searches": [
                {"type": "lex", "query": query},
                {"type": "vec", "query": query},
            ],
            "limit": limit,
            "minScore": min_score,
            "rerank": True,
        }
        if collections:
            params["collections"] = collections
        return self._call("query", params)

    def get_document(self, path: str) -> dict | None:
        """Retrieve a specific document by path."""
        return self._call("get", {"path": path})

    def health(self) -> bool:
        """Check if qmd service is running."""
        try:
            resp = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_knowledge.py -v
```

Expected: all 3 tests pass.

**Step 5: Commit**

```bash
git add wko5/knowledge.py tests/test_knowledge.py
git commit -m "feat: add qmd knowledge client for platform search integration"
```

---

### Task 9: Add /api/knowledge endpoint to Flask

**Files:**
- Modify: `wko5/api/routes.py`
- Test: `tests/test_knowledge.py` (add integration test)

**Step 1: Write failing test for the endpoint**

```python
# Add to tests/test_knowledge.py

def test_knowledge_endpoint(client):
    """Test /api/knowledge returns search results."""
    # This test requires the FastAPI test client fixture from conftest
    response = client.get("/api/knowledge?q=FTP+testing")
    assert response.status_code in (200, 503)  # 503 if qmd not running
```

**Step 2: Add the endpoint to routes.py**

Add to `wko5/api/routes.py`:

```python
from wko5.knowledge import KnowledgeClient

_knowledge = KnowledgeClient()

@router.get("/knowledge")
async def knowledge_search(q: str, collections: str | None = None,
                           limit: int = 10, token=Depends(verify_token)):
    """Search the knowledge base for relevant training science context."""
    colls = collections.split(",") if collections else None
    result = _knowledge.search(q, collections=colls, limit=limit)
    if result is None:
        raise HTTPException(503, "Knowledge service unavailable")
    return result
```

**Step 3: Run test**

```bash
pytest tests/test_knowledge.py -v
```

**Step 4: Commit**

```bash
git add wko5/api/routes.py tests/test_knowledge.py
git commit -m "feat: add /api/knowledge endpoint for training science search"
```

---

### Task 10: Start qmd HTTP daemon and verify end-to-end

**Step 1: Start qmd daemon**

```bash
qmd --index /Users/jshin/Documents/wko5-experiments/.qmd/qmd.yml mcp --http --daemon
```

Expected: daemon starts, PID written to `~/.cache/qmd/mcp.pid`.

**Step 2: Verify health**

```bash
curl http://localhost:8181/health
```

Expected: `{"status":"ok","uptime":...}`

**Step 3: Test MCP query via HTTP**

```bash
curl -X POST http://localhost:8181/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"query","arguments":{"searches":[{"type":"lex","query":"durability fatigue"}],"limit":5}}}'
```

Expected: search results from wiki + EC collections.

**Step 4: Test via Flask endpoint**

```bash
# Start Flask API if not running, then:
curl "http://localhost:8000/api/knowledge?q=pacing+strategy+for+ultra+ride" \
  -H "Authorization: Bearer <token>"
```

Expected: relevant results from wiki, nutrition, and EC collections.

**Step 5: Add daemon startup to launch script**

Check if there's an existing launch script (referenced in git log: `.runtime.json config coordination + launcher script`). Add qmd daemon startup alongside the Flask server.

---

## Execution Order

```
Task 1: Install qmd                          [5 min]
Task 2: Convert remaining TP articles        [10 min]  
Task 3: Clean nutrition docs                 [5 min]
  ↓ (Tasks 2+3 can run in parallel)
Task 4: Configure qmd collections            [5 min]
Task 5: Compile wiki (HEAVY — parallel agents) [30-45 min]
Task 6: Index and embed                      [10-15 min, mostly waiting]
  ↓ (Tasks 7+8 can start during Task 6)
Task 7: Configure MCP                        [5 min]
Task 8: Python HTTP client                   [10 min]
Task 9: /api/knowledge endpoint              [10 min]
Task 10: End-to-end verification             [10 min]
```

## Post-Completion

- Future content (new TP scrapes, EC episodes) follows the same pipeline: raw → convert → compile wiki pages → `qmd update && qmd embed`
- The `qmd context add` command can be used to refine context annotations as we learn which searches work best
- Wiki pages should be periodically re-compiled as new sources accumulate (lint pass to find gaps)
