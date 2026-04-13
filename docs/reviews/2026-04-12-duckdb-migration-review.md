# DuckDB Migration Spec -- Consolidated Review

**Document:** `docs/plans/2026-04-12-duckdb-migration.md`
**Reviewers:** Principal Engineer (PE), Product Designer (PD), Security Engineer (SE)
**Date:** 2026-04-12

---

## Cross-Review Consensus

Issues independently identified by 2+ reviewers, ordered by severity.

### 1. `cursor.lastrowid` replacement with `MAX(rowid)` is unsafe (PE, PD, SE)

All three reviewers flagged this. The plan proposes `MAX(rowid)` in one place and `currval('activities_id_seq')` in another -- both are wrong for DuckDB. `MAX(rowid)` has a race condition (even with single-writer, in-flight concurrent reads or a crash between INSERT and MAX create an integrity gap). DuckDB sequences don't use that syntax.

**Correct fix:** `INSERT INTO ... RETURNING id`. All 7 sites need this:
- `wko5/strava_sync.py:294`
- `wko5/garmin_sync.py:192`
- `wko5/garmin_mcp_sync.py:200`
- `wko5/ingest_missing.py:124`
- `wko5/rwgps.py:91`
- `wko5/routes.py:202` (save_route)
- `wko5/routes.py:563` (save_ride_plan)

### 2. Three files completely missing from the plan (PE, PD)

The plan lists ~10 files to modify but omits three files that directly `import sqlite3` and hardcode `cycling_power.db`:
- `wko5/backfill_altitude.py` -- uses `sqlite3.connect(DB_PATH)` directly (line 23)
- `wko5/garmin_mcp_sync.py` -- uses `sqlite3.connect(DB_PATH)` directly (line 253)
- `wko5/migrate_to_parquet.py` -- uses `sqlite3.connect(DB_PATH)` directly (line 156)

These bypass `get_connection()` entirely, so updating `db.py` alone does not catch them.

### 3. DuckDB single-writer constraint is under-addressed (PE, PD, SE)

The plan says "close connections promptly" -- this is insufficient. FastAPI server holds a connection while sync scripts also need write access. SQLite WAL mode allows concurrent readers + single writer; DuckDB is stricter (one process with write access at a time, period).

PE recommends a connection context manager in `db.py`. PD recommends a lock file or guard. Both approaches are needed: a context manager for the common case, and user-facing documentation that sync scripts and the API server cannot run simultaneously.

### 4. `conn.commit()` semantics differ -- autocommit risk (PE, PD)

DuckDB autocommits by default. The 22 `conn.commit()` calls across the codebase will silently become no-ops, which is fine when they happen after a single INSERT -- but the sync scripts (strava, garmin, garmin_mcp, ingest_missing) do multi-table inserts (activity + records + laps) that should be atomic. Without explicit `BEGIN TRANSACTION`, a crash between inserting the activity row and inserting records/laps leaves an orphaned activity.

**Verified 22 commit sites** in: `routes.py` (4), `garmin_sync.py` (1), `backfill_altitude.py` (1), `bayesian.py` (1), `ingest_missing.py` (1), `pdcurve.py` (2), `config.py` (2), `blocks.py` (1), `migrate_to_parquet.py` (1), `ftp_test.py` (1), `garmin_mcp_sync.py` (1), `rwgps.py` (1), `strava_sync.py` (1), `tp_ingest.py` (2), `training_load.py` (2).

### 5. `AUTOINCREMENT` keyword does not exist in DuckDB (PE, PD implied)

6 DDL sites use `INTEGER PRIMARY KEY AUTOINCREMENT`:
- `wko5/routes.py` lines 29, 41, 52 (routes, route_points, ride_plans)
- `wko5/tp_ingest.py` line 16 (tp_workouts)
- `wko5/ftp_test.py` line 21 (ftp_tests)
- `wko5/blocks.py` line 18 (training_phases)

DuckDB equivalent: use a `SEQUENCE` or simply omit `AUTOINCREMENT` and rely on `DEFAULT nextval('seq_name')`.

### 6. `executescript()` is SQLite-specific (PD, PE implied)

`wko5/routes.py:81` calls `conn.executescript(ROUTES_DDL)` -- this is a `sqlite3` method that does not exist in DuckDB. The multi-statement DDL string must be split and executed as individual statements or use DuckDB's `execute()` which handles semicolons differently.

### 7. No backup step before migration (PE, SE)

No `cp` or `sqlite3 .backup` command before the migration script runs. A bug in the migration script corrupts the source while the target is incomplete.

### 8. No partial-migration recovery (PD, SE)

If the migration script is killed mid-step-2 (during Parquet import at file 800 of 1700), there is no way to resume. The partial `.duckdb` file must be deleted and the process restarted from zero. SE additionally notes there is no transaction wrapping in the migration script itself.

---

## Conflicts & Disagreements

### 1. INSERT OR REPLACE behavior -- disagreement on severity

PE flags it as a behavioral difference (4 sites). The actual DuckDB docs confirm `INSERT OR REPLACE` is supported but creates a new row rather than updating in-place. For the 4 sites (`routes.py` x2, `bayesian.py`, `training_load.py`), all use compound primary keys -- behavior difference is subtle but exists when there are foreign key references. PE rates this as requiring attention; PD and SE do not mention it.

**Resolution:** PE is correct. The 4 sites should be audited. For `activity_routes` (composite PK), current behavior is fine. For `posterior_samples` and `tss_cache`, the INSERT OR REPLACE pattern is safe because these tables have no inbound foreign keys.

### 2. Migration atomicity -- PE says steps 4-9 must be ONE commit; PD says checkpointing needed

PE argues all code changes should land as a single atomic git commit to prevent a state where `db.py` expects DuckDB but sync scripts still use SQLite. PD argues the Parquet import loop needs checkpointing for crash recovery.

**Resolution:** Both are right about different things. The *code changes* (steps 4-9) should be one commit. The *data migration script* (step 2) should have checkpointing. These are independent concerns.

### 3. File scope -- PE says ~23 files, plan says ~10

PE's count of ~23 is more accurate. The plan's "Files Changed" section explicitly names 9 categories but several are underspecified (section 8 "All files using pd.read_sql_query" and section 9 "cursor.execute" are hand-waved). Additionally missing: `migrate_to_parquet.py`, `backfill_altitude.py`, `garmin_mcp_sync.py`, Rust extension (`frechet-rs/src/lib.rs` which hardcodes `cycling_power.db` on line 176), `tools/backfill-altitude/src/main.rs` (line 13), `setup.sh` (line 51), `test_db.py` (line 14), `README.md` (lines 82, 156), `.gitignore`.

---

## Prioritized Action List

### P0 -- Blocks implementation (must fix before any code is written)

| # | Issue | Source | Action |
|---|-------|--------|--------|
| P0.1 | RWGPS API key + auth token hardcoded on public GitHub | SE-C1 | **Rotate immediately.** Remove from `rwgps.py:15-16`, require env vars, add to `.env.example`. This is independent of the DuckDB migration. |
| P0.2 | Complete file inventory | PE, PD | Update plan to list ALL files: 8 Python files with `import sqlite3`, 7 with `lastrowid`, 6 with `AUTOINCREMENT` DDL, 1 with `executescript()`, 2 Rust files with hardcoded DB path, `setup.sh`, `test_db.py`, `README.md`, `.gitignore`. |
| P0.3 | RETURNING clause instead of MAX(rowid) | PE, PD, SE | Replace all 7 `lastrowid` sites with `INSERT ... RETURNING id` pattern. |
| P0.4 | AUTOINCREMENT removal | PE | Replace 6 DDL sites with DuckDB-compatible auto-increment (sequences or generated columns). |
| P0.5 | executescript() replacement | PD | Split `ROUTES_DDL` multi-statement string in `routes.py:81` and execute individually. |
| P0.6 | Transaction wrapping for multi-table inserts | PE, PD | Add explicit `BEGIN TRANSACTION` / `COMMIT` to `ingest_activity()`, `ingest_fit_bytes()`, `ingest_fit_parquet()`, `ingest_file()` in the 4 sync/ingest files. |
| P0.7 | Backup step in migration script | PE, SE | Add `shutil.copy2()` of SQLite DB before migration begins. |

### P1 -- Before production use (first week)

| # | Issue | Source | Action |
|---|-------|--------|--------|
| P1.1 | Connection context manager | PE | Add `def get_connection()` as a context manager (or separate `@contextmanager` wrapper) in `db.py` with try/finally close. |
| P1.2 | DuckDB single-writer guard | PE, PD | Either (a) use read-only connections for the API server with `duckdb.connect(DB_PATH, read_only=True)` where possible, or (b) document mutual exclusivity, or (c) add a file-lock wrapper. |
| P1.3 | SQL injection in migration script | SE-H1 | The `read_parquet('{first}')` f-string interpolates file paths into SQL. Use parameterized queries or validate paths. |
| P1.4 | SQL injection in config.py | SE-H2 | `set_config()` line 103: `f"UPDATE athlete_config SET {key} = ?"` -- `key` comes from user input (validated against DEFAULTS dict, so exploitability is low, but fix to parameterize or whitelist explicitly). |
| P1.5 | DuckDB file permissions | SE-H3 | Set `os.chmod(DUCKDB_PATH, 0o600)` after creation. File contains GPS location history and physiological data. |
| P1.6 | .gitignore glob for DuckDB | SE-H4 | Use `wko5/cycling_power.duckdb*` to catch `.wal`, `.tmp`, and any other DuckDB sidecar files. |
| P1.7 | `duckdb` in pip install | PD | Add `duckdb` to `setup.sh` line 19 pip install list. |
| P1.8 | test_db.py assertion fix | PD | `test_db.py:14` asserts `"cycling_power.db" in DB_PATH` -- must update to `.duckdb`. |
| P1.9 | setup.sh print string | PD | Line 51 prints `cycling_power.db` -- update to `.duckdb`. |
| P1.10 | Explicit type definitions in migration DDL | PE | Don't use `CREATE TABLE AS SELECT` (which infers types from SQLite's dynamic typing). Write explicit DDL with proper DuckDB column types, then `INSERT INTO ... SELECT`. |
| P1.11 | Parquet import checkpointing | PD | Add checkpoint every N files (e.g., 100) with a progress marker, so a crash at file 1500 resumes from the last checkpoint instead of restarting. |
| P1.12 | Migration PASS/FAIL verdict | PD | Add a final verification step that prints explicit PASS or FAIL based on row count comparison. |

### P2 -- Before v2 / before sharing via GitHub

| # | Issue | Source | Action |
|---|-------|--------|--------|
| P2.1 | Dependency pinning for duckdb | SE-M5 | Pin `duckdb>=1.1,<2.0` (or exact version) in requirements. |
| P2.2 | Rollback procedure documentation | PD | Document: "If migration fails, delete .duckdb, your SQLite DB is untouched." |
| P2.3 | SQLite-or-DuckDB diagnostic | PD | Add a `/health` or CLI check that reports which storage backend is active. |
| P2.4 | Pre-migration detection for git pull users | PD | If code expects DuckDB but only SQLite exists, print actionable error (not silent failure). |
| P2.5 | Strava/Garmin token dirs in .gitignore | SE-L1 | Add `~/.strava_tokens/` and `~/.garth/` patterns defensively (already outside repo, but belt-and-suspenders). |
| P2.6 | Frechet Rust extension DB path | PE (verified) | `tools/frechet-rs/src/lib.rs:176` hardcodes `cycling_power.db`. Must update to `.duckdb` or make configurable. Same for `tools/backfill-altitude/src/main.rs:13`. |
| P2.7 | INSERT OR REPLACE audit | PE | Verify behavior at 4 sites: `routes.py` (2), `bayesian.py` (1), `training_load.py` (1). |
| P2.8 | README.md references | -- | Lines 82, 156 reference `cycling_power.db`. |

### P3 -- Defer

| # | Issue | Source | Action |
|---|-------|--------|--------|
| P3.1 | MMP cache import | PE | Can be deferred -- rebuild on first access. The migration script can skip step 3 entirely. |
| P3.2 | GPS data consolidation risk | SE-M4 | All location history in one file vs 1700. Accepted risk for single-user local tool; document in threat model if sharing. |
| P3.3 | Dynamic DDL generation from DEFAULTS dict | SE-L3 | Pre-existing issue in `config.py`. Not migration-specific. |
| P3.4 | try/finally on migration connection | SE-L2 | Nice-to-have cleanup, not blocking. |

---

## Open Questions

1. **Frechet Rust extension:** `frechet_rs.find_matching_activities()` takes a `db_path` parameter and presumably opens it as SQLite internally. Does the Rust code use SQLite bindings? If so, this function must be updated to read from DuckDB or have its DB access pattern changed. What is the Rust-side implementation?

2. **Single-writer in practice:** How often do you actually run sync scripts while the FastAPI server is up? If the answer is "never concurrently," a documented constraint is sufficient. If sync runs on a cron or timer, you need a real locking mechanism.

3. **pd.read_sql_query migration scope:** The plan lists many files under section 8, but `wko5/ride.py:125` and `wko5/tp_ingest.py:202,246` also use `pd.read_sql_query`. Were these intentionally omitted or just missed?

4. **Parquet records schema consistency:** Do all 1700 Parquet files have identical column sets? If some early files lack `elapsed_seconds` or have extra columns, `CREATE TABLE AS SELECT * FROM read_parquet(first_file)` will set the schema from one file and subsequent inserts may fail on schema mismatch.

5. **DuckDB version target:** DuckDB is pre-1.0 in some feature areas and has had breaking changes between minor versions. What version are you targeting, and should it be pinned?

6. **`datetime('now')` in DDL defaults:** Three tables use `DEFAULT (datetime('now'))` -- is this syntax supported in DuckDB? DuckDB uses `DEFAULT current_timestamp` instead.

---

## Scope Reduction Opportunities

1. **Drop MMP cache migration entirely (P3.1).** The MMP cache is a performance optimization that can be rebuilt on-demand. Skip step 3 of the migration script, saving ~30% of migration complexity and the entire MMP Parquet import loop.

2. **Defer `backfill_altitude.py` and `migrate_to_parquet.py`.** These are one-time utility scripts that have already run. They could be left as-is (pointing at the now-gone SQLite DB) with a comment noting they are pre-migration artifacts. They only need updating if you plan to run them again.

3. **Defer Rust extension updates.** If `frechet_rs` reads from SQLite directly, updating it requires Rust changes + recompilation. The Python fallback path works. Defer the Rust update and disable `frechet_rs` during migration. Add a TODO.

4. **Batch the pd.read_sql_query changes.** These are all mechanical `pd.read_sql_query(sql, conn, params=x)` to `conn.execute(sql, list(x)).df()` transformations. They can be done with a single search-and-replace agent dispatch.

---

## Implementation Cost Estimate

### Files to Modify

| Category | Files | Estimated Changes |
|----------|-------|-------------------|
| Core data layer | `db.py`, `config.py` | 2 files, ~40 lines each |
| Sync scripts | `garmin_sync.py`, `strava_sync.py`, `garmin_mcp_sync.py`, `ingest_missing.py` | 4 files, ~20 lines each (import, DB_PATH, lastrowid, commit) |
| DDL owners | `routes.py`, `blocks.py`, `ftp_test.py`, `tp_ingest.py` | 4 files: AUTOINCREMENT removal + executescript fix |
| Query consumers | `ride.py`, `training_load.py`, `pdcurve.py`, `bayesian.py`, `rwgps.py`, `gap_analysis.py` | 6 files, ~5 lines each (pd.read_sql_query swap) |
| API layer | `wko5/api/routes.py` | 1 file, mostly inherits from db.py changes |
| Utility scripts | `backfill_altitude.py`, `migrate_to_parquet.py` | 2 files (defer or update) |
| Migration script | `tools/migrate_to_duckdb.py` (new) | 1 file, ~120 lines (with backup, checkpointing, verification) |
| Tests | `test_db.py`, `conftest.py` | 2 files |
| Infra/config | `.gitignore`, `setup.sh`, `README.md` | 3 files |
| Rust extensions | `frechet-rs/src/lib.rs`, `backfill-altitude/src/main.rs` | 2 files (defer recommended) |

**Total: ~27 files, ~350-400 lines of changes.**

### Agent Dispatch Strategy

| Dispatch | Scope | Risk |
|----------|-------|------|
| Agent 1 | Migration script (new file): backup, SQLite attach, Parquet import with checkpointing, verification, file permissions | Medium -- needs testing against real data |
| Agent 2 | Core layer (`db.py`, `config.py`): connection manager, DuckDB swap, autocommit handling | High -- everything depends on this |
| Agent 3 | DDL updates (`routes.py`, `blocks.py`, `ftp_test.py`, `tp_ingest.py`): AUTOINCREMENT removal, executescript fix, RETURNING clause | Medium -- mechanical but 6 DDL sites + 2 lastrowid sites |
| Agent 4 | Sync scripts (`garmin_sync.py`, `strava_sync.py`, `garmin_mcp_sync.py`, `ingest_missing.py`): import swap, DB_PATH, lastrowid, transaction wrapping | Medium -- 4 files with near-identical patterns |
| Agent 5 | Query consumers (6 files): `pd.read_sql_query` to `.execute().df()` | Low -- mechanical transformation |
| Agent 6 | Tests + infra (`.gitignore`, `setup.sh`, `test_db.py`, `README.md`) | Low |

**Recommended sequence:** Agent 1 (migration script, can be written and tested independently) in parallel with Agent 2 (core layer). Then Agents 3+4 in parallel (both depend on Agent 2). Then Agent 5. Finally Agent 6.

### Risk Areas Requiring Iteration

1. **Type inference during migration.** SQLite's dynamic typing means a column like `total_work` might contain integers in some rows and floats in others. DuckDB is strict. The migration script's `CREATE TABLE AS SELECT` will infer types from the first batch -- expect type mismatch errors on edge cases. This is why PE recommends explicit DDL.

2. **Parquet schema inconsistency.** If early Parquet files have different column sets than recent ones (e.g., `elapsed_seconds` added later), the `INSERT INTO records SELECT ... FROM read_parquet()` will fail. Need a UNION ALL approach or schema normalization step.

3. **Garmin semicircle coordinates.** The `records` table stores latitude/longitude as both semicircles (large integers from Garmin FIT) and decimal degrees (from Strava). DuckDB's strict typing will expose this if the column is typed as INTEGER vs DOUBLE. The `_get_activity_track()` function in `routes.py` already handles this at read time, but the migration should standardize the storage format.

4. **BLOB storage for posterior samples.** `bayesian.py` stores numpy arrays as BLOBs (`arr.tobytes()`). Verify DuckDB BLOB handling matches SQLite for this pattern.

---

<details>
<summary>Principal Engineer Review (full)</summary>

Key findings:
1. DuckDB single-writer lock is a real constraint -- FastAPI server + sync scripts can't coexist like they can with SQLite WAL. Plan's "close connections promptly" is insufficient.
2. conn.commit() semantics differ -- DuckDB autocommits by default. Multi-table inserts (activity + records + laps) lose atomicity without explicit BEGIN TRANSACTION.
3. INSERT OR REPLACE syntax exists in DuckDB but behaves differently (4 call sites).
4. AUTOINCREMENT keyword doesn't exist in DuckDB (6 DDL sites in routes.py, blocks.py, ftp_test.py, tp_ingest.py).
5. cursor.lastrowid replacement with MAX(rowid) is unsafe -- must use RETURNING clause (7 sites).
6. Schema column type rigidity -- SQLite is dynamic, DuckDB is strict. Type inference during migration could fail.
7. Three files completely missing from plan: backfill_altitude.py, garmin_mcp_sync.py, migrate_to_parquet.py.
8. Steps 4-9 must be ONE atomic commit, not 7 sequential steps.
9. MMP cache import can be deferred (rebuild on first access).
10. Actual file count: ~23 files, not ~10. 45+ cursor sites, 22 commit sites, 7 lastrowid sites, 6 AUTOINCREMENT DDL sites.
11. Recommends connection context manager in db.py.
12. Recommends explicit type definitions in migration (not CREATE TABLE AS SELECT).

</details>

<details>
<summary>Product Designer Review (full)</summary>

Key findings:
1. duckdb not in setup.sh or README pip install -- new user onboarding breaks immediately.
2. test_db.py:14 asserts "cycling_power.db" in DB_PATH -- breaks on first test run.
3. setup.sh line 51 hardcodes old DB name string.
4. routes.py uses executescript() -- sqlite3-specific method, no DuckDB equivalent. Same issue in ftp_test.py, tp_ingest.py, blocks.py.
5. backfill_altitude.py and garmin_mcp_sync.py bypass get_connection() -- missing from plan.
6. lastrowid should use RETURNING, not MAX(rowid).
7. No partial-migration detection -- killed mid-step-2 leaves partial .duckdb file.
8. No rollback procedure documented.
9. Users who pull updated code before running migration get silent failures.
10. No "am I on SQLite or DuckDB?" diagnostic.
11. Parquet import loop has no checkpointing -- crash at file 1500 means restart from 0.
12. Migration output has no PASS/FAIL verdict.
13. conn.commit() behavior differs -- 22 commit calls need auditing.
14. Single-writer constraint not operationalized (no lock file or guard).

</details>

<details>
<summary>Security Engineer Review (full)</summary>

Key findings:

CRITICAL:
- C1: RWGPS API key and auth token HARDCODED in rwgps.py lines 15-16, committed to public GitHub repo. Must rotate immediately.

HIGH:
- H1: SQL injection via f-string path interpolation in migration script (read_parquet calls). File paths inserted raw into SQL.
- H2: set_config() SQL injection via column name interpolation in config.py:103 (pre-existing).
- H3: No file permissions on new DuckDB file -- created world-readable (0o644). Contains GPS location history, PII, physiological data.
- H4: .gitignore should use glob pattern (cycling_power.duckdb.*) to catch .wal, .tmp, etc.

MEDIUM:
- M1: No backup step before migration -- should cp or sqlite3 .backup first.
- M2: No transaction wrapping in migration script -- partial migration on crash.
- M3: MAX(rowid) race condition (same as principal + designer).
- M4: GPS data consolidation risk -- all location history now in single file vs 1700 separate files.
- M5: No dependency pinning for duckdb package.

LOW:
- L1: Strava/Garmin token dirs not defensively in .gitignore.
- L2: No try/finally on DuckDB connection in migration.
- L3: Dynamic DDL generation from DEFAULTS dict (pre-existing).

</details>
