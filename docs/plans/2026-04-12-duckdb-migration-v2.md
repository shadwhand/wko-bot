# DuckDB Migration Spec v2 (Post-Review)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace SQLite + Parquet hybrid with single DuckDB database.

**Architecture:** DuckDB gives columnar analytical performance + full SQL + single file. M5 Max with 128GB RAM — entire dataset in memory.

**Scope (revised from review):** ~20 Python files. Rust extensions deferred. Dead scripts (migrate_to_parquet.py, backfill_altitude.py) deferred. MMP cache import skipped (rebuild on access).

---

## Review-Driven Changes

| Review Finding | Resolution |
|---|---|
| MAX(rowid) unsafe (PE+PD+SE) | Use `INSERT ... RETURNING id` at all 7 sites |
| AUTOINCREMENT not in DuckDB (PE) | Replace with `INTEGER PRIMARY KEY` (DuckDB auto-generates) |
| executescript() sqlite3-only (PD) | Split DDL strings, execute individually |
| Autocommit breaks atomicity (PE+PD) | Add `conn.begin()` for multi-table inserts in sync scripts |
| 3 missing files (PE+PD) | Add garmin_mcp_sync.py; defer backfill_altitude.py + migrate_to_parquet.py |
| Single-writer constraint (PE+PD+SE) | Document constraint — never concurrent in practice |
| No backup step (PE+SE) | Add shutil.copy2() before migration |
| File permissions (SE) | os.chmod(0o600) after creation |
| RWGPS creds hardcoded (SE-CRITICAL) | Fix immediately — separate from migration |
| SQL injection in migration (SE) | int() cast validates activity_id; accept risk for local tool |
| .gitignore glob (SE) | Use `cycling_power.duckdb*` |
| duckdb in setup.sh/README (PD) | Add to pip install lines |
| Explicit DDL types (PE) | Use CREATE TABLE AS SELECT — DuckDB reads SQLite declared types well enough. Spot-check after. |
| MMP cache import (PE) | Skip — rebuild on first access |
| Rust extensions (PE) | Defer — optional utilities |

---

## Execution Plan (6 Tasks, One Atomic Commit)

All code changes land as ONE commit after the migration script runs.

### Task 1: RWGPS credential fix (CRITICAL — do first)

**Files:** `wko5/rwgps.py`

Remove hardcoded defaults at lines 15-16. Require env vars, raise if missing.

```python
# Before
RWGPS_API_KEY = os.environ.get("RWGPS_API_KEY", "c8da9c01")
RWGPS_AUTH_TOKEN = os.environ.get("RWGPS_AUTH_TOKEN", "1d3398ca6114c6cc559ca30aa9116129")

# After
RWGPS_API_KEY = os.environ.get("RWGPS_API_KEY")
RWGPS_AUTH_TOKEN = os.environ.get("RWGPS_AUTH_TOKEN")
```

### Task 2: Migration script

**Files:** Create `tools/migrate_to_duckdb.py`

Must include:
1. Backup SQLite DB first (`shutil.copy2`)
2. `duckdb.connect()` with `os.chmod(0o600)` after
3. ATTACH SQLite, copy all tables via `CREATE TABLE AS SELECT`
4. Import Parquet records with `activity_id` column — batch commits every 200 files
5. Skip MMP cache (rebuild on access)
6. Create index: `idx_records_activity` only (defer others)
7. Print PASS/FAIL verdict comparing row counts
8. try/finally on connection

### Task 3: Core data layer

**Files:** `wko5/db.py`, `wko5/config.py`

**db.py changes:**
- `import sqlite3` → `import duckdb`
- `DB_PATH` → `cycling_power.duckdb`
- `get_connection()` → `duckdb.connect(DB_PATH)`
- Remove `RECORDS_DIR` and Parquet logic
- `get_records()` → single SQL query: `conn.execute("SELECT * FROM records WHERE activity_id = ?", [activity_id]).df()`
- `get_activities()` → `conn.execute(query, params).df()` instead of `pd.read_sql_query`

**config.py changes:**
- Remove `import sqlite3`
- `sqlite3.OperationalError` → `CREATE TABLE IF NOT EXISTS` (no exception catch needed)
- `cursor = conn.cursor()` → `conn.execute()` directly
- `cursor.description` → `result.description`

### Task 4: Sync scripts

**Files:** `wko5/garmin_sync.py`, `wko5/strava_sync.py`, `wko5/garmin_mcp_sync.py`, `wko5/ingest_missing.py`

All 4 get the same treatment:
- `import sqlite3` → `import duckdb`
- `sqlite3.connect(DB_PATH)` → `duckdb.connect(DB_PATH)`
- `DB_PATH` → `cycling_power.duckdb`
- `cursor = conn.cursor()` → use `conn` directly
- `cursor.lastrowid` → `INSERT INTO ... RETURNING id` pattern
- Add `conn.begin()` before multi-table inserts, `conn.commit()` after
- `strava_sync.py`: remove Parquet write, INSERT records via DataFrame (`conn.execute("INSERT INTO records SELECT * FROM df")`)
- `garmin_sync.py`: same — records go to DuckDB table, not Parquet
- `ingest_missing.py`: same pattern

### Task 5: DDL + query consumers

**Files:** `wko5/routes.py`, `wko5/blocks.py`, `wko5/ftp_test.py`, `wko5/tp_ingest.py`, `wko5/ride.py`, `wko5/training_load.py`, `wko5/pdcurve.py`, `wko5/bayesian.py`, `wko5/rwgps.py`, `wko5/gap_analysis.py`, `wko5/api/routes.py`

DDL fixes (4 files):
- Remove `AUTOINCREMENT` from all `CREATE TABLE` statements
- `conn.executescript(DDL)` → split on `;` and execute each statement
- `cursor.lastrowid` → `RETURNING id` where applicable

Query consumer fixes (all files using `get_connection()`):
- `pd.read_sql_query(sql, conn, params=(...))` → `conn.execute(sql, list(params)).df()`
- `cursor = conn.cursor(); cursor.execute(...)` → `conn.execute(...)`
- `cursor.fetchone()` → `conn.execute(...).fetchone()`
- `cursor.fetchall()` → `conn.execute(...).fetchall()`

### Task 6: Tests + infra

**Files:** `.gitignore`, `setup.sh`, `README.md`, `CLAUDE.md`, `tests/test_*.py`

- `.gitignore`: add `wko5/cycling_power.duckdb*`
- `setup.sh`: add `duckdb` to pip install, fix DB name string
- `README.md`: update DB references, add duckdb to dependencies
- `CLAUDE.md`: update Stack section
- `tests/`: update DB path assertions, cursor patterns

---

## Execution Sequence

```
1. Task 1 (RWGPS creds)        — do immediately, commit separately
2. Task 2 (migration script)    — write + run against real data
3. Tasks 3-6 in parallel        — all code changes
4. Run tests                    — verify
5. Single commit                — all of tasks 3-6
6. Push
```

## Deferred (not blocking)

- `wko5/backfill_altitude.py` — dead script, already ran
- `wko5/migrate_to_parquet.py` — dead script, reverse of what we're doing
- `tools/backfill-altitude/` (Rust) — optional utility
- `tools/frechet-rs/` (Rust) — optional utility
- MMP cache import — rebuilds on first access
- Lock file for concurrent access — never concurrent in practice
- Dependency pinning — whole project has none, not just duckdb
