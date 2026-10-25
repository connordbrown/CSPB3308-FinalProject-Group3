"""
Unit tests for the Prospex database schema (schema.sql).

Each test class covers one table, and each test maps to a numbered
"Table Tests" entry in SQL_TESTING.md (e.g. "Users #3"). Every test runs
against a fresh in-memory SQLite database, so tests never share data.

Run with:  python3 -m unittest tests.test_schema.py -v
"""

import os
import sqlite3
import unittest

# Resolve schema.sql relative to this file so tests run from any directory
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema.sql")

# Matches SQLite's CURRENT_TIMESTAMP format: "YYYY-MM-DD HH:MM:SS"
TIMESTAMP_REGEX = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"

# An id that will never exist in a fresh test database
NONEXISTENT_ID = 9999


class DatabaseTestCase(unittest.TestCase):
    """Base class: builds a fresh database for each test and provides insert helpers."""

    def setUp(self):
        # Connect to a fresh in-memory database
        self.conn = sqlite3.connect(":memory:")

        # SQLite ignores foreign keys unless this is turned on for every connection
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Build all tables from schema.sql
        with open(SCHEMA_PATH) as f:
            self.conn.executescript(f.read())

    def tearDown(self):
        self.conn.close()

    # ------------------------------------------------------------------
    # Helpers: insert one valid row with every column filled in and return
    # its id. Tests use these to set up rows they are NOT directly testing.
    # ------------------------------------------------------------------

    def _insert_default_user(self, email="ozzy@example.com", display_name="Ozzy"):
        return self.conn.execute(
            """
            INSERT INTO users (first_name, last_name, email, password_hash, display_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("John", "Osbourne", email, "fakehash1234", display_name),
        ).lastrowid

    def _insert_default_company(self, user_id, name="Black Sabbath"):
        return self.conn.execute(
            """
            INSERT INTO companies (user_id, name, city, region, website, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, "Birmingham", "UK", "blacksabbath.com", "Forever #1"),
        ).lastrowid

    def _insert_default_job(self, user_id, company_id):
        return self.conn.execute(
            """
            INSERT INTO jobs (user_id, company_id, title, link, work_type, notes, status, date_applied)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, company_id, "Singer", "https://fakelink.blacksabbath.com",
             "in person", "Singer wanted", "applied", "1968-01-01"),
        ).lastrowid

    def _insert_default_contact(self, user_id, company_id=None, job_id=None):
        return self.conn.execute(
            """
            INSERT INTO contacts (user_id, company_id, job_id, name, title, designation,
                                  email, phone, linkedin_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, company_id, job_id, "Geezer Butler", "Bassist", "hiring manager",
             "geezer@example.com", "555-666-7777", "https://linkedin.com/in/geezerbutler",
             "Some notes"),
        ).lastrowid

    def _count(self, table, where="1", params=()):
        """Return the number of rows in `table` matching the WHERE clause."""
        return self.conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {where}", params
        ).fetchone()[0]


class TestUsers(DatabaseTestCase):
    """Tests for the users table (SQL_TESTING.md, section 1)."""

    def test_insert_valid_user(self):
        """Users #1: Insert a valid user succeeds."""
        self.conn.execute(
            """
            INSERT INTO users (first_name, last_name, email, password_hash, display_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("John", "Osbourne", "ozzy@example.com", "fakehash1234", "Ozzy"),
        )

        row = self.conn.execute(
            """
            SELECT first_name, last_name, email, password_hash, display_name
            FROM users
            WHERE email = ?
            """,
            ("ozzy@example.com",),
        ).fetchone()

        # Every value we inserted should be stored unchanged
        self.assertIsNotNone(row, "user row not found")
        self.assertEqual(row[0], "John", "first_name not saved")
        self.assertEqual(row[1], "Osbourne", "last_name not saved")
        self.assertEqual(row[2], "ozzy@example.com", "email not saved")
        self.assertEqual(row[3], "fakehash1234", "password_hash not saved")
        self.assertEqual(row[4], "Ozzy", "display_name not saved")

    def test_insert_user_missing_email(self):
        """Users #2: Insert user with missing email fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL constraint failed: users.email"):
            self.conn.execute(
                """
                INSERT INTO users (first_name, last_name, password_hash, display_name)
                VALUES (?, ?, ?, ?)
                """,
                ("John", "Osbourne", "fakehash1234", "Ozzy"),
            )

    def test_insert_user_missing_name(self):
        """Users #3: Insert user with missing first_name or last_name fails."""
        # Missing first_name
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL constraint failed: users.first_name"):
            self.conn.execute(
                """
                INSERT INTO users (last_name, email, password_hash, display_name)
                VALUES (?, ?, ?, ?)
                """,
                ("Osbourne", "ozzy@example.com", "fakehash1234", "Ozzy"),
            )

        # Missing last_name
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL constraint failed: users.last_name"):
            self.conn.execute(
                """
                INSERT INTO users (first_name, email, password_hash, display_name)
                VALUES (?, ?, ?, ?)
                """,
                ("John", "ozzy@example.com", "fakehash1234", "Ozzy"),
            )

    def test_insert_user_missing_password(self):
        """Users #4: Insert user with missing password hash fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL constraint failed: users.password_hash"):
            self.conn.execute(
                """
                INSERT INTO users (first_name, last_name, email, display_name)
                VALUES (?, ?, ?, ?)
                """,
                ("John", "Osbourne", "ozzy@example.com", "Ozzy"),
            )

    def test_insert_user_existing_email(self):
        """Users #5: Insert user with an existing email fails, including the same email in different case."""
        self._insert_default_user(email="ozzy@example.com")

        # Exact same email
        with self.assertRaisesRegex(sqlite3.IntegrityError, "UNIQUE constraint failed: users.email"):
            self._insert_default_user(email="ozzy@example.com", display_name="Lemmy")

        # Same email, different case (email column is COLLATE NOCASE)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "UNIQUE constraint failed: users.email"):
            self._insert_default_user(email="Ozzy@Example.com", display_name="Lemmy")

        self.assertEqual(self._count("users"), 1, "duplicate email was saved")

    def test_id_timestamp_at_creation(self):
        """Users #6: New user gets an auto-generated id and created_at."""
        # Insert two users without supplying id or created_at
        self._insert_default_user(email="ozzy@example.com", display_name="Ozzy")
        self._insert_default_user(email="lemmy@example.com", display_name="Lemmy")

        row_1 = self.conn.execute(
            "SELECT id, created_at FROM users WHERE email = ?", ("ozzy@example.com",)
        ).fetchone()
        row_2 = self.conn.execute(
            "SELECT id, created_at FROM users WHERE email = ?", ("lemmy@example.com",)
        ).fetchone()

        # Each user gets its own integer id
        self.assertIsInstance(row_1[0], int, "id not generated as an integer")
        self.assertIsInstance(row_2[0], int, "id not generated as an integer")
        self.assertNotEqual(row_1[0], row_2[0], "same id generated for separate users")

        # Each user gets a created_at timestamp in SQLite's default format
        self.assertIsNotNone(row_1[1], "created_at not generated")
        self.assertIsNotNone(row_2[1], "created_at not generated")
        self.assertRegex(row_1[1], TIMESTAMP_REGEX, "created_at not in expected format")
        self.assertRegex(row_2[1], TIMESTAMP_REGEX, "created_at not in expected format")

    def test_cascade_on_delete_user(self):
        """Users #7: Deleting a user who has a company, job, and contact deletes all of them."""
        # Create one row in every table, all owned by the same user
        user_id = self._insert_default_user()
        company_id = self._insert_default_company(user_id=user_id)
        job_id = self._insert_default_job(user_id=user_id, company_id=company_id)
        self._insert_default_contact(user_id=user_id, company_id=company_id, job_id=job_id)

        # Before: one row per table
        self.assertEqual(self._count("users", "id = ?", (user_id,)), 1)
        self.assertEqual(self._count("companies", "user_id = ?", (user_id,)), 1)
        self.assertEqual(self._count("jobs", "user_id = ?", (user_id,)), 1)
        self.assertEqual(self._count("contacts", "user_id = ?", (user_id,)), 1)

        # Delete the user. This must succeed even though the job still points at the
        # company (jobs.company_id is NO ACTION, which is checked at end of statement).
        self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

        # After: every row owned by the user is gone
        self.assertEqual(self._count("users", "id = ?", (user_id,)), 0, "user not deleted")
        self.assertEqual(self._count("companies", "user_id = ?", (user_id,)), 0, "company not cascaded")
        self.assertEqual(self._count("jobs", "user_id = ?", (user_id,)), 0, "job not cascaded")
        self.assertEqual(self._count("contacts", "user_id = ?", (user_id,)), 0, "contact not cascaded")


class TestJobs(DatabaseTestCase):
    """Tests for the jobs table (SQL_TESTING.md, section 2)."""

    def setUp(self):
        # Every job needs an existing user and company
        super().setUp()
        self.user_id = self._insert_default_user()
        self.company_id = self._insert_default_company(user_id=self.user_id)

    def test_insert_valid_job(self):
        """Jobs #1: Insert a valid job succeeds."""
        job_id = self.conn.execute(
            """
            INSERT INTO jobs (user_id, company_id, title, link, work_type, notes, status, date_applied)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (self.user_id, self.company_id, "Singer", "https://fakelink.blacksabbath.com",
             "in person", "Singer wanted", "applied", "1968-01-01"),
        ).lastrowid

        row = self.conn.execute(
            """
            SELECT user_id, company_id, title, link, work_type, notes, status, date_applied
            FROM jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()

        # Every value we inserted should be stored unchanged
        self.assertIsNotNone(row, "job row not found")
        self.assertEqual(row[0], self.user_id, "user_id not saved")
        self.assertEqual(row[1], self.company_id, "company_id not saved")
        self.assertEqual(row[2], "Singer", "title not saved")
        self.assertEqual(row[3], "https://fakelink.blacksabbath.com", "link not saved")
        self.assertEqual(row[4], "in person", "work_type not saved")
        self.assertEqual(row[5], "Singer wanted", "notes not saved")
        self.assertEqual(row[6], "applied", "status not saved")
        self.assertEqual(row[7], "1968-01-01", "date_applied not saved")

    def test_insert_job_missing_title(self):
        """Jobs #2: Insert job with missing title fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL constraint failed: jobs.title"):
            self.conn.execute(
                """
                INSERT INTO jobs (user_id, company_id, link, work_type, notes, status, date_applied)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (self.user_id, self.company_id, "https://fakelink.blacksabbath.com",
                 "in person", "Singer wanted", "applied", "1968-01-01"),
            )

    def test_insert_job_missing_companyid(self):
        """Jobs #3: Insert job with missing company_id fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL constraint failed: jobs.company_id"):
            self.conn.execute(
                """
                INSERT INTO jobs (user_id, title, link, work_type, notes, status, date_applied)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (self.user_id, "Singer", "https://fakelink.blacksabbath.com",
                 "in person", "Singer wanted", "applied", "1968-01-01"),
            )

    def test_insert_job_nonexistent_companyid(self):
        """Jobs #4: Insert job with a company_id that doesn't exist fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY constraint failed"):
            self._insert_default_job(user_id=self.user_id, company_id=NONEXISTENT_ID)

    def test_insert_job_nonexistent_userid(self):
        """Jobs #5: Insert job with a user_id that doesn't exist fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY constraint failed"):
            self._insert_default_job(user_id=NONEXISTENT_ID, company_id=self.company_id)

    def test_insert_job_default_status(self):
        """Jobs #6: Insert job with no status gets 'saved' by default."""
        # status column is left out of the INSERT
        job_id = self.conn.execute(
            """
            INSERT INTO jobs (user_id, company_id, title, link, work_type, notes, date_applied)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (self.user_id, self.company_id, "Singer", "https://fakelink.blacksabbath.com",
             "in person", "Singer wanted", "1968-01-01"),
        ).lastrowid

        status = self.conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()[0]

        self.assertEqual(status, "saved", "status did not default to 'saved'")

    def test_insert_job_unlisted_status(self):
        """Jobs #7: Insert job with a status not on the list fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CHECK constraint failed"):
            self.conn.execute(
                """
                INSERT INTO jobs (user_id, company_id, title, link, work_type, notes, status, date_applied)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (self.user_id, self.company_id, "Singer", "https://fakelink.blacksabbath.com",
                 "in person", "Singer wanted", "appiled", "1968-01-01"),  # typo: "appiled"
            )

    def test_insert_job_unlisted_worktype(self):
        """Jobs #8: Insert job with a work_type not on the list fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CHECK constraint failed"):
            self.conn.execute(
                """
                INSERT INTO jobs (user_id, company_id, title, link, work_type, notes, status, date_applied)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (self.user_id, self.company_id, "Singer", "https://fakelink.blacksabbath.com",
                 "in persone", "Singer wanted", "applied", "1968-01-01"),  # typo: "in persone"
            )

    def test_insert_job_missing_nullable_fields(self):
        """Jobs #9: Insert job with no date_applied, link, notes, or work_type succeeds."""
        # Only required columns (plus status) are supplied
        job_id = self.conn.execute(
            """
            INSERT INTO jobs (user_id, company_id, title, status)
            VALUES (?, ?, ?, ?)
            """,
            (self.user_id, self.company_id, "Singer", "applied"),
        ).lastrowid

        row = self.conn.execute(
            "SELECT date_applied, link, notes, work_type FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

        # Row exists and every optional field was stored as NULL
        self.assertIsNotNone(row, "job row not found")
        self.assertIsNone(row[0], "date_applied should be NULL")
        self.assertIsNone(row[1], "link should be NULL")
        self.assertIsNone(row[2], "notes should be NULL")
        self.assertIsNone(row[3], "work_type should be NULL")

    def test_delete_job(self):
        """Jobs #10: Deleting a job keeps its contacts but clears their job_id (SET NULL)."""
        job_id = self._insert_default_job(user_id=self.user_id, company_id=self.company_id)
        contact_id = self._insert_default_contact(
            user_id=self.user_id, company_id=self.company_id, job_id=job_id
        )

        # Before: contact is linked to the job
        linked_job_id = self.conn.execute(
            "SELECT job_id FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()[0]
        self.assertEqual(linked_job_id, job_id, "contact not linked to job")

        self.conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))

        # After: job is gone, contact remains with job_id cleared and company_id untouched
        contact_row = self.conn.execute(
            "SELECT job_id, company_id FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()

        self.assertEqual(self._count("jobs", "id = ?", (job_id,)), 0, "job not deleted")
        self.assertIsNotNone(contact_row, "contact was deleted along with the job")
        self.assertIsNone(contact_row[0], "contact job_id not set to NULL")
        self.assertEqual(contact_row[1], self.company_id, "contact company_id changed by job deletion")


class TestContacts(DatabaseTestCase):
    """Tests for the contacts table (SQL_TESTING.md, section 3)."""

    def setUp(self):
        # Most contact tests need an existing user, company, and job to link to
        super().setUp()
        self.user_id = self._insert_default_user()
        self.company_id = self._insert_default_company(user_id=self.user_id)
        self.job_id = self._insert_default_job(user_id=self.user_id, company_id=self.company_id)

    def test_insert_valid_contact(self):
        """Contacts #1: Insert a valid contact succeeds."""
        contact_id = self.conn.execute(
            """
            INSERT INTO contacts (user_id, company_id, job_id, name, title, designation,
                                  email, phone, linkedin_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (self.user_id, self.company_id, self.job_id, "Geezer Butler", "Bassist",
             "hiring manager", "geezer@example.com", "+1 (555) 666-7777",
             "https://linkedin.com/in/geezerbutler", "Some notes"),
        ).lastrowid

        row = self.conn.execute(
            """
            SELECT user_id, company_id, job_id, name, title, designation,
                   email, phone, linkedin_url, notes
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        ).fetchone()

        # Every value we inserted should be stored unchanged
        self.assertIsNotNone(row, "contact row not found")
        self.assertEqual(row[0], self.user_id, "user_id not saved")
        self.assertEqual(row[1], self.company_id, "company_id not saved")
        self.assertEqual(row[2], self.job_id, "job_id not saved")
        self.assertEqual(row[3], "Geezer Butler", "name not saved")
        self.assertEqual(row[4], "Bassist", "title not saved")
        self.assertEqual(row[5], "hiring manager", "designation not saved")
        self.assertEqual(row[6], "geezer@example.com", "email not saved")
        # phone is TEXT so +, spaces, dashes, and parentheses are kept as typed
        self.assertEqual(row[7], "+1 (555) 666-7777", "phone not saved as text")
        self.assertEqual(row[8], "https://linkedin.com/in/geezerbutler", "linkedin_url not saved")
        self.assertEqual(row[9], "Some notes", "notes not saved")

    def test_insert_contact_missing_name(self):
        """Contacts #2: Insert contact with missing name fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL constraint failed: contacts.name"):
            self.conn.execute(
                """
                INSERT INTO contacts (user_id, company_id, job_id, title, designation,
                                      email, phone, linkedin_url, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (self.user_id, self.company_id, self.job_id, "Bassist", "hiring manager",
                 "geezer@example.com", "555-666-7777", "https://linkedin.com/in/geezerbutler",
                 "Some notes"),
            )

    def test_insert_contact_missing_nullables(self):
        """Contacts #3: Insert contact with only a name (no company, job, or contact info) succeeds."""
        contact_id = self.conn.execute(
            "INSERT INTO contacts (user_id, name) VALUES (?, ?)",
            (self.user_id, "Geezer Butler"),
        ).lastrowid

        row = self.conn.execute(
            """
            SELECT name, company_id, job_id, title, designation, email, phone, linkedin_url, notes
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        ).fetchone()

        # Row exists, name is saved, and every optional field is NULL
        self.assertIsNotNone(row, "contact row not found")
        self.assertEqual(row[0], "Geezer Butler", "name not saved")
        for column, value in zip(
            ["company_id", "job_id", "title", "designation", "email", "phone", "linkedin_url", "notes"],
            row[1:],
        ):
            self.assertIsNone(value, f"{column} should be NULL")

    def test_insert_contact_nonexistent_companyid(self):
        """Contacts #4: Insert contact with a company_id that doesn't exist fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY constraint failed"):
            self._insert_default_contact(
                user_id=self.user_id, company_id=NONEXISTENT_ID, job_id=self.job_id
            )

    def test_insert_contact_nonexistent_jobid(self):
        """Contacts #5: Insert contact with a job_id that doesn't exist fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY constraint failed"):
            self._insert_default_contact(
                user_id=self.user_id, company_id=self.company_id, job_id=NONEXISTENT_ID
            )

    def test_insert_contact_unlisted_designation(self):
        """Contacts #6: Insert contact with a designation not on the list fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "CHECK constraint failed"):
            self.conn.execute(
                """
                INSERT INTO contacts (user_id, company_id, job_id, name, title, designation,
                                      email, phone, linkedin_url, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (self.user_id, self.company_id, self.job_id, "Geezer Butler", "Bassist",
                 "hiring managers",  # typo: "hiring managers"
                 "geezer@example.com", "555-666-7777", "https://linkedin.com/in/geezerbutler",
                 "Some notes"),
            )

    def test_insert_contact_duplicate_email(self):
        """Contacts #7: Two contacts with the same email succeed (email is not unique)."""
        self.conn.execute(
            "INSERT INTO contacts (user_id, name, email) VALUES (?, ?, ?)",
            (self.user_id, "Geezer Butler", "recruiting@example.com"),
        )
        self.conn.execute(
            "INSERT INTO contacts (user_id, name, email) VALUES (?, ?, ?)",
            (self.user_id, "Tony Iommi", "recruiting@example.com"),
        )

        count = self._count("contacts", "email = ?", ("recruiting@example.com",))

        self.assertEqual(count, 2, "second contact with the same email was not saved")


class TestCompanies(DatabaseTestCase):
    """Tests for the companies table (SQL_TESTING.md, section 4)."""

    def setUp(self):
        # Every company needs an existing user
        super().setUp()
        self.user_id = self._insert_default_user()

    def test_insert_valid_company(self):
        """Companies #1: Insert a valid company succeeds."""
        company_id = self.conn.execute(
            """
            INSERT INTO companies (user_id, name, city, region, website, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (self.user_id, "Black Sabbath", "Birmingham", "UK", "blacksabbath.com", "Forever #1"),
        ).lastrowid

        row = self.conn.execute(
            """
            SELECT user_id, name, city, region, website, notes
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

        # Every value we inserted should be stored unchanged
        self.assertIsNotNone(row, "company row not found")
        self.assertEqual(row[0], self.user_id, "user_id not saved")
        self.assertEqual(row[1], "Black Sabbath", "name not saved")
        self.assertEqual(row[2], "Birmingham", "city not saved")
        self.assertEqual(row[3], "UK", "region not saved")
        self.assertEqual(row[4], "blacksabbath.com", "website not saved")
        self.assertEqual(row[5], "Forever #1", "notes not saved")

    def test_insert_company_missing_name(self):
        """Companies #2: Insert company with missing name fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "NOT NULL constraint failed: companies.name"):
            self.conn.execute(
                """
                INSERT INTO companies (user_id, city, region, website, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (self.user_id, "Birmingham", "UK", "blacksabbath.com", "Forever #1"),
            )

    def test_insert_company_nonexistent_userid(self):
        """Companies #3: Insert company with a user_id that doesn't exist fails."""
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY constraint failed"):
            self._insert_default_company(user_id=NONEXISTENT_ID)

    def test_insert_company_duplicate_name(self):
        """Companies #4: Insert a company name the same user already has fails, including different case."""
        self._insert_default_company(user_id=self.user_id, name="Black Sabbath")

        # Exact same name for the same user
        with self.assertRaisesRegex(sqlite3.IntegrityError, "UNIQUE constraint failed"):
            self._insert_default_company(user_id=self.user_id, name="Black Sabbath")

        # Same name in different case (name column is COLLATE NOCASE)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "UNIQUE constraint failed"):
            self._insert_default_company(user_id=self.user_id, name="black sabbath")

        self.assertEqual(self._count("companies"), 1, "duplicate company name was saved")

    def test_insert_same_company_multiple_users(self):
        """Companies #5: Two different users can each have a company with the same name."""
        user_2_id = self._insert_default_user(email="lemmy@example.com", display_name="Lemmy")

        self._insert_default_company(user_id=self.user_id, name="Black Sabbath")
        self._insert_default_company(user_id=user_2_id, name="Black Sabbath")

        count = self._count("companies", "name = ?", ("Black Sabbath",))

        self.assertEqual(count, 2, "same company name blocked for separate users")

    def test_company_generated_id(self):
        """Companies #6: New company gets an auto-generated id."""
        user_2_id = self._insert_default_user(email="lemmy@example.com", display_name="Lemmy")

        # Two companies for the first user, one for the second (no id supplied)
        ids = [
            self._insert_default_company(user_id=self.user_id, name="Black Sabbath"),
            self._insert_default_company(user_id=self.user_id, name="Motorhead"),
            self._insert_default_company(user_id=user_2_id, name="Judas Priest"),
        ]

        # Read the ids back from the table rather than trusting lastrowid
        stored_ids = [
            row[0] for row in self.conn.execute("SELECT id FROM companies ORDER BY id").fetchall()
        ]

        self.assertEqual(stored_ids, ids, "stored ids do not match generated ids")
        for company_id in stored_ids:
            self.assertIsInstance(company_id, int, "company id must be an integer")
        self.assertEqual(len(set(stored_ids)), 3, "generated company ids are not unique")

    def test_delete_company_with_jobs(self):
        """Companies #7: Deleting a company that still has jobs fails (NO ACTION)."""
        company_id = self._insert_default_company(user_id=self.user_id)
        self._insert_default_job(user_id=self.user_id, company_id=company_id)

        # Before: company and job both exist
        self.assertEqual(self._count("companies", "id = ?", (company_id,)), 1)
        self.assertEqual(self._count("jobs", "company_id = ?", (company_id,)), 1)

        # The job still references the company, so the delete is blocked
        with self.assertRaisesRegex(sqlite3.IntegrityError, "FOREIGN KEY constraint failed"):
            self.conn.execute("DELETE FROM companies WHERE id = ?", (company_id,))

        # After: nothing was removed
        self.assertEqual(self._count("companies", "id = ?", (company_id,)), 1, "company was deleted")
        self.assertEqual(self._count("jobs", "company_id = ?", (company_id,)), 1, "job was deleted")

    def test_delete_company_with_contacts(self):
        """Companies #8: Deleting a company with contacts (but no jobs) succeeds and sets their company_id to NULL."""
        company_id = self._insert_default_company(user_id=self.user_id)
        contact_id = self._insert_default_contact(user_id=self.user_id, company_id=company_id)

        # Before: contact is linked to the company
        linked_company_id = self.conn.execute(
            "SELECT company_id FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()[0]
        self.assertEqual(linked_company_id, company_id, "contact not linked to company")

        self.conn.execute("DELETE FROM companies WHERE id = ?", (company_id,))

        # After: company is gone, contact (and user) remain, contact's company_id is NULL
        self.assertEqual(self._count("companies", "id = ?", (company_id,)), 0, "company not deleted")
        self.assertEqual(self._count("users", "id = ?", (self.user_id,)), 1, "user was deleted")
        self.assertEqual(self._count("contacts", "id = ?", (contact_id,)), 1, "contact was deleted")

        linked_company_id = self.conn.execute(
            "SELECT company_id FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()[0]
        self.assertIsNone(linked_company_id, "contact company_id not set to NULL")


if __name__ == "__main__":
    unittest.main()
