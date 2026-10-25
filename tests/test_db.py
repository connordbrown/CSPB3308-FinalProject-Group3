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

from werkzeug.security import generate_password_hash, check_password_hash

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
 
    def test_returns_user_fields(self):
        result = db.get_user_by_email(self.conn, USER_A["email"])
        self.assertEqual(result["id"], self.user_a)
        self.assertEqual(result["first_name"], USER_A["first_name"])
        self.assertEqual(result["last_name"], USER_A["last_name"])
        self.assertEqual(result["email"], USER_A["email"])
        self.assertEqual(result["display_name"], USER_A["display_name"])
 
    def test_returns_password_hash_that_verifies_the_password(self):
        # The login route checks this hash, so it must be the stored one.
        result = db.get_user_by_email(self.conn, USER_A["email"])
        self.assertTrue(check_password_hash(result["password_hash"], USER_A["password"]))
        self.assertFalse(check_password_hash(result["password_hash"], USER_B["password"]))
 
    def test_returns_only_the_documented_columns(self):
        result = db.get_user_by_email(self.conn, USER_A["email"])
        expected = {"id", "first_name", "last_name", "email", "password_hash", "display_name"}
        self.assertSetEqual(set(result.keys()), expected)
 
    def test_returns_the_user_with_that_email_when_there_are_several(self):
        result_a = db.get_user_by_email(self.conn, USER_A["email"])
        result_b = db.get_user_by_email(self.conn, USER_B["email"])
        self.assertEqual(result_a["id"], self.user_a)
        self.assertEqual(result_b["id"], self.user_b)
 
    def test_match_is_case_insensitive(self):
        # Needs email to be COLLATE NOCASE in schema.sql
        for email in (USER_A["email"].upper(), "Alex.Demo@Example.com"):
            with self.subTest(email=email):
                result = db.get_user_by_email(self.conn, email)
                self.assertIsNotNone(result)
                self.assertEqual(result["id"], self.user_a)
 
    def test_user_without_display_name_has_none(self):
        user_id = self._insert_user("Marcus", "Lee", "marcus.demo@example.com", "MarcusPass789!")
        result = db.get_user_by_email(self.conn, "marcus.demo@example.com")
        self.assertEqual(result["id"], user_id)
        self.assertIsNone(result["display_name"])
 
    def test_returns_none_if_email_not_found(self):
        self.assertIsNone(db.get_user_by_email(self.conn, "nobody@example.com"))
 
    def test_returns_none_for_empty_email(self):
        for email in ("", None):
            with self.subTest(email=email):
                self.assertIsNone(db.get_user_by_email(self.conn, email))
 
    def test_only_exact_emails_match(self):
        # Partial emails and wildcard characters must not match anyone
        for email in ("alex.demo", "alex.demo@example", "%", "alex.demo@example.co", "%@example.com"):
            with self.subTest(email=email):
                self.assertIsNone(db.get_user_by_email(self.conn, email))
 
    def test_sql_in_email_is_treated_as_plain_text(self):
        email = USER_A["email"] + "' OR '1'='1"
        self.assertIsNone(db.get_user_by_email(self.conn, email))
        self.assertEqual(self._count("users"), 2, "Users table should be untouched")

class TestGeneratePasswordHash(AccessTestCase):
    """Tests for db.generate_password_hash (SQL_TESTING.md, Access Method: generate_password_hash)."""
 
    def test_returns_a_nonempty_string(self):
        result = db.generate_password_hash("DemoPass123!")
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "", "Hash should not be empty")
 
    def test_hash_is_not_the_plain_password(self):
        password = "DemoPass123!"
        result = db.generate_password_hash(password)
        self.assertNotEqual(result, password, "Hash must not equal the plain password")
        self.assertNotIn(password, result, "Hash must not contain the plain password")
 
    def test_hash_verifies_only_with_the_original_password(self):
        password = "DemoPass123!"
        result = db.generate_password_hash(password)
        self.assertTrue(check_password_hash(result, password))
        self.assertFalse(check_password_hash(result, "WrongPass123!"))
        # Passwords are case sensitive
        self.assertFalse(check_password_hash(result, password.lower()))
 
    def test_same_password_gives_different_hashes(self):
        # Each hash is salted, so two hashes of one password differ but both still verify.
        password = "DemoPass123!"
        hash_1 = db.generate_password_hash(password)
        hash_2 = db.generate_password_hash(password)
        self.assertNotEqual(hash_1, hash_2, "Hashes should be salted")
        self.assertTrue(check_password_hash(hash_1, password))
        self.assertTrue(check_password_hash(hash_2, password))
 
    def test_handles_unicode_and_long_passwords(self):
        for password in ["p\u00e4ssw\u00f6rd\U0001F511", "a" * 200]:
            with self.subTest(length=len(password)):
                result = db.generate_password_hash(password)
                self.assertTrue(check_password_hash(result, password))
 
    def test_empty_or_non_string_password_raises_value_error(self):
        for password in ["", None, 123, [], {}, True]:
            with self.subTest(password=password):
                with self.assertRaises(ValueError):
                    db.generate_password_hash(password)

class TestCreateUser(AccessTestCase):
    """Tests for db.create_user (SQL_TESTING.md, Access Method: create_user)."""
 
    def _new_user_args(self, **overrides):
        """Valid arguments for a user who is not one of the seeded users A and B."""
        args = {
            "first_name": "Jamie",
            "last_name": "Fox",
            "email": "jamie.fox@example.com",
            "password_hash": "not-a-real-hash-value",
            "display_name": "jamie_f",
        }
        args.update(overrides)
        return args
 
    def test_returns_new_user_id_and_saves_fields(self):
        user_id = db.create_user(self.conn, **self._new_user_args())
        self.assertIsInstance(user_id, int)
        row = self._fetch("users", user_id)
        self.assertIsNotNone(row, "Row was not saved")
        self.assertEqual(row["first_name"], "Jamie")
        self.assertEqual(row["last_name"], "Fox")
        self.assertEqual(row["email"], "jamie.fox@example.com")
        self.assertEqual(row["display_name"], "jamie_f")
 
    def test_new_user_gets_new_id_and_created_at(self):
        user_id = db.create_user(self.conn, **self._new_user_args())
        self.assertNotIn(user_id, (self.user_a, self.user_b))
        self.assertIsNotNone(self._fetch("users", user_id)["created_at"])
 
    def test_stores_given_password_hash_unchanged(self):
        # create_user must not hash again: the route already hashed the password.
        user_id = db.create_user(self.conn, **self._new_user_args(password_hash="already-hashed-value"))
        self.assertEqual(self._fetch("users", user_id)["password_hash"], "already-hashed-value")
 
    def test_display_name_is_optional(self):
        args = self._new_user_args()
        del args["display_name"]
        user_id = db.create_user(self.conn, **args)
        self.assertIsNone(self._fetch("users", user_id)["display_name"])
 
    def test_empty_display_name_is_stored_as_null(self):
        for i, display_name in enumerate(["", "   "]):
            with self.subTest(display_name=display_name):
                user_id = db.create_user(
                    self.conn, **self._new_user_args(email=f"blank{i}@example.com", display_name=display_name)
                )
                self.assertIsNone(self._fetch("users", user_id)["display_name"])
 
    def test_two_users_without_display_name_succeed(self):
        # display_name is UNIQUE, but NULL is not a duplicate of NULL.
        id_1 = db.create_user(self.conn, **self._new_user_args(email="one@example.com", display_name=None))
        id_2 = db.create_user(self.conn, **self._new_user_args(email="two@example.com", display_name=None))
        self.assertNotEqual(id_1, id_2)
 
    def test_same_name_with_different_email_succeeds(self):
        user_id = db.create_user(
            self.conn,
            **self._new_user_args(first_name=USER_A["first_name"], last_name=USER_A["last_name"], display_name=None),
        )
        self.assertIsNotNone(self._fetch("users", user_id))
 
    def test_missing_required_field_raises_value_error(self):
        for field in ("first_name", "last_name", "email", "password_hash"):
            for bad_value in ("", "   ", None, 123):
                with self.subTest(field=field, value=bad_value):
                    with self.assertRaises(ValueError):
                        db.create_user(self.conn, **self._new_user_args(**{field: bad_value}))
 
    def test_invalid_input_adds_no_row(self):
        before = self._count("users")
        with self.assertRaises(ValueError):
            db.create_user(self.conn, **self._new_user_args(first_name=""))
        self.assertEqual(self._count("users"), before)
 
    def test_duplicate_email_raises_integrity_error(self):
        with self.assertRaises(sqlite3.IntegrityError):
            db.create_user(self.conn, **self._new_user_args(email=USER_A["email"]))
 
    def test_duplicate_email_in_different_case_raises_integrity_error(self):
        # Needs email to be COLLATE NOCASE in schema.sql
        with self.assertRaises(sqlite3.IntegrityError):
            db.create_user(self.conn, **self._new_user_args(email=USER_A["email"].upper()))
 
    def test_duplicate_display_name_raises_integrity_error(self):
        with self.assertRaises(sqlite3.IntegrityError):
            db.create_user(self.conn, **self._new_user_args(display_name=USER_B["display_name"]))
 
    def test_duplicate_failure_adds_no_row_and_leaves_connection_usable(self):
        before = self._count("users")
        with self.assertRaises(sqlite3.IntegrityError):
            db.create_user(self.conn, **self._new_user_args(email=USER_A["email"]))
        self.assertEqual(self._count("users"), before)
        # The route shows an error and carries on, so a valid signup must still work afterwards.
        user_id = db.create_user(self.conn, **self._new_user_args())
        self.assertIsNotNone(self._fetch("users", user_id))


class TestGetUser(AccessTestCase):
    """Tests for db.get_user (SQL_TESTING.md, Access Method: get_user)."""
    def test_returns_correct_user(self):
        result = db.get_user(self.conn, self.user_a)
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], self.user_a)
        self.assertEqual(result["first_name"], USER_A["first_name"])
        self.assertEqual(result["last_name"], USER_A["last_name"])
        self.assertEqual(result["display_name"], USER_A["display_name"])
        self.assertEqual(result["email"], USER_A["email"])
        self.assertIsNotNone(result["created_at"])

    def returns_the_user_requested(self):
        result = db.get_user(self.conn, self.user_b)
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], self.user_b)

    # check no password hash included
    def test_returns_no_extra_info(self):
        result = db.get_user(self.conn, self.user_a)
        self.assertSetEqual(set(result.keys()), {
            "id",
            "first_name",
            "last_name",
            "email",
            "display_name",
            "created_at"
        })

    def test_returns_none_if_no_user(self):
        result = db.get_user(self.conn, NONEXISTENT_ID)
        self.assertIsNone(result)


class TestUpdateUser(AccessTestCase):
    """Tests for db.update_user (SQL_TESTING.md, Access Method: update_user)."""
    def test_false_if_no_user(self):
        result = db.update_user(self.conn, NONEXISTENT_ID, "New_First_Name", "New_last_name", "new.email@bob.com")
        self.assertFalse(result)

    def test_updates_fields(self):
        result = db.update_user(self.conn, self.user_a, "New_First_Name", "New_last_name", "new.email@bob.com")
        self.assertTrue(result)
        updated_user = self._fetch("users", self.user_a)
        self.assertEqual(updated_user["first_name"], "New_First_Name")
        self.assertEqual(updated_user["last_name"], "New_last_name")
        self.assertEqual(updated_user["email"], "new_email")

    def test_only_changes_target_user(self):
        db.update_user(self.conn, self.user_a, "New_First_Name", "New_last_name", "new.email@bob.com")
        unchanged_user = self._fetch("users", self.user_b)
        self.assertEqual(unchanged_user["first_name"], USER_B["first_name"])
        self.assertEqual(unchanged_user["last_name"], USER_B["last_name"])
        self.assertEqual(unchanged_user["email"], USER_B["email"])

    def test_unchanged_email_succeeds(self):
        result = db.update_user(self.conn, self.user_a, "New_First_Name", "New_last_name", USER_A["email"])
        self.assertTrue(result)
        updated_user = self._fetch("users", self.user_a)
        self.assertEqual(updated_user["first_name"], "New_First_Name")
        self.assertEqual(updated_user["last_name"], "New_last_name")
        self.assertEqual(updated_user["email"], USER_A["email"])

    def test_blank_name_error(self):
        for blank in ["", " ", None]:
            with self.subTest(first_name=blank):
                with self.assertRaises(ValueError):
                    db.update_user(self.conn, self.user_a, blank, USER_A["last_name"], USER_A["email"])
            with self.subTest(last_name=blank):
                with self.assertRaises(ValueError):
                    db.update_user(self.conn, self.user_a, USER_A["first_name"], blank, USER_A["email"])
    
    def test_duplicated_email(self):
        for dup in [USER_B["email"], USER_B["email"].upper()]:
            with self.subTest(email=dup):
                with self.assertRaises(sqlite3.IntegrityError):
                    db.update_user(self.conn, self.user_a, USER_A["first_name"], USER_A["last_name"], dup)

    def test_fail_does_not_change_user(self):
        with self.assertRaises(sqlite3.IntegrityError):
            db.update_user(self.conn, self.user_a, USER_A["first_name"], USER_A["last_name"], USER_B["email"])
        
        updated_user = self._fetch("users", self.user_a)
        self.assertEqual(updated_user["email"], USER_A["email"])

    def test_hash_unchanged(self):
        before = self._fetch("users", self.user_a)["password_hash"]
        db.update_user(self.conn, self.user_a, "Bob", "Smith", "bobsmith@bob.com")
        after = self._fetch("users", self.user_a)["password_hash"]

        self.assertEqual(before, after)


class TestChangePassword(AccessTestCase):
    """Tests for db.change_password (SQL_TESTING.md, Access Method: change_password)."""


# ---------- Jobs ----------

class TestGetJob(AccessTestCase):
    """Tests for db.get_job (SQL_TESTING.md, Access Method: get_job)."""
 
    def setUp(self):
        super().setUp()
        # One fully filled job for user A and one job for user B
        self.company_a = self._insert_company(self.user_a, name="Acme Corp", city="Denver", region="CO")
        self.job_a = self._insert_job(
            self.user_a, self.company_a, title="Junior Backend Developer", status="interviewing",
            work_type="hybrid", link="https://www.acme-example.com/careers/junior-backend",
            notes="Python and Flask stack.", date_applied="2026-09-10",
        )
        self.company_b = self._insert_company(self.user_b, name="Beta Ltd", city="Seattle", region="WA")
        self.job_b = self._insert_job(self.user_b, self.company_b, title="Data Analyst")
 
    def test_returns_job_fields(self):
        result = db.get_job(self.conn, self.user_a, self.job_a)
        self.assertEqual(result["id"], self.job_a)
        self.assertEqual(result["title"], "Junior Backend Developer")
        self.assertEqual(result["status"], "interviewing")
        self.assertEqual(result["work_type"], "hybrid")
        self.assertEqual(result["link"], "https://www.acme-example.com/careers/junior-backend")
        self.assertEqual(result["notes"], "Python and Flask stack.")
        self.assertEqual(result["date_applied"], "2026-09-10")
 
    def test_returns_company_fields(self):
        result = db.get_job(self.conn, self.user_a, self.job_a)
        self.assertEqual(result["company_id"], self.company_a)
        self.assertEqual(result["company_name"], "Acme Corp")
        self.assertEqual(result["city"], "Denver")
        self.assertEqual(result["region"], "CO")
 
    def test_returns_only_the_documented_columns(self):
        result = db.get_job(self.conn, self.user_a, self.job_a)
        expected = {"id", "title", "status", "work_type", "link", "notes", "date_applied",
                    "company_id", "company_name", "city", "region"}
        self.assertSetEqual(set(result.keys()), expected)
 
    def test_returns_the_requested_job_when_user_has_several(self):
        other_company = self._insert_company(self.user_a, name="Northwind")
        other_job = self._insert_job(self.user_a, other_company, title="Data Analyst")
        first = db.get_job(self.conn, self.user_a, self.job_a)
        second = db.get_job(self.conn, self.user_a, other_job)
        self.assertEqual((first["title"], first["company_name"]), ("Junior Backend Developer", "Acme Corp"))
        self.assertEqual((second["title"], second["company_name"]), ("Data Analyst", "Northwind"))
 
    def test_empty_optional_fields_are_none(self):
        # A job with only the required fields, at a company with no location
        bare_company = self._insert_company(self.user_a, name="Summit Cloud")
        bare_job = self._insert_job(self.user_a, bare_company, title="Support Engineer")
        result = db.get_job(self.conn, self.user_a, bare_job)
        self.assertEqual(result["title"], "Support Engineer")
        self.assertEqual(result["status"], "saved", "Status should default to 'saved'")
        for column in ("work_type", "link", "notes", "date_applied", "city", "region"):
            with self.subTest(column=column):
                self.assertIsNone(result[column])
 
    def test_returns_none_if_job_does_not_exist(self):
        self.assertIsNone(db.get_job(self.conn, self.user_a, NONEXISTENT_ID))
 
    def test_returns_none_if_job_belongs_to_another_user(self):
        # User A cannot see user B's job, but user B can.
        self.assertIsNone(db.get_job(self.conn, self.user_a, self.job_b))
        self.assertIsNotNone(db.get_job(self.conn, self.user_b, self.job_b))
 
    def test_returns_none_if_user_does_not_exist(self):
        self.assertIsNone(db.get_job(self.conn, NONEXISTENT_ID, self.job_a))


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
    def test_updates_contact(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job, and update the contact's attributes using db.update_contact.
        company_id = self._insert_company(self.user_a, name="Acme Corp")
        job_id = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id)
        contact_id = self._insert_contact(
            self.user_a, name="Charlie Brown", title="Developer", designation="recruiter", email="charlie.brown@example.com", company_id=company_id, job_id=job_id
        )
        # Update the contact's attributes.
        update = db.update_contact(
            self.conn, self.user_a, contact_id, name="Charlie Brown Jr.", title="Senior Developer", designation="recruiter", email="charlie.brown.jr@example.com"
        )
        self.assertTrue(update, "Expected update_contact to return True for successful update")
        # Check that the contact's attributes have been updated in the database.
        result = db.get_contact(self.conn, self.user_a, contact_id)
        self.assertEqual(result['name'], "Charlie Brown Jr.", "Contact name was not updated")
        self.assertEqual(result['title'], "Senior Developer", "Contact title was not updated")
        self.assertEqual(result['email'], "charlie.brown.jr@example.com", "Contact email was not updated")

    def test_nonexistent_contact(self):
        # Check that db.update_contact returns False when attempting to update a non-existent contact.
        update = db.update_contact(
            self.conn, self.user_a, NONEXISTENT_ID, name="Nonexistent Contact", title="N/A", designation="recruiter"
        )
        self.assertFalse(update, "Expected update_contact to return False for non-existent contact")

    def test_contact_belongs_to_another_user(self):
        # Check that db.update_contact returns False when attempting to update a contact that belongs to another user.
        # Insert a company and a job for user B, then insert a contact for user B linked to that job.
        company_id_b = self._insert_company(self.user_b, name="Beta Ltd")
        job_id_b = self._insert_job(self.user_b, title="Product Manager", company_id=company_id_b)
        contact_id_b = self._insert_contact(
            self.user_b, name="David Wilson", title="Analyst", designation="recruiter", email="david.wilson@example.com", company_id=company_id_b, job_id=job_id_b
        )
        # Attempt to update the contact that belongs to user B using user A's credentials.
        update = db.update_contact(
            self.conn, self.user_a, contact_id_b, name="Updated Contact", title="Updated Title", designation="other"
        )
        self.assertFalse(update, "Expected update_contact to return False for contact belonging to another user")


    def test_contact_belongs_to_user_after_update(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job.
        company_id_a = self._insert_company(self.user_a, name="Alpha Inc")
        job_id_a = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id_a)
        contact_id_a = self._insert_contact(
            self.user_a, name="Alice Smith", title="Developer", designation="recruiter", email="alice.smith@example.com", company_id=company_id_a, job_id=job_id_a
        )
        # Update the contact that belongs to user A.
        update = db.update_contact(
            self.conn, self.user_a, contact_id_a, name="Updated Alice Smith", title="Senior Developer", designation="other"
        )
        self.assertTrue(update, "Expected update_contact to return True for successful update")
        # Check that the contact still belongs to user A after the update.
        result = db.get_contact(self.conn, self.user_a, contact_id_a)
        self.assertEqual(result['user_id'], self.user_a, "Contact does not belong to the correct user after update")        

    def test_only_updates_target_contact(self):
        # Insert a company and a job for user A, then insert two contacts for user A linked to that job.
        company_id_a = self._insert_company(self.user_a, name="Alpha Inc")
        job_id_a = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id_a)
        contact_id_1 = self._insert_contact(
            self.user_a, name="Alice Smith", title="Developer", designation="recruiter", email="alice.smith@example.com", company_id=company_id_a, job_id=job_id_a
        )
        contact_id_2 = self._insert_contact(
            self.user_a, name="Bob Johnson", title="Analyst", designation="recruiter", email="bob.johnson@example.com", company_id=company_id_a, job_id=job_id_a
        )
        # Update only the first contact.
        update = db.update_contact(
            self.conn, self.user_a, contact_id_1, name="Updated Alice Smith", title="Senior Developer", designation="other"
        )
        self.assertTrue(update, "Expected update_contact to return True for successful update")
        # Check that the first contact has been updated.
        result_1 = db.get_contact(self.conn, self.user_a, contact_id_1)
        self.assertEqual(result_1['name'], "Updated Alice Smith", "First contact was not updated")
        # Check that the second contact has not been updated.
        result_2 = db.get_contact(self.conn, self.user_a, contact_id_2)
        self.assertEqual(result_2['name'], "Bob Johnson", "Second contact was incorrectly updated")

    def test_empty_or_invalid_updated_name(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job.
        company_id_a = self._insert_company(self.user_a, name="Alpha Inc")
        job_id_a = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id_a)
        contact_id_a = self._insert_contact(
            self.user_a, name="Alice Smith", title="Developer", designation="recruiter", email="alice.smith@example.com", company_id=company_id_a, job_id=job_id_a
        )
        # Check that db.update_contact raises a ValueError when the updated name is not a string.
        invalid_data_type = [123, [], {}, True, False]
        for type in invalid_data_type:
            with self.subTest(type=type):
                with self.assertRaises(ValueError):
                    db.update_contact(self.conn, self.user_a, contact_id_a, name=type, title="Senior Developer", designation="other")

        # Check that db.update_contact raises an error when the updated name is empty.
        with self.assertRaises(ValueError):
            db.update_contact(self.conn, self.user_a, contact_id_a, name="", title="Senior Developer", designation="other")
        with self.assertRaises(ValueError):
            db.update_contact(self.conn, self.user_a, contact_id_a, name=None, title="Senior Developer", designation="other")

    def test_updated_designation_invalid(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job.
        company_id_a = self._insert_company(self.user_a, name="Alpha Inc")
        job_id_a = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id_a)
        contact_id_a = self._insert_contact(
            self.user_a, name="Alice Smith", title="Developer", designation="recruiter", email="alice.smith@example.com", company_id=company_id_a, job_id=job_id_a
        )
        # Check that db.update_contact raises a ValueError when the updated designation is not in the allowed set of values.
        invalid_designations = ["invalid", "manager", 123, [], {}, True, False]
        for designation in invalid_designations:
            with self.subTest(designation=designation):
                with self.assertRaises(ValueError):
                    db.update_contact(self.conn, self.user_a, contact_id_a, name="Alice Smith", title="Senior Developer", designation=designation)

    def test_updated_job_id_does_not_belong_to_user(self):
        # Insert a company and a job for user B.
        company_id_b = self._insert_company(self.user_b, name="Beta Corp")
        job_id_b = self._insert_job(self.user_b, title="Data Analyst", company_id=company_id_b)
        # Insert a contact for user A.
        contact_id_a = self._insert_contact(
            self.user_a, name="Alice Smith", title="Developer", designation="recruiter", email="alice.smith@example.com"
        )
        # Check that db.update_contact raises a ValueError when the updated job ID does not belong to the user.
        with self.assertRaises(ValueError):
            db.update_contact(self.conn, self.user_a, contact_id_a, name="Alice Smith", title="Senior Developer", designation="other", job_id=job_id_b)

    def test_Updated_company_id_does_not_belong_to_user(self):
        # Insert a company for user B.
        company_id_b = self._insert_company(self.user_b, name="Beta Corp")
        # Insert a contact for user A.
        contact_id_a = self._insert_contact(
            self.user_a, name="Alice Smith", title="Developer", designation="recruiter", email="alice.smith@example.com"
        )
        # Check that db.update_contact raises a ValueError when the updated company ID does not belong to the user.
        with self.assertRaises(ValueError):
            db.update_contact(self.conn, self.user_a, contact_id_a, name="Alice Smith", title="Senior Developer", designation="other", company_id=company_id_b)

    def test_succeeds_with_name_only(self):
        # Check that db.update_contact succeeds when only the name is provided, and other optional fields are omitted.
        # Insert a contact for user A.
        contact_id_a = self._insert_contact(
            self.user_a, name="Alice Smith", title="Developer", designation="recruiter", email="alice.smith@example.com"
        )
        # Check that db.update_contact succeeds when only the name is provided, and other optional fields are omitted.
        db.update_contact(self.conn, self.user_a, contact_id_a, name="Alice Johnson")

    def test_failure_leaves_contact_unchanged(self):
        # Insert a company and a job for user A, then insert a contact for user A linked to that job.
        company_id_a = self._insert_company(self.user_a, name="Alpha Inc")
        job_id_a = self._insert_job(self.user_a, title="Software Engineer", company_id=company_id_a)
        contact_id_a = self._insert_contact(
            self.user_a, name="Alice Smith", title="Developer", designation="recruiter", email="alice.smith@example.com", company_id=company_id_a, job_id=job_id_a
        )
        # Attempt to update the contact with an invalid designation, which should raise a ValueError.
        with self.assertRaises(ValueError):
            db.update_contact(self.conn, self.user_a, contact_id_a, name="Alice Smith", title="Senior Developer", designation="invalid_designation")
        # Check that the contact's attributes have not changed.
        result = db.get_contact(self.conn, self.user_a, contact_id_a)
        self.assertEqual(result['name'], "Alice Smith", "Contact name should not have changed")
        self.assertEqual(result['title'], "Developer", "Contact title should not have changed")
        self.assertEqual(result['designation'], "recruiter", "Contact designation should not have changed")
        self.assertEqual(result['email'], "alice.smith@example.com", "Contact email should not have changed")
        self.assertEqual(result['company_id'], company_id_a, "Contact company_id should not have changed")
        self.assertEqual(result['job_id'], job_id_a, "Contact job_id should not have changed")


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
