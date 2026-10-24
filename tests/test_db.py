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
    def test_returns_user_contacts(self):
        # Insert three contacts for user A and check that get_contacts_for_user returns them all with the correct attributes.
        contact_1 = self._insert_contact(
            self.user_a, name="Alice Smith", title="Engineer", designation="recruiter", email="alice@example.com"
            )
        contact_2 = self._insert_contact(
            self.user_a, name="Bob Johnson", title="Designer", designation="recruiter", email="bob@example.com"
        )
        contact_3 = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com"
        )

        result = db.get_contacts_for_user(self.conn, self.user_a)
        # Check that the result contains all three contacts.
        self.assertEqual(len(result), 3)
        # Check that the returned contacts are the same as the inserted contacts by comparing their ids.
        # Checks agains ID set to avoid ordering issues
        returned_ids = {contact['id'] for contact in result}
        self.assertSetEqual(returned_ids, {contact_1, contact_2, contact_3})
        

    def test_returns_contact_attributes(self):
        # Insert a company and a job for user A, then insert a contact for user A with those company_id and job_id.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        # Insert a contact for user A and check that get_contacts_for_user returns the correct attributes.
        contact_id = self._insert_contact(
            self.user_a, name="Alice Smith", title="Engineer", designation="recruiter", email="alice@example.com", company_id=company_id, job_id=job_id
        )

        result = db.get_contacts_for_user(self.conn, self.user_a)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], contact_id)
        self.assertEqual(result[0]['name'], "Alice Smith")
        self.assertEqual(result[0]['title'], "Engineer")
        self.assertEqual(result[0]['company_name'], "Acme Corp")
        

    def test_does_not_return_other_users_contacts(self):
        # Insert a company and a job for users A and B
        company_id_a = self._insert_company(self.user_a, name="Acme Corp")
        job_id_a = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id_a)
        company_id_b = self._insert_company(self.user_b, name="Beta Ltd")
        job_id_b = self._insert_job(self.user_b, title="Product Manager", company_id=company_id_b)
        # Insert a contact for user A and a contact for user B, and check that get_contacts_for_user only returns user A's contact.
        contact_a_id = self._insert_contact(
            self.user_a, name="Alice Smith", title="Engineer", designation="recruiter", email="alice@example.com", company_id=company_id_a, job_id=job_id_a
        )
        contact_b_id = self._insert_contact(
            self.user_b, name="Bob Johnson", title="Designer", designation="recruiter", email="bob@example.com", company_id=company_id_b, job_id=job_id_b
        )
        # Check that get_contacts_for_user only returns user A's contact.
        result_a = db.get_contacts_for_user(self.conn, self.user_a)
        self.assertEqual(len(result_a), 1)
        self.assertEqual(result_a[0]['id'], contact_a_id)
        # Check that get_contacts_for_user only returns user B's contact.
        result_b = db.get_contacts_for_user(self.conn, self.user_b)
        self.assertEqual(len(result_b), 1)
        self.assertEqual(result_b[0]['id'], contact_b_id)



    def test_returns_empty_list_if_no_contacts(self):
        # Run get_contacts_for_user for user A when no contacts exist and check that it returns an empty list.
        result = db.get_contacts_for_user(self.conn, self.user_a)
        self.assertEqual(result, [])
        

    def test_returns_empty_list_if_user_does_not_exist(self):
        # Run get_contacts_for_user for a non-existent user and check that it returns an empty list.
        result = db.get_contacts_for_user(self.conn, NONEXISTENT_ID)
        self.assertEqual(result, [])    

    def test_returns_contacts_without_company_or_job(self):
        # Insert a contact for user A without a company_id
        contact_id = self._insert_contact(
            self.user_a, name="Alice Smith", title="Engineer", designation="recruiter", email="alice@example.com"
        )
        # Insert a contact for user A without a job_id
        contact_id_2 = self._insert_contact(
            self.user_a, name="Bob Johnson", title="Designer", designation="recruiter", email="bob@example.com"
        )
        # Check that get_contacts_for_user returns both contacts without company_id or job_id.
        result = db.get_contacts_for_user(self.conn, self.user_a)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], contact_id, "Contact not returned with no company_id")
        self.assertEqual(result[1]['id'], contact_id_2, "Contact not returned with no job_id")

    def test_results_are_ordered_by_name(self):
        # Insert companies and jobs for user A to associate with contacts
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        # Insert three contacts for user A with different names and check that get_contacts_for_user returns them ordered by name.
        contact_1 = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id
        )
        contact_2 = self._insert_contact(
            self.user_a, name="David Wilson", title="Analyst", designation="recruiter", email="david@example.com", company_id=company_id, job_id=job_id
        )
        contact_3 = self._insert_contact(
            self.user_a, name="Eve Davis", title="Coordinator", designation="recruiter", email="eve@example.com", company_id=company_id, job_id=job_id
        )
        # Check that get_contacts_for_user returns the contacts ordered by name.
        result = db.get_contacts_for_user(self.conn, self.user_a)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['name'], "Charlie Brown")
        self.assertEqual(result[1]['name'], "David Wilson")
        self.assertEqual(result[2]['name'], "Eve Davis")


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
