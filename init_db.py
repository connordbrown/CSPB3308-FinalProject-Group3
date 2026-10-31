"""
Creates a new db from schema.sql and fills it with the sample data in sample_data.json.
If a previous version exists, this script DELETES THE OLD VERSION
"""
import json
import os
import sqlite3


BASE_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR_PATH, "prospex.db")
SCHEMA_PATH = os.path.join(BASE_DIR_PATH, "schema.sql")
DATA_PATH = os.path.join(BASE_DIR_PATH, "static/testing/sample_data.json")

# Parents before children, so foreign keys always point at rows that already exist.
# Other keys in the JSON file (such as "_about") are documentation and are skipped.
TABLE_ORDER = ["users", "companies", "jobs", "contacts"]


def insert_rows(conn, table, rows):
    """Insert a list of row dicts (keys are column names). Returns the number of rows."""
    if not rows:
        return 0
    columns = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    conn.executemany(sql, [[row[c] for c in columns] for row in rows])
    return len(rows)


# Read the sample data first, so a missing or broken file doesn't cost us the old db
with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")  # SQLite ignores foreign keys unless this is set
with open(SCHEMA_PATH) as f:
    conn.executescript(f.read())

try:
    counts = {}
    with conn:  # one transaction: if any row fails, none of the sample data is saved
        for table in TABLE_ORDER:
            counts[table] = insert_rows(conn, table, data[table])
    problems = conn.execute("PRAGMA foreign_key_check").fetchall()
    if problems:
        raise sqlite3.IntegrityError(f"Foreign key problems found: {problems}")
except (sqlite3.Error, KeyError, ValueError) as e:
    conn.close()
    os.remove(DB_PATH)  # don't leave a half-filled db behind
    raise SystemExit(f"\nCould not load sample data: {e!r}\n")

conn.close()

print("\ndb created successfully\n")
for table, count in counts.items():
    print(f"  {table}: {count} rows")
print()