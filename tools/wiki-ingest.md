# Wiki Ingest Prompt

Use this prompt to ingest a new source into the wiki. Pass the source path as an argument.

## Usage

```
claude -p "$(cat tools/wiki-ingest.md)" -- <source-path>
```

Or paste this prompt directly when you have a new source to ingest.

---

## Prompt

You are ingesting a new source into the cycling training science wiki. Follow the SCHEMA.md ingest workflow exactly.

**Schema:** Read `docs/research/wiki/SCHEMA.md` first for page structure, evidence tags, and cross-reference format.

**Source to ingest:** [provided as argument]

**Steps:**

1. Read the source fully.
2. Read `docs/research/wiki/index.md` to see existing pages.
3. Identify which wiki pages this source is relevant to (typically 3-8 pages).
4. For each relevant page:
   - Read the current page
   - Add new evidence to the appropriate section with [R]/[E]/[O] tags
   - Add the source to the Sources section
   - Update Cross-References if new connections emerge
5. If the source covers a topic with no existing page, create one following the SCHEMA.md template.
6. Update `docs/research/wiki/index.md` if new pages were created.
7. Append to `docs/research/wiki/log.md` with date, source, pages updated/created, key findings.
8. Run `qmd update` and `qmd embed` to re-index.

**Key principle:** One source should touch multiple pages. If you're only updating one page, you're probably missing connections.
