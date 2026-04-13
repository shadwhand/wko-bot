#!/usr/bin/env python3
"""Migrate cycling_power from SQLite + Parquet to a single DuckDB file.

Usage:
    python tools/migrate_to_duckdb.py          # first run
    python tools/migrate_to_duckdb.py --force   # overwrite existing .duckdb
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

import duckdb

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent / "wko5"
SQLITE_PATH = BASE_DIR / "cycling_power.db"
DUCKDB_PATH = BASE_DIR / "cycling_power.duckdb"
RECORDS_DIR = BASE_DIR / "records"
BACKUP_PATH = SQLITE_PATH.with_suffix(".db.bak")

# Tables to skip during SQLite copy (empty or rebuild-on-access)
SKIP_TABLES = {"mmp_cache", "sqlite_sequence"}

BATCH_SIZE = 200  # Parquet files per commit batch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate to DuckDB")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing .duckdb file"
    )
    return parser.parse_args()


def backup_sqlite() -> None:
    """Create a safety copy of the SQLite database."""
    print(f"  Backing up SQLite -> {BACKUP_PATH.name} ... ", end="", flush=True)
    shutil.copy2(SQLITE_PATH, BACKUP_PATH)
    print("done")


def copy_sqlite_tables(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """ATTACH SQLite and copy every table (except skips) into DuckDB."""
    con.execute(f"ATTACH '{SQLITE_PATH}' AS sqlite_src (TYPE SQLITE, READ_ONLY)")

    tables = [
        row[2]
        for row in con.execute("SHOW ALL TABLES").fetchall()
        if row[0] == "sqlite_src"
    ]

    counts: dict[str, int] = {}
    for tbl in tables:
        if tbl in SKIP_TABLES:
            print(f"  skip  {tbl}")
            continue
        con.execute(f'CREATE TABLE main."{tbl}" AS SELECT * FROM sqlite_src."{tbl}"')
        n = con.execute(f'SELECT COUNT(*) FROM main."{tbl}"').fetchone()[0]
        counts[tbl] = n
        print(f"  copy  {tbl:25s}  {n:>8,} rows")

    con.execute("DETACH sqlite_src")
    return counts


def _build_select(pf: Path, activity_id: int) -> str:
    """Build a SELECT that normalises any Parquet schema variant into the
    canonical records columns.  Handles: missing elapsed_seconds, files that
    already carry activity_id, and mixed numeric types (int16/32/64/double/null).
    """
    import pyarrow.parquet as pq

    schema = pq.read_schema(pf)
    col_names = {f.name for f in schema}

    cols = [f"{activity_id} AS activity_id"]

    # timestamp is always VARCHAR
    cols.append("CAST(timestamp AS VARCHAR) AS timestamp")

    # elapsed_seconds may be missing in files that already have activity_id
    if "elapsed_seconds" in col_names:
        cols.append("CAST(elapsed_seconds AS DOUBLE) AS elapsed_seconds")
    else:
        cols.append("NULL::DOUBLE AS elapsed_seconds")

    for c in ("power", "heart_rate", "cadence", "speed",
              "altitude", "temperature", "latitude", "longitude", "distance"):
        if c in col_names:
            cols.append(f"CAST({c} AS DOUBLE) AS {c}")
        else:
            cols.append(f"NULL::DOUBLE AS {c}")

    return f"SELECT {', '.join(cols)} FROM read_parquet('{pf}')"


def import_parquet_records(con: duckdb.DuckDBPyConnection) -> int:
    """Import per-activity Parquet files into a single records table.

    Returns total row count inserted.
    """
    parquet_files = sorted(RECORDS_DIR.glob("*.parquet"))
    total_files = len(parquet_files)
    if total_files == 0:
        print("  WARNING: no Parquet files found in records/")
        return 0

    # Create table with explicit widened schema
    con.execute("""
        CREATE TABLE records (
            activity_id     BIGINT,
            timestamp       VARCHAR,
            elapsed_seconds DOUBLE,
            power           DOUBLE,
            heart_rate      DOUBLE,
            cadence         DOUBLE,
            speed           DOUBLE,
            altitude        DOUBLE,
            temperature     DOUBLE,
            latitude        DOUBLE,
            longitude       DOUBLE,
            distance        DOUBLE
        )
    """)

    done = 0
    con.execute("BEGIN TRANSACTION")
    batch_count = 0
    for pf in parquet_files:
        aid = int(pf.stem)
        sql = _build_select(pf, aid)
        con.execute(f"INSERT INTO records {sql}")
        batch_count += 1
        done += 1

        if batch_count >= BATCH_SIZE:
            con.execute("COMMIT")
            row_so_far = con.execute("SELECT COUNT(*) FROM records").fetchone()[0]
            print(
                f"  parquet  {done:>5}/{total_files}  "
                f"({row_so_far:>12,} rows committed)",
                end="\r",
            )
            con.execute("BEGIN TRANSACTION")
            batch_count = 0

    # Final commit for any remaining files
    if batch_count > 0:
        con.execute("COMMIT")

    total_rows = con.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    print(
        f"  parquet  {done:>5}/{total_files}  "
        f"({total_rows:>12,} rows total)       "
    )
    return total_rows


def create_index(con: duckdb.DuckDBPyConnection) -> None:
    print("  Creating index idx_records_activity ... ", end="", flush=True)
    con.execute("CREATE INDEX idx_records_activity ON records(activity_id)")
    print("done")


def verify(con: duckdb.DuckDBPyConnection, sqlite_counts: dict[str, int]) -> bool:
    """Compare row counts between SQLite source and DuckDB. Return True if all match."""
    import sqlite3

    print("\n=== Verification ===")
    ok = True
    sqlite_con = sqlite3.connect(str(SQLITE_PATH))
    try:
        for tbl, expected in sorted(sqlite_counts.items()):
            actual = con.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
            status = "OK" if actual == expected else "MISMATCH"
            if actual != expected:
                ok = False
            print(f"  {tbl:25s}  sqlite={expected:>8,}  duckdb={actual:>8,}  {status}")
    finally:
        sqlite_con.close()

    # Verify records table: count of Parquet files == distinct activity_ids
    parquet_count = len(list(RECORDS_DIR.glob("*.parquet")))
    duck_activities = con.execute(
        "SELECT COUNT(DISTINCT activity_id) FROM records"
    ).fetchone()[0]
    duck_rows = con.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    pq_status = "OK" if duck_activities == parquet_count else "MISMATCH"
    if duck_activities != parquet_count:
        ok = False
    print(
        f"  {'records (activities)':25s}  parquet_files={parquet_count:>5,}  "
        f"duckdb_distinct={duck_activities:>5,}  {pq_status}"
    )
    print(f"  {'records (total rows)':25s}  {duck_rows:>12,}")

    return ok


def main() -> None:
    args = parse_args()

    # Guard against re-run
    if DUCKDB_PATH.exists() and not args.force:
        print(
            f"ERROR: {DUCKDB_PATH} already exists. "
            f"Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)
    if DUCKDB_PATH.exists() and args.force:
        DUCKDB_PATH.unlink()
        print(f"Removed existing {DUCKDB_PATH.name}")

    if not SQLITE_PATH.exists():
        print(f"ERROR: SQLite DB not found at {SQLITE_PATH}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Migrate to DuckDB ===")
    t0 = time.time()

    # 1. Backup
    backup_sqlite()

    # 2-5. Open DuckDB, copy, import, index
    con = duckdb.connect(str(DUCKDB_PATH))
    try:
        print("\n--- SQLite tables ---")
        sqlite_counts = copy_sqlite_tables(con)

        print("\n--- Parquet records ---")
        import_parquet_records(con)

        print("\n--- Index ---")
        create_index(con)

        # 7. Verify
        passed = verify(con, sqlite_counts)
    finally:
        con.close()

    # 6. File permissions
    os.chmod(DUCKDB_PATH, 0o600)

    elapsed = time.time() - t0
    size_mb = DUCKDB_PATH.stat().st_size / (1024 * 1024)

    print(f"\n=== Result ===")
    print(f"  File:     {DUCKDB_PATH}")
    print(f"  Size:     {size_mb:.1f} MB")
    print(f"  Time:     {elapsed:.1f}s")
    print(f"  Verdict:  {'PASS' if passed else 'FAIL'}")

    if not passed:
        sys.exit(2)


if __name__ == "__main__":
    main()
