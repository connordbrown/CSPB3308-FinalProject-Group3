"""
Unit tests for the Prospex data access layer (db.py).

Each test class covers one access method, and each test maps to a numbered
row in that method's "Tests" table under "Data Access Methods" in
SQL_TESTING.md (e.g. "create_job #3"). Every test runs against a fresh
in-memory SQLite database built from schema.sql and seeded with two users,
A and B, so every method can be checked against another user's data.

Run from the project root with:  python3 -m unittest tests.test_db -v
Run one method's tests with:     python3 -m unittest tests.test_db.TestCreateJob -v

Conventions for adding tests:
- Put each test in the class for the method it calls. Classes follow the
  same order and sections as db.py.
- Name tests test_<what_is_checked> 
- Set up rows with the _insert_* helpers below, not with other db.py
  functions, so a test only fails when the method under test is wrong.
- If a class needs the same rows in every test, give it its own setUp()
  that calls super().setUp() first (see TestJobs in test_schema.py).
"""

import os
import sqlite3
import unittest

from werkzeug.security import generate_password_hash

import db

# Resolve schema.sql (in the project root) relative to this file so tests run from any directory
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema.sql")

# An id that will never exist in a fresh test database
NONEXISTENT_ID = 9999

# Seeded users. A matches the demo login used across SQL_TESTING.md.
USER_A = {
    "first_name": "Alex",
    "last_name": "Morgan",
    "email": "alex.demo@example.com",
    "password": "DemoPass123!",
    "display_name": "alex",
}
USER_B = {
    "first_name": "Priya",
    "last_name": "Shah",
    "email": "priya.demo@example.com",
    "password": "PriyaPass456!",
    "display_name": "priya_s",
}


class AccessTestCase(unittest.TestCase):
    """
    Base class: builds a fresh database for each test, seeds users A and B,
    and provides insert helpers.

    Available in every test:
        self.conn       connection from db.get_connection (foreign keys on, sqlite3.Row rows)
        self.user_a     user A's id
        self.user_b     user B's id
    """

    def setUp(self):
        # get_connection turns on foreign keys and row access by column name,
        # so tests use the same connection settings as the app
        self.conn = db.get_connection(":memory:")

        # Build all tables from schema.sql
        with open(SCHEMA_PATH) as f:
            self.conn.executescript(f.read())

        self.user_a = self._insert_user(**USER_A)
        self.user_b = self._insert_user(**USER_B)

    def tearDown(self):
        self.conn.close()

    # ------------------------------------------------------------------
    # Helpers: insert one row with raw SQL and return its id. Pass keyword
    # arguments to override any column; the rest get valid defaults.
    # ------------------------------------------------------------------

    def _insert_user(self, first_name, last_name, email, password, display_name=None):
        # A low-cost hash method keeps setUp fast; check_password_hash reads any method
        password_hash = generate_password_hash(password, method="pbkdf2:sha256:1000")
        return self.conn.execute(
            """
            INSERT INTO users (first_name, last_name, email, password_hash, display_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (first_name, last_name, email, password_hash, display_name),
        ).lastrowid

    def _insert_company(self, user_id, name="Spotify", city=None, region=None,
                        website=None, notes=None):
        return self.conn.execute(
            """
            INSERT INTO companies (user_id, name, city, region, website, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, city, region, website, notes),
        ).lastrowid

    def _insert_job(self, user_id, company_id, title="Software Engineer", status="saved",
                    work_type=None, link=None, notes=None, date_applied=None):
        return self.conn.execute(
            """
            INSERT INTO jobs (user_id, company_id, title, status, work_type, link, notes, date_applied)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, company_id, title, status, work_type, link, notes, date_applied),
        ).lastrowid

    def _insert_contact(self, user_id, name="Jordan Rivera", title=None, designation=None,
                        company_id=None, job_id=None, email=None, phone=None,
                        linkedin_url=None, notes=None):
        return self.conn.execute(
            """
            INSERT INTO contacts (user_id, company_id, job_id, name, title, designation,
                                  email, phone, linkedin_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, company_id, job_id, name, title, designation,
             email, phone, linkedin_url, notes),
        ).lastrowid

    def _fetch(self, table, row_id):
        """Return one row from `table` by id (or None), read directly without db.py."""
        return self.conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()

    def _count(self, table, where="1", params=()):
        """Return the number of rows in `table` matching the WHERE clause."""
        return self.conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {where}", params
        ).fetchone()[0]


# ---------- Users ----------

class TestGetUserByEmail(AccessTestCase):
    """Tests for db.get_user_by_email (SQL_TESTING.md, Access Method: get_user_by_email)."""


class TestCreateUser(AccessTestCase):
    """Tests for db.create_user (SQL_TESTING.md, Access Method: create_user)."""


class TestGetUser(AccessTestCase):
    """Tests for db.get_user (SQL_TESTING.md, Access Method: get_user)."""


class TestUpdateUser(AccessTestCase):
    """Tests for db.update_user (SQL_TESTING.md, Access Method: update_user)."""


class TestChangePassword(AccessTestCase):
    """Tests for db.change_password (SQL_TESTING.md, Access Method: change_password)."""


# ---------- Jobs ----------

class TestGetJob(AccessTestCase):
    """Tests for db.get_job (SQL_TESTING.md, Access Method: get_job)."""


class TestCreateJob(AccessTestCase):
    """Tests for db.create_job (SQL_TESTING.md, Access Method: create_job)."""


class TestUpdateJob(AccessTestCase):
    """Tests for db.update_job (SQL_TESTING.md, Access Method: update_job)."""


# ---------- Contacts ----------

class TestGetContactsForUser(AccessTestCase):
    """Tests for db.get_contacts_for_user (SQL_TESTING.md, Access Method: get_contacts_for_user)."""


class TestGetContactsForJob(AccessTestCase):
    """Tests for db.get_contacts_for_job (SQL_TESTING.md, Access Method: get_contacts_for_job)."""


class TestGetContact(AccessTestCase):
    """Tests for db.get_contact (SQL_TESTING.md, Access Method: get_contact)."""


class TestCreateContact(AccessTestCase):
    """Tests for db.create_contact (SQL_TESTING.md, Access Method: create_contact)."""


class TestUpdateContact(AccessTestCase):
    """Tests for db.update_contact (SQL_TESTING.md, Access Method: update_contact)."""


class TestDeleteContact(AccessTestCase):
    """Tests for db.delete_contact (SQL_TESTING.md, Access Method: delete_contact)."""


# ---------- Companies ----------

class TestGetOrCreateCompany(AccessTestCase):
    """Tests for db.get_or_create_company (SQL_TESTING.md, Access Method: get_or_create_company)."""


# ---------- Dropdown data ----------

class TestGetCompaniesForUser(AccessTestCase):
    """Tests for db.get_companies_for_user (SQL_TESTING.md, Access Method: get_companies_for_user)."""


class TestGetJobsForUser(AccessTestCase):
    """Tests for db.get_jobs_for_user (SQL_TESTING.md, Access Method: get_jobs_for_user)."""


if __name__ == "__main__":
    unittest.main()
