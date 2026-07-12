#!/usr/bin/env python3
"""Restore data from memristive_biosensor_backup.db into memristive_biosensor.db

Behavior:
- For each target table, insert rows missing in main DB.
- If a row exists in main and is marked as test (`is_test=1`) it will be updated from backup.
- Rows in main that are non-test are NOT overwritten.

Usage: run from repository root: `python backend/scripts/restore_from_backup.py`
"""
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MAIN_DB = ROOT / "memristive_biosensor.db"
BACKUP_DB = ROOT / "memristive_biosensor_backup.db"

TABLES = [
    "Analytes",
    "ImmobilizationLayers",
    "BioRecognitionLayers",
    "MemristiveLayers",
]

PK_MAP = {
    "Analytes": "TA_ID",
    "BioRecognitionLayers": "BRE_ID",
    "ImmobilizationLayers": "IM_ID",
    "MemristiveLayers": "MEM_ID",
}


def ensure_is_test_column(conn, table: str):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [r[1] for r in cur.fetchall()]
    if "is_test" not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN is_test INTEGER DEFAULT 0")


def get_columns(conn, table: str):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [r[1] for r in cur.fetchall()]


def row_to_dict(cols, row):
    return dict(zip(cols, row))


def main():
    if not MAIN_DB.exists():
        print(f"Main DB not found: {MAIN_DB}")
        sys.exit(1)
    if not BACKUP_DB.exists():
        print(f"Backup DB not found: {BACKUP_DB}")
        sys.exit(1)

    main_conn = sqlite3.connect(str(MAIN_DB))
    bak_conn = sqlite3.connect(str(BACKUP_DB))
    # Use row_factory for convenience
    main_conn.row_factory = sqlite3.Row
    bak_conn.row_factory = sqlite3.Row

    summary = {}

    try:
        for table in TABLES:
            summary[table] = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
            try:
                # Ensure is_test column exists in main
                ensure_is_test_column(main_conn, table)

                bak_cols = get_columns(bak_conn, table)
                main_cols = get_columns(main_conn, table)

                # Use intersection of columns
                cols = [c for c in bak_cols if c in main_cols]
                if not cols:
                    print(f"No common columns for table {table}, skipping")
                    continue

                pk = PK_MAP.get(table)
                if pk not in cols:
                    print(f"Primary key {pk} not found in common columns for {table}, skipping")
                    continue

                placeholders = ", ".join(["?" for _ in cols])
                col_list_sql = ", ".join(cols)

                bak_cur = bak_conn.execute(f"SELECT {col_list_sql} FROM {table}")
                rows = bak_cur.fetchall()

                main_cur = main_conn.cursor()
                for r in rows:
                    try:
                        row = row_to_dict(cols, r)
                        pk_val = row[pk]
                        main_row = main_conn.execute(f"SELECT {col_list_sql}, is_test FROM {table} WHERE {pk} = ?", (pk_val,)).fetchone()
                        if main_row is None:
                            # Insert
                            vals = [row[c] for c in cols]
                            main_cur.execute(f"INSERT INTO {table} ({col_list_sql}) VALUES ({placeholders})", vals)
                            summary[table]["inserted"] += 1
                        else:
                            is_test = main_row["is_test"] if "is_test" in main_row.keys() else 0
                            try:
                                is_test_flag = int(is_test) if is_test is not None else 0
                            except Exception:
                                is_test_flag = 0
                            if is_test_flag == 1 or (str(pk_val).endswith("_TEST") or str(pk_val).endswith("_DUP")):
                                # Update only columns that are present
                                set_clause = ", ".join([f"{c} = ?" for c in cols])
                                vals = [row[c] for c in cols] + [pk_val]
                                main_cur.execute(f"UPDATE {table} SET {set_clause} WHERE {pk} = ?", vals)
                                summary[table]["updated"] += 1
                            else:
                                summary[table]["skipped"] += 1
                    except Exception as e:
                        summary[table]["errors"] += 1
                        print(f"Error processing row in {table}: {e}")

                main_conn.commit()
            except Exception as e:
                print(f"Error with table {table}: {e}")

        print("\nRestore summary:")
        for t, stats in summary.items():
            print(f"{t}: inserted={stats['inserted']} updated={stats['updated']} skipped={stats['skipped']} errors={stats['errors']}")

    finally:
        main_conn.close()
        bak_conn.close()


if __name__ == '__main__':
    main()
