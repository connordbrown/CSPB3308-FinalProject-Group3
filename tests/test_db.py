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
        self.assertEqual(result[0]['id'], contact_id, "Returned contact id does not match inserted contact id")
        self.assertEqual(result[0]['name'], "Alice Smith", "Returned contact name does not match inserted contact name")
        self.assertEqual(result[0]['title'], "Engineer", "Returned contact title does not match inserted contact title")
        self.assertEqual(result[0]['company_name'], "Acme Corp", "Returned company name does not match linked company name")
        

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
    def test_returns_job_contacts(self):
        # Insert a company and a job for user A, then insert three contacts for user A linked to that job, and check that get_contacts_for_job returns them all.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_1 = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id
        )
        contact_2 = self._insert_contact(
            self.user_a, name="David Wilson", title="Analyst", designation="recruiter", email="david@example.com", company_id=company_id, job_id=job_id
        )
        contact_3 = self._insert_contact(
            self.user_a, name="Eve Davis", title="Coordinator", designation="recruiter", email="eve@example.com", company_id=company_id, job_id=job_id
        )
        # Check that get_contacts_for_job returns the contacts linked to the job.
        result = db.get_contacts_for_job(self.conn, self.user_a, job_id)
        self.assertEqual(len(result), 3)
        # Check that the returned contacts are the same as the inserted contacts by comparing their ids.
        # Checks against ID set to avoid ordering issues
        result_ids = {contact['id'] for contact in result}
        self.assertSetEqual(result_ids, {contact_1, contact_2, contact_3})

    def test_returns_only_contacts_for_job(self):
        # Insert a company and two jobs for user A, then insert contacts for each job.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id_1 = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        job_id_2 = self._insert_job(self.user_a, title="Product Manager", company_id=company_id)
        contact_1 = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id_1
        )
        contact_2 = self._insert_contact(
            self.user_a, name="David Wilson", title="Analyst", designation="recruiter", email="david@example.com", company_id=company_id, job_id=job_id_2
        )
        # Check that get_contacts_for_job only returns contacts linked to the specified job.
        result_1 = db.get_contacts_for_job(self.conn, self.user_a, job_id_1)
        self.assertEqual(len(result_1), 1)
        self.assertEqual(result_1[0]['id'], contact_1)

        result_2 = db.get_contacts_for_job(self.conn, self.user_a, job_id_2)
        self.assertEqual(len(result_2), 1)
        self.assertEqual(result_2[0]['id'], contact_2)


    def test_returns_contact_attributes(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job, and check that get_contacts_for_job returns the correct attributes.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id
        )
        # Check that get_contacts_for_job returns the correct attributes.
        result = db.get_contacts_for_job(self.conn, self.user_a, job_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], contact_id, "Returned contact id does not match inserted contact id")
        self.assertEqual(result[0]['name'], "Charlie Brown", "Returned contact name does not match inserted contact name")
        self.assertEqual(result[0]['title'], "Developer", "Returned contact title does not match inserted contact title")
        self.assertEqual(result[0]['designation'], "recruiter", "Returned contact designation does not match inserted contact designation")

    def test_returns_empty_list_if_no_contacts(self):
        # Insert a company and a job for user A, but do not insert any contacts, and check that get_contacts_for_job returns an empty list.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        result = db.get_contacts_for_job(self.conn, self.user_a, job_id)
        self.assertEqual(result, [])
        

    def test_returns_empty_list_if_job_does_not_exist(self):
        # Run get_contacts_for_job for a non-existent job and check that it returns an empty list.
        result = db.get_contacts_for_job(self.conn, self.user_a, NONEXISTENT_ID)
        self.assertEqual(result, [])

    def test_contacts_sorted_by_name(self):
        # Insert a company and a job for user A, then insert three contacts for user A linked to that job with different names.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_1 = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id
        )
        contact_2 = self._insert_contact(
            self.user_a, name="Alice Smith", title="Sales Associate", designation="recruiter", email="alice@example.com", company_id=company_id, job_id=job_id
        )
        contact_3 = self._insert_contact(
            self.user_a, name="Bob Johnson", title="Marketing Specialist", designation="recruiter", email="bob@example.com", company_id=company_id, job_id=job_id
        )
        # Check that get_contacts_for_job returns the contacts ordered by name.
        result = db.get_contacts_for_job(self.conn, self.user_a, job_id)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['id'], contact_2, "Returned contact id does not match inserted contact id")
        self.assertEqual(result[1]['id'], contact_3, "Returned contact id does not match inserted contact id")
        self.assertEqual(result[2]['id'], contact_1, "Returned contact id does not match inserted contact id")


class TestGetContact(AccessTestCase):
    def test_returns_contact(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id
        )
        # Check that get_contact returns the correct contact.
        result = db.get_contact(self.conn, self.user_a, contact_id)
        self.assertEqual(result['id'], contact_id, "Returned contact id does not match inserted contact id")
        self.assertEqual(result['name'], "Charlie Brown", "Returned contact name does not match inserted contact name")

    def test_returns_contact_attributes(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id
        )
        # Check that get_contact returns the correct contact attributes.
        result = db.get_contact(self.conn, self.user_a, contact_id)
        self.assertEqual(result['id'], contact_id, "Returned contact id does not match inserted contact id")
        self.assertEqual(result['name'], "Charlie Brown", "Returned contact name does not match inserted contact name")
        self.assertEqual(result['title'], "Developer", "Returned contact title does not match inserted contact title")
        self.assertEqual(result['designation'], "recruiter", "Returned contact designation does not match inserted contact designation")
        self.assertEqual(result['email'], "charlie@example.com", "Returned contact email does not match inserted contact email")
        self.assertEqual(result['company_name'], "Acme Corp", "Returned company name does not match linked company name")
        self.assertEqual(result['job_title'], "Software Engineer", "Returned job title does not match linked job title")

    def test_returns_only_user_contact(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id
        )
        # Insert a company and a job for user B, then insert a contact for user B linked to that job.
        company_id_b = self._insert_company(self.user_b, name="Beta Ltd")
        job_id_b = self._insert_job(self.user_b, title="Product Manager", company_id=company_id_b)
        contact_id_b = self._insert_contact(
            self.user_b, name="David Wilson", title="Analyst", designation="recruiter", email="david@example.com", company_id=company_id_b, job_id=job_id_b
        )
        # Check that get_contact returns the correct contact.
        result = db.get_contact(self.conn, self.user_a, contact_id)
        self.assertEqual(result['id'], contact_id, "Returned contact id does not belong to user A")

    def test_returns_none_if_another_users_contact(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie@example.com", company_id=company_id, job_id=job_id
        )
    
        # Check that get_contact returns None when querying for that contact from user B.
        result = db.get_contact(self.conn, self.user_b, contact_id)
        self.assertIsNone(result, "Expected None for contact that belongs to another user")

    def test_returns_none_if_contact_does_not_exist(self):
        # Check that get_contact returns None for a non-existent contact.
        result = db.get_contact(self.conn, self.user_a, NONEXISTENT_ID)
        self.assertIsNone(result, "Expected None for non-existent contact")

    def test_returns_contact_without_company_or_job(self):
        # Insert a contact without linking it to a company or job.
        contact_id = self._insert_contact(
            self.user_a, name="Alice Smith", title="Manager", designation="recruiter", email="alice@example.com"
        )
        # Check that get_contact returns the correct contact.
        result = db.get_contact(self.conn, self.user_a, contact_id)
        self.assertEqual(result['id'], contact_id, "Returned contact id does not match inserted contact id")


class TestCreateContact(AccessTestCase):
    def test_creates_contact(self):
        # Insert a company and a job for user A, then create a contact for user A linked to that job using db.create_contact.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = db.create_contact(
            self.conn, self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", company_id=company_id, job_id=job_id, email="charlie@example.com"
        )
        # Check that the contact is created in the database.
        result = db.get_contact(self.conn, self.user_a, contact_id)
        self.assertEqual(result['id'], contact_id, "Created contact id does not match expected id")

    def test_contact_belongs_to_user(self):
        # Insert a company and a job for user A, then create a contact for user A linked to that job using db.create_contact.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = db.create_contact(
            self.conn, self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", company_id=company_id, job_id=job_id, email="charlie@example.com"
        )
        # Check that the contact belongs to the correct user.
        result = db.get_contact(self.conn, self.user_a, contact_id)
        self.assertEqual(result['user_id'], self.user_a, "Contact does not belong to the correct user")

    def test_contact_attributes(self):
        # Insert a company and a job for user A, then create a contact for user A linked to that job using db.create_contact.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = db.create_contact(
            self.conn, self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", company_id=company_id, job_id=job_id, email="charlie@example.com"
        )
        # Check that the contact has the correct attributes.
        result = db.get_contact(self.conn, self.user_a, contact_id)
        self.assertEqual(result['name'], "Charlie Brown", "Contact name does not match")
        self.assertEqual(result['title'], "Developer", "Contact title does not match")
        self.assertEqual(result['designation'], "recruiter", "Contact designation does not match")
        self.assertEqual(result['company_id'], company_id, "Contact company_id does not match")
        self.assertEqual(result['job_id'], job_id, "Contact job_id does not match")
        self.assertEqual(result['email'], "charlie@example.com", "Contact email does not match")

    def test_empty_or_invalid_name(self):
        # Check that db.create_contact raises a ValueError when the name is not a string.
        invalid_data_type = [123, [], {}, True, False]
        for type in invalid_data_type:
            with self.subTest(type=type):
                with self.assertRaises(ValueError):
                    db.create_contact(self.conn, self.user_a, name=type, title="Developer", designation="recruiter")
        # Check that db.create_contact raises an error when the name is empty.
        with self.assertRaises(ValueError):
            db.create_contact(self.conn, self.user_a, name="", title="Developer", designation="recruiter")
        with self.assertRaises(ValueError):
            db.create_contact(self.conn, self.user_a, name=None, title="Developer", designation="recruiter")    

    def test_designation_invalid(self):
        # Check that db.create_contact raises a ValueError when the designation is not in the allowed set of values.
        invalid_designations = ["invalid", "manager", 123, [], {}, True, False]
        for designation in invalid_designations:
            with self.subTest(designation=designation):
                with self.assertRaises(ValueError):
                    db.create_contact(self.conn, self.user_a, name="Charlie Brown", title="Developer", designation=designation)

    def test_designation_none_or_empty(self):
        # Check that db.create_contact allows designation to be None or an empty string.
        try:
            contact_id_none = db.create_contact(self.conn, self.user_a, name="Charlie Brown", title="Developer", designation=None)
            contact_id_empty = db.create_contact(self.conn, self.user_a, name="Charlie Brown", title="Developer", designation="")
            result_none = db.get_contact(self.conn, self.user_a, contact_id_none)
            result_empty = db.get_contact(self.conn, self.user_a, contact_id_empty)   
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")

    def test_job_id_does_not_belong_to_user(self):
        # Insert a company and a job for user B, then attempt to create a contact for user A linked to that job.
        company_id_b = self._insert_company(self.user_b, name="Beta Ltd")
        job_id_b = self._insert_job(self.user_b, title="Product Manager", company_id=company_id_b)
        # Insert a company for user A to use in the contact creation.
        company_id_a = self._insert_company(self.user_a, name="Acme Corp")
        # Check that db.create_contact raises a ValueError when the job_id does not belong to the user.
        with self.assertRaises(ValueError):
            db.create_contact(
                self.conn, self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", company_id=company_id_a, job_id=job_id_b,
            )

    def test_company_id_does_not_belong_to_user(self):
        # Insert a company for user B, then attempt to create a contact for user A linked to that company.
        company_id_b = self._insert_company(self.user_b, name="Beta Ltd")
        # Check that db.create_contact raises a ValueError when the company_id does not belong to the user.
        with self.assertRaises(ValueError):
            db.create_contact(
                self.conn, self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", company_id=company_id_b
            )

    def test_succeeds_with_name_only(self):
        # Check that db.create_contact succeeds when only the name is provided, and other optional fields are omitted.
        try:
            contact_id = db.create_contact(self.conn, self.user_a, name="Charlie Brown")
            result = db.get_contact(self.conn, self.user_a, contact_id)
            self.assertEqual(result['name'], "Charlie Brown", "Contact name does not match")
            self.assertIsNone(result['title'], "Contact title should be None")
            self.assertIsNone(result['designation'], "Contact designation should be None")
            self.assertIsNone(result['company_id'], "Contact company_id should be None")
            self.assertIsNone(result['job_id'], "Contact job_id should be None")
            self.assertIsNone(result['email'], "Contact email should be None")
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")

    def test_failure_creates_no_rows(self):
        # Check that db.create_contact does not create any rows in the contacts table when it raises an error.
        initial_count = self._count("contacts")
        # Attempt to create a contact with an invalid designation, which should raise a ValueError.
        with self.assertRaises(ValueError):
            db.create_contact(self.conn, self.user_a, name="Charlie Brown", designation="invalid_designation")
        # Check that the number of rows in the contacts table has not changed.
        self.assertEqual(self._count("contacts"), initial_count)

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
