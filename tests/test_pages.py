import unittest
import os
import sqlite3
import tempfile

from werkzeug.security import generate_password_hash
from app import app
import db
from tests.test_db import USER_A, USER_B, SCHEMA_PATH

class PageTestCase(unittest.TestCase):
    """Base class, sets up temporary db with users  A and B an a test client"""
    def setUp(self):
        # temp db for each test
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        app.config["DATABASE"] = self.db_path
        app.config["TESTING"] = True

        self.conn = db.get_connection(self.db_path)
        with open(SCHEMA_PATH) as f:
            self.conn.executescript(f.read())
        self.user_a = self._insert_user(**USER_A)
        self.user_b = self._insert_user(**USER_B)
        self.conn.commit()

        self.client = app.test_client()

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_path)

    # ------------------------------------------------------------------
    # Helpers we are re-using from test_db: insert one row with raw SQL and return its id. Pass keyword
    # arguments to override any column; the rest get valid defaults.
    # ------------------------------------------------------------------

    def _insert_user(self, first_name, last_name, email, password, display_name=None):
        # A low-cost hash method
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
        return self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]

    def _login(self, user=USER_A):
        return self.client.post("/login", data={
            "action": "login", "email": user["email"], "password": user["password"]
        })
    

class TestLogin(PageTestCase):
    """tests for /login """


    # 1. GET /login returns 200 and shows the form with both buttons.
    # def test_login_returns_200_and_buttons(self):
    #     return NotImplementedError

    # 2. Log in with a valid email and password (e.g., alex.demo@example.com / DemoPass123!) redirects to / and the session holds Alex's user_id.
    def test_valid_login_redirects_and_sets_session(self):
        response = self._login()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("user_id"), self.user_a)
    
    # 3. Log in with the right email in different case (ALEX.DEMO@example.com) succeeds.
    # def test_email_dif_case_works(self):
    #     return NotImplementedError
    
    # 4. Log in with a wrong password stays on /login, shows an error, and creates no session.
    # def test_wrong_pass_errors_changes_nothing(self):
    #     return NotImplementedError
    
    # 5. Log in with an unknown email gives the same generic error as test 4, so the page doesn't reveal which emails exist.
    # def test_unknown_email_doesnt_reveal_data(self):
    #     return NotImplementedError
    
    # 6. Sign up with valid fields creates one new users row, logs the user in, and redirects to /.
    # 7. The new row's password_hash is a hash, not the plain password.
    # 8. Sign up with an email that already exists (including different case) stays on /login, shows an error, and adds no row.
    # 9. Sign up with a missing first_name, last_name, or password shows an error and adds no row.
    # 10. Sign up with a display_name already in use shows an error and adds no row.
    # 11. Two sign-ups with a blank display_name both succeed (stored as NULL).
    # 12. A logged-in user who opens /login is redirected to /.
    # 13. /logout clears the session; the nav bar goes back to its logged-out state.




if __name__ == '__main__':
    unittest.main()