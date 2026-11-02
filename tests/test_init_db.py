"""
Tests for init_db.py.

init_db.py runs as soon as it is loaded and works on files relative to itself, so each test
copies init_db.py, schema.sql, and static/testing/sample_data.json into a fresh temporary
folder (keeping that layout), runs the
script there, and checks the prospex.db it makes. The real prospex.db is never touched.

Run from the project root:  python3 -m unittest tests.test_init_db
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from werkzeug.security import check_password_hash

import db

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = ["users", "companies", "jobs", "contacts"]
DEMO_PASSWORD = "DemoPass123!"  # password of every demo user in sample_data.json
DATA_RELATIVE_PATH = os.path.join("static", "testing", "sample_data.json")  # where init_db.py looks for the data


class InitDbTestCase(unittest.TestCase):
    """Gives each test its own temporary copy of the project files."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name in ("init_db.py", "schema.sql"):
            shutil.copy(os.path.join(ROOT, name), self.tmp.name)
        self.data_path = os.path.join(self.tmp.name, DATA_RELATIVE_PATH)
        os.makedirs(os.path.dirname(self.data_path))
        shutil.copy(os.path.join(ROOT, DATA_RELATIVE_PATH), self.data_path)
        self.db_path = os.path.join(self.tmp.name, "prospex.db")

    # ---------- helpers ----------

    def _path(self, name):
        return os.path.join(self.tmp.name, name)

    def _run(self):
        """Run init_db.py in the temporary folder and return the finished process."""
        return subprocess.run(
            [sys.executable, "init_db.py"], cwd=self.tmp.name, capture_output=True, text=True
        )

    def _run_ok(self):
        result = self._run()
        self.assertEqual(result.returncode, 0, f"init_db.py failed: {result.stderr}")
        return result

    def _json(self):
        with open(self.data_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, data):
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self.addCleanup(conn.close)
        return conn

    def _count(self, table):
        return self._connect().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def _counts(self):
        return {table: self._count(table) for table in TABLES}

    def _db_bytes(self):
        with open(self.db_path, "rb") as f:
            return f.read()


class TestBuildsDatabase(InitDbTestCase):
    """The normal run: the script builds a database that matches the sample data."""

    def test_runs_and_creates_the_database_file(self):
        result = self._run_ok()
        self.assertIn("db created successfully", result.stdout)
        self.assertTrue(os.path.exists(self.db_path), "prospex.db was not created")

    def test_creates_the_four_tables_and_no_about_table(self):
        self._run_ok()
        rows = self._connect().execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        names = {row["name"] for row in rows}
        for table in TABLES:
            self.assertIn(table, names)
        self.assertNotIn("_about", names, "The _about documentation key must not become a table")

    def test_row_counts_match_the_sample_data(self):
        self._run_ok()
        data = self._json()
        for table in TABLES:
            with self.subTest(table=table):
                self.assertEqual(self._count(table), len(data[table]))

    def test_every_row_matches_the_sample_data(self):
        self._run_ok()
        data = self._json()
        conn = self._connect()
        for table in TABLES:
            expected_rows = sorted(data[table], key=lambda row: row["id"])  # JSON rows are not always in id order
            columns = list(expected_rows[0].keys())
            saved_rows = conn.execute(
                f"SELECT {', '.join(columns)} FROM {table} ORDER BY id"
            ).fetchall()
            for expected, saved in zip(expected_rows, saved_rows):
                with self.subTest(table=table, id=expected["id"]):
                    # Empty values must be real NULLs (None), not the text "None" or ""
                    self.assertEqual(dict(saved), expected)

    def test_foreign_key_and_integrity_checks_pass(self):
        self._run_ok()
        conn = self._connect()
        self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_demo_users_can_log_in_with_db_py(self):
        # Checks that init_db.py and db.py work together
        self._run_ok()
        conn = db.get_connection(self.db_path)
        self.addCleanup(conn.close)
        for user in self._json()["users"]:
            with self.subTest(email=user["email"]):
                found = db.get_user_by_email(conn, user["email"])
                self.assertIsNotNone(found)
                self.assertEqual(found["id"], user["id"])
                self.assertTrue(check_password_hash(found["password_hash"], DEMO_PASSWORD))

    def test_extra_documentation_keys_in_the_json_are_ignored(self):
        data = self._json()
        data["_notes"] = {"anything": "documentation only"}
        self._write_json(data)
        self._run_ok()
        self.assertEqual(self._count("users"), len(data["users"]))


class TestRebuild(InitDbTestCase):
    """Running the script again replaces the old database."""

    def test_running_twice_gives_the_same_counts(self):
        self._run_ok()
        first = self._counts()
        self._run_ok()
        self.assertEqual(self._counts(), first, "Second run added or lost rows")

    def test_rows_added_by_hand_are_gone_after_a_rerun(self):
        self._run_ok()
        conn = self._connect()
        conn.execute(
            "INSERT INTO users (first_name, last_name, email, password_hash) VALUES ('Test', 'Person', 'extra@example.com', 'x')"
        )
        conn.commit()
        conn.close()
        self._run_ok()
        found = self._connect().execute("SELECT id FROM users WHERE email = 'extra@example.com'").fetchone()
        self.assertIsNone(found, "The old database was not replaced")
        self.assertEqual(self._count("users"), len(self._json()["users"]))


class TestFailures(InitDbTestCase):
    """Problems with the input leave no half-built database, and never cost the old one."""

    def test_bad_foreign_key_fails_and_leaves_no_database(self):
        data = self._json()
        data["jobs"][0]["company_id"] = 999999  # no such company
        self._write_json(data)
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Could not build the database", result.stderr)
        self.assertFalse(os.path.exists(self.db_path), "A half-filled database was left behind")

    def test_invalid_value_fails_and_leaves_no_database(self):
        data = self._json()
        data["jobs"][0]["status"] = "not a real status"  # fails the schema's CHECK
        self._write_json(data)
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(os.path.exists(self.db_path))

    def test_missing_table_in_the_json_fails_and_leaves_no_database(self):
        data = self._json()
        del data["contacts"]
        self._write_json(data)
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Could not build the database", result.stderr)
        self.assertFalse(os.path.exists(self.db_path))

    def test_missing_sample_data_keeps_the_existing_database(self):
        self._run_ok()
        before = self._db_bytes()
        os.remove(self.data_path)
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(self.db_path), "The existing database was deleted")
        self.assertEqual(self._db_bytes(), before, "The existing database was changed")

    def test_malformed_sample_data_keeps_the_existing_database(self):
        self._run_ok()
        before = self._db_bytes()
        with open(self.data_path, "w") as f:
            f.write("{ this is not valid json")
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self._db_bytes(), before, "The existing database was changed")

    def test_missing_schema_keeps_the_existing_database(self):
        self._run_ok()
        before = self._db_bytes()
        os.remove(self._path("schema.sql"))
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(self.db_path), "The existing database was deleted")
        self.assertEqual(self._db_bytes(), before, "The existing database was changed")


if __name__ == "__main__":
    unittest.main()