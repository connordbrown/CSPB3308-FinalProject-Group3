"""
Creates a new blank db to use for sign-in.
If a previous version exists, this script DELETES THE OLD VERSION
"""
import os
import sqlite3


BASE_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR_PATH, "prospex.db")
SCHEMA_PATH = os.path.join(BASE_DIR_PATH, "schema.sql")


if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
with open(SCHEMA_PATH) as f:
    conn.executescript(f.read())
conn.close()

print("\ndb created successfully\n")