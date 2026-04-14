# Wiki Schema

Defines structure, naming conventions, page templates, and operational workflows for the cycling training science knowledge base.

Co-evolved by human and LLM. Last updated: 2026-04-12.

---

## Directory Structure

```
docs/research/wiki/
  SCHEMA.md          # This file — the governing document
  index.md           # Master catalog of all pages (auto-generated)
  log.md             # Append-only record of every ingest, lint, and maintenance action
  concepts/          # Training science concepts (one page per topic)
  entities/          # Athletes, races, coaches, tools, methods
  nutrition/         # Nutrition science (fueling, hydration, supplements)
```

## Naming Conventions

- **Files:** lowercase, hyphen-separated, descriptive. `ftp-threshold-testing.md`, not `ftp.md`.
- **Concepts:** named for the training concept. `durability-fatigue.md`, `vo2max-training.md`.
- **Entities:** named for the entity type. `pro-race-analyses.md`, `notable-coaches-methods.md`.
- **Nutrition:** named for the nutrition topic. `fueling-fundamentals.md`, `ultra-nutrition.md`.

## Page Template

Every wiki page must follow this structure:

```markdown
# Page Title

One-paragraph summary of what this page covers and why it matters to the platform.

Evidence levels: **[R]** = Research-backed, **[E]** = Experience-based, **[O]** = Opinion.

---

## Key Principles
- **Claim** — explanation [evidence tag] (source: episode ID, article slug, or paper)

## Specific Numbers & Thresholds
| Metric | Value | Source |
|--------|-------|--------|

## [Topic-specific sections]
(Varies by page — protocols, methods, comparisons, etc.)

## Common Mistakes
1. Numbered list with evidence tags

## Platform Integration
- Module mapping: which `wko5/*.py` files use this knowledge
- How the platform should apply these findings

## Cross-References
- [[Related page]](../category/related-page.md) — one-line description of relationship
- [[Another page]](../category/another.md) — why these connect

## Sources
- EC episodes: TMT-XX, WD-XX, Persp-XX
- TP articles: article-slug.md
- Papers: Author et al. YYYY

## Conflicts & Caveats
- Where sources disagree or findings are uncertain
- Conventional wisdom vs evidence-based position
```

## Evidence Tags

Every claim must be tagged:

| Tag | Meaning | Standard |
|-----|---------|----------|
| **[R]** | Research-backed | Peer-reviewed paper or systematic review |
| **[E]** | Experience-based | Expert coach/practitioner with track record |
| **[O]** | Opinion | Plausible but unvalidated; flag as such |

When sources conflict, present both positions with their evidence tags. Do not silently pick one.

## Cross-Reference Format

Use relative markdown links between wiki pages:

```markdown
See also: [Durability & Fatigue](../concepts/durability-fatigue.md) — durability degrades pacing targets over time
```

Every page must have a `## Cross-References` section listing all related pages with a one-line description of the relationship.

---

## Operations

**Universal rule: every operation that modifies wiki pages MUST end with re-indexing.**

```bash
qmd update && qmd embed
```

This is non-negotiable. The wiki is only as good as its index. If pages are updated but not re-indexed, qmd search returns stale results. Run this after every ingest, file-back, lint fix, or maintenance change.

### 1. Ingest

**When:** A new source arrives (podcast episode, TP article, research paper, scraped doc).

**Process:**
1. Add raw source to `docs/research/raw/` (immutable, never modified)
2. Convert to markdown in appropriate collection dir (e.g., `docs/research/trainingpeaks/`)
3. Read the new source fully
4. Identify which wiki pages it's relevant to (typically 3-8 pages per source)
5. For each relevant page:
   - Add new evidence to the appropriate section
   - Tag with [R]/[E]/[O]
   - Add source to the Sources section
   - Update cross-references if new connections emerge
6. If the source covers a topic with no existing page, create a new page following the template
7. Update `index.md` if new pages were created
8. Append to `log.md`:
   ```
   ## YYYY-MM-DD — Ingest: [source title]
   - Source: [path or URL]
   - Pages updated: [list]
   - Pages created: [list, if any]
   - Key findings: [1-2 sentence summary of what was new]
   ```
9. Run `qmd update && qmd embed` to re-index

**Key principle:** One source should touch multiple pages. If you're only updating one page, you're probably missing connections.

### 2. Query → File Back

**When:** A question is asked that the wiki should be able to answer.

**Retrieval flow:**
1. **Read `index.md` first** — scan the catalog to identify which pages likely answer the question. At small scale (~50 pages) this is sufficient.
2. **If ambiguous, use qmd** — `qmd query "the question" -c wiki` to search wiki pages specifically. qmd is the scaling layer over the wiki, not a replacement for navigating it.
3. **Read the relevant wiki pages** and synthesize an answer with citations.

**File-back flow (the wiki compounds here):**

After answering, ask: "Did this query reveal connections, patterns, or applications not captured in existing pages?" If yes:

4. **Identify file-back targets** — which wiki pages should be updated with the new connection? Typical triggers:
   - A concept page's content applies to a use case not mentioned on that page
   - Two pages contain related findings that aren't cross-referenced
   - A recently ingested source has implications for a topic not covered during ingest
   - A practical application (race plan, training block) synthesizes multiple pages in a new way

5. **Update each target page:**
   - Add the new finding to the appropriate section with evidence tags
   - Cite the original source (episode ID, article) not the query
   - Add cross-references if the connection links pages not yet linked

6. **If the query produced a valuable output** (race plan, training analysis, coaching recommendation), save it to `docs/reports/` — these become searchable context for future queries.

7. **Append to `log.md`:**
   ```
   ## YYYY-MM-DD — Query→File back: [query topic]
   - Query: [one-line summary]
   - Connections found: [what was new]
   - Pages updated: [list]
   - Report created: [path, if applicable]
   ```

8. Run `qmd update && qmd embed` to re-index.

**Key principles:**
- Every valuable query should make the wiki slightly better. The wiki compounds.
- File back the *connection*, not the answer. The wiki stores knowledge; reports store applications.
- Search the *wiki*, not the raw sources. The wiki is the compiled knowledge. Raw sources are for ingest.
- Use `index.md` as the primary entry point. Use qmd when the wiki outgrows what the index can navigate (~100+ pages).
- The more queries that file back, the better the wiki gets at answering future queries. This is the compounding loop.

### 3. Lint

**When:** Periodically (every ~10 ingests or monthly, whichever comes first).

**Process:**
1. **Contradictions:** Scan for claims in different pages that conflict without acknowledgment
2. **Orphans:** Pages not listed in `index.md`
3. **Stale claims:** Claims citing sources that have been superseded by newer evidence
4. **Missing cross-references:** Pages that discuss related topics but don't link to each other
5. **Coverage gaps:** Topics referenced in cross-references or platform modules that have no wiki page
6. **Evidence gaps:** Claims tagged [O] that could be upgraded to [E] or [R] with available sources
7. **Source coverage:** Sources in `docs/research/` not referenced by any wiki page

Report findings and fix issues. Append to `log.md`:
```
## YYYY-MM-DD — Lint pass
- Contradictions found: N (fixed: M)
- Orphan pages: N
- Missing cross-refs added: N
- Coverage gaps identified: [list]
- Evidence upgrades: N claims upgraded
```

8. Run `qmd update && qmd embed` to re-index.

### 4. Maintenance

**Structural changes:**
- Adding a new category (beyond concepts/entities/nutrition) requires updating this schema
- Merging or splitting pages: update index.md, redirect cross-references, log the change
- Renaming pages: update all cross-references that point to the old name

**Quality standards:**
- No page should exceed ~600 lines. Split if growing too large.
- Every page must have at least 3 cross-references to other wiki pages.
- Every claim must have an evidence tag and a source.
- The Sources section must be comprehensive — no uncited claims.

**After any maintenance change:** Run `qmd update && qmd embed` to re-index.

---

## Source Collections

| Collection | Path | Content | Index Default |
|------------|------|---------|---------------|
| wiki | `docs/research/wiki/` | Compiled knowledge pages | Included |
| empirical-cycling | `docs/research/empirical-cycling/` | EC podcast insights (53 eps) | Included |
| trainingpeaks | `docs/research/trainingpeaks/` | 2,012 TP blog articles | Excluded (opt-in) |
| nutrition | `docs/research/nutrition-*.md` | 3 deep nutrition syntheses | Included |
| reports | `docs/reports/` | Generated analysis reports | Included |
| code | `wko5/` | Python platform source | Excluded (opt-in) |

## Platform Module Mapping

Wiki pages should reference which platform modules they inform:

| Module | Wiki Pages |
|--------|------------|
| `pdcurve.py` | power-duration-modeling, ftp-threshold-testing |
| `durability.py` | durability-fatigue, pacing-strategy |
| `pacing.py` | pacing-strategy, durability-fatigue, ultra-endurance |
| `physics.py` | pacing-strategy |
| `segments.py` | pacing-strategy, ultra-endurance |
| `training_load.py` | training-load-recovery, training-periodization |
| `zones.py` | endurance-base-training, interval-design |
| `gap_analysis.py` | power-duration-modeling, durability-fatigue |
| `nutrition_engine.py` | fueling-fundamentals, race-day-nutrition, ultra-nutrition |
| `knowledge.py` | All (search interface) |
