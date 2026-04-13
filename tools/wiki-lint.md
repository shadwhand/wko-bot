# Wiki Lint Prompt

Use this prompt to run a lint pass on the wiki. Should be run every ~10 ingests or monthly.

## Usage

```
claude -p "$(cat tools/wiki-lint.md)"
```

---

## Prompt

You are running a lint pass on the cycling training science wiki. Follow the SCHEMA.md lint workflow.

**Schema:** Read `docs/research/wiki/SCHEMA.md` first.

**Checks to perform:**

1. **Contradictions:** Read all wiki pages and identify claims that conflict across pages without acknowledgment. List each contradiction with file:line references.

2. **Orphans:** Compare files in `docs/research/wiki/` against entries in `index.md`. Flag any pages not listed.

3. **Missing cross-references:** For each page, check if its Cross-References section links to all obviously related pages. Flag pages with fewer than 3 cross-references.

4. **Evidence gaps:** Find claims tagged [O] (opinion) that could be upgraded to [E] or [R] using available sources in the knowledge base. Search qmd for supporting evidence.

5. **Coverage gaps:** Check if any topics referenced in cross-references or Platform Integration sections have no wiki page.

6. **Source coverage:** Sample 20 random TrainingPeaks articles from `docs/research/trainingpeaks/` and check if their key findings are represented in any wiki page. Report coverage percentage.

7. **Stale claims:** Flag any claims citing sources older than 5 years without a "still valid as of" note.

**Output:** Write findings to `docs/research/wiki/eval/lint-YYYY-MM-DD.md` and append summary to `docs/research/wiki/log.md`.

**Fix:** After reporting, fix all issues you can (add missing cross-refs, update index, resolve contradictions by adding Conflicts sections). Do not fix evidence upgrades — flag those for a dedicated ingest pass.
